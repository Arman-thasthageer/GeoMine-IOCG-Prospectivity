
import os
import csv
from collections import defaultdict

from qgis.core import (
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsProject,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsWkbTypes
)

from qgis.PyQt.QtCore import QVariant

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

GRID_FILE = os.path.join(
    BASE, "data", "processed",
    "geological_features_spatial_blocks.gpkg"
)

PREDICTION_FILE = os.path.join(
    BASE, "outputs",
    "final_pu_prospectivity.csv"
)

OUTPUT_FILE = os.path.join(
    BASE, "data", "processed",
    "final_pu_prospectivity.gpkg"
)

OUTPUT_LAYER_NAME = "final_pu_prospectivity"

print("=" * 70)
print("CREATING FULL-AREA PU PROSPECTIVITY GEOPACKAGE")
print("=" * 70)

# --------------------------------------------------
# 1. LOAD GRID
# --------------------------------------------------

print("\n1. LOADING ORIGINAL GRID")
print("-" * 50)

grid = QgsVectorLayer(
    GRID_FILE + "|layername=geological_features_spatial_blocks",
    "geological_features_spatial_blocks",
    "ogr"
)

if not grid.isValid():
    raise RuntimeError("Could not load original grid layer.")

if grid.featureCount() != 112179:
    raise ValueError(
        "Unexpected grid feature count: "
        + str(grid.featureCount())
    )

if grid.crs().authid() != "EPSG:3577":
    raise ValueError(
        "Expected EPSG:3577, found "
        + grid.crs().authid()
    )

print("Grid cells:", grid.featureCount())
print("CRS:", grid.crs().authid())
print("Geometry:", QgsWkbTypes.displayString(grid.wkbType()))

# --------------------------------------------------
# 2. LOAD PREDICTIONS
# --------------------------------------------------

print("\n2. LOADING PU PREDICTIONS")
print("-" * 50)

predictions = {}

with open(
    PREDICTION_FILE,
    "r",
    newline="",
    encoding="utf-8-sig"
) as f:

    reader = csv.DictReader(f)

    required = {
        "fid",
        "block_id",
        "label",
        "pu_score",
        "model_repetitions"
    }

    missing = required - set(reader.fieldnames or [])

    if missing:
        raise ValueError(
            "Missing prediction columns: "
            + str(sorted(missing))
        )

    for row in reader:

        fid = int(row["fid"])
        score = float(row["pu_score"])

        if fid in predictions:
            raise ValueError(
                "Duplicate prediction fid: " + str(fid)
            )

        if not (0 <= score <= 1):
            raise ValueError(
                "Invalid PU score for fid " + str(fid)
            )

        predictions[fid] = {
            "score": score,
            "block_id": row["block_id"],
            "label": row["label"]
        }

print("Prediction records:", len(predictions))

if len(predictions) != 112179:
    raise ValueError("Expected 112179 prediction records.")

# --------------------------------------------------
# 3. CALCULATE RANK AND PERCENTILE
# --------------------------------------------------

print("\n3. CALCULATING PU RANKS")
print("-" * 50)

score_groups = defaultdict(list)

for fid, data in predictions.items():
    score_groups[data["score"]].append(fid)

unique_scores_desc = sorted(
    score_groups.keys(),
    reverse=True
)

rank_by_fid = {}

current_position = 1

for score in unique_scores_desc:

    tied_fids = score_groups[score]
    tie_count = len(tied_fids)

    # Average rank for tied scores
    average_rank = (
        current_position
        + current_position + tie_count - 1
    ) / 2.0

    for fid in tied_fids:
        rank_by_fid[fid] = average_rank

    current_position += tie_count

total_cells = len(predictions)

percentile_by_fid = {}

for fid, rank in rank_by_fid.items():

    if total_cells > 1:
        percentile = (
            (total_cells - rank)
            / (total_cells - 1)
        ) * 100.0
    else:
        percentile = 100.0

    percentile_by_fid[fid] = percentile

print("Unique score values:", len(unique_scores_desc))
print("Ranked grid cells:", len(rank_by_fid))

# --------------------------------------------------
# 4. CREATE OUTPUT MEMORY LAYER
# --------------------------------------------------

print("\n4. CREATING GIS OUTPUT LAYER")
print("-" * 50)

geometry_type = QgsWkbTypes.displayString(
    grid.wkbType()
)

