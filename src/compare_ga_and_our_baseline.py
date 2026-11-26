
from qgis.core import QgsVectorLayer

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

our_file = (
    project_dir
    + r"\data\processed\iocg_prospectivity_v4.gpkg"
)

ga_file = (
    project_dir
    + r"\data\processed\ga_baseline_grid.gpkg"
)

our_layer = QgsVectorLayer(
    our_file + "|layername=iocg_prospectivity_v4",
    "our_baseline",
    "ogr"
)

ga_layer = QgsVectorLayer(
    ga_file + "|layername=ga_baseline_grid",
    "ga_baseline",
    "ogr"
)

if not our_layer.isValid():
    raise Exception("Could not load our baseline.")

if not ga_layer.isValid():
    raise Exception("Could not load GA baseline.")

if our_layer.featureCount() != ga_layer.featureCount():
    raise Exception("Grid cell counts do not match.")

if our_layer.fields().indexFromName("label") == -1:
    raise Exception("Deposit label field missing.")

if our_layer.fields().indexFromName("iocg_score") == -1:
    raise Exception("Our score field missing.")

if ga_layer.fields().indexFromName("ga_mean") == -1:
    raise Exception("GA score field missing.")

# Read values by feature ID
our_scores = {}
ga_scores = {}
labels = {}

for feature in our_layer.getFeatures():
    fid = feature.id()
    our_scores[fid] = float(feature["iocg_score"])
    labels[fid] = feature["label"] == 1

for feature in ga_layer.getFeatures():
    fid = feature.id()
    ga_scores[fid] = float(feature["ga_mean"])

if set(our_scores) != set(ga_scores):
    raise Exception("Feature IDs do not match between layers.")

deposit_total = sum(labels.values())

if deposit_total == 0:
    raise Exception("No positive deposit cells found.")

print("\nBASELINE COMPARISON")
print("===================")
print("Grid cells:", len(our_scores))
print("Known deposit cells:", deposit_total)

def evaluate(scores, model_name):

    records = [
        {
            "fid": fid,
            "score": scores[fid],
            "positive": labels[fid]
        }
        for fid in scores
    ]

    records.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    total = len(records)

    print("\n", model_name)
    print("-" * len(model_name))

    for percentage in [5, 10, 20]:

        target_cells = total * percentage / 100.0
        selected_cells = 0
        captured = 0.0
        index = 0

        while index < total and selected_cells < target_cells:

            boundary_score = records[index]["score"]

            end = index

            while (
                end < total
                and records[end]["score"] == boundary_score
            ):
                end += 1

            group = records[index:end]
            group_size = len(group)

            remaining = target_cells - selected_cells
            fraction = min(1.0, remaining / group_size)

            group_deposits = sum(
                item["positive"] for item in group
            )

            captured += fraction * group_deposits
            selected_cells += fraction * group_size

            index = end

        capture_rate = captured / deposit_total * 100

        print(
            "Top", percentage, "%",
            "| Deposits captured:",
            round(captured, 4), "/", deposit_total,
            "| Capture rate:",
            round(capture_rate, 2), "%"
        )

evaluate(our_scores, "OUR EXPERT-WEIGHTED BASELINE")
evaluate(ga_scores, "GEOSCIENCE AUSTRALIA GA BASELINE")

print("\nCOMPARISON COMPLETED")
