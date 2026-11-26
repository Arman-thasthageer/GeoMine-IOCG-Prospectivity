
from qgis.core import QgsVectorLayer

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

input_file = (
    project_dir
    + r"\data\processed\geological_features.gpkg"
)

layer = QgsVectorLayer(
    input_file + "|layername=geological_features",
    "label_value_inspection",
    "ogr"
)

if not layer.isValid():
    raise Exception("Could not load geological_features.")

values = {}

for feature in layer.getFeatures():

    value = feature["label"]

    key = str(value)

    values[key] = values.get(key, 0) + 1

print("\nDISTINCT LABEL VALUES")
print("=====================")

for value, count in sorted(
    values.items(),
    key=lambda item: item[1],
    reverse=True
):
    print("Value:", value, "| Count:", count)

print("\nTOTAL DISTINCT VALUES:", len(values))
print("TOTAL FEATURES:", layer.featureCount())
print("\nINSPECTION COMPLETED")
