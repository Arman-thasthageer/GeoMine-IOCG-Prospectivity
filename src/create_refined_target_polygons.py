
import os
import csv
from collections import deque, defaultdict

from qgis.core import (
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsProject,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsWkbTypes
)

from qgis.PyQt.QtCore import QVariant

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

INPUT = os.path.join(
    BASE, "data", "processed",
    "final_pu_prospectivity.gpkg"
)

OUTPUT = os.path.join(
    BASE, "data", "processed",
    "pu_refined_target_polygons.gpkg"
)

THRESHOLD = 99.0
MINIMUM_CELLS = 3

print("=" * 70)
print("CREATING REFINED IOCG TARGET POLYGONS")
print("=" * 70)

# --------------------------------------------------
# 1. LOAD PROSPECTIVITY GRID
# --------------------------------------------------

layer = QgsVectorLayer(
    INPUT + "|layername=final_pu_prospectivity",
    "final_pu_prospectivity",
    "ogr"
)

if not layer.isValid():
    raise RuntimeError("Could not load prospectivity layer.")

if layer.crs().authid() != "EPSG:3577":
    raise ValueError("Expected EPSG:3577.")

print("\nInput cells:", layer.featureCount())
print("Threshold percentile:", THRESHOLD)

# --------------------------------------------------
# 2. COLLECT HIGH-SCORING CELLS
# --------------------------------------------------

cells = {}

for feature in layer.getFeatures():

    percentile = float(feature["pu_percentile"])

    if percentile < THRESHOLD:
        continue

    position = (
        int(feature["row_index"]),
        int(feature["col_index"])
    )

    if position in cells:
        raise ValueError("Duplicate grid position.")

    cells[position] = {
        "geometry": QgsGeometry(feature.geometry()),
        "score": float(feature["pu_score"]),
        "percentile": percentile,
        "label": str(feature["label"]).strip()
    }

print("Selected cells:", len(cells))

# --------------------------------------------------
# 3. FIND CONNECTED CLUSTERS
# --------------------------------------------------

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

    positions = []

    while queue:

        current = queue.popleft()
        positions.append(current)

        row, col = current

        for dr, dc in neighbours:

            neighbour = (row + dr, col + dc)

            if neighbour in cells and neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)

    if len(positions) < MINIMUM_CELLS:
        continue

    cluster_data = [cells[p] for p in positions]

    scores = [item["score"] for item in cluster_data]

    percentiles = [
        item["percentile"] for item in cluster_data
    ]

    deposits = sum(
        item["label"] == "1" for item in cluster_data
    )

    geometries = [
        QgsGeometry(item["geometry"])
        for item in cluster_data
    ]

    # Dissolve all cell geometries belonging to this cluster
    dissolved_geometry = QgsGeometry.unaryUnion(geometries)

    if dissolved_geometry.isNull() or dissolved_geometry.isEmpty():
        raise RuntimeError("Failed to dissolve cluster geometry.")

    if not dissolved_geometry.isGeosValid():
        dissolved_geometry = dissolved_geometry.makeValid()

    if dissolved_geometry.isEmpty():
        raise RuntimeError("Invalid dissolved cluster geometry.")

    area_km2 = dissolved_geometry.area() / 1000000.0

    centroid = dissolved_geometry.centroid()

    centroid_point = centroid.asPoint()

    clusters.append({
        "geometry": dissolved_geometry,
        "cell_count": len(positions),
        "area_km2": area_km2,
        "mean_score": sum(scores) / len(scores),
        "max_score": max(scores),
        "mean_percentile": sum(percentiles) / len(percentiles),
        "known_deposits": deposits,
        "centroid_x": centroid_point.x(),
        "centroid_y": centroid_point.y()
    })

# --------------------------------------------------
# 4. SORT CLUSTERS BY MEAN PU SCORE
# --------------------------------------------------

