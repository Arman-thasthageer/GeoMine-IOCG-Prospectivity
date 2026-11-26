
import os
import csv
from collections import defaultdict

from qgis.core import QgsVectorLayer

# =====================================================
# 1. PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "geological_features_spatial_blocks.gpkg"
)

output_file = os.path.join(
    project_dir,
    "reports",
    "positive_block_distribution.csv"
)

# =====================================================
# 2. LOAD DATA
# =====================================================

print("======================================")
print("POSITIVE SPATIAL BLOCK ANALYSIS")
print("======================================")

layer = QgsVectorLayer(
    input_file,
    "spatial_blocks",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load spatial block dataset.")

print("Total grid cells:", layer.featureCount())

# =====================================================
# 3. COUNT POSITIVE CELLS BY BLOCK
# =====================================================

block_data = defaultdict(lambda: {
    "total_cells": 0,
    "positive_cells": 0
})

for feature in layer.getFeatures():

    block_id = str(feature["block_id"])

    block_data[block_id]["total_cells"] += 1

    if feature["label"] == 1:
        block_data[block_id]["positive_cells"] += 1

# =====================================================
# 4. FILTER POSITIVE BLOCKS
# =====================================================

positive_blocks = {
    block_id: values
    for block_id, values in block_data.items()
    if values["positive_cells"] > 0
}

# =====================================================
# 5. SAVE CSV
# =====================================================

os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)

    writer.writerow([
        "block_id",
        "total_grid_cells",
        "known_deposit_cells"
    ])

    for block_id, values in sorted(positive_blocks.items()):

        writer.writerow([
            block_id,
            values["total_cells"],
            values["positive_cells"]
        ])

# =====================================================
# 6. DISPLAY RESULTS
# =====================================================

print("\nPOSITIVE BLOCK DISTRIBUTION")
print("--------------------------------------")

for block_id, values in sorted(positive_blocks.items()):

    print(
        block_id,
        "| Total cells:", values["total_cells"],
        "| Known deposits:", values["positive_cells"]
    )

print("\nTotal spatial blocks:", len(block_data))
print("Blocks containing deposits:", len(positive_blocks))
print(
    "Known deposit cells:",
    sum(v["positive_cells"] for v in positive_blocks.values())
)

print("\nOutput:", output_file)
print("\nPOSITIVE BLOCK ANALYSIS COMPLETED")
