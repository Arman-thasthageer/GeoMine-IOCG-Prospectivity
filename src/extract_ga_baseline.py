
import os
import processing

from qgis.core import (
    QgsApplication,
    QgsVectorLayer,
    QgsProject
)

# =====================================================
# 1. PATHS
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "geological_features.gpkg"
)

raster_file = os.path.join(
    project_dir,
    "data",
    "raw",
    "baseline_maps",
    "IOCG_Prospectivity",
    "IOCG_Final.tif"
)

output_file = os.path.join(
    project_dir,
    "data",
    "processed",
    "ga_baseline_grid.gpkg"
)

# =====================================================
# 2. CHECK INPUTS
# =====================================================

if not os.path.exists(input_file):
    raise Exception("Geological features file not found.")

if not os.path.exists(raster_file):
    raise Exception("GA final raster not found.")

if os.path.exists(output_file):
    raise Exception(
        "Output already exists. Rename or remove it manually: "
        + output_file
    )

# =====================================================
# 3. LOAD INPUT LAYERS
# =====================================================

print("Loading grid layer...")

grid = QgsVectorLayer(
    input_file + "|layername=geological_features",
    "geological_features",
    "ogr"
)

if not grid.isValid():
    raise Exception("Could not load geological features.")

print("Grid cells:", grid.featureCount())
print("Grid CRS:", grid.crs().authid())

print("\nLoading GA raster...")

raster = QgsRasterLayer(
    raster_file,
    "GA_Final"
)

if not raster.isValid():
    raise Exception("Could not load GA raster.")

print("GA raster CRS:", raster.crs().authid())

# =====================================================
# 4. RUN ZONAL STATISTICS
# =====================================================

print("\nExtracting GA mean values...")
print("Method: Mean zonal statistics")
print("Raster band: 1")

parameters = {
    "INPUT": grid,
    "INPUT_RASTER": raster,
    "RASTER_BAND": 1,
    "COLUMN_PREFIX": "ga_",
    "STATISTICS": [2],
    "OUTPUT": output_file
}

result = processing.run(
    "native:zonalstatisticsfb",
    parameters
)

print("\nZonal statistics completed.")

# =====================================================
# 5. VERIFY OUTPUT
# =====================================================

output = QgsVectorLayer(
    output_file + "|layername=ga_baseline_grid",
    "GA Baseline Grid",
    "ogr"
)

if not output.isValid():
    raise Exception("Could not load output layer.")

if output.featureCount() != grid.featureCount():
    raise Exception("Input and output cell counts differ.")

field_index = output.fields().indexFromName("ga_mean")

if field_index == -1:
    raise Exception("ga_mean field was not created.")

null_count = 0
valid_count = 0
minimum = float("inf")
maximum = float("-inf")
total = 0.0

for feature in output.getFeatures():

    value = feature["ga_mean"]

    if value is None:
        null_count += 1
        continue

    value = float(value)

    if value < -1e-10 or value > 1.0:
        raise Exception(
            "Unexpected GA value: " + str(value)
        )

    valid_count += 1
    total += value

    minimum = min(minimum, value)
    maximum = max(maximum, value)

if valid_count == 0:
    raise Exception("No valid GA values were extracted.")

print("\nGA BASELINE EXTRACTION VALIDATION")
print("=================================")
print("Total grid cells:", output.featureCount())
print("Valid GA values:", valid_count)
print("NULL GA values:", null_count)
print("Minimum GA mean:", minimum)
print("Maximum GA mean:", maximum)
print("Mean of grid-cell GA means:", total / valid_count)
print("Output:", output_file)

QgsProject.instance().addMapLayer(output)

print("\nGA BASELINE EXTRACTION COMPLETED")
