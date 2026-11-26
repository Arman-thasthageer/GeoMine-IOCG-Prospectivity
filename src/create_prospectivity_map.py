
from pathlib import Path
import json
import numpy as np
from osgeo import gdal, osr
from PIL import Image

gdal.UseExceptions()
osr.UseExceptions()

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE = Path(r"C:\Users\Ermus\Desktop\GeoMine")

INPUT = BASE / "data" / "processed" / "final_pu_prospectivity.gpkg"

RASTER = BASE / "data" / "processed" / "pu_prospectivity.tif"

PNG = BASE / "app" / "public" / "prospectivity.png"

BOUNDS = BASE / "app" / "public" / "prospectivity_bounds.json"

# --------------------------------------------------
# STEP 1: OPEN INPUT DATA
# --------------------------------------------------

print("=" * 60)
print("GEOMINE PROSPECTIVITY MAP GENERATION")
print("=" * 60)

print("\nOpening prospectivity GeoPackage...")

ds = gdal.OpenEx(str(INPUT), gdal.OF_VECTOR)

if ds is None:
    raise RuntimeError(f"Cannot open input file: {INPUT}")

layer = ds.GetLayerByName("final_pu_prospectivity")

if layer is None:
    raise RuntimeError("Layer final_pu_prospectivity not found.")

feature_count = layer.GetFeatureCount()

extent = layer.GetExtent()

xmin, xmax, ymin, ymax = extent

print("Layer:", layer.GetName())
print("Features:", feature_count)
print("Extent:", extent)

# --------------------------------------------------
# STEP 2: CREATE GEOTIFF
# --------------------------------------------------

pixel_size = 2000

width = int(np.ceil((xmax - xmin) / pixel_size))
height = int(np.ceil((ymax - ymin) / pixel_size))

print("\nCreating raster...")
print("Raster width:", width)
print("Raster height:", height)

driver = gdal.GetDriverByName("GTiff")

out = driver.Create(
    str(RASTER),
    width,
    height,
    1,
    gdal.GDT_Float32,
    options=["COMPRESS=LZW"]
)

if out is None:
    raise RuntimeError("Unable to create GeoTIFF.")

out.SetGeoTransform(
    (xmin, pixel_size, 0, ymax, 0, -pixel_size)
)

source_srs = layer.GetSpatialRef()

if source_srs is None:
    raise RuntimeError("Input layer CRS is missing.")

out.SetProjection(source_srs.ExportToWkt())

band = out.GetRasterBand(1)

band.SetNoDataValue(-9999)
band.Fill(-9999)

print("Rasterizing PU scores...")

gdal.RasterizeLayer(
    out,
    [1],
    layer,
    options=["ATTRIBUTE=pu_score"]
)

band.FlushCache()
out.FlushCache()

scores = band.ReadAsArray()

valid = np.isfinite(scores) & (scores != -9999)

if not np.any(valid):
    raise RuntimeError("No valid prospectivity scores found.")

# --------------------------------------------------
# STEP 3: CREATE COLOUR-CODED PNG
# --------------------------------------------------

print("\nGenerating colour-coded PNG...")

stops = [
    (0.00, (35, 70, 180)),
    (0.25, (40, 170, 220)),
    (0.50, (245, 220, 65)),
    (0.75, (245, 125, 40)),
    (1.00, (190, 25, 35))
]

rgba = np.zeros(
    (height, width, 4),
    dtype=np.uint8
)

# Use vectorised interpolation for faster processing.

values = np.clip(scores[valid], 0, 1)

for channel in range(3):

    channel_values = np.interp(
        values,
        [stop[0] for stop in stops],
        [stop[1][channel] for stop in stops]
    )

    rgba[valid, channel] = channel_values.astype(np.uint8)

rgba[valid, 3] = 220

Image.fromarray(rgba, "RGBA").save(PNG)

# --------------------------------------------------
# STEP 4: CALCULATE CORRECT MAP BOUNDS
# --------------------------------------------------

print("\nCalculating geographic map bounds...")

target_srs = osr.SpatialReference()

target_srs.ImportFromEPSG(4326)

# Important: enforce traditional GIS order:
# X = longitude, Y = latitude.

source_srs.SetAxisMappingStrategy(
    osr.OAMS_TRADITIONAL_GIS_ORDER
)

target_srs.SetAxisMappingStrategy(
    osr.OAMS_TRADITIONAL_GIS_ORDER
)

transform = osr.CoordinateTransformation(
    source_srs,
    target_srs
)

corners = [
    transform.TransformPoint(xmin, ymin),
    transform.TransformPoint(xmin, ymax),
    transform.TransformPoint(xmax, ymin),
    transform.TransformPoint(xmax, ymax)
]

longitudes = [point[0] for point in corners]
latitudes = [point[1] for point in corners]

bounds_data = {
    "south": min(latitudes),
    "west": min(longitudes),
    "north": max(latitudes),
    "east": max(longitudes)
}

# Validate Australian study-area coordinates.

if not (
    -30 < bounds_data["south"] < -10
    and -30 < bounds_data["north"] < -10
    and 120 < bounds_data["west"] < 150
    and 120 < bounds_data["east"] < 150
):
    raise RuntimeError(
        f"Unexpected geographic bounds: {bounds_data}"
    )

BOUNDS.write_text(
    json.dumps(bounds_data, indent=2),
    encoding="utf-8"
)

# --------------------------------------------------
# STEP 5: CLOSE DATASETS
# --------------------------------------------------

out = None
ds = None

# --------------------------------------------------
# STEP 6: FINAL REPORT
# --------------------------------------------------

print("\n" + "=" * 60)
print("PROSPECTIVITY MAP GENERATED SUCCESSFULLY")
print("=" * 60)

print("\nGeoTIFF:")
print(RASTER)

print("\nPNG:")
print(PNG)

print("\nMap bounds:")
print(json.dumps(bounds_data, indent=2))

print("\nScore minimum:", float(np.min(scores[valid])))
print("Score maximum:", float(np.max(scores[valid])))
print("Valid raster pixels:", int(np.sum(valid)))

print("\nAll output files generated successfully.")
