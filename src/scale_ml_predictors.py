
import os
import csv

# =====================================================
# 1. PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "ml_training_dataset.csv"
)

output_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "ml_training_dataset_scaled.csv"
)

# =====================================================
# 2. LOAD DATA
# =====================================================

print("======================================")
print("ML PREDICTOR SCALING")
print("======================================")

rows = []

with open(input_file, "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    columns = reader.fieldnames

    predictors = [
        column for column in columns
        if column.endswith("_mean")
    ]

    for row in reader:
        rows.append(row)

if len(predictors) != 31:
    raise Exception("Expected 31 predictors.")

print("Total records:", len(rows))
print("Predictors:", len(predictors))

# =====================================================
# 3. CALCULATE MINIMUM AND MAXIMUM
# =====================================================

print("\nCalculating predictor ranges...")

ranges = {}

for predictor in predictors:

    values = [float(row[predictor]) for row in rows]

    minimum = min(values)
    maximum = max(values)

    if maximum == minimum:
        raise Exception(
            "Constant predictor: " + predictor
        )

    ranges[predictor] = {
        "min": minimum,
        "max": maximum
    }

# =====================================================
# 4. MIN-MAX SCALING
# =====================================================

print("\nApplying Min-Max scaling...")

for row in rows:

    for predictor in predictors:

        value = float(row[predictor])

        minimum = ranges[predictor]["min"]
        maximum = ranges[predictor]["max"]

        scaled_value = (
            (value - minimum) / (maximum - minimum)
        )

        row[predictor] = scaled_value

# =====================================================
# 5. SAVE SCALED DATASET
# =====================================================

with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=columns
    )

    writer.writeheader()
    writer.writerows(rows)

# =====================================================
# 6. VALIDATION
# =====================================================

print("\nSCALING VALIDATION")
print("--------------------------------------")

for predictor in predictors:

    values = [float(row[predictor]) for row in rows]

    print(
        predictor,
        "| Min:", min(values),
        "| Max:", max(values)
    )

print("\nOutput:", output_file)
print("\nML PREDICTOR SCALING COMPLETED")
