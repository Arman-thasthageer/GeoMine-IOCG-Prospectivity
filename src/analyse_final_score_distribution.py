
from qgis.core import QgsVectorLayer
import math

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\iocg_prospectivity_v4.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=iocg_prospectivity_v4",
    "final_score_analysis",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load final prospectivity layer.")

scores = []
null_count = 0
invalid_count = 0

for feature in layer.getFeatures():

    value = feature["iocg_score"]

    if value is None:
        null_count += 1
        continue

    value = float(value)

    if not math.isfinite(value):
        invalid_count += 1
        continue

    scores.append(value)

if not scores:
    raise Exception("No valid scores found.")

scores.sort()

total = len(scores)

def percentile(data, p):
    index = round((len(data) - 1) * p / 100)
    return data[index]

zero_count = sum(value == 0 for value in scores)
positive_count = sum(value > 0 for value in scores)

print("\nFINAL IOCG SCORE DISTRIBUTION")
print("=============================")

print("Total cells:", layer.featureCount())
print("Valid scores:", total)
print("NULL scores:", null_count)
print("Invalid scores:", invalid_count)

print("\nBASIC STATISTICS")
print("Minimum:", round(scores[0], 4))
print("Maximum:", round(scores[-1], 4))
print("Mean:", round(sum(scores) / total, 4))
print("Median:", round(percentile(scores, 50), 4))

print("\nPERCENTILE DISTRIBUTION")

for p in [10, 25, 50, 75, 90, 95, 99]:
    print(
        str(p) + "th percentile:",
        round(percentile(scores, p), 4)
    )

print("\nZERO AND POSITIVE SCORES")
print("Zero-score cells:", zero_count)
print("Positive-score cells:", positive_count)
print(
    "Positive-score percentage:",
    round(positive_count / total * 100, 2),
    "%"
)

print("\nSCORE INTERVAL DISTRIBUTION")

intervals = [
    (0, 10),
    (10, 20),
    (20, 30),
    (30, 40),
    (40, 50),
    (50, 60),
    (60, 70),
    (70, 80),
    (80, 90),
    (90, 100)
]

for lower, upper in intervals:

    count = sum(
        lower <= value < upper
        for value in scores
    )

    if upper == 100:
        count += sum(value == 100 for value in scores)

    print(
        str(lower) + "-" + str(upper),
        ":",
        count,
        "cells"
    )

print("\nSCORE DISTRIBUTION ANALYSIS COMPLETED")
