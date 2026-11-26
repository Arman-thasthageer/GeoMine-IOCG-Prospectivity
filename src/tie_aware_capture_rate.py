
from qgis.core import QgsVectorLayer

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\iocg_prospectivity_v4.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=iocg_prospectivity_v4",
    "tie_aware_evaluation",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load prospectivity layer.")

records = []

for feature in layer.getFeatures():

    records.append({
        "score": float(feature["iocg_score"]),
        "positive": feature["label"] == 1
    })

total = len(records)
deposit_total = sum(r["positive"] for r in records)

records.sort(key=lambda r: r["score"], reverse=True)

print("\nTIE-AWARE CAPTURE RATE")
print("======================")
print("Total cells:", total)
print("Known deposits:", deposit_total)

for percentage in [5, 10, 20]:

    target_cells = total * percentage / 100.0

    selected_cells = 0
    captured_deposits = 0.0

    index = 0

    while index < total and selected_cells < target_cells:

        score = records[index]["score"]

        # Identify all cells sharing this score
        end = index

        while end < total and records[end]["score"] == score:
            end += 1

        group = records[index:end]

        group_size = len(group)
        remaining = target_cells - selected_cells

        fraction = min(1.0, remaining / group_size)

        group_deposits = sum(
            item["positive"] for item in group
        )

        captured_deposits += fraction * group_deposits
        selected_cells += fraction * group_size

        index = end

    capture_rate = (
        captured_deposits / deposit_total
    ) * 100

    print("\nTOP", percentage, "% AREA")
    print("Target cells:", round(target_cells, 2))
    print("Deposits captured (tie-adjusted):",
          round(captured_deposits, 4))
    print("Capture rate:", round(capture_rate, 2), "%")

print("\nTIE-AWARE EVALUATION COMPLETED")
