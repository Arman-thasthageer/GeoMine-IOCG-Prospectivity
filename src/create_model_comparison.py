
import os
import csv

BASE = r"C:\Users\Ermus\Desktop\GeoMine"
REPORTS = os.path.join(BASE, "reports")

INPUT = os.path.join(
    REPORTS, "pu_spatial_cv_evaluation.csv"
)

SUMMARY_OUTPUT = os.path.join(
    REPORTS, "model_comparison_summary.csv"
)

FOLD_OUTPUT = os.path.join(
    REPORTS, "pu_fold_comparison.csv"
)

print("=" * 65)
print("CONSOLIDATED MODEL COMPARISON")
print("=" * 65)

if not os.path.exists(INPUT):
    raise FileNotFoundError(INPUT)

# Read PU fold evaluation results
with open(INPUT, "r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    pu_rows = list(reader)

if not pu_rows:
    raise ValueError("PU evaluation CSV contains no records.")

required = {
    "fold_id",
    "block_id",
    "known_deposits",
    "top_area_percent",
    "deposits_captured_tie_aware",
    "capture_rate_percent"
}

missing = required - set(pu_rows[0].keys())

if missing:
    raise ValueError(
        "Missing required CSV columns: " + str(sorted(missing))
    )

# Aggregate PU capture within each held-out block
percentages = [5, 10, 20]
pu_summary = {}

for percentage in percentages:
    selected = [
        row for row in pu_rows
        if float(row["top_area_percent"]) == percentage
    ]

    total_deposits = sum(
        int(row["known_deposits"]) for row in selected
    )

    captured = sum(
        float(row["deposits_captured_tie_aware"])
        for row in selected
    )

    rate = (
        captured / total_deposits * 100
        if total_deposits else 0
    )

    pu_summary[percentage] = {
        "captured": captured,
        "total": total_deposits,
        "rate": rate
    }

# Baseline metrics previously calculated over the full study area.
# These are in-sample baseline results, not spatial CV results.
models = [
    {
        "model": "Expert-weighted baseline",
        "evaluation_scope": "Full study area; in-sample",
        "method": "Tie-aware top-area capture",
        5: 93.75,
        10: 93.75,
        20: 94.20
    },
    {
        "model": "GA baseline",
        "evaluation_scope": "Full study area; in-sample",
        "method": "Top-area capture",
        5: 87.50,
        10: 93.75,
        20: 100.00
    },
    {
        "model": "PU Random Forest",
        "evaluation_scope": "Four held-out positive blocks only",
        "method": "Aggregated fold-wise tie-aware capture",
        5: pu_summary[5]["rate"],
        10: pu_summary[10]["rate"],
        20: pu_summary[20]["rate"]
    }
]

# Save consolidated summary
with open(
    SUMMARY_OUTPUT, "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.writer(f)

    writer.writerow([
        "model",
        "evaluation_scope",
        "method",
        "top_5_capture_percent",
        "top_10_capture_percent",
        "top_20_capture_percent",
        "comparability_note"
    ])

    for model in models:
        if model["model"] == "PU Random Forest":
            note = (
                "Fold-wise capture within four held-out positive blocks; "
                "not directly comparable with full-area baselines."
            )
        else:
            note = (
                "In-sample full-area baseline; not independent "
                "spatial validation."
            )

        writer.writerow([
            model["model"],
            model["evaluation_scope"],
            model["method"],
            round(model[5], 2),
            round(model[10], 2),
            round(model[20], 2),
            note
        ])

# Save individual PU fold results
with open(
    FOLD_OUTPUT, "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.writer(f)

    writer.writerow([
        "fold_id",
        "block_id",
        "known_deposits",
        "top_area_percent",
        "deposits_captured",
        "capture_rate_percent"
    ])

    for row in sorted(
        pu_rows,
        key=lambda x: (
            int(x["fold_id"]),
            float(x["top_area_percent"])
        )
    ):
        writer.writerow([
            row["fold_id"],
            row["block_id"],
            row["known_deposits"],
            row["top_area_percent"],
            row["deposits_captured_tie_aware"],
            row["capture_rate_percent"]
        ])

# Console summary
print("\nMODEL COMPARISON")
print("-" * 65)

for model in models:
    print("\nModel:", model["model"])
    print("Scope:", model["evaluation_scope"])
    print("Top 5% :", round(model[5], 2), "%")
    print("Top 10%:", round(model[10], 2), "%")
    print("Top 20%:", round(model[20], 2), "%")

print("\nPU AGGREGATED CAPTURE COUNTS")
print("-" * 65)

for percentage in percentages:
    result = pu_summary[percentage]
    print(
        "Top", percentage, "%:",
        round(result["captured"], 2),
        "/", result["total"],
        "deposits =",
        round(result["rate"], 2), "%"
    )

print("\nIMPORTANT METHODOLOGY NOTES")
print("-" * 65)
print("1. Expert and GA baselines use the full study area.")
print("2. Expert and GA results are in-sample.")
print("3. PU results use four held-out positive blocks.")
print("4. PU percentages are calculated separately within each block.")
print("5. Do not interpret unlabelled cells as confirmed negatives.")
print("6. These three model results are not directly comparable.")

print("\nOUTPUT FILES")
print(SUMMARY_OUTPUT)
print(FOLD_OUTPUT)

print("\nMODEL COMPARISON COMPLETED")
