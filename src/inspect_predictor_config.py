
import os
import csv

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

config_file = os.path.join(
    project_dir,
    "config",
    "predictor_config.csv"
)

print("======================================")
print("PREDICTOR CONFIGURATION INSPECTION")
print("======================================")

with open(
    config_file,
    "r",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    print("\nCSV COLUMN HEADERS:")
    print(reader.fieldnames)

    print("\nFIRST FIVE ROWS:")
    for index, row in enumerate(reader):
        print(row)

        if index == 4:
            break

print("\nINSPECTION COMPLETED")
