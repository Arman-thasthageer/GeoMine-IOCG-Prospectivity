
import os
import sys
import csv
import json
import random
from collections import defaultdict

# =====================================================
# 1. PROJECT PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

package_dir = os.path.join(project_dir, "ml_packages")
sys.path.insert(0, package_dir)

input_file = os.path.join(
    project_dir, "data", "processed",
    "ml_training_dataset.csv"
)

fold_file = os.path.join(
    project_dir, "reports",
    "spatial_validation_folds.csv"
)

config_file = os.path.join(
    project_dir, "config",
    "pu_learning_config.json"
)

output_file = os.path.join(
    project_dir, "outputs",
    "pu_spatial_cv_predictions.csv"
)

# =====================================================
# 2. IMPORT ML LIBRARIES
# =====================================================

import numpy as np
from sklearn.ensemble import RandomForestClassifier

# =====================================================
# 3. LOAD CONFIGURATION
# =====================================================

with open(config_file, "r", encoding="utf-8") as file:
    config = json.load(file)

sampling_ratio = config["sampling"]["unlabelled_per_positive"]
repetitions = config["sampling"]["repetitions"]
base_seed = config["sampling"]["random_seed"]

rf_config = config["random_forest"]

# =====================================================
# 4. LOAD FOLD DEFINITIONS
# =====================================================

print("======================================")
print("PU SPATIAL VALIDATION")
print("======================================")

test_blocks = set()

with open(fold_file, "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        if row["role"] == "TEST":
            test_blocks.add(row["block_id"])

if len(test_blocks) != 4:
    raise Exception(
        "Expected 4 positive test blocks. Found: "
        + str(len(test_blocks))
    )

# =====================================================
# 5. LOAD ML DATASET
# =====================================================

print("\nLoading ML dataset...")

rows = []

with open(input_file, "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    predictor_fields = [
        name for name in reader.fieldnames
        if name.endswith("_mean")
    ]

    for row in reader:
        rows.append(row)

if len(predictor_fields) != 31:
    raise Exception("Expected 31 geological predictors.")

print("Grid cells:", len(rows))
print("Predictors:", len(predictor_fields))
print("Test blocks:", len(test_blocks))

# =====================================================
# 6. PREPARE DATA
# =====================================================

for row in rows:
    row["_x"] = np.array(
        [float(row[name]) for name in predictor_fields],
        dtype=np.float64
    )

# =====================================================
# 7. RUN FOUR SPATIAL FOLDS
# =====================================================

all_predictions = []

for fold_id, test_block in enumerate(sorted(test_blocks), start=1):

    print("\n--------------------------------------")
    print("FOLD:", fold_id)
    print("Held-out block:", test_block)
    print("--------------------------------------")

    training_positives = [
        row for row in rows
        if row["label"] == "1"
        and row["block_id"] != test_block
    ]

    training_unlabelled = [
        row for row in rows
        if row["label"] == ""
        and row["block_id"] != test_block
    ]

    test_rows = [
        row for row in rows
        if row["block_id"] == test_block
    ]

    test_positive_count = sum(
        1 for row in test_rows
        if row["label"] == "1"
    )

    if not training_positives:
        raise Exception("No positive training observations.")

    if not test_rows or test_positive_count == 0:
        raise Exception("Invalid held-out positive block.")

    sample_count = (
        len(training_positives) * sampling_ratio
    )

    if len(training_unlabelled) < sample_count:
        raise Exception("Insufficient unlabelled training cells.")

    score_sum = defaultdict(float)
    score_count = defaultdict(int)

    # =================================================
    # 8. REPEATED UNLABELLED SAMPLING
    # =================================================

    for repetition in range(1, repetitions + 1):

        rng = random.Random(
            base_seed + fold_id * 1000 + repetition
        )

        sampled_unlabelled = rng.sample(
            training_unlabelled,
            sample_count
        )

        train_rows = training_positives + sampled_unlabelled

        X_train = np.vstack([
            row["_x"] for row in train_rows
        ])

        y_train = np.array(
            [1] * len(training_positives)
            + [0] * len(sampled_unlabelled)
        )

        # Fit scaling only on this fold's training data.
        train_min = X_train.min(axis=0)
        train_max = X_train.max(axis=0)

        train_range = train_max - train_min
        train_range[train_range == 0] = 1.0

        X_train_scaled = (
            (X_train - train_min) / train_range
        )

        X_test = np.vstack([
            row["_x"] for row in test_rows
        ])

        X_test_scaled = (
            (X_test - train_min) / train_range
        )

        model = RandomForestClassifier(
            n_estimators=rf_config["n_estimators"],
            max_depth=rf_config["max_depth"],
            min_samples_leaf=rf_config["min_samples_leaf"],
            max_features=rf_config["max_features"],
            class_weight=rf_config["class_weight"],
            random_state=base_seed + fold_id * 1000 + repetition,
            n_jobs=rf_config["n_jobs"]
        )

        model.fit(X_train_scaled, y_train)

        positive_class_index = list(
            model.classes_
        ).index(1)

        scores = model.predict_proba(
            X_test_scaled
        )[:, positive_class_index]

        for row, score in zip(test_rows, scores):
            fid = row["fid"]
            score_sum[fid] += float(score)
            score_count[fid] += 1

        print(
            "Repetition:", repetition,
            "| Training positives:", len(training_positives),
            "| Sampled unlabelled:", len(sampled_unlabelled)
        )

    # =================================================
    # 9. SAVE HELD-OUT PREDICTIONS
    # =================================================

    for row in test_rows:

        fid = row["fid"]

        average_score = (
            score_sum[fid] / score_count[fid]
        )

        all_predictions.append({
            "fold_id": fold_id,
            "fid": fid,
            "block_id": test_block,
            "label": row["label"],
            "pu_score": average_score,
            "repetitions": score_count[fid]
        })

    print("Held-out cells:", len(test_rows))
    print("Held-out known deposits:", test_positive_count)

# =====================================================
# 10. EXPORT VALIDATION PREDICTIONS
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
            "fid",
            "block_id",
            "label",
            "pu_score",
            "repetitions"
        ]
    )

    writer.writeheader()
    writer.writerows(all_predictions)

# =====================================================
# 11. FINAL SUMMARY
# =====================================================

total_test_cells = len(all_predictions)

total_test_positives = sum(
    1 for row in all_predictions
    if row["label"] == "1"
)

print("\n======================================")
print("PU SPATIAL VALIDATION SUMMARY")
print("======================================")

print("Spatial folds:", len(test_blocks))
print("Repeated sampling runs:", repetitions)
print("Total held-out cells:", total_test_cells)
print("Held-out known deposits:", total_test_positives)
print("Predictors:", len(predictor_fields))

print("\nOutput:", output_file)
print("\nPU SPATIAL VALIDATION COMPLETED")
