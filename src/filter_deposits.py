
from pathlib import Path
from osgeo import ogr
import csv

project_dir = Path(__file__).resolve().parent.parent

deposit_file = (
    project_dir / "data" / "processed" /
    "iocg_deposits_review.csv"
)

boundary_file = (
    project_dir / "data" / "raw" / "baseline_maps" /
    "IOCG_Prospectivity" / "TISA_Investigation_Area" /
    "TISA_Investigation_Area.shp"
)

output_dir = project_dir / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

inside_file = output_dir / "iocg_deposits_inside_study_area.csv"
outside_file = output_dir / "iocg_deposits_outside_study_area.csv"

ogr.UseExceptions()

# Load study-area polygon
boundary_ds = ogr.Open(str(boundary_file))
boundary_layer = boundary_ds.GetLayer(0)

boundary_feature = boundary_layer.GetNextFeature()
boundary_geometry = boundary_feature.GetGeometryRef().Clone()

# Read original deposit records
inside_records = []
outside_records = []

with open(deposit_file, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    for record in reader:
        longitude = float(record["Longitude"])
        latitude = float(record["Latitude"])

        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(longitude, latitude)

        if boundary_geometry.Intersects(point):
            inside_records.append(record)
            status = "INSIDE"
        else:
            outside_records.append(record)
            status = "OUTSIDE"

        print(
            status,
            "|",
            record["Deposit"],
            "|",
            longitude,
            latitude
        )

# Save both groups separately
fieldnames = list(inside_records[0].keys()) if inside_records else []

for path, records in [
    (inside_file, inside_records),
    (outside_file, outside_records)
]:
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

print("\n========== SUMMARY ==========")
print("Total deposits:", len(inside_records) + len(outside_records))
print("Inside study area:", len(inside_records))
print("Outside study area:", len(outside_records))
print("Inside CSV:", inside_file)
print("Outside CSV:", outside_file)
