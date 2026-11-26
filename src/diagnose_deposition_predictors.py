
from qgis.core import QgsVectorLayer
import math

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\geological_features.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=geological_features",
    "deposition_predictor_diagnostic",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load geological_features layer.")

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

total = layer.featureCount()

print("\nDEPOSITION PREDICTOR DIAGNOSTIC")
print("================================")
print("Total grid cells:", total)

for name in predictors:

    if layer.fields().indexFromName(name) == -1:
        print("\nMISSING FIELD:", name)
        continue

    zero = 0
    positive = 0
    null = 0
    invalid = 0

    minimum = float("inf")
    maximum = float("-inf")

    for feature in layer.getFeatures():

        value = feature[name]

        if value is None:
            null += 1
            continue

        try:
            value = float(value)
        except (ValueError, TypeError):
            invalid += 1
            continue

        if not math.isfinite(value):
            invalid += 1
            continue

        minimum = min(minimum, value)
        maximum = max(maximum, value)

        if value == 0:
            zero += 1
        elif value > 0:
            positive += 1

    print("\n", name)
    print("  Zero:", zero)
    print("  Positive:", positive)
    print("  NULL:", null)
    print("  Invalid:", invalid)

    if minimum != float("inf"):
        print("  Minimum:", minimum)
        print("  Maximum:", maximum)

print("\nDIAGNOSTIC COMPLETED")
