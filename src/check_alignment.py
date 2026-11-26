
from pathlib import Path
from osgeo import gdal
import math

project_dir = Path(__file__).resolve().parent.parent
raster_dir = project_dir / "data" / "raw" / "input_rasters"

files = sorted(raster_dir.rglob("*.tif"))

reference = None
aligned = []
not_aligned = []

for path in files:
    ds = gdal.Open(str(path))

    current = {
        "name": path.name,
        "width": ds.RasterXSize,
        "height": ds.RasterYSize,
        "transform": ds.GetGeoTransform(),
        "projection": ds.GetProjection()
    }

    if reference is None:
        reference = current
        aligned.append(path.name)
        ds = None
        continue

    same_dimensions = (
        current["width"] == reference["width"]
        and current["height"] == reference["height"]
    )

    same_transform = all(
        math.isclose(a, b, rel_tol=0, abs_tol=1e-10)
        for a, b in zip(
            current["transform"],
            reference["transform"]
        )
    )

    same_crs = current["projection"] == reference["projection"]

    if same_dimensions and same_transform and same_crs:
        aligned.append(path.name)
    else:
        not_aligned.append({
            "name": path.name,
            "dimensions_match": same_dimensions,
            "transform_match": same_transform,
            "crs_match": same_crs,
            "transform": current["transform"]
        })

    ds = None

print("REFERENCE RASTER:", reference["name"])
print("REFERENCE TRANSFORM:", reference["transform"])
print("TOTAL RASTERS:", len(files))
print("ALIGNED RASTERS:", len(aligned))
print("NOT ALIGNED:", len(not_aligned))

for item in not_aligned:
    print("\nMISMATCH:", item)
