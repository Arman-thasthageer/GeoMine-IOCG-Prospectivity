
from qgis.core import QgsVectorLayer

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\iocg_prospectivity_v4.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=iocg_prospectivity_v4",
    "exact_capture_evaluation",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load prospectivity layer.")

records = []

for feature in layer.getFeatures():

    score = float(feature["iocg_score"])
    label = feature["label"]

    records.append({
        "fid": feature.id(),
        "score": score,
        "positive": label == 1
    })

# Rank by score descending.
# Feature ID provides a reproducible tie-breaker.
records.sort(
    key=lambda item: (-item["score"], item["fid"])
)

total = len(records)
deposit_total = sum(item["positive"] for item in records)

print("\nEXACT AREA CAPTURE RATE")
print("=======================")
print("Total cells:", total)
print("Known deposit cells:", deposit_total)

for percentage in [5, 10, 20]:

    selected_count = round(total * percentage / 100)

    selected = records[:selected_count]

    captured = sum(
        item["positive"] for item in selected
    )

    capture_rate = (
        captured / deposit_total * 100
    )

    boundary_score = selected[-1]["score"]

    selected_ties = sum(
        item["score"] == boundary_score
        for item in selected
    )

    total_boundary_ties = sum(
        item["score"] == boundary_score
        for item in records
    )

    print("\nTOP", percentage, "% AREA")
    print("Selected cells:", selected_count)
    print("Actual area percentage:",
          round(selected_count / total * 100, 4))
    print("Score at selection boundary:", boundary_score)
    print("Deposits captured:", captured, "/", deposit_total)
    print("Capture rate:", round(capture_rate, 2), "%")
    print("Cells tied at boundary:", total_boundary_ties)
    print("Boundary-tied cells selected:", selected_ties)

print("\nEVALUATION COMPLETED")
print("Tie-breaking: score descending, feature ID ascending")