memory = QgsVectorLayer(
    geometry_type + "?crs=EPSG:3577",
    OUTPUT_LAYER_NAME,
    "memory"
)

provider = memory.dataProvider()

output_fields = QgsFields()

# Preserve source attributes except provider-managed fid
for field in grid.fields():

    if field.name().lower() == "fid":
        continue

    output_fields.append(field)

# Add original feature ID as a normal attribute
output_fields.append(
    QgsField("grid_fid", QVariant.LongLong)
)

output_fields.append(
    QgsField("pu_score", QVariant.Double)
)

output_fields.append(
    QgsField("pu_rank", QVariant.Double)
)

output_fields.append(
    QgsField("pu_percentile", QVariant.Double)
)

provider.addAttributes(output_fields)
memory.updateFields()

# --------------------------------------------------
# 5. JOIN SCORES TO GRID GEOMETRIES
# --------------------------------------------------

print("\n5. JOINING PU SCORES TO GRID CELLS")
print("-" * 50)

new_features = []
matched = 0
missing = 0

for source_feature in grid.getFeatures():

    fid = source_feature.id()

    if fid not in predictions:
        missing += 1
        continue

    data = predictions[fid]

    feature = QgsFeature(memory.fields())

    feature.setGeometry(source_feature.geometry())

    # Preserve source attributes except provider fid
    attributes = []

    for field in grid.fields():

        if field.name().lower() == "fid":
            continue

        attributes.append(
            source_feature[field.name()]
        )

    attributes.extend([
        fid,
        data["score"],
        rank_by_fid[fid],
        percentile_by_fid[fid]
    ])

    feature.setAttributes(attributes)

    new_features.append(feature)
    matched += 1

if missing > 0:
    raise ValueError(
        "Grid cells without predictions: "
        + str(missing)
    )

if matched != 112179:
    raise ValueError(
        "Unexpected matched feature count: "
        + str(matched)
    )

provider.addFeatures(new_features)
memory.updateExtents()

print("Matched grid cells:", matched)
print("Missing predictions:", missing)
print("Output memory features:", memory.featureCount())

# --------------------------------------------------
# 6. SAVE GEOPACKAGE
# --------------------------------------------------

print("\n6. SAVING GEOPACKAGE")
print("-" * 50)

if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "GPKG"
options.layerName = OUTPUT_LAYER_NAME
options.fileEncoding = "UTF-8"

result = QgsVectorFileWriter.writeAsVectorFormatV3(
    memory,
    OUTPUT_FILE,
    QgsProject.instance().transformContext(),
    options
)

error_code = result[0]

if error_code != QgsVectorFileWriter.NoError:
    raise RuntimeError(
        "GeoPackage writing failed: " + str(result)
    )

print("Saved:", OUTPUT_FILE)

# --------------------------------------------------
# 7. RELOAD AND VALIDATE OUTPUT
# --------------------------------------------------

print("\n7. RELOADING AND VALIDATING OUTPUT")
print("-" * 50)

output = QgsVectorLayer(
    OUTPUT_FILE + "|layername=" + OUTPUT_LAYER_NAME,
    OUTPUT_LAYER_NAME,
    "ogr"
)

if not output.isValid():
    raise RuntimeError("Saved GeoPackage could not be reopened.")

if output.featureCount() != 112179:
    raise ValueError(
        "Saved output has incorrect feature count: "
        + str(output.featureCount())
    )

required_output_fields = {
    "grid_fid",
    "pu_score",
    "pu_rank",
    "pu_percentile"
}

actual_fields = {
    field.name() for field in output.fields()
}

if not required_output_fields.issubset(actual_fields):
    raise ValueError("Required output fields are missing.")

score_values = [
    feature["pu_score"]
    for feature in output.getFeatures()
]

percentile_values = [
    feature["pu_percentile"]
    for feature in output.getFeatures()
]

print("Output features:", output.featureCount())
print("Output CRS:", output.crs().authid())
print("Output fields:", output.fields().names())
print("PU score minimum:", min(score_values))
print("PU score maximum:", max(score_values))
print("Percentile minimum:", min(percentile_values))
print("Percentile maximum:", max(percentile_values))

# Add output to current QGIS project
QgsProject.instance().addMapLayer(output)

print("\n" + "=" * 70)
print("FULL-AREA PU GEOPACKAGE CREATED SUCCESSFULLY")
print("=" * 70)
