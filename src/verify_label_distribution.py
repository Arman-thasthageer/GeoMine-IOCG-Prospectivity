
from qgis.core import QgsVectorLayer

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\geological_features.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=geological_features",
    "label_verification",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load geological_features.")

label_index = layer.fields().indexFromName("label")

if label_index == -1:
    raise Exception("Label field not found.")

counts = {
    "NULL": 0,
    "ZERO": 0,
    "ONE": 0,
    "OTHER": 0
}

for feature in layer.getFeatures():

    value = feature["label"]

    if value is None:
        counts["NULL"] += 1
    elif value == 0:
        counts["ZERO"] += 1
    elif value == 1:
        counts["ONE"] += 1
    else:
        counts["OTHER"] += 1

print("\nLABEL DISTRIBUTION VERIFICATION")
print("================================")
print("Total cells:", layer.featureCount())

for key, value in counts.items():
    print(key, ":", value)

print("\nLABEL FIELD TYPE:", layer.fields()[label_index].typeName())
print("VERIFICATION COMPLETED")
