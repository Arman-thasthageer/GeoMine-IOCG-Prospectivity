
import os
import sys
import csv
import sqlite3
import re
from pathlib import Path

BASE = Path(os.environ.get("GEOMINE_BASE", Path(__file__).resolve().parent.parent))
PACKAGE_DIR = BASE / "ml_packages"
sys.path.insert(0, str(PACKAGE_DIR))

from flask import Flask, jsonify, request
# ============================================================
# GEOMINE IOCG PROSPECTIVITY API
# ============================================================

BASE = Path(os.environ.get("GEOMINE_BASE", Path(__file__).resolve().parent.parent))

PACKAGE_DIR = BASE / "ml_packages"
sys.path.insert(0, str(PACKAGE_DIR))

EXPLANATIONS_FILE = BASE / "reports" / "cell_explanations.csv"

TARGETS_GPKG = (
    BASE / "data" / "processed" /
    "pu_refined_target_polygons.gpkg"
)

PU_GPKG = BASE / "data" / "processed" / "final_pu_prospectivity.gpkg"
EXPERT_GPKG = BASE / "data" / "processed" / "iocg_prospectivity_v4.gpkg"
GA_GPKG = BASE / "data" / "processed" / "ga_baseline_grid.gpkg"

app = Flask(__name__)

# ============================================================
# LOAD CELL EXPLANATIONS
# ============================================================

print("=" * 65)
print("STARTING GEOMINE API")
print("=" * 65)

if not EXPLANATIONS_FILE.exists():
    raise FileNotFoundError(
        f"Cell explanation CSV not found: {EXPLANATIONS_FILE}"
    )

CELL_DATA = {}

