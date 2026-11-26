
import os
import csv
import math

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

# =====================================================
# 2. INITIALIZE VALIDATION
# =====================================================

print("======================================")
print("ML DATASET QUALITY VALIDATION")
print("======================================")

total = 0
positive = 0
unlabelled = 0
duplicate_ids = 0

seen_ids = set()
statistics = {}

# =====================================================
# 3. READ DATASET
# =====================================================

with open(
    input_file,
    "r",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    columns = reader.fieldnames

    predictors = [
        column for column in columns
        if column.endswith("_mean")
    ]

    for name in predictors:

        statistics[name] = {
            "count": 0,
            "missing": 0,
            "invalid": 0,
            "minimum": float("inf"),
            "maximum": float("-inf"),
            "sum": 0.0,
            "unique": set()
        }

    # =================================================
    # 4. VALIDATE EACH ROW
    # =================================================

    for row in reader:

        total += 1

        fid = row["fid"]

        if fid in seen_ids:
            duplicate_ids += 1

        seen_ids.add(fid)

        if row["label"] == "1":
            positive += 1
        elif row["label"] == "":
            unlabelled += 1
        else:
            raise Exception(
                "Unexpected label: " + str(row["label"])
            )

        for name in predictors:

            value = row[name]

            if value is None or value.strip() == "":
                statistics[name]["missing"] += 1
                continue

            try:
                number = float(value)

                if not math.isfinite(number):
                    statistics[name]["invalid"] += 1
                    continue

                item = statistics[name]

                item["count"] += 1
                item["minimum"] = min(item["minimum"], number)
                item["maximum"] = max(item["maximum"], number)
                item["sum"] += number
                item["unique"].add(number)

            except ValueError:
                statistics[name]["invalid"] += 1

# =====================================================
# 5. DISPLAY GENERAL SUMMARY
# =====================================================

print("\nGENERAL DATASET SUMMARY")
print("--------------------------------------")

print("Total rows:", total)
print("Predictors:", len(predictors))
print("Known positives:", positive)
print("Unlabelled:", unlabelled)
print("Duplicate IDs:", duplicate_ids)

# =====================================================
# 6. DISPLAY PREDICTOR QUALITY
# =====================================================

print("\nPREDICTOR QUALITY SUMMARY")
print("--------------------------------------")

for name, item in statistics.items():

    if item["count"] > 0:
        mean = item["sum"] / item["count"]
        minimum = item["minimum"]
        maximum = item["maximum"]
        unique = len(item["unique"])
    else:
        mean = minimum = maximum = "N/A"
        unique = 0

    print(
        name,
        "| Min:", minimum,
        "| Max:", maximum,
        "| Mean:", mean,
        "| Unique:", unique,
        "| Missing:", item["missing"],
        "| Invalid:", item["invalid"]
    )

# =====================================================
# 7. FINAL CHECKS
# =====================================================

print("\nFINAL VALIDATION")
print("--------------------------------------")

if total != 112179:
    raise Exception("Unexpected row count.")

if len(predictors) != 31:
    raise Exception("Expected 31 predictors.")

if positive != 16 or unlabelled != 112163:
    raise Exception("Label distribution mismatch.")

if duplicate_ids != 0:
    raise Exception("Duplicate feature IDs detected.")

bad_predictors = [
    name for name, item in statistics.items()
    if (
        item["missing"] > 0
        or item["invalid"] > 0
        or item["count"] != total
        or len(item["unique"]) <= 1
    )
]

print("Predictors requiring attention:", bad_predictors)

if bad_predictors:
    raise Exception("Predictor quality checks failed.")

print("\nML DATASET QUALITY VALIDATION COMPLETED")
