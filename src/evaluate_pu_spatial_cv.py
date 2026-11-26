
import os
import csv
import math

from collections import defaultdict

# =====================================================
# 1. PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "outputs",
    "pu_spatial_cv_predictions.csv"
)

output_file = os.path.join(
    project_dir,
    "reports",
    "pu_spatial_cv_evaluation.csv"
)

# =====================================================
# 2. LOAD PREDICTIONS
# =====================================================

print("======================================")
print("PU SPATIAL CV EVALUATION")
print("======================================")

fold_data = defaultdict(list)

with open(
    input_file,
    "r",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        fold_id = int(row["fold_id"])

        fold_data[fold_id].append({
            "fid": row["fid"],
            "block_id": row["block_id"],
            "label": int(row["label"]) if row["label"] == "1" else 0,
            "score": float(row["pu_score"])
        })

if len(fold_data) != 4:
    raise Exception("Expected 4 spatial folds.")

# =====================================================
# 3. TIE-AWARE CAPTURE RATE
# =====================================================

def calculate_capture(data, fraction):

    total_cells = len(data)

    target_cells = total_cells * fraction

    sorted_scores = sorted(
        item["score"]
        for item in data
    )

    # Score threshold at the requested area fraction.
    boundary_index = max(
        0,
        math.ceil(target_cells) - 1
    )

    threshold = sorted_scores[
        total_cells - 1 - boundary_index
    ]

    higher = [
        item for item in data
        if item["score"] > threshold
    ]

    tied = [
        item for item in data
        if item["score"] == threshold
    ]

    positives_higher = sum(
        item["label"] for item in higher
    )

    positives_tied = sum(
        item["label"] for item in tied
    )

    remaining_slots = max(
        0,
        target_cells - len(higher)
    )

    if len(tied) > 0:
        tie_fraction = remaining_slots / len(tied)
    else:
        tie_fraction = 0

    captured = (
        positives_higher
        + positives_tied * tie_fraction
    )

    total_positives = sum(
        item["label"] for item in data
    )

    capture_rate = (
        captured / total_positives * 100
        if total_positives > 0
        else 0
    )

    return captured, capture_rate, threshold

# =====================================================
# 4. EVALUATE EACH FOLD
# =====================================================

evaluation_rows = []

for fold_id in sorted(fold_data):

    data = fold_data[fold_id]

    total_cells = len(data)

    total_positives = sum(
        item["label"] for item in data
    )

    block_id = data[0]["block_id"]

    print("\n--------------------------------------")
    print("FOLD:", fold_id)
    print("Block:", block_id)
    print("Cells:", total_cells)
    print("Known deposits:", total_positives)
    print("--------------------------------------")

    if total_positives == 0:
        raise Exception("Fold has no known positive deposits.")

    for fraction in [0.05, 0.10, 0.20]:

        captured, rate, threshold = calculate_capture(
            data,
            fraction
        )

        percentage = int(fraction * 100)

        print(
            "Top", percentage, "%",
            "| Captured:", round(captured, 4),
            "/", total_positives,
            "| Capture rate:", round(rate, 2), "%"
        )

        evaluation_rows.append({
            "fold_id": fold_id,
            "block_id": block_id,
            "total_cells": total_cells,
            "known_deposits": total_positives,
            "top_area_percent": percentage,
            "deposits_captured_tie_aware": round(captured, 6),
            "capture_rate_percent": round(rate, 4),
            "score_threshold": threshold
        })

# =====================================================
# 5. SAVE RESULTS
# =====================================================

os.makedirs(
    os.path.dirname(output_file),
    exist_ok=True
)

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
            "total_cells",
            "known_deposits",
            "top_area_percent",
            "deposits_captured_tie_aware",
            "capture_rate_percent",
            "score_threshold"
        ]
    )

    writer.writeheader()
    writer.writerows(evaluation_rows)

# =====================================================
# 6. FINAL SUMMARY
# =====================================================

print("\n======================================")
print("PU SPATIAL CV EVALUATION SUMMARY")
print("======================================")

print("Spatial folds evaluated:", len(fold_data))
print("Total held-out cells:", sum(len(x) for x in fold_data.values()))
print(
    "Total held-out deposits:",
    sum(
        sum(item["label"] for item in data)
        for data in fold_data.values()
    )
)

print("\nEvaluation CSV:")
print(output_file)

print("\nPU SPATIAL CV EVALUATION COMPLETED")
