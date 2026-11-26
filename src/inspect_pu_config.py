
import os
import json

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

path = os.path.join(
    BASE, "config", "pu_learning_config.json"
)

print("=" * 60)
print("PU LEARNING CONFIGURATION")
print("=" * 60)

with open(path, "r", encoding="utf-8") as f:
    config = json.load(f)

for section, values in config.items():
    print("\nSECTION:", section)

    if isinstance(values, dict):
        for key, value in values.items():
            print(" ", key, ":", value)
    else:
        print(" ", values)

print("\nCONFIGURATION INSPECTION COMPLETED")
