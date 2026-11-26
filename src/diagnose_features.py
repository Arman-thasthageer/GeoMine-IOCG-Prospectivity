
from math import isnan, isfinite

layer = QgsProject.instance().mapLayersByName("geological_features")[0]

feature_fields = [
    field.name()
    for field in layer.fields()
    if field.name().endswith("_mean")
]

print("\nFEATURE VALUE DIAGNOSTIC")
print("========================")

for name in feature_fields:
    total = 0
    null_count = 0
    nan_count = 0
    valid_count = 0
    sample_values = []

    for ft in layer.getFeatures():
        value = ft[name]
        total += 1

        if value is None:
            null_count += 1
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if isnan(value):
            nan_count += 1
        elif isfinite(value):
            valid_count += 1

            if len(sample_values) < 3:
                sample_values.append(value)

    print(
        name,
        "| TOTAL:", total,
        "| NULL:", null_count,
        "| NaN:", nan_count,
        "| VALID:", valid_count,
        "| SAMPLE:", sample_values
    )
