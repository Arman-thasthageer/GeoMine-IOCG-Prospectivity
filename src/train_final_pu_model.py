
import os
import sys
import csv
import json
import numpy as np
import joblib

from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier

# ============================================================
# PATHS
# ============================================================

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

ML_PACKAGES = os.path.join(BASE, "ml_packages")

if ML_PACKAGES not in sys.path:
    sys.path.insert(0, ML_PACKAGES)

INPUT_CSV = os.path.join(
    BASE, "data", "processed",
    "ml_training_dataset.csv"
)

CONFIG_PATH = os.path.join(
    BASE, "config",
    "pu_learning_config.json"
)

OUTPUT_CSV = os.path.join(
    BASE, "outputs",
    "final_pu_prospectivity.csv"
)

MODEL_OUTPUT = os.path.join(
    BASE, "models",
    "final_pu_random_forest_ensemble.joblib"
)

print("=" * 70)
print("FINAL FULL-STUDY-AREA PU MODEL TRAINING")
print("=" * 70)

# ============================================================
# 1. LOAD CONFIGURATION
# ============================================================

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(CONFIG_PATH)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

dataset_config = config["dataset"]
sampling_config = config["sampling"]
rf_config = config["random_forest"]

UNLABELLED_PER_POSITIVE = int(
    sampling_config["unlabelled_per_positive"]
)

REPETITIONS = int(
    sampling_config["repetitions"]
)

BASE_SEED = int(
    sampling_config["random_seed"]
)

N_ESTIMATORS = int(rf_config["n_estimators"])
MAX_DEPTH = int(rf_config["max_depth"])
MIN_SAMPLES_LEAF = int(rf_config["min_samples_leaf"])
MAX_FEATURES = rf_config["max_features"]
CLASS_WEIGHT = rf_config["class_weight"]
N_JOBS = int(rf_config["n_jobs"])

EXPECTED_POSITIVES = int(
    dataset_config["expected_positive_cells"]
)

EXPECTED_UNLABELLED = int(
    dataset_config["expected_unlabelled_cells"]
)

EXPECTED_PREDICTORS = int(
    dataset_config["expected_predictors"]
)

print("\nCONFIGURATION")
print("-" * 50)
print("Model:", config["model_name"])
print("Learning strategy:", config["learning_strategy"])
print("Random seed:", BASE_SEED)
print("Repetitions:", REPETITIONS)
print("Unlabelled per positive:", UNLABELLED_PER_POSITIVE)
print("Random Forest trees:", N_ESTIMATORS)
print("Maximum depth:", MAX_DEPTH)

# ============================================================
# 2. VERIFY INPUT FILES
# ============================================================

for path in [INPUT_CSV, CONFIG_PATH]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)

# ============================================================
# 3. LOAD ML DATASET
# ============================================================

print("\nLOADING ML DATASET")
print("-" * 50)

with open(
    INPUT_CSV,
    "r",
    newline="",
    encoding="utf-8-sig"
) as f:

    reader = csv.DictReader(f)
    rows = list(reader)
    columns = reader.fieldnames

if not rows:
    raise ValueError("ML dataset is empty.")

required_columns = {"fid", "label", "block_id"}

missing_columns = required_columns - set(columns or [])

if missing_columns:
    raise ValueError(
        "Missing required columns: "
        + str(sorted(missing_columns))
    )

feature_columns = [
    column for column in columns
    if column not in ("fid", "label", "block_id")
]

if len(feature_columns) != EXPECTED_PREDICTORS:
    raise ValueError(
        "Expected "
        + str(EXPECTED_PREDICTORS)
        + " predictors, found "
        + str(len(feature_columns))
    )

fids = []
labels = []
block_ids = []
feature_values = []

for row in rows:

    fids.append(int(row["fid"]))
    labels.append(row["label"].strip())
    block_ids.append(row["block_id"])

    values = [
        float(row[column])
        for column in feature_columns
    ]

    if not np.all(np.isfinite(values)):
        raise ValueError(
            "Invalid predictor values at fid "
            + str(row["fid"])
        )

    feature_values.append(values)

X = np.asarray(feature_values, dtype=np.float64)

positive_indices = np.array([
    i for i, value in enumerate(labels)
    if value == "1"
], dtype=int)

unlabelled_indices = np.array([
    i for i, value in enumerate(labels)
    if value == ""
], dtype=int)

# ============================================================
# 4. DATA VALIDATION
# ============================================================

print("\nDATASET VALIDATION")
print("-" * 50)

print("Total grid cells:", len(rows))
print("Predictor count:", len(feature_columns))
print("Known positives:", len(positive_indices))
print("Unlabelled cells:", len(unlabelled_indices))

if len(positive_indices) != EXPECTED_POSITIVES:
    raise ValueError(
        "Positive count mismatch. Expected "
        + str(EXPECTED_POSITIVES)
        + ", found "
        + str(len(positive_indices))
    )

if len(unlabelled_indices) != EXPECTED_UNLABELLED:
    raise ValueError(
        "Unlabelled count mismatch. Expected "
        + str(EXPECTED_UNLABELLED)
        + ", found "
        + str(len(unlabelled_indices))
    )

if len(rows) != len(positive_indices) + len(unlabelled_indices):
    raise ValueError("Unexpected label categories found.")

if len(set(fids)) != len(fids):
    raise ValueError("Duplicate grid cell IDs detected.")

if X.shape != (len(rows), len(feature_columns)):
    raise ValueError("Unexpected predictor matrix dimensions.")

# ============================================================
# 5. TRAIN REPEATED PU RANDOM FOREST ENSEMBLE
# ============================================================

