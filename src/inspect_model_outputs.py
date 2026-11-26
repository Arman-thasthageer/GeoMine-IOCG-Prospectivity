
import os
import csv
from qgis.core import QgsVectorLayer

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

print("=" * 60)
print("MODEL OUTPUT INSPECTION")
print("=" * 60)

# Inspect GeoPackage layers and their fields
gpkg_files = [
    (
        "Expert baseline",
        os.path.join(
            BASE, "data", "processed",
            "iocg_prospectivity_v4.gpkg"
        ),
        "iocg_prospectivity_v4"
    ),
    (
        "GA baseline",
        os.path.join(
            BASE, "data", "processed",
            "ga_baseline_grid.gpkg"
        ),
        "ga_baseline_grid"
    ),
    (
        "Spatial blocks / labels",
        os.path.join(
            BASE, "data", "processed",
            "geological_features_spatial_blocks.gpkg"
        ),
        "geological_features_spatial_blocks"
    )
]

for title, path, layer_name in gpkg_files:
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)

    if not os.path.exists(path):
        print("FILE NOT FOUND:", path)
        continue

    layer = QgsVectorLayer(
        path + "|layername=" + layer_name,
        layer_name,
        "ogr"
    )

    if not layer.isValid():
        print("LAYER COULD NOT BE OPENED")
        continue

    print("Feature count:", layer.featureCount())
    print("Fields:")

    for field in layer.fields():
        print(" -", field.name(), "|", field.typeName())

# Inspect CSV headers in reports folder
reports_dir = os.path.join(BASE, "reports")

print("\n" + "=" * 60)
print("REPORT CSV FILES")
print("=" * 60)

for filename in sorted(os.listdir(reports_dir)):
    if not filename.lower().endswith(".csv"):
        continue

    path = os.path.join(reports_dir, filename)

    print("\nFile:", filename)

    try:
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, [])

        print("Columns:", header)

    except Exception as e:
        print("Could not inspect:", str(e))

print("\n" + "=" * 60)
print("INSPECTION COMPLETED")
print("=" * 60)
