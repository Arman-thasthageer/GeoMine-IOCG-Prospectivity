
import os
import csv

from qgis.core import QgsVectorLayer

# =====================================================
# 1. PROJECT PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "geological_features_spatial_blocks.gpkg"
)

config_file = os.path.join(
    project_dir,
    "config",
    "predictor_config.csv"
)

output_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "ml_training_dataset.csv"
)

# =====================================================
# 2. LOAD SPATIAL DATASET
# =====================================================

print("======================================")
print("ML DATASET PREPARATION")
print("======================================")

layer = QgsVectorLayer(
    input_file,
    "spatial_blocks",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load spatial block dataset.")

print("Input grid cells:", layer.featureCount())

# =====================================================
# 3. LOAD PREDICTOR CONFIGURATION
# =====================================================

print("\nLoading predictor configuration...")

predictors = []

with open(
    config_file,
    "r",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    required_columns = [
        "criterion_code",
        "feature_field",
        "IOCG_Comprehensive"
    ]

    for column in required_columns:
        if column not in reader.fieldnames:
            raise Exception(
                "Missing configuration column: " + column
            )

    for row in reader:

        if row["IOCG_Comprehensive"].strip().upper() == "Y":

            predictors.append({
                "criterion_code": row["criterion_code"].strip(),
                "feature_field": row["feature_field"].strip()
            })

if len(predictors) != 31:
    raise Exception(
        "Expected 31 Comprehensive predictors. Found: "
        + str(len(predictors))
    )

feature_fields = [
    item["feature_field"]
    for item in predictors
]

print("Comprehensive predictors:", len(feature_fields))

# =====================================================
# 4. VALIDATE PREDICTOR FIELDS
# =====================================================

available_fields = [
    field.name()
    for field in layer.fields()
]

missing_fields = [
    field
    for field in feature_fields
    if field not in available_fields
]

if missing_fields:
    raise Exception(
        "Missing predictor fields: "
        + str(missing_fields)
    )

print("All 31 predictor fields are available.")

# =====================================================
# 5. DEFINE OUTPUT COLUMNS
# =====================================================

output_columns = [
    "fid",
    "label",
    "block_id"
] + feature_fields

# =====================================================
# 6. EXPORT ML DATASET
# =====================================================

print("\nExporting ML dataset...")

os.makedirs(
    os.path.dirname(output_file),
    exist_ok=True
)

total = 0
positive = 0
unlabelled = 0

with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=output_columns
    )

    writer.writeheader()

    for feature in layer.getFeatures():

        label_value = feature["label"]

        if label_value == 1:

            label = 1
            positive += 1

        elif str(label_value) in ("NULL", "None", ""):

            # Preserve positive-unlabelled semantics.
            # Unlabelled cells are NOT negative labels.
            label = ""
            unlabelled += 1

        else:
            raise Exception(
                "Unexpected label value: "
                + str(label_value)
            )

        row = {
            "fid": feature["fid"],
            "label": label,
            "block_id": feature["block_id"]
        }

        for field_name in feature_fields:

            value = feature[field_name]

            if value is None or str(value) == "NULL":
                raise Exception(
                    "Missing predictor value: "
                    + field_name
                )

            row[field_name] = value

        writer.writerow(row)
        total += 1

# =====================================================
# 7. FINAL VALIDATION
# =====================================================

print("\n======================================")
print("ML DATASET VALIDATION")
print("======================================")

print("Total cells:", total)
print("Predictor count:", len(feature_fields))
print("Known positive cells:", positive)
print("Unlabelled cells:", unlabelled)
print("Confirmed negative cells: 0")

print("\nOutput file:")
print(output_file)

if total != 112179:
    raise Exception("Unexpected total cell count.")

if positive != 16:
    raise Exception("Expected 16 known positive cells.")

if unlabelled != 112163:
    raise Exception("Unexpected unlabelled cell count.")

print("\nML DATASET PREPARATION COMPLETED")
