
import os
import csv
import json
import math

from qgis.core import QgsVectorLayer

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

INPUT = os.path.join(
    BASE, "data", "processed",
    "final_pu_prospectivity.gpkg"
)

CONFIG = os.path.join(
    BASE, "config",
    "predictor_config.csv"
)

OUTPUT = os.path.join(
    BASE, "reports",
    "cell_explanations.csv"
)

print("=" * 70)
print("GENERATING CELL-LEVEL EXPLANATIONS")
print("=" * 70)

# --------------------------------------------------
# 1. LOAD INPUT LAYER
# --------------------------------------------------

layer = QgsVectorLayer(
    INPUT + "|layername=final_pu_prospectivity",
    "final_pu_prospectivity",
    "ogr"
)

if not layer.isValid():
    raise RuntimeError("Could not load final PU prospectivity layer.")

print("Input cells:", layer.featureCount())

# --------------------------------------------------
# 2. LOAD PREDICTOR CONFIGURATION
# --------------------------------------------------

predictors = []

with open(CONFIG, "r", encoding="utf-8-sig", newline="") as f:

    reader = csv.DictReader(f)

    required = {
        "criterion_code",
        "feature_field",
        "component",
        "IOCG_Comprehensive",
        "official_final_weight"
    }

    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("Predictor configuration headers do not match.")

    for row in reader:

        if row["IOCG_Comprehensive"].strip().upper() != "Y":
            continue

        predictors.append({
            "code": row["criterion_code"].strip(),
            "field": row["feature_field"].strip(),
            "component": row["component"].strip(),
            "weight": float(row["official_final_weight"])
        })

if len(predictors) != 31:
    raise ValueError(
        "Expected 31 Comprehensive predictors. Found: "
        + str(len(predictors))
    )

# Group predictors by component
component_weights = {}

for p in predictors:
    component_weights[p["component"]] = (
        component_weights.get(p["component"], 0.0)
        + p["weight"]
    )

components = [
    "Sources",
    "Energy",
    "Pathways",
    "Deposition"
]

if set(component_weights.keys()) != set(components):
    raise ValueError(
        "Unexpected component names: "
        + str(list(component_weights.keys()))
    )

# Validate predictor fields
layer_fields = layer.fields().names()

for p in predictors:

    if p["field"] not in layer_fields:
        raise ValueError(
            "Missing predictor field: " + p["field"]
        )

for required_field in ["pu_score", "pu_percentile"]:
    if required_field not in layer_fields:
        raise ValueError(
            "Missing required field: " + required_field
        )

print("Predictors loaded:", len(predictors))
print("Components:", components)

# --------------------------------------------------
# 3. PREPARE OUTPUT
# --------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

headers = [
    "grid_fid",
    "label",
    "pu_score",
    "pu_percentile",
    "sources_score",
    "energy_score",
    "pathways_score",
    "deposition_score",
    "valid_predictor_count",
    "total_predictor_count",
    "predictor_completeness_percent",
    "top_driver_1",
    "top_driver_1_component",
    "top_driver_1_contribution",
    "top_driver_2",
    "top_driver_2_component",
    "top_driver_2_contribution",
    "top_driver_3",
    "top_driver_3_component",
    "top_driver_3_contribution"
]

# --------------------------------------------------
# 4. PROCESS EVERY GRID CELL
# --------------------------------------------------

processed = 0
invalid_scores = 0
coverage_counts = {}
component_min = {c: 999999.0 for c in components}
component_max = {c: -999999.0 for c in components}

with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as f:

    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()

    for feature in layer.getFeatures():

        # PU model outputs
        pu_score = float(feature["pu_score"])
        pu_percentile = float(feature["pu_percentile"])

        if not math.isfinite(pu_score) or not math.isfinite(pu_percentile):
            invalid_scores += 1
            continue

        # Read predictor values
        valid_count = 0
        driver_contributions = []
        component_scores = {
            c: 0.0 for c in components
        }

        for p in predictors:

            raw_value = feature[p["field"]]

            valid = False
            value = 0.0

            try:
                value = float(raw_value)

                if math.isfinite(value) and abs(value) < 1e9:
                    valid = True

            except (TypeError, ValueError):
                valid = False

            if not valid:
                continue

            valid_count += 1

            # Original predictor scale: 0 to 1000
            # Convert to 0 to 100
            scaled_value = value / 10.0

            # Normalise official weight within component
            normalised_weight = (
                p["weight"] / component_weights[p["component"]]
            )

            # Weighted contribution to component score
            contribution = scaled_value * normalised_weight

            component_scores[p["component"]] += contribution

            driver_contributions.append({
                "code": p["code"],
                "component": p["component"],
                "contribution": contribution
            })

        # Sort predictors by weighted contribution
        driver_contributions.sort(
            key=lambda x: x["contribution"],
            reverse=True
        )

        top_drivers = driver_contributions[:3]

        # Completeness of extracted predictor fields
        completeness = (
            valid_count / len(predictors)
        ) * 100.0

        for c in components:
            component_min[c] = min(
                component_min[c], component_scores[c]
            )
            component_max[c] = max(
                component_max[c], component_scores[c]
            )

        coverage_counts[valid_count] = (
            coverage_counts.get(valid_count, 0) + 1
        )

        # Preserve the existing label without converting
        # unlabelled cells into negative examples
        label = feature["label"] if "label" in layer_fields else ""

        grid_fid = (
            feature["grid_fid"]
            if "grid_fid" in layer_fields
            else feature.id()
        )

        row = {
            "grid_fid": grid_fid,
            "label": label,
            "pu_score": pu_score,
            "pu_percentile": pu_percentile,
            "sources_score": component_scores["Sources"],
            "energy_score": component_scores["Energy"],
            "pathways_score": component_scores["Pathways"],
            "deposition_score": component_scores["Deposition"],
            "valid_predictor_count": valid_count,
            "total_predictor_count": len(predictors),
            "predictor_completeness_percent": completeness
        }

        for i in range(3):

            if i < len(top_drivers):
                driver = top_drivers[i]
                n = i + 1

                row[f"top_driver_{n}"] = driver["code"]
                row[f"top_driver_{n}_component"] = driver["component"]
                row[f"top_driver_{n}_contribution"] = driver["contribution"]

            else:
                n = i + 1
                row[f"top_driver_{n}"] = ""
                row[f"top_driver_{n}_component"] = ""
                row[f"top_driver_{n}_contribution"] = ""

        writer.writerow(row)
        processed += 1

# --------------------------------------------------
# 5. VALIDATION SUMMARY
# --------------------------------------------------

print("\nEXPLANATION OUTPUT SUMMARY")
print("-" * 70)

print("Processed cells:", processed)
print("Invalid PU score rows skipped:", invalid_scores)
print("Predictors per cell:", len(predictors))

print("\nCOMPONENT SCORE RANGES")

for c in components:
    print(
        c,
        "| Minimum:", round(component_min[c], 4),
        "| Maximum:", round(component_max[c], 4)
    )

print("\nPREDICTOR COMPLETENESS DISTRIBUTION")

for count in sorted(coverage_counts):
    print(
        str(count) + "/" + str(len(predictors)),
        "predictors:",
        coverage_counts[count],
        "cells"
    )

print("\nOUTPUT FILE:")
print(OUTPUT)

print("\n" + "=" * 70)
print("CELL-LEVEL EXPLANATIONS GENERATED")
print("=" * 70)
