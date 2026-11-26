
import os
import csv

# =====================================================
# 1. PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "reports",
    "positive_block_distribution.csv"
)

output_file = os.path.join(
    project_dir,
    "reports",
    "spatial_validation_folds.csv"
)

# =====================================================
# 2. LOAD POSITIVE BLOCKS
# =====================================================

print("======================================")
print("SPATIAL VALIDATION FOLD CREATION")
print("======================================")

positive_blocks = []

with open(input_file, "r", encoding="utf-8") as file:

    reader = csv.DictReader(file)

    for row in reader:

        positive_blocks.append({
            "block_id": row["block_id"],
            "total_cells": int(row["total_grid_cells"]),
            "positive_cells": int(row["known_deposit_cells"])
        })

if len(positive_blocks) != 4:
    raise Exception(
        "Expected 4 positive blocks. Found: "
        + str(len(positive_blocks))
    )

# =====================================================
# 3. CREATE LEAVE-ONE-POSITIVE-BLOCK-OUT FOLDS
# =====================================================

folds = []

for index, test_block in enumerate(positive_blocks, start=1):

    for block in positive_blocks:

        if block["block_id"] == test_block["block_id"]:
            role = "TEST"
        else:
            role = "TRAIN"

        folds.append({
            "fold_id": index,
            "block_id": block["block_id"],
            "role": role,
            "total_cells": block["total_cells"],
            "known_deposit_cells": block["positive_cells"]
        })

# =====================================================
# 4. SAVE FOLD ASSIGNMENTS
# =====================================================

os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "fold_id",
            "block_id",
            "role",
            "total_cells",
            "known_deposit_cells"
        ]
    )

    writer.writeheader()
    writer.writerows(folds)

# =====================================================
# 5. DISPLAY VALIDATION PLAN
# =====================================================

print("\nVALIDATION FOLD SUMMARY")
print("--------------------------------------")

for index, test_block in enumerate(positive_blocks, start=1):

    training_positives = sum(
        block["positive_cells"]
        for block in positive_blocks
        if block["block_id"] != test_block["block_id"]
    )

    print(
        "Fold:", index,
        "| Test block:", test_block["block_id"],
        "| Test deposits:", test_block["positive_cells"],
        "| Training deposits:", training_positives
    )

print("\nTotal folds:", len(positive_blocks))
print("Total fold assignments:", len(folds))
print("Validation method: Leave-one-positive-block-out")

print("\nOutput:", output_file)
print("\nFOLD CREATION COMPLETED")
