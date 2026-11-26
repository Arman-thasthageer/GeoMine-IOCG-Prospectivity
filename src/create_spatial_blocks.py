
import os
import csv
import processing

from qgis.core import (
    QgsVectorLayer,
    QgsProject
)

# =====================================================
# 1. PROJECT PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "geological_features.gpkg"
)

output_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "geological_features_spatial_blocks.gpkg"
)

summary_file = os.path.join(
    project_dir,
    "reports",
    "spatial_block_summary.csv"
)

# =====================================================
# 2. SETTINGS
# =====================================================

block_size = 50000  # 50 km in metres

print("======================================")
print("50 KM SPATIAL BLOCK CREATION")
print("======================================")

# =====================================================
# 3. LOAD INPUT GRID
# =====================================================

print("\nLoading geological features...")

input_layer = QgsVectorLayer(
    input_file + "|layername=geological_features",
    "geological_features",
    "ogr"
)

if not input_layer.isValid():
    raise Exception("Input geological features layer could not be loaded.")

print("Grid cells:", input_layer.featureCount())
print("CRS:", input_layer.crs().authid())

if input_layer.crs().authid() != "EPSG:3577":
    raise Exception("Input layer must use EPSG:3577.")

# =====================================================
# 4. CREATE 50 KM BLOCK ID FIELD
# =====================================================

print("\nCalculating spatial block IDs...")

expression = """
concat(
    'B_',
    to_string(floor(x(centroid($geometry)) / 50000)),
    '_',
    to_string(floor(y(centroid($geometry)) / 50000))
)
"""

if os.path.exists(output_file):
    os.remove(output_file)

result = processing.run(
    "native:fieldcalculator",
    {
        "INPUT": input_layer,
        "FIELD_NAME": "block_id",
        "FIELD_TYPE": 2,
        "FIELD_LENGTH": 40,
        "FIELD_PRECISION": 0,
        "FORMULA": expression,
        "OUTPUT": output_file
    }
)

print("Spatial block field created.")

# =====================================================
# 5. LOAD OUTPUT
# =====================================================

print("\nLoading spatial block output...")

output_layer = QgsVectorLayer(
    output_file + "|layername=geological_features_spatial_blocks",
    "geological_features_spatial_blocks",
    "ogr"
)

if not output_layer.isValid():
    # If the provider chose a different layer name,
    # load the GeoPackage directly.
    output_layer = QgsVectorLayer(
        output_file,
        "geological_features_spatial_blocks",
        "ogr"
    )

if not output_layer.isValid():
    raise Exception("Output GeoPackage could not be loaded.")

# =====================================================
# 6. VALIDATE BLOCK ASSIGNMENT
# =====================================================

print("\nValidating spatial blocks...")

block_counts = {}
total_cells = 0
known_deposit_cells = 0
missing_blocks = 0

for feature in output_layer.getFeatures():

    total_cells += 1

    block_id = feature["block_id"]

    if block_id is None or str(block_id) in ("", "NULL"):
        missing_blocks += 1
        continue

    if block_id not in block_counts:
        block_counts[block_id] = {
            "cells": 0,
            "known_deposits": 0
        }

    block_counts[block_id]["cells"] += 1

    if feature["label"] == 1:
        block_counts[block_id]["known_deposits"] += 1
        known_deposit_cells += 1

# =====================================================
# 7. SAVE BLOCK SUMMARY CSV
# =====================================================

os.makedirs(os.path.dirname(summary_file), exist_ok=True)

with open(
    summary_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "block_id",
        "cells",
        "known_deposit_cells"
    ])

    for block_id in sorted(block_counts):

        values = block_counts[block_id]

        writer.writerow([
            block_id,
            values["cells"],
            values["known_deposits"]
        ])

# =====================================================
# 8. FINAL VALIDATION
# =====================================================

positive_blocks = sum(
    1 for values in block_counts.values()
    if values["known_deposits"] > 0
)

print("\n======================================")
print("SPATIAL BLOCK SUMMARY")
print("======================================")

print("Total grid cells:", total_cells)
print("Block size:", block_size, "metres")
print("Total spatial blocks:", len(block_counts))
print("Blocks containing known deposits:", positive_blocks)
print("Known deposit cells:", known_deposit_cells)
print("Missing block IDs:", missing_blocks)

print("\nOUTPUT FILES")
print("--------------------------------------")
print("GeoPackage:", output_file)
print("Summary CSV:", summary_file)

if total_cells != input_layer.featureCount():
    raise Exception("Grid cell count mismatch.")

if missing_blocks > 0:
    raise Exception("Some cells do not have a block ID.")

if known_deposit_cells != 16:
    raise Exception("Expected 16 known deposit cells. Check labels.")

print("\nSPATIAL BLOCK CREATION COMPLETED")