sample_size = (
    len(positive_indices) * UNLABELLED_PER_POSITIVE
)

if sample_size > len(unlabelled_indices):
    raise ValueError("Insufficient unlabelled cells.")

prediction_sum = np.zeros(
    len(rows),
    dtype=np.float64
)

ensemble_models = []

print("\nTRAINING ENSEMBLE")
print("-" * 50)

print("Unlabelled sample per repetition:", sample_size)
print("Total repetitions:", REPETITIONS)

for repetition in range(REPETITIONS):

    seed = BASE_SEED + repetition

    rng = np.random.default_rng(seed)

    # Sample unlabelled cells without replacement
    sampled_unlabelled = rng.choice(
        unlabelled_indices,
        size=sample_size,
        replace=False
    )

    # Combine all known positives with sampled unlabelled cells
    training_indices = np.concatenate([
        positive_indices,
        sampled_unlabelled
    ])

    y_train = np.concatenate([
        np.ones(len(positive_indices), dtype=int),
        np.zeros(len(sampled_unlabelled), dtype=int)
    ])

    X_train_raw = X[training_indices]

    # Fit scaler only on training samples
    scaler = MinMaxScaler()

    X_train = scaler.fit_transform(X_train_raw)

    # Transform all grid cells using the training scaler
    X_all = scaler.transform(X)

    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        max_features=MAX_FEATURES,
        class_weight=CLASS_WEIGHT,
        random_state=seed,
        n_jobs=N_JOBS
    )

    model.fit(X_train, y_train)

    positive_class_position = list(
        model.classes_
    ).index(1)

    predictions = model.predict_proba(
        X_all
    )[:, positive_class_position]

    prediction_sum += predictions

    ensemble_models.append({
        "scaler": scaler,
        "model": model,
        "seed": seed
    })

    print(
        "Repetition",
        repetition + 1,
        "/",
        REPETITIONS,
        "| Training rows:",
        len(training_indices),
        "| Completed"
    )

# ============================================================
# 6. AVERAGE ENSEMBLE PREDICTIONS
# ============================================================

print("\nCALCULATING FINAL PU SCORES")
print("-" * 50)

final_scores = prediction_sum / REPETITIONS

if len(final_scores) != len(rows):
    raise ValueError("Prediction count does not match grid cells.")

if not np.all(np.isfinite(final_scores)):
    raise ValueError("Invalid prediction scores detected.")

if not np.all(
    (final_scores >= 0) & (final_scores <= 1)
):
    raise ValueError("Prediction scores outside [0, 1].")

# ============================================================
# 7. SAVE FULL-STUDY-AREA PREDICTIONS
# ============================================================

print("\nSAVING PREDICTION CSV")
print("-" * 50)

with open(
    OUTPUT_CSV,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "fid",
        "block_id",
        "label",
        "pu_score",
        "model_repetitions"
    ])

    for i in range(len(rows)):

        writer.writerow([
            fids[i],
            block_ids[i],
            labels[i],
            float(final_scores[i]),
            REPETITIONS
        ])

# ============================================================
# 8. SAVE TRAINED ENSEMBLE
# ============================================================

print("\nSAVING TRAINED ENSEMBLE")
print("-" * 50)

model_bundle = {
    "model_name": "Final Full-Area PU Random Forest Ensemble",
    "learning_strategy": config["learning_strategy"],
    "predictor_columns": feature_columns,
    "ensemble_models": ensemble_models,
    "repetitions": REPETITIONS,
    "unlabelled_per_positive": UNLABELLED_PER_POSITIVE,
    "random_seed": BASE_SEED,
    "random_forest_parameters": {
        "n_estimators": N_ESTIMATORS,
        "max_depth": MAX_DEPTH,
        "min_samples_leaf": MIN_SAMPLES_LEAF,
        "max_features": MAX_FEATURES,
        "class_weight": CLASS_WEIGHT,
        "n_jobs": N_JOBS
    },
    "training_rows_per_repetition": (
        len(positive_indices) + sample_size
    ),
    "positive_cells": len(positive_indices),
    "unlabelled_cells": len(unlabelled_indices),
    "total_grid_cells": len(rows),
    "prediction_interpretation": (
        "PU ranking score from positive versus sampled-unlabelled "
        "classification. Not a calibrated mineralization probability."
    )
}

joblib.dump(
    model_bundle,
    MODEL_OUTPUT
)

# ============================================================
# 9. FINAL OUTPUT VALIDATION
# ============================================================

print("\nFINAL MODEL SUMMARY")
print("-" * 50)

print("Total grid cells predicted:", len(final_scores))
print("Known positive cells:", len(positive_indices))
print("Unlabelled cells:", len(unlabelled_indices))
print("Predictors:", len(feature_columns))
print("Ensemble repetitions:", REPETITIONS)

print("\nPU SCORE STATISTICS")
print("-" * 50)

print("Minimum:", float(final_scores.min()))
print("Maximum:", float(final_scores.max()))
print("Mean:", float(final_scores.mean()))
print("Standard deviation:", float(final_scores.std()))

print(
    "All scores within [0,1]:",
    bool(np.all((final_scores >= 0) & (final_scores <= 1)))
)

print("\nGENERATED FILES")
print("-" * 50)

print("Prediction CSV:")
print(OUTPUT_CSV)

print("\nTrained model:")
print(MODEL_OUTPUT)

print("\n" + "=" * 70)
print("FINAL FULL-STUDY-AREA PU MODEL TRAINING COMPLETED")
print("=" * 70)
