
import os
import math
import gc

from qgis.core import (
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsProject,
    QgsField
)
from qgis.PyQt.QtCore import QVariant


# =====================================================
# 1. PROJECT PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "geological_component_scores.gpkg"
)

output_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "iocg_prospectivity_v4.gpkg"
)

layer_name = "iocg_prospectivity_v4"

component_fields = [
    "sources_score",
    "energy_score",
    "pathways_score",
    "deposition_score"
]


# =====================================================
# 2. CHECK FILES
# =====================================================

if not os.path.exists(input_file):
    raise Exception("Input file not found: " + input_file)

if os.path.exists(output_file):
    raise Exception(
        "Output already exists. Rename or remove it manually:\n"
        + output_file
    )


# =====================================================
# 3. LOAD SOURCE LAYER
# =====================================================

print("Loading component scores...")

source = QgsVectorLayer(
    input_file + "|layername=geological_component_scores",
    "component_scores_source",
    "ogr"
)

if not source.isValid():
    raise Exception("Could not load source layer.")

total_cells = source.featureCount()

for name in component_fields:
    if source.fields().indexFromName(name) == -1:
        raise Exception("Missing field: " + name)

print("Total input cells:", total_cells)


# =====================================================
# 4. CREATE NEW OUTPUT GEOPACKAGE
# =====================================================

print("Creating independent output GeoPackage...")

options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "GPKG"
options.layerName = layer_name

result = QgsVectorFileWriter.writeAsVectorFormatV3(
    source,
    output_file,
    QgsProject.instance().transformContext(),
    options
)

if result[0] != QgsVectorFileWriter.NoError:
    raise Exception("GeoPackage creation failed: " + str(result))

del source
gc.collect()


# =====================================================
# 5. LOAD OUTPUT LAYER
# =====================================================

print("Loading output layer...")

layer = QgsVectorLayer(
    output_file + "|layername=" + layer_name,
    "IOCG Prospectivity Final",
    "ogr"
)

if not layer.isValid():
    raise Exception("Output layer could not be loaded.")

if layer.featureCount() != total_cells:
    raise Exception("Input and output feature counts differ.")


# =====================================================
# 6. ADD FINAL SCORE FIELD
# =====================================================

print("Adding iocg_score field...")

if not layer.startEditing():
    raise Exception("Could not start editing.")

if not layer.addAttribute(
    QgsField("iocg_score", QVariant.Double, "double", 12, 4)
):
    layer.rollBack()
    raise Exception("Could not add iocg_score field.")

layer.updateFields()

score_index = layer.fields().indexFromName("iocg_score")

if score_index == -1:
    layer.rollBack()
    raise Exception("iocg_score field was not created.")


# =====================================================
# 7. CALCULATE FINAL SCORES
# =====================================================

print("Calculating geometric mean...")

processed = 0
zero_scores = 0

minimum = float("inf")
maximum = float("-inf")

for feature in layer.getFeatures():

    values = [
        float(feature[name])
        for name in component_fields
    ]

    # Validate component values
    if any(
        not math.isfinite(value)
        or value < 0
        or value > 100
        for value in values
    ):
        layer.rollBack()
        raise Exception(
            "Invalid component score at feature ID "
            + str(feature.id())
        )

    # Normalize values to 0-1
    normalized = [
        value / 100.0
        for value in values
    ]

    # Equal-weight geometric mean
    if any(value == 0 for value in normalized):
        final_score = 0.0
        zero_scores += 1
    else:
        final_score = (
            math.prod(normalized) ** 0.25
        ) * 100.0

    # Update through QGIS editing buffer
    success = layer.changeAttributeValue(
        feature.id(),
        score_index,
        final_score
    )

    if not success:
        layer.rollBack()
        raise Exception(
            "Could not update feature ID "
            + str(feature.id())
        )

    minimum = min(minimum, final_score)
    maximum = max(maximum, final_score)

    processed += 1

    if processed % 10000 == 0:
        print("Processed:", processed, "/", total_cells)


# =====================================================
# 8. SAVE CHANGES
# =====================================================

print("Saving final scores...")

if not layer.commitChanges():
    errors = layer.commitErrors()
    layer.rollBack()
    raise Exception("Could not save changes: " + str(errors))

print("All changes committed successfully.")


# =====================================================
# 9. VERIFY SAVED LAYER
# =====================================================

print("Validating saved output...")

# Reload the saved file to verify persisted values
QgsProject.instance().removeMapLayer(layer.id())

del layer
gc.collect()

check_layer = QgsVectorLayer(
    output_file + "|layername=" + layer_name,
    "IOCG Prospectivity Final",
    "ogr"
)

if not check_layer.isValid():
    raise Exception("Could not reopen saved GeoPackage.")

null_count = 0
invalid_count = 0
verified_count = 0

for feature in check_layer.getFeatures():

    value = feature["iocg_score"]

    if value is None:
        null_count += 1
        continue

    value = float(value)

    if not math.isfinite(value) or value < 0 or value > 100:
        invalid_count += 1

    verified_count += 1

if check_layer.featureCount() != total_cells:
    raise Exception("Saved feature count mismatch.")

if null_count > 0 or invalid_count > 0:
    raise Exception(
        "Validation failed. NULL: "
        + str(null_count)
        + ", INVALID: "
        + str(invalid_count)
    )

QgsProject.instance().addMapLayer(check_layer)


# =====================================================
# 10. FINAL REPORT
# =====================================================

print("\n========================================")
print("FINAL IOCG PROSPECTIVITY CALCULATION")
print("========================================")

print("Total cells:", total_cells)
print("Processed cells:", processed)
print("Verified cells:", verified_count)

print("\nCOMPONENT WEIGHTS")
print("Sources: 25%")
print("Energy: 25%")
print("Pathways: 25%")
print("Deposition: 25%")

print("\nFINAL SCORE STATISTICS")
print("Minimum score:", round(minimum, 4))
print("Maximum score:", round(maximum, 4))
print("Zero-score cells:", zero_scores)

print("\nVALIDATION")
print("NULL scores:", null_count)
print("Invalid scores:", invalid_count)

print("\nOUTPUT FILE:")
print(output_file)

print("\nOriginal component scores were not modified.")
print("FINAL IOCG PROSPECTIVITY COMPLETED SUCCESSFULLY")
