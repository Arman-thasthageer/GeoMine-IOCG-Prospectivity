
import os
import csv
from collections import Counter

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

PREDICTION_FILE = os.path.join(
    BASE, "outputs", "pu_spatial_cv_predictions.csv"
)

MODEL_DIR = os.path.join(BASE, "models")
OUTPUT_DIR = os.path.join(BASE, "outputs")

print("=" * 65)
print("PU MODEL ARTEFACT AND PREDICTION COVERAGE INSPECTION")
print("=" * 65)

# --------------------------------------------------
# 1. Inspect saved model files
# --------------------------------------------------

print("\n1. SAVED MODEL FILES")
print("-" * 65)

if os.path.exists(MODEL_DIR):
    files_found = []

    for root, dirs, files in os.walk(MODEL_DIR):
        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, BASE)
            size_mb = os.path.getsize(full_path) / (1024 * 1024)

            files_found.append(relative_path)

            print(
                relative_path,
                "| Size:",
                round(size_mb, 3),
                "MB"
            )

    if not files_found:
        print("No saved model files found.")
else:
    print("Models directory not found.")

# --------------------------------------------------
# 2. Inspect output files
# --------------------------------------------------

print("\n2. OUTPUT DIRECTORY FILES")
print("-" * 65)

if os.path.exists(OUTPUT_DIR):
    for filename in sorted(os.listdir(OUTPUT_DIR)):
        path = os.path.join(OUTPUT_DIR, filename)

        if os.path.isfile(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)

            print(
                filename,
                "| Size:",
                round(size_mb, 3),
                "MB"
            )
else:
    print("Outputs directory not found.")

# --------------------------------------------------
# 3. Inspect spatial CV prediction CSV
# --------------------------------------------------

print("\n3. SPATIAL CV PREDICTION COVERAGE")
print("-" * 65)

if not os.path.exists(PREDICTION_FILE):
    print("Prediction CSV not found:", PREDICTION_FILE)

else:
    with open(
        PREDICTION_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames

    print("Columns:", columns)
    print("Total prediction records:", len(rows))

    if rows:
        required_columns = {
            "fold_id",
            "fid",
            "block_id",
            "label",
            "pu_score",
            "repetitions"
        }

        missing = required_columns - set(columns or [])

        if missing:
            print("Missing expected columns:", sorted(missing))

        else:
            unique_cells = len(set(row["fid"] for row in rows))
            unique_blocks = sorted(
                set(row["block_id"] for row in rows)
            )

            print("Unique grid cells:", unique_cells)
            print("Blocks represented:", unique_blocks)

            print("\nRecords by validation block:")

            block_counts = Counter(
                row["block_id"] for row in rows
            )

            for block_id, count in sorted(block_counts.items()):
                print(block_id, ":", count, "records")

            print("\nKnown positive and unlabelled records:")

            label_counts = Counter(
                row["label"] for row in rows
            )

            for label, count in label_counts.items():
                print(repr(label), ":", count)

            print("\nPrediction score range:")

            scores = [
                float(row["pu_score"])
                for row in rows
                if row["pu_score"] not in ("", None)
            ]

            if scores:
                print("Minimum:", min(scores))
                print("Maximum:", max(scores))
                print("Mean:", sum(scores) / len(scores))

            print("\nRepetition counts:")

            repetition_counts = Counter(
                row["repetitions"] for row in rows
            )

            for repetitions, count in repetition_counts.items():
                print(repetitions, ":", count)

# --------------------------------------------------
# 4. Inspect relevant configuration files
# --------------------------------------------------

print("\n4. ML CONFIGURATION FILES")
print("-" * 65)

config_files = [
    os.path.join(BASE, "config", "pu_learning_config.json"),
    os.path.join(BASE, "config", "predictor_config.json")
]

for path in config_files:
    if os.path.exists(path):
        print("FOUND:", os.path.relpath(path, BASE))
    else:
        print("NOT FOUND:", os.path.relpath(path, BASE))

print("\n" + "=" * 65)
print("INSPECTION COMPLETED")
print("=" * 65)