clusters.sort(
    key=lambda c: (
        c["mean_score"],
        c["cell_count"],
        c["max_score"]
    ),
    reverse=True
)

print("\nConnected clusters:", len(clusters))

if len(clusters) != 11:
    raise ValueError(
        "Expected 11 clusters, found " + str(len(clusters))
    )

# --------------------------------------------------
# 5. CREATE POLYGON MEMORY LAYER
# --------------------------------------------------

memory = QgsVectorLayer(
    "MultiPolygon?crs=EPSG:3577",
    "pu_refined_target_polygons",
    "memory"
)

provider = memory.dataProvider()

fields = QgsFields()

fields.append(QgsField("target_id", QVariant.String))
fields.append(QgsField("cell_count", QVariant.Int))
fields.append(QgsField("area_km2", QVariant.Double))
fields.append(QgsField("mean_score", QVariant.Double))
fields.append(QgsField("max_score", QVariant.Double))
fields.append(QgsField("mean_pct", QVariant.Double))
fields.append(QgsField("deposit_cells", QVariant.Int))
fields.append(QgsField("centroid_x", QVariant.Double))
fields.append(QgsField("centroid_y", QVariant.Double))

provider.addAttributes(fields)
memory.updateFields()

# --------------------------------------------------
# 6. ADD CLUSTER POLYGONS
# --------------------------------------------------

print("\nTARGET POLYGON SUMMARY")
print("-" * 70)

new_features = []

for index, cluster in enumerate(clusters, start=1):

    target_id = "R" + str(index)

    feature = QgsFeature(memory.fields())

    feature.setGeometry(cluster["geometry"])

    feature.setAttributes([
        target_id,
        cluster["cell_count"],
        cluster["area_km2"],
        cluster["mean_score"],
        cluster["max_score"],
        cluster["mean_percentile"],
        cluster["known_deposits"],
        cluster["centroid_x"],
        cluster["centroid_y"]
    ])

    new_features.append(feature)

    print(
        target_id,
        "| Cells:", cluster["cell_count"],
        "| Actual area:", round(cluster["area_km2"], 2), "km2",
        "| Mean score:", round(cluster["mean_score"], 4),
        "| Deposit cells:", cluster["known_deposits"]
    )

provider.addFeatures(new_features)
memory.updateExtents()

# --------------------------------------------------
# 7. SAVE GEOPACKAGE
# --------------------------------------------------

print("\nSAVING TARGET POLYGONS")
print("-" * 70)

if os.path.exists(OUTPUT):
    os.remove(OUTPUT)

options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "GPKG"
options.layerName = "pu_refined_target_polygons"
options.fileEncoding = "UTF-8"

result = QgsVectorFileWriter.writeAsVectorFormatV3(
    memory,
    OUTPUT,
    QgsProject.instance().transformContext(),
    options
)

if result[0] != QgsVectorFileWriter.NoError:
    raise RuntimeError("GeoPackage save failed: " + str(result))

# --------------------------------------------------
# 8. RELOAD AND VALIDATE
# --------------------------------------------------

output_layer = QgsVectorLayer(
    OUTPUT + "|layername=pu_refined_target_polygons",
    "pu_refined_target_polygons",
    "ogr"
)

if not output_layer.isValid():
    raise RuntimeError("Could not reopen output GeoPackage.")

if output_layer.featureCount() != 11:
    raise ValueError("Expected 11 target polygons.")

print("\nOUTPUT VALIDATION")
print("-" * 70)
print("Polygon features:", output_layer.featureCount())
print("CRS:", output_layer.crs().authid())
print("Geometry:", QgsWkbTypes.displayString(output_layer.wkbType()))
print("Fields:", output_layer.fields().names())

# Add target polygon layer to QGIS
QgsProject.instance().addMapLayer(output_layer)

print("\nSaved:", OUTPUT)

print("\n" + "=" * 70)
print("REFINED TARGET POLYGON CREATION COMPLETED")
print("=" * 70)
