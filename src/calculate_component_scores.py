
import os
import json

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsField,
    QgsFeature
)

from qgis.PyQt.QtCore import QVariant

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

config_path = os.path.join(
    project_dir, "config", "predictor_config.json"
)

output_path = os.path.join(
    project_dir, "data", "processed",
    "geological_component_scores.gpkg"
)

# --------------------------------------------------
# 2. LOAD CONFIGURATION
# --------------------------------------------------

with open(config_path, "r", encoding="utf-8") as f:
    predictors = json.load(f)

# Use only predictors included in the comprehensive model
predictors = [
    p for p in predictors
    if p["IOCG_Comprehensive"] == "Y"
]

assert len(predictors) == 31, "Expected 31 predictors"

components = [
    "Sources",
    "Energy",
    "Pathways",
    "Deposition"
]

component_fields = {
    "Sources": "sources_score",
    "Energy": "energy_score",
    "Pathways": "pathways_score",
    "Deposition": "deposition_score"
}

# --------------------------------------------------
# 3. GROUP PREDICTORS BY COMPONENT
# --------------------------------------------------

groups = {}

for component in components:
    groups[component] = [
        p for p in predictors
        if p["component"] == component
    ]

print("COMPONENT WEIGHT SUMMARY")

for component, items in groups.items():
    total_weight = sum(
        p["official_final_weight"] for p in items
    )

    print(
        component,
        "| Predictors:", len(items),
        "| Total weight:", round(total_weight, 4)
    )

# --------------------------------------------------
# 4. LOAD GEOLOGICAL FEATURE LAYER
# --------------------------------------------------

matches = QgsProject.instance().mapLayersByName(
    "geological_features"
)

if not matches:
    raise Exception(
        "geological_features layer not found. "
        "Load the GeoPackage into QGIS first."
    )

source = matches[0]

if not source.isValid():
    raise Exception("Source layer is invalid")

print("\nSOURCE FEATURES:", source.featureCount())

# Check that every configured field exists
source_field_names = [
    field.name() for field in source.fields()
]

for p in predictors:
    if p["feature_field"] not in source_field_names:
        raise Exception(
            "Missing feature field: " + p["feature_field"]
        )

# --------------------------------------------------
# 5. CREATE OUTPUT MEMORY LAYER
# --------------------------------------------------

geometry_type = source.geometryType()

if geometry_type != 2:
    raise Exception("Expected a polygon grid layer")

crs = source.crs().authid()

memory_layer = QgsVectorLayer(
    "Polygon?crs=" + crs,
    "geological_component_scores",
    "memory"
)

provider = memory_layer.dataProvider()

# Copy original attributes except the source primary key
attribute_names = [
    field.name()
    for field in source.fields()
    if field.name().lower() != "fid"
]

original_fields = [
    source.fields().field(name)
    for name in attribute_names
]

provider.addAttributes(original_fields)

# Add four component score fields
new_fields = [
    QgsField(name, QVariant.Double, len=20, prec=4)
    for name in component_fields.values()
]

provider.addAttributes(new_fields)
memory_layer.updateFields()

# --------------------------------------------------
# 6. CALCULATE COMPONENT SCORES
# --------------------------------------------------

output_features = []

for number, ft in enumerate(source.getFeatures(), start=1):

    values = {}

    for p in predictors:
        value = ft[p["feature_field"]]

        if value is None:
            raise Exception(
                "NULL value found in " + p["feature_field"]
            )

        value = float(value)

        if not 0 <= value <= 1000.001:
            raise Exception(
                "Unexpected value in " + p["feature_field"]
            )

        values[p["feature_field"]] = value / 1000.0

    scores = {}

    for component, items in groups.items():

        weighted_total = 0.0
        weight_total = 0.0

        for p in items:
            weight = float(p["official_final_weight"])
            value = values[p["feature_field"]]

            weighted_total += value * weight
            weight_total += weight

        if weight_total == 0:
            raise Exception(
                "Zero total weight for " + component
            )

        score = (weighted_total / weight_total) * 100.0

        scores[component] = score

    # Copy source attributes
    output_attributes = [
        ft[name] for name in attribute_names
    ]

    # Append four component scores
    output_attributes.extend([
        scores[component]
        for component in components
    ])

    output_feature = QgsFeature(memory_layer.fields())
    output_feature.setGeometry(ft.geometry())
    output_feature.setAttributes(output_attributes)

    output_features.append(output_feature)

    if number % 20000 == 0:
        print("Processed grid cells:", number)

# Add features to memory layer
provider.addFeatures(output_features)
memory_layer.updateExtents()

# --------------------------------------------------
# 7. SAVE AS GEOPACKAGE
# --------------------------------------------------

options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "GPKG"
options.layerName = "geological_component_scores"
options.fileEncoding = "UTF-8"

if os.path.exists(output_path):
    options.actionOnExistingFile = (
        QgsVectorFileWriter.CreateOrOverwriteFile
    )

result = QgsVectorFileWriter.writeAsVectorFormatV3(
    memory_layer,
    output_path,
    QgsProject.instance().transformContext(),
    options
)

if result[0] != QgsVectorFileWriter.NoError:
    raise Exception("GeoPackage save failed: " + str(result))

# --------------------------------------------------
# 8. LOAD OUTPUT INTO QGIS
# --------------------------------------------------

output_layer = QgsVectorLayer(
    output_path + "|layername=geological_component_scores",
    "geological_component_scores",
    "ogr"
)

if not output_layer.isValid():
    raise Exception("Output GeoPackage is invalid")

QgsProject.instance().addMapLayer(output_layer)

print("\nCOMPONENT SCORE CALCULATION COMPLETED")
print("=====================================")
print("Grid cells:", output_layer.featureCount())
print("CRS:", output_layer.crs().authid())
print("Output:", output_path)

print("New score fields:")

for name in component_fields.values():
    print(name)

print("\nOriginal geological_features layer was not modified.")
