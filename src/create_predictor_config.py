
import os
import csv
import json

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"
config_dir = os.path.join(project_dir, "config")
os.makedirs(config_dir, exist_ok=True)

# Values transcribed from the official
# IOCG Assessment Criteria Table.xlsx

predictors = [
    # SOURCES
    ("S1b", "s1b_mean", "Sources", "Y", "N", 0.8, 0.4, 0.8, 0.256),
    ("S2", "s2_mean", "Sources", "Y", "N", 0.8, 0.4, 0.6, 0.192),
    ("S3a", "s3a_mean", "Sources", "Y", "N", 0.8, 0.6, 0.8, 0.384),
    ("S3b", "s3b_mean", "Sources", "Y", "N", 0.8, 0.2, 0.8, 0.128),
    ("S4", "s4_mean", "Sources", "Y", "N", 0.6, 0.7, 0.8, 0.336),
    ("S5", "s5_mean", "Sources", "Y", "N", 0.9, 0.5, 0.7, 0.315),
    ("S6", "s6_mean", "Sources", "Y", "Y", 0.5, 0.3, 0.7, 0.105),

    # ENERGY / FLUID DRIVERS
    ("D1a", "d1a_mean", "Energy", "Y", "N", 0.8, 0.6, 0.4, 0.192),
    ("D1b", "d1b_mean", "Energy", "Y", "N", 0.8, 0.4, 0.4, 0.128),
    ("D1c", "d1c_mean", "Energy", "Y", "N", 0.8, 0.2, 0.4, 0.064),
    ("D2a", "d2a_mean", "Energy", "Y", "N", 0.8, 0.6, 0.8, 0.384),
    ("D2b", "d2b_mean", "Energy", "Y", "N", 0.8, 0.2, 0.8, 0.128),
    ("D2c", "d2c_mean", "Energy", "Y", "N", 0.8, 0.4, 0.8, 0.256),
    ("D2d", "d2d_mean", "Energy", "Y", "N", 0.8, 0.1, 0.8, 0.064),
    ("D3", "d3_mean", "Energy", "Y", "Y", 0.5, 0.3, 0.4, 0.060),

    # PATHWAYS
    ("P1", "p1_mean", "Pathways", "Y", "N", 0.8, 0.7, 0.5, 0.280),
    ("P2a", "p2a_mean", "Pathways", "Y", "Y", 1.0, 0.8, 0.4, 0.320),
    ("P2b", "p2b_mean", "Pathways", "Y", "Y", 1.0, 0.3, 0.4, 0.120),
    ("P3", "p3_mean", "Pathways", "Y", "Y", 0.8, 0.4, 0.5, 0.160),
    ("P4", "p4_mean", "Pathways", "Y", "Y", 0.5, 0.3, 0.7, 0.105),

    # ORE DEPOSITIONAL GRADIENTS
    ("T1a", "t1a_mean", "Deposition", "Y", "N", 0.5, 0.4, 0.6, 0.120),
    ("T1b1", "t1b1_mean", "Deposition", "Y", "Y", 1.0, 0.6, 0.5, 0.300),
    ("T1b2", "t1b2_mean", "Deposition", "Y", "Y", 1.0, 0.5, 0.5, 0.250),
    ("T1b3", "t1b3_mean", "Deposition", "Y", "Y", 1.0, 0.4, 0.5, 0.200),
    ("T1b4", "t1b4_mean", "Deposition", "Y", "Y", 1.0, 0.3, 0.5, 0.150),
    ("T1c1", "t1c1_mean", "Deposition", "Y", "Y", 1.0, 0.8, 0.5, 0.400),
    ("T1c2", "t1c2_mean", "Deposition", "Y", "Y", 1.0, 0.7, 0.5, 0.350),
    ("T1c3", "t1c3_mean", "Deposition", "Y", "Y", 1.0, 0.6, 0.5, 0.300),
    ("T1c4", "t1c4_mean", "Deposition", "Y", "Y", 1.0, 0.5, 0.5, 0.250),
    ("T2", "t2_mean", "Deposition", "Y", "Y", 1.0, 0.9, 0.5, 0.450),
    ("T3", "t3_mean", "Deposition", "Y", "N", 0.9, 0.7, 0.5, 0.315),
]

columns = [
    "criterion_code",
    "feature_field",
    "component",
    "IOCG_Comprehensive",
    "IOCG_Coverage",
    "importance",
    "applicability",
    "confidence",
    "official_final_weight"
]

records = [
    dict(zip(columns, row))
    for row in predictors
]

# Save CSV
csv_path = os.path.join(config_dir, "predictor_config.csv")

with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(records)

# Save JSON
json_path = os.path.join(config_dir, "predictor_config.json")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=4)

# Summary
print("PREDICTOR CONFIGURATION CREATED")
print("================================")
print("Total predictors:", len(records))

for component in ["Sources", "Energy", "Pathways", "Deposition"]:
    count = sum(1 for r in records if r["component"] == component)
    print(component + ":", count)

comprehensive = sum(
    1 for r in records if r["IOCG_Comprehensive"] == "Y"
)
coverage = sum(
    1 for r in records if r["IOCG_Coverage"] == "Y"
)

print("Comprehensive predictors:", comprehensive)
print("Coverage predictors:", coverage)
print("CSV:", csv_path)
print("JSON:", json_path)
