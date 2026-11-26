
from pathlib import Path
from openpyxl import load_workbook
import csv

project_dir = Path(__file__).resolve().parent.parent
excel_file = project_dir / "data" / "raw" / "australian_deposits.xlsx"
output_dir = project_dir / "data" / "processed"

output_dir.mkdir(parents=True, exist_ok=True)

workbook = load_workbook(
    excel_file,
    read_only=True,
    data_only=True
)

sheet = workbook["Australia"]

rows = sheet.iter_rows(values_only=True)
headers = list(next(rows))

required_columns = [
    "Deposit",
    "Principal deposit group",
    "Principal deposit type",
    "Longitude",
    "Latitude",
    "State",
    "District",
    "Province"
]

indexes = {name: headers.index(name) for name in required_columns}

iocg_records = []

for row in rows:
    group = row[indexes["Principal deposit group"]]

    if group and group.strip() == "Iron oxide copper-gold":
        record = {
            name: row[indexes[name]]
            for name in required_columns
        }
        iocg_records.append(record)

output_file = output_dir / "iocg_deposits_review.csv"

with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=required_columns)
    writer.writeheader()
    writer.writerows(iocg_records)

print("IOCG RECORDS:", len(iocg_records))
print("\nDEPOSIT TYPE COUNTS:")

from collections import Counter

type_counts = Counter(
    record["Principal deposit type"]
    for record in iocg_records
)

for deposit_type, count in type_counts.items():
    print(deposit_type, ":", count)

print("\nDEPOSIT RECORDS:")

for record in iocg_records:
    print(
        record["Deposit"],
        "|",
        record["Principal deposit type"],
        "| Longitude:", record["Longitude"],
        "| Latitude:", record["Latitude"]
    )

print("\nCSV SAVED:", output_file)
