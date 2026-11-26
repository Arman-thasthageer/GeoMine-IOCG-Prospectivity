
from qgis.core import QgsVectorLayer

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\geological_features.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=geological_features",
    "deposition_coverage_analysis",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load geological features.")

predictors = [
    "t1a_mean",
    "t1b1_mean",
    "t1b2_mean",
    "t1b3_mean",
    "t1b4_mean",
    "t1c1_mean",
    "t1c2_mean",
    "t1c3_mean",
    "t1c4_mean",
    "t2_mean",
    "t3_mean"
]

for name in predictors:
    if layer.fields().indexFromName(name) == -1:
        raise Exception("Missing predictor: " + name)

if layer.fields().indexFromName("label") == -1:
    raise Exception("Missing label field.")

# Number of positive predictors per cell
coverage_counts = {i: 0 for i in range(12)}

# Deposit-cell analysis
deposit_total = 0
deposit_with_deposition = 0
deposit_without_deposition = 0

unlabelled_total = 0

for feature in layer.getFeatures():

    values = [
        float(feature[name])
        for name in predictors
    ]

    positive_count = sum(value > 0 for value in values)

    coverage_counts[positive_count] += 1

    label = feature["label"]

    if label == 1:
        deposit_total += 1

        if positive_count > 0:
            deposit_with_deposition += 1
        else:
            deposit_without_deposition += 1

    elif label is None:
        unlabelled_total += 1

total = layer.featureCount()

print("\nDEPOSITION COVERAGE ANALYSIS")
print("============================")
print("Total cells:", total)

print("\nPOSITIVE DEPOSITION PREDICTORS PER CELL")

for count in range(12):
    cells = coverage_counts[count]
    percentage = cells / total * 100

    print(
        str(count),
        "positive predictors:",
        cells,
        "cells |",
        round(percentage, 2),
        "%"
    )

print("\nKNOWN DEPOSIT CELL ANALYSIS")
print("===========================")
print("Known deposit cells:", deposit_total)
print("With at least one positive T predictor:",
      deposit_with_deposition)
print("With all T predictors zero:",
      deposit_without_deposition)

print("\nUNLABELLED CELLS:", unlabelled_total)

print("\nANALYSIS COMPLETED")
