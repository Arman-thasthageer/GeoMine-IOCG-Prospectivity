
import os
import csv
from collections import deque
from qgis.core import QgsVectorLayer

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

INPUT = os.path.join(
    BASE, "data", "processed",
    "final_pu_prospectivity.gpkg"
)

OUTPUT = os.path.join(
    BASE, "reports",
    "pu_refined_clusters_99.csv"
)

THRESHOLD = 99.0
MINIMUM_CELLS = 3

layer = QgsVectorLayer(
    INPUT + "|layername=final_pu_prospectivity",
    "final_pu_prospectivity",
    "ogr"
)

if not layer.isValid():
    raise RuntimeError("Could not load PU layer.")

print("=" * 65)
print("REFINED PU TARGET CLUSTER ANALYSIS")
print("=" * 65)

cells = {}

for feature in layer.getFeatures():

    if float(feature["pu_percentile"]) < THRESHOLD:
        continue

    position = (
        int(feature["row_index"]),
        int(feature["col_index"])
    )

    cells[position] = {
        "score": float(feature["pu_score"]),
        "percentile": float(feature["pu_percentile"]),
        "label": str(feature["label"]).strip()
    }

print("\nThreshold:", THRESHOLD)
print("Selected cells:", len(cells))
print("Selected area:", round(len(cells) * 4, 2), "km2")

neighbours = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

visited = set()
clusters = []

for start in cells:

    if start in visited:
        continue

    queue = deque([start])
    visited.add(start)
    cluster_positions = []

    while queue:

        current = queue.popleft()
        cluster_positions.append(current)

        row, col = current

        for dr, dc in neighbours:

            neighbour = (row + dr, col + dc)

            if neighbour in cells and neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)

    if len(cluster_positions) < MINIMUM_CELLS:
        continue

    data = [cells[p] for p in cluster_positions]

    scores = [item["score"] for item in data]
    percentiles = [item["percentile"] for item in data]

    deposits = sum(
        item["label"] == "1" for item in data
    )

    clusters.append({
        "cell_count": len(cluster_positions),
        "area_km2": len(cluster_positions) * 4,
        "mean_score": sum(scores) / len(scores),
        "max_score": max(scores),
        "mean_percentile": sum(percentiles) / len(percentiles),
        "known_deposits": deposits,
        "min_row": min(p[0] for p in cluster_positions),
        "max_row": max(p[0] for p in cluster_positions),
        "min_col": min(p[1] for p in cluster_positions),
        "max_col": max(p[1] for p in cluster_positions)
    })

clusters.sort(
    key=lambda c: (
        c["mean_score"],
        c["cell_count"],
        c["max_score"]
    ),
    reverse=True
)

print("\nREFINED CLUSTER COUNT:", len(clusters))
print("\nTOP REFINED CLUSTERS")
print("-" * 65)

for i, c in enumerate(clusters[:20], 1):

    print(
        "R" + str(i),
        "| Cells:", c["cell_count"],
        "| Area:", round(c["area_km2"], 2), "km2",
        "| Mean score:", round(c["mean_score"], 4),
        "| Maximum:", round(c["max_score"], 4),
        "| Known deposits:", c["known_deposits"]
    )

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:

    writer = csv.writer(f)

    writer.writerow([
        "target_id",
        "cell_count",
        "area_km2",
        "mean_pu_score",
        "maximum_pu_score",
        "mean_pu_percentile",
        "known_deposit_cells",
        "min_row",
        "max_row",
        "min_col",
        "max_col"
    ])

    for i, c in enumerate(clusters, 1):

        writer.writerow([
            "R" + str(i),
            c["cell_count"],
            round(c["area_km2"], 2),
            round(c["mean_score"], 6),
            round(c["max_score"], 6),
            round(c["mean_percentile"], 4),
            c["known_deposits"],
            c["min_row"],
            c["max_row"],
            c["min_col"],
            c["max_col"]
        ])

print("\nOutput:", OUTPUT)
print("\nREFINED CLUSTER ANALYSIS COMPLETED")
