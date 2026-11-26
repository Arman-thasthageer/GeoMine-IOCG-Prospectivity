
import os
import glob
import processing

from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsVectorFileWriter
)
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsVectorFileWriter
)
# 1. Project paths
base = r"C:\Users\Ermus\Desktop\GeoMine"

raster_folder = os.path.join(
    base, "data", "raw", "input_rasters", "IOCG_Input_Data"
)

output_file = os.path.join(
    base, "data", "processed", "geological_features.gpkg"
)

# 2. Get the labelled grid
project = QgsProject.instance()

layers = project.mapLayersByName("grid_labeled")

if not layers:
    raise Exception("grid_labeled layer not found in QGIS!")

current = layers[0]

if not current.isValid():
    raise Exception("The grid_labeled layer is invalid!")

print("Starting grid:", current.featureCount())

# 3. Find all geological rasters
raster_files = sorted(
    glob.glob(os.path.join(raster_folder, "*_norm_int.tif"))
)

print("Rasters found:", len(raster_files))

if len(raster_files) != 31:
    raise Exception(
        f"Expected 31 geological rasters, found {len(raster_files)}"
    )

# 4. Extract mean values from every raster
for index, raster_path in enumerate(raster_files, start=1):

    raster_name = os.path.basename(raster_path)
    prefix = raster_name.replace("_norm_int.tif", "").lower() + "_"

    raster = QgsRasterLayer(raster_path, raster_name)

    if not raster.isValid():
        raise Exception("Invalid raster: " + raster_path)

    print(
        f"[{index}/31] Processing {raster_name}"
    )

    result = processing.run(
        "native:zonalstatisticsfb",
        {
            "INPUT": current,
            "INPUT_RASTER": raster,
            "RASTER_BAND": 1,
            "COLUMN_PREFIX": prefix,
            "STATISTICS": [2],
            "OUTPUT": "memory:"
        }
    )

    current = result["OUTPUT"]

    if not current.isValid():
        raise Exception(
            "Zonal statistics failed for " + raster_name
        )

    print("Completed:", prefix + "mean")

# 5. Save the final feature dataset
options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "GPKG"
options.layerName = "geological_features"

result = QgsVectorFileWriter.writeAsVectorFormatV3(
    current,
    output_file,
    project.transformContext(),
    options
)

if result[0] != QgsVectorFileWriter.NoError:
    raise Exception("Could not save output: " + str(result))

# 6. Load final output into QGIS
final_layer = QgsVectorLayer(
    output_file + "|layername=geological_features",
    "geological_features",
    "ogr"
)

if not final_layer.isValid():
    raise Exception("Final output layer could not be loaded!")

project.addMapLayer(final_layer)

print("--------------------------------")
print("FEATURE EXTRACTION COMPLETED")
print("Total grid cells:", final_layer.featureCount())
print("Output:", output_file)
print("Total fields:", len(final_layer.fields()))
print("--------------------------------")
