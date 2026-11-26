
import os
import sys
import csv
import joblib
import numpy as np

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

ML_PACKAGES = os.path.join(BASE, "ml_packages")
if ML_PACKAGES not in sys.path:
    sys.path.insert(0, ML_PACKAGES)

PREDICTION_FILE = os.path.join(
    BASE, "outputs", "final_pu_prospectivity.csv"
)

MODEL_FILE = os.path.join(
    BASE, "models",
    "final_pu_random_forest_ensemble.joblib"
)

print("=" * 65)
print("FINAL PU MODEL OUTPUT VALIDATION")
print("=" * 65)

# --------------------------------------------------
# 1. Validate prediction CSV
# --------------------------------------------------

with open(
    PREDICTION_FILE,
    "r",
    newline="",
    encoding="utf-8-sig"
) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("\nPREDICTION CSV")
print("-" * 50)

print("Total records:", len(rows))

required = {
    "fid", "block_id", "label",
    "pu_score", "model_repetitions"
}

missing = required - set(rows[0].keys()) if rows else required

if missing:
    raise ValueError("Missing columns: " + str(missing))

fids = [int(row["fid"]) for row in rows]
scores = np.array(
    [float(row["pu_score"]) for row in rows],
    dtype=float
)

labels = [row["label"].strip() for row in rows]

positive_count = sum(label == "1" for label in labels)
unlabelled_count = sum(label == "" for label in labels)

print("Unique grid cells:", len(set(fids)))
print("Known positive cells:", positive_count)
print("Unlabelled cells:", unlabelled_count)

print("Missing scores:", int(np.isnan(scores).sum()))
print("Non-finite scores:", int((~np.isfinite(scores)).sum()))

print("Minimum score:", float(scores.min()))
print("Maximum score:", float(scores.max()))
print("Mean score:", float(scores.mean()))

print(
    "Scores within [0,1]:",
    bool(np.all((scores >= 0) & (scores <= 1)))
)

if len(rows) != 112179:
    raise ValueError("Incorrect prediction record count.")

if len(set(fids)) != len(fids):
    raise ValueError("Duplicate grid cell IDs.")

if positive_count != 16:
    raise ValueError("Expected 16 known positive cells.")

if unlabelled_count != 112163:
    raise ValueError("Unexpected unlabelled cell count.")

if not np.all(np.isfinite(scores)):
    raise ValueError("Invalid prediction scores.")

if not np.all((scores >= 0) & (scores <= 1)):
    raise ValueError("Scores outside [0,1].")

# --------------------------------------------------
# 2. Check known deposit scores
# --------------------------------------------------

print("\nKNOWN DEPOSIT SCORE CHECK")
print("-" * 50)

positive_scores = [
    float(row["pu_score"])
    for row in rows
    if row["label"].strip() == "1"
]

for index, score in enumerate(
    sorted(positive_scores, reverse=True), start=1
):
    print("Positive", index, "| Score:", round(score, 6))

# --------------------------------------------------
# 3. Reload saved model
# --------------------------------------------------

print("\nSAVED MODEL CHECK")
print("-" * 50)

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(MODEL_FILE)

bundle = joblib.load(MODEL_FILE)

print("Model name:", bundle["model_name"])
print("Ensemble models:", len(bundle["ensemble_models"]))
print("Predictor count:", len(bundle["predictor_columns"]))
print("Training grid cells:", bundle["total_grid_cells"])
print("Known positives:", bundle["positive_cells"])
print("Unlabelled cells:", bundle["unlabelled_cells"])

if len(bundle["ensemble_models"]) != 10:
    raise ValueError("Expected 10 saved ensemble models.")

if len(bundle["predictor_columns"]) != 31:
    raise ValueError("Expected 31 saved predictors.")

# --------------------------------------------------
# 4. Final validation
# --------------------------------------------------

print("\n" + "=" * 65)
print("VALIDATION COMPLETED SUCCESSFULLY")
print("=" * 65)