with open(
    EXPLANATIONS_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:

    reader = csv.DictReader(file)

    required_fields = {
        "grid_fid",
        "pu_score",
        "pu_percentile",
        "sources_score",
        "energy_score",
        "pathways_score",
        "deposition_score",
        "top_driver_1",
        "top_driver_2",
        "top_driver_3"
    }

    if not required_fields.issubset(set(reader.fieldnames or [])):
        raise ValueError("Explanation CSV is missing required fields.")

    for row in reader:
        cell_id = str(row["grid_fid"]).strip()

        if cell_id:
            if cell_id in CELL_DATA:
                raise ValueError(f"Duplicate grid_fid: {cell_id}")

            CELL_DATA[cell_id] = row

print("Explanation records loaded:", len(CELL_DATA))


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_cell_record(cell_id):
    return CELL_DATA.get(str(cell_id).strip())


def get_target_table():
    if not TARGETS_GPKG.exists():
        raise FileNotFoundError(str(TARGETS_GPKG))

    connection = sqlite3.connect(str(TARGETS_GPKG))
    connection.row_factory = sqlite3.Row

    try:
        result = connection.execute("""
            SELECT table_name
            FROM gpkg_contents
            WHERE data_type = 'features'
              AND table_name = 'pu_refined_target_polygons'
        """).fetchone()

        if result is None:
            raise RuntimeError("Target polygon layer not found.")

        return connection

    except Exception:
        connection.close()
        raise


def get_targets_data():
    connection = get_target_table()

    try:
        rows = connection.execute("""
            SELECT
                target_id,
                cell_count,
                area_km2,
                mean_score,
                max_score,
                mean_pct,
                deposit_cells,
                centroid_x,
                centroid_y
            FROM pu_refined_target_polygons
            ORDER BY mean_score DESC
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def build_cell_response(row):
    return {
        "grid_fid": integer(row.get("grid_fid")),
        "label": row.get("label"),
        "prospectivity": {
            "pu_score": number(row.get("pu_score")),
            "pu_percentile": number(row.get("pu_percentile"))
        },
        "components": {
            "sources": number(row.get("sources_score")),
            "energy": number(row.get("energy_score")),
            "pathways": number(row.get("pathways_score")),
            "deposition": number(row.get("deposition_score"))
        },
        "data_coverage": {
            "valid_predictors": integer(
                row.get("valid_predictor_count")
            ),
            "total_predictors": integer(
                row.get("total_predictor_count")
            ),
            "completeness_percent": number(
                row.get("predictor_completeness_percent")
            )
        }
    }


def build_explanation(row):
    drivers = []

    for index in range(1, 4):
        code = row.get(f"top_driver_{index}")

        if code:
            drivers.append({
                "criterion": code,
                "component": row.get(
                    f"top_driver_{index}_component"
                ),
                "weighted_component_contribution": number(
                    row.get(f"top_driver_{index}_contribution")
                )
            })

    return {
        "grid_fid": integer(row.get("grid_fid")),
        "pu_score": number(row.get("pu_score")),
        "pu_percentile": number(row.get("pu_percentile")),
        "component_scores": {
            "sources": number(row.get("sources_score")),
            "energy": number(row.get("energy_score")),
            "pathways": number(row.get("pathways_score")),
            "deposition": number(row.get("deposition_score"))
        },
        "top_geological_drivers": drivers,
        "data_coverage": {
            "valid_predictors": integer(
                row.get("valid_predictor_count")
            ),
            "total_predictors": integer(
                row.get("total_predictor_count")
            ),
            "completeness_percent": number(
                row.get("predictor_completeness_percent")
            )
        },
        "interpretation_note": (
            "Driver contributions represent weighted contributions "
            "to mineral-system component scores. They are not causal "
            "explanations of the Random Forest prediction."
        )
    }


# ============================================================
# GROUNDED ANALYST
# ============================================================

def analyst_answer(question):
    """
    Answers supported questions using GeoMine project data.
    Declines requests for information not contained in the data.
    """

    q = question.lower().strip()

    if not q:
        return {
            "answer": "Please enter a geological question.",
            "grounded": True,
            "supported": False,
            "sources": []
        }

    # --------------------------------------------------------
    # UNSUPPORTED DATA QUESTIONS
    # --------------------------------------------------------

    unsupported_terms = [
        "copper grade",
        "gold grade",
        "iron grade",
        "metal grade",
        "assay value",
        "ore grade",
        "drill hole",
        "drillhole",
        "drilling data",
        "resource estimate",
        "mineral resource",
        "reserve estimate",
        "ore reserve",
        "production volume",
        "copper price",
        "gold price",
        "tonnage"
    ]

    if any(term in q for term in unsupported_terms):
        return {
            "answer": (
                "The available GeoMine project data does not contain "
                "the requested information, such as assay results, "
                "drilling records, mineral grades, or resource estimates. "
                "I cannot determine or estimate this value from the "
                "available dataset."
            ),
            "grounded": True,
            "supported": False,
            "sources": [
                "GeoMine available project datasets"
            ]
        }

    # --------------------------------------------------------
    # CELL-LEVEL QUESTIONS
    # --------------------------------------------------------

    cell_match = re.search(
        r"(?:grid\s*fid|cell)\s*(?:number|id)?\s*[:#]?\s*(\d+)",
        q
    )

    if cell_match:
        cell_id = cell_match.group(1)
        row = get_cell_record(cell_id)

        if row is None:
            return {
                "answer": f"Grid cell {cell_id} was not found.",
                "grounded": True,
                "supported": False,
                "sources": []
            }

        data = build_cell_response(row)
        explanation = build_explanation(row)

        components = data["components"]

        lowest = min(
            components,
            key=lambda key: (
                components[key]
                if components[key] is not None
                else float("inf")
            )
        )

        drivers = explanation["top_geological_drivers"]

        driver_text = ", ".join(
            f'{item["criterion"]} ({item["component"]})'
            for item in drivers
        )

        answer = (
            f"Grid cell {cell_id} has a PU ranking score of "
            f'{data["prospectivity"]["pu_score"]:.4f} and a PU '
            f'percentile of '
            f'{data["prospectivity"]["pu_percentile"]:.4f}%. '
            f'Its component scores are Sources '
            f'{components["sources"]:.4f}, Energy '
            f'{components["energy"]:.4f}, Pathways '
            f'{components["pathways"]:.4f}, and Deposition '
            f'{components["deposition"]:.4f}. '
            f"The lowest component is {lowest.title()}. "
            f"Data completeness is "
            f'{data["data_coverage"]["completeness_percent"]}%. '
            f"Top geological drivers: {driver_text}."
        )

        return {
            "answer": answer,
            "grounded": True,
            "supported": True,
            "sources": [
                f"reports/cell_explanations.csv, grid_fid={cell_id}"
            ],
            "cell": data,
            "explanation": explanation
        }

    # --------------------------------------------------------
    # LOAD TARGET DATA
    # --------------------------------------------------------

    try:
        targets = get_targets_data()

    except Exception as error:
        return {
            "answer": "Unable to retrieve target data.",
            "grounded": False,
            "supported": False,
            "error": str(error),
            "sources": []
        }

    # --------------------------------------------------------
    # INDIVIDUAL TARGET QUESTIONS
    # --------------------------------------------------------

    target_match = re.search(
        r"\bR(?:10|11|[1-9])\b",
        q,
        re.I
    )

    if target_match:
        target_id = target_match.group(0).upper()

        target = next(
            (
                item for item in targets
                if item["target_id"].upper() == target_id
            ),
            None
        )

        if target is None:
            return {
                "answer": f"Target {target_id} was not found.",
                "grounded": True,
                "supported": False,
                "sources": []
            }

        answer = (
            f"Target {target_id} has a mean PU score of "
            f'{target["mean_score"]:.4f}, maximum PU score of '
            f'{target["max_score"]:.4f}, area of '
            f'{target["area_km2"]:.2f} km², and '
            f'{target["cell_count"]} grid cells. '
            f'Known deposit cells: {target["deposit_cells"]}. '
            f'Mean PU percentile: {target["mean_pct"]:.4f}.'
        )

        return {
            "answer": answer,
            "grounded": True,
            "supported": True,
            "sources": [
                "data/processed/pu_refined_target_polygons.gpkg"
            ],
            "target": target
        }

    # --------------------------------------------------------
    # TARGET COUNT
    # --------------------------------------------------------

    if any(term in q for term in [
        "how many targets",
        "number of targets",
        "total targets",
        "count of targets"
    ]):
        return {
            "answer": (
                f"The GeoMine dataset contains "
                f"{len(targets)} refined target polygons."
            ),
            "grounded": True,
            "supported": True,
            "sources": [
                "data/processed/pu_refined_target_polygons.gpkg"
            ],
            "target_count": len(targets)
        }

    # --------------------------------------------------------
    # HIGHEST / BEST TARGET
    # --------------------------------------------------------

    if any(term in q for term in [
        "highest",
        "best target",
        "top target",
        "most prospective",
        "highest scoring"
    ]):
        best = max(
            targets,
            key=lambda item: item["mean_score"]
        )

        return {
            "answer": (
                f'The highest mean PU score belongs to '
                f'{best["target_id"]}, with a mean score of '
                f'{best["mean_score"]:.4f}. Its area is '
                f'{best["area_km2"]:.2f} km² and it contains '
                f'{best["deposit_cells"]} known deposit cells.'
            ),
            "grounded": True,
            "supported": True,
            "sources": [
                "data/processed/pu_refined_target_polygons.gpkg"
            ],
            "target": best
        }

    # --------------------------------------------------------
    # LOWEST TARGET
    # --------------------------------------------------------

    if any(term in q for term in [
        "lowest",
        "weakest target",
        "minimum score",
        "lowest scoring"
    ]):
        lowest = min(
            targets,
            key=lambda item: item["mean_score"]
        )

        return {
            "answer": (
                f'The lowest mean PU score belongs to '
                f'{lowest["target_id"]}, with a mean score of '
                f'{lowest["mean_score"]:.4f}.'
            ),
            "grounded": True,
            "supported": True,
            "sources": [
                "data/processed/pu_refined_target_polygons.gpkg"
            ],
            "target": lowest
        }

    # --------------------------------------------------------
    # KNOWN DEPOSITS IN TARGETS
    # --------------------------------------------------------

    if "deposit" in q:
        total = sum(
            int(item["deposit_cells"] or 0)
            for item in targets
        )

        target_details = ", ".join(
            f'{item["target_id"]}: {item["deposit_cells"]}'
            for item in targets
        )

        return {
            "answer": (
                f"The target polygons contain {total} known deposit "
                f"cells in total. By target: {target_details}. "
                "These are spatial overlaps with known deposit cells."
            ),
            "grounded": True,
            "supported": True,
            "sources": [
                "data/processed/pu_refined_target_polygons.gpkg"
            ]
        }

    # --------------------------------------------------------
    # TARGET RANKING
    # --------------------------------------------------------

    if any(term in q for term in [
        "rank",
        "ranking",
        "list targets",
        "compare targets",
        "all targets"
    ]):
        ranking = sorted(
            targets,
            key=lambda item: item["mean_score"],
            reverse=True
        )

        lines = [
            f'{index}. {item["target_id"]}: '
            f'{item["mean_score"]:.4f}'
            for index, item in enumerate(ranking, start=1)
        ]

        return {
            "answer": (
                "Target ranking by mean PU score:\n"
                + "\n".join(lines)
            ),
            "grounded": True,
            "supported": True,
            "sources": [
                "data/processed/pu_refined_target_polygons.gpkg"
            ],
            "targets": ranking
        }

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return {
        "answer": (
            "I could not identify a supported question from the "
            "available GeoMine data. I can answer questions about "
            "grid-cell explanations, target scores, target areas, "
            "target rankings, and known deposit overlaps. "
            "I will not invent information that is not available "
            "in the project datasets."
        ),
        "grounded": True,
        "supported": False,
        "sources": []
    }


# ============================================================
# 1. HEALTH
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "GeoMine IOCG Prospectivity API",
        "explanation_records": len(CELL_DATA)
    })


# ============================================================
# 2. METADATA
# ============================================================

@app.route("/meta", methods=["GET"])
def metadata():
    return jsonify({
        "project": "GeoMine",
        "assessment": "IOCG Prospectivity",
        "study_area": "Tennant Creek-Mount Isa",
        "crs": "EPSG:3577",
        "grid_resolution_metres": 2000,
        "grid_cells": len(CELL_DATA),
        "predictor_count": 31,
        "mineral_system_components": [
            "Sources",
            "Energy",
            "Pathways",
            "Deposition"
        ],
        "known_positive_cells": 16,
        "unlabelled_cells": 112163,
        "model": "Repeated Unlabelled Sampling Random Forest",
        "score_interpretation": (
            "PU ranking score, not calibrated probability"
        )
    })


# ============================================================
# 3. CELL
# ============================================================

@app.route("/cell", methods=["GET"])
def cell():
    cell_id = request.args.get("grid_fid")

    if cell_id is None:
        return jsonify({
            "error": "Provide grid_fid parameter."
        }), 400

    row = get_cell_record(cell_id)

    if row is None:
        return jsonify({
            "error": "Grid cell not found.",
            "grid_fid": cell_id
        }), 404

    return jsonify(build_cell_response(row))


# ============================================================
# 4. EXPLANATION
# ============================================================

@app.route("/explain", methods=["GET"])
def explain():
    cell_id = request.args.get("grid_fid")

    if cell_id is None:
        return jsonify({
            "error": "Provide grid_fid parameter."
        }), 400

    row = get_cell_record(cell_id)

    if row is None:
        return jsonify({
            "error": "Grid cell not found.",
            "grid_fid": cell_id
        }), 404

    return jsonify(build_explanation(row))


# ============================================================
# 5. TARGETS
# ============================================================

@app.route("/targets", methods=["GET"])
def targets_endpoint():
    try:
        result = []

        for row in get_targets_data():
            result.append({
                "target_id": row["target_id"],
                "cell_count": row["cell_count"],
                "area_km2": row["area_km2"],
                "mean_pu_score": row["mean_score"],
                "maximum_pu_score": row["max_score"],
                "mean_percentile": row["mean_pct"],
                "known_deposit_cells": row["deposit_cells"],
                "centroid": {
                    "x": row["centroid_x"],
                    "y": row["centroid_y"],
                    "crs": "EPSG:3577"
                }
            })

        return jsonify({
            "target_count": len(result),
            "targets": result
        })

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# 6. LAYERS
# ============================================================

@app.route("/layers", methods=["GET"])
def layers():
    layer_files = [
        {
            "name": "PU Prospectivity",
            "file": PU_GPKG,
            "layer": "final_pu_prospectivity",
            "role": "Full-area PU ranking map"
        },
        {
            "name": "Expert Baseline",
            "file": EXPERT_GPKG,
            "layer": "iocg_prospectivity_v4",
            "role": "Expert geological baseline"
        },
        {
            "name": "GA Baseline",
            "file": GA_GPKG,
            "layer": "ga_baseline_grid",
            "role": "Genetic algorithm comparison baseline"
        },
        {
            "name": "Refined Target Polygons",
            "file": TARGETS_GPKG,
            "layer": "pu_refined_target_polygons",
            "role": "11 refined candidate target polygons"
        }
    ]

    result = []

    for item in layer_files:
        result.append({
            "name": item["name"],
            "file": str(item["file"].relative_to(BASE)),
            "layer": item["layer"],
            "role": item["role"],
            "available": item["file"].exists()
        })

    return jsonify({
        "layer_count": len(result),
        "layers": result
    })


# ============================================================
# 7. GROUNDED ANALYST QUESTION ENDPOINT
# ============================================================

@app.route("/ask", methods=["POST", "GET"])
def ask():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        question = payload.get("question", "")
    else:
        question = request.args.get("question", "")

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "error": "Provide a question.",
            "example": {
                "question": "Which target has the highest score?"
            }
        }), 400

    result = analyst_answer(question)

    return jsonify({
        "question": question,
        "analyst": "GeoMine Grounded Analyst",
        **result
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    print("\nAvailable API endpoints:")
    print("GET  /health")
    print("GET  /meta")
    print("GET  /cell?grid_fid=ID")
    print("GET  /explain?grid_fid=ID")
    print("GET  /targets")
    print("GET  /layers")
    print("GET  /ask?question=Which%20target%20has%20the%20highest%20score")
    print("POST /ask  JSON: {'question': 'Tell me about R2'}")

    print("\nServer URL: http://127.0.0.1:5000")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
        use_reloader=False
    )
