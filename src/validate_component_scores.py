
from qgis.core import QgsVectorLayer
from math import isfinite

path = r"C:\Users\Ermus\Desktop\GeoMine\data\processed\geological_component_scores.gpkg"

layer = QgsVectorLayer(
    path + "|layername=geological_component_scores",
    "component_validation",
    "ogr"
)

if not layer.isValid():
    raise Exception("Component score layer is invalid")

fields = [
    "sources_score",
    "energy_score",
    "pathways_score",
    "deposition_score"
]

print("\nCOMPONENT SCORE VALIDATION")
print("===========================")
print("Total grid cells:", layer.featureCount())

for name in fields:
    minimum = float("inf")
    maximum = float("-inf")
    null_count = 0
    invalid_count = 0

    for ft in layer.getFeatures():
        value = ft[name]

        if value is None:
            null_count += 1
            continue

        value = float(value)

        if not isfinite(value):
            invalid_count += 1
            continue

        minimum = min(minimum, value)
        maximum = max(maximum, value)

    print(
        name,
        "| MIN:", round(minimum, 4),
        "| MAX:", round(maximum, 4),
        "| NULL:", null_count,
        "| INVALID:", invalid_count
    )

print("\nVALIDATION FINISHED")
