
from qgis.core import QgsVectorLayer
import math

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\geological_component_scores.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=geological_component_scores",
    "component_diagnostic",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load component scores.")

fields = [
    "sources_score",
    "energy_score",
    "pathways_score",
    "deposition_score"
]

zero_counts = {name: 0 for name in fields}
positive_counts = {name: 0 for name in fields}

all_positive = 0
one_or_more_zero = 0
all_zero = 0

final_scores = []

for feature in layer.getFeatures():

    values = [float(feature[name]) for name in fields]

    for name, value in zip(fields, values):
        if value == 0:
            zero_counts[name] += 1
        else:
            positive_counts[name] += 1

    if all(value > 0 for value in values):
        all_positive += 1
    else:
        one_or_more_zero += 1

    if all(value == 0 for value in values):
        all_zero += 1

    if all(value > 0 for value in values):
        score = (
            math.prod(value / 100 for value in values) ** 0.25
        ) * 100
        final_scores.append(score)

total = layer.featureCount()

print("\nZERO SCORE DIAGNOSTIC")
print("=====================")
print("Total cells:", total)

for name in fields:
    print(
        name,
        "| Zero:", zero_counts[name],
        "| Positive:", positive_counts[name],
        "| Zero %:", round(zero_counts[name] / total * 100, 2)
    )

print("\nCOMBINATION ANALYSIS")
print("All four components positive:", all_positive)
print("At least one component zero:", one_or_more_zero)
print("All four components zero:", all_zero)

if final_scores:
    final_scores.sort()

    def percentile(data, p):
        index = round((len(data) - 1) * p / 100)
        return data[index]

    print("\nNON-ZERO FINAL SCORE DISTRIBUTION")
    print("Count:", len(final_scores))
    print("Minimum:", round(final_scores[0], 4))
    print("25th percentile:", round(percentile(final_scores, 25), 4))
    print("Median:", round(percentile(final_scores, 50), 4))
    print("75th percentile:", round(percentile(final_scores, 75), 4))
    print("90th percentile:", round(percentile(final_scores, 90), 4))
    print("Maximum:", round(final_scores[-1], 4))

print("\nDIAGNOSTIC COMPLETED")
