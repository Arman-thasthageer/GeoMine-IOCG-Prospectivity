
from qgis.core import QgsVectorLayer
import bisect

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\iocg_prospectivity_v4.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=iocg_prospectivity_v4",
    "deposit_score_evaluation",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load final prospectivity layer.")

if layer.fields().indexFromName("label") == -1:
    raise Exception("Label field is missing.")

if layer.fields().indexFromName("iocg_score") == -1:
    raise Exception("iocg_score field is missing.")

all_scores = []
deposit_records = []

for feature in layer.getFeatures():

    score = float(feature["iocg_score"])
    all_scores.append(score)

    if feature["label"] == 1:
        deposit_records.append({
            "id": feature.id(),
            "score": score
        })

all_scores.sort()

total = len(all_scores)

if not deposit_records:
    raise Exception("No positive deposit labels found.")

deposit_records.sort(
    key=lambda item: item["score"],
    reverse=True
)

print("\nKNOWN DEPOSIT SCORE EVALUATION")
print("================================")
print("Total grid cells:", total)
print("Known deposit cells:", len(deposit_records))

print("\nINDIVIDUAL DEPOSIT CELL SCORES")
print("--------------------------------")

for item in deposit_records:

    score = item["score"]

    # Empirical percentile rank across all grid cells
    rank = (
        bisect.bisect_right(all_scores, score)
        / total
    ) * 100

    print(
        "Feature ID:", item["id"],
        "| Score:", round(score, 4),
        "| Percentile:", round(rank, 2)
    )

print("\nDEPOSIT CAPTURE RATE")
print("--------------------")

for area_percentage in [5, 10, 20]:

    threshold_index = int(
        total * (1 - area_percentage / 100)
    )

    threshold = all_scores[threshold_index]

    captured = sum(
        item["score"] >= threshold
        for item in deposit_records
    )

    print(
        "Top", area_percentage, "% area",
        "| Score threshold:", round(threshold, 4),
        "| Deposits captured:", captured,
        "/", len(deposit_records),
        "| Capture rate:",
        round(captured / len(deposit_records) * 100, 2),
        "%"
    )

print("\nEVALUATION COMPLETED")
