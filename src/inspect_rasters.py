
import csv
from pathlib import Path
from osgeo import gdal, osr

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
RASTER_DIR = PROJECT_DIR / "data" / "raw" / "input_rasters"
OUTPUT_DIR = PROJECT_DIR / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

output_file = OUTPUT_DIR / "raster_inventory.csv"

# Find all input GeoTIFF files
raster_files = sorted(RASTER_DIR.rglob("*.tif"))

columns = [
    "filename",
    "component",
    "crs",
    "width",
    "height",
    "bands",
    "pixel_size_x",
    "pixel_size_y",
    "data_type",
    "nodata",
    "minimum",
    "maximum",
    "mean",
    "stddev",
    "extent"
]

rows = []

for raster_path in raster_files:
    dataset = gdal.Open(str(raster_path))

    if dataset is None:
        print(f"Could not open: {raster_path.name}")
        continue

    transform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()

    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromWkt(projection)

    crs = spatial_ref.GetAuthorityCode(None)

    band = dataset.GetRasterBand(1)
    stats = band.GetStatistics(True, True)

    filename = raster_path.stem
    prefix = filename.split("_")[0]

    if prefix.startswith("S"):
        component = "Sources"
    elif prefix.startswith("D"):
        component = "Energy"
    elif prefix.startswith("P"):
        component = "Pathways"
    elif prefix.startswith("T"):
        component = "Deposition"
    else:
        component = "Reference"

    nodata = band.GetNoDataValue()

    row = {
        "filename": raster_path.name,
        "component": component,
        "crs": crs,
        "width": dataset.RasterXSize,
        "height": dataset.RasterYSize,
        "bands": dataset.RasterCount,
        "pixel_size_x": transform[1],
        "pixel_size_y": transform[5],
        "data_type": gdal.GetDataTypeName(band.DataType),
        "nodata": nodata,
        "minimum": stats[0] if stats else None,
        "maximum": stats[1] if stats else None,
        "mean": stats[2] if stats else None,
        "stddev": stats[3] if stats else None,
        "extent": str(dataset.GetGeoTransform())
    }

    rows.append(row)

    print(f"Inspected: {raster_path.name}")

    dataset = None

# Write CSV report
with open(output_file, "w", newline="", encoding="utf-8-sig") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print("\nInspection completed!")
print(f"Total rasters found: {len(raster_files)}")
print(f"Total rasters inspected: {len(rows)}")
print(f"Report saved to: {output_file}")
