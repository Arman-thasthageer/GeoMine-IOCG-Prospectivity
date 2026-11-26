
from math import isfinite

layer = QgsProject.instance().mapLayersByName(
    "geological_features"
)[0]

feature_fields = [
    f.name() for f in layer.fields()
    if f.name().endswith("_mean")
]

stats = {
    name: {
        "min": None,
        "max": None,
        "zeros": 0,
        "sentinels": 0
    }
    for name in feature_fields
}

for ft in layer.getFeatures():
    for name in feature_fields:
        value = ft[name]

        if value is None:
            continue

        value = float(value)

        if not isfinite(value):
            continue

        s = stats[name]

        s["min"] = value if s["min"] is None else min(s["min"], value)
        s["max"] = value if s["max"] is None else max(s["max"], value)

        if value == 0:
            s["zeros"] += 1

        if value >= 2147483647:
            s["sentinels"] += 1

print("\nFEATURE RANGE REPORT")
print("====================")

for name, s in stats.items():
    print(
        name,
        "| MIN:", s["min"],
        "| MAX:", s["max"],
        "| ZERO COUNT:", s["zeros"],
        "| SENTINELS:", s["sentinels"]
    )
