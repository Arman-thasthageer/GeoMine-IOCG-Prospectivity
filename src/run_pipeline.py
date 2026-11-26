
import os
import sys
import runpy
import argparse
from pathlib import Path

# ============================================================
# GEOMINE MASTER PIPELINE
# Safe resume + application validation
# ============================================================

BASE = Path(r"C:\Users\Ermus\Desktop\GeoMine")

QGIS_PLUGINS = Path(
    r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins"
)

ML_PACKAGES = BASE / "ml_packages"
PROJECT_FILE = BASE / "GeoMine.qgz"

# ============================================================
# PIPELINE STAGES
# ============================================================

STAGES = [
    {
        "name": "Extract geological raster features",
        "script": "src/extract_all_features.py",
        "outputs": ["data/processed/geological_features.gpkg"],
        "layers": [
            ("grid_labeled", "data/processed/grid_labeled.gpkg")
        ],
    },
    {
        "name": "Calculate geological component scores",
        "script": "src/calculate_component_scores.py",
        "outputs": ["data/processed/geological_component_scores.gpkg"],
        "layers": [
            ("geological_features", "data/processed/geological_features.gpkg")
        ],
    },
    {
        "name": "Calculate expert prospectivity baseline",
        "script": "src/calculate_final_prospectivity.py",
        "outputs": ["data/processed/iocg_prospectivity_v4.gpkg"],
        "layers": [],
    },
    {
        "name": "Create 50 km spatial blocks",
        "script": "src/create_spatial_blocks.py",
        "outputs": [
            "data/processed/geological_features_spatial_blocks.gpkg"
        ],
        "layers": [],
    },
    {
        "name": "Prepare positive-unlabelled ML dataset",
        "script": "src/prepare_ml_dataset.py",
        "outputs": [
            "data/processed/ml_training_dataset.csv"
        ],
        "layers": [],
    },
    {
        "name": "Run spatial validation",
        "script": "src/run_pu_spatial_validation.py",
        "outputs": [
            "outputs/pu_spatial_cv_predictions.csv"
        ],
        "layers": [],
    },
    {
        "name": "Train final PU Random Forest model",
        "script": "src/train_final_pu_model.py",
        "outputs": [
            "models/final_pu_random_forest_ensemble.joblib",
            "outputs/final_pu_prospectivity.csv",
        ],
        "layers": [],
    },
    {
        "name": "Create final PU prospectivity GeoPackage",
        "script": "src/create_final_pu_geopackage.py",
        "outputs": [
            "data/processed/final_pu_prospectivity.gpkg"
        ],
        "layers": [],
    },
    {
        "name": "Create refined target polygons",
        "script": "src/create_refined_target_polygons.py",
        "outputs": [
            "data/processed/pu_refined_target_polygons.gpkg"
        ],
        "layers": [],
    },
    {
        "name": "Generate cell explanations",
        "script": "src/generate_cell_explanations.py",
        "outputs": [
            "reports/cell_explanations.csv"
        ],
        "layers": [],
    },
]

# ============================================================
# COMMON FUNCTIONS
# ============================================================

def absolute(relative_path):
    return BASE / relative_path


def stage_is_complete(stage):
    return all(
        absolute(item).is_file()
        for item in stage["outputs"]
    )


def check_project_files():
    required = [
        PROJECT_FILE,
        BASE / "data/processed/grid_labeled.gpkg",
        BASE / "data/raw/input_rasters/IOCG_Input_Data",
        BASE / "config/predictor_config.json",
        BASE / "config/predictor_config.csv",
        BASE / "config/pu_learning_config.json",
        ML_PACKAGES,
    ]

    missing = [
        str(path)
        for path in required
        if not path.exists()
    ]

    for stage in STAGES:
        script = absolute(stage["script"])
        if not script.is_file():
            missing.append(str(script))

    raster_folder = (
        BASE / "data/raw/input_rasters/IOCG_Input_Data"
    )

    rasters = list(raster_folder.glob("*_norm_int.tif"))

    print("\nGeological rasters found:", len(rasters))

    if len(rasters) != 31:
        missing.append(
            "Expected exactly 31 geological *_norm_int.tif rasters"
        )

    if missing:
        print("\nPREFLIGHT FAILED")

        for item in missing:
            print("[MISSING]", item)

        raise SystemExit(1)

    print("[OK] Required project files")
    print("[OK] QGIS project")
    print("[OK] Configuration files")
    print("[OK] Pipeline scripts")
    print("[OK] ML package directory")
    print("[OK] 31 geological rasters")


def print_status():
    print("\n" + "=" * 68)
    print("GEOMINE MASTER PIPELINE - STATUS CHECK")
    print("=" * 68)

    for index, stage in enumerate(STAGES, start=1):

        status = (
            "COMPLETE - REUSE"
            if stage_is_complete(stage)
            else "PENDING"
        )

        print(
            f"{index:02d}. [{status}] {stage['name']}"
        )

        for output in stage["outputs"]:
            print("      ", output)

    print("=" * 68)


# ============================================================
# APPLICATION VALIDATION
# ============================================================

def validate_application():

    print("\n" + "=" * 68)
    print("GEOMINE APPLICATION VALIDATION")
    print("=" * 68)

    results = []

    def record(name, passed, detail=""):

        status = "PASS" if passed else "FAIL"

        print(f"[{status}] {name}")

        if detail:
            print("       " + str(detail))

        results.append(bool(passed))

    # --------------------------------------------------------
    # 1. Validate all geological and ML outputs
    # --------------------------------------------------------

    required_outputs = [
        "data/processed/geological_features.gpkg",
        "data/processed/geological_component_scores.gpkg",
        "data/processed/iocg_prospectivity_v4.gpkg",
        "data/processed/geological_features_spatial_blocks.gpkg",
        "data/processed/ml_training_dataset.csv",
        "outputs/pu_spatial_cv_predictions.csv",
        "models/final_pu_random_forest_ensemble.joblib",
        "outputs/final_pu_prospectivity.csv",
        "data/processed/final_pu_prospectivity.gpkg",
        "data/processed/pu_refined_target_polygons.gpkg",
        "reports/cell_explanations.csv",
    ]

    for item in required_outputs:

        path = absolute(item)

        record(
            "Output: " + item,
            path.is_file(),
            (
                f"{path.stat().st_size:,} bytes"
                if path.is_file()
                else "File missing"
            )
        )

    # --------------------------------------------------------
    # 2. Validate frontend production build
    # --------------------------------------------------------

    dist = BASE / "app" / "dist"
    index_file = dist / "index.html"

    assets_folder = dist / "assets"

    assets = (
        list(assets_folder.glob("*"))
        if assets_folder.exists()
        else []
    )

    record(
        "Frontend index.html",
        index_file.is_file()
    )

    has_js = any(
        file.suffix == ".js"
        for file in assets
    )

    has_css = any(
        file.suffix == ".css"
        for file in assets
    )

    record(
        "Frontend JavaScript and CSS",
        has_js and has_css,
        f"{len(assets)} assets found"
    )

    # --------------------------------------------------------
    # 3. Validate Flask API
    # --------------------------------------------------------

    try:

        sys.path.insert(0, str(BASE))
        sys.path.insert(0, str(ML_PACKAGES))

        from api.app import app as flask_app

        client = flask_app.test_client()

        # Health endpoint
        health = client.get("/health")

        record(
            "API /health",
            health.status_code == 200,
            f"HTTP {health.status_code}"
        )

        # Metadata endpoint
        meta = client.get("/meta")

        meta_data = meta.get_json() or {}

        record(
            "API /meta",
            (
                meta.status_code == 200
                and meta_data.get("grid_cells") == 112179
                and meta_data.get("predictor_count") == 31
            ),
            (
                f"Grid cells: {meta_data.get('grid_cells')}, "
                f"predictors: {meta_data.get('predictor_count')}"
            )
        )

        # Targets endpoint
        targets = client.get("/targets")

        target_data = targets.get_json() or {}

        record(
            "API /targets",
            (
                targets.status_code == 200
                and target_data.get("target_count") == 11
            ),
            f"Targets: {target_data.get('target_count')}"
        )

        # Grounded analyst endpoint
        analyst = client.post(
            "/ask",
            json={
                "question": "Which target has the highest score?"
            }
        )

        analyst_data = analyst.get_json() or {}

        record(
            "API grounded analyst",
            (
                analyst.status_code == 200
                and analyst_data.get("grounded") is True
                and analyst_data.get("supported") is True
            ),
            analyst_data.get("answer", "No answer returned")
        )

    except Exception as error:

        record(
            "API validation",
            False,
            repr(error)
        )

    # --------------------------------------------------------
    # 4. Final validation report
    # --------------------------------------------------------

    passed = sum(results)
    failed = len(results) - passed

    print("\n" + "=" * 68)
    print("GEOMINE VALIDATION SUMMARY")
    print("=" * 68)

    print("Total checks :", len(results))
    print("Passed       :", passed)
    print("Failed       :", failed)

    if failed:

        print("\nGEOMINE VALIDATION FAILED")

        raise SystemExit(1)

    print("\nGEOMINE APPLICATION VALIDATION PASSED")
    print("Existing geological and ML results were not retrained.")


# ============================================================
# QGIS INITIALIZATION
# ============================================================

def initialize_qgis():

    sys.path.insert(0, str(QGIS_PLUGINS))
    sys.path.insert(0, str(ML_PACKAGES))

    from qgis.core import (
        QgsApplication,
        QgsProject,
        QgsVectorLayer
    )

    QgsApplication.setPrefixPath(
        r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr",
        True
    )

    app = QgsApplication([], False)
    app.initQgis()

    import processing

    from processing.core.Processing import Processing

    Processing.initialize()

    project = QgsProject.instance()

    if not project.read(str(PROJECT_FILE)):
        raise RuntimeError(
            "Could not open GeoMine.qgz"
        )

    def ensure_layer(layer_name, relative_path):

        existing = project.mapLayersByName(layer_name)

        if existing and existing[0].isValid():

            print(
                f"[OK] Project layer available: {layer_name}"
            )

            return

        path = absolute(relative_path)

        if not path.exists():
            raise FileNotFoundError(path)

        layer = QgsVectorLayer(
            str(path),
            layer_name,
            "ogr"
        )

        if not layer.isValid():

            raise RuntimeError(
                f"Could not load layer: {path}"
            )

        project.addMapLayer(layer)

        print(
            f"[OK] Loaded project layer: {layer_name}"
        )

    return app, project, ensure_layer


# ============================================================
# MASTER PIPELINE EXECUTION
# ============================================================

def run_pipeline():

    check_project_files()
    print_status()

    pending = [
        stage
        for stage in STAGES
        if not stage_is_complete(stage)
    ]

    if not pending:

        print("\nALL PIPELINE OUTPUTS ALREADY EXIST.")
        print("Existing outputs will be reused.")

        validate_application()

        return

    print(
        f"\nStages requiring execution: {len(pending)}"
    )

    print(
        "Completed stages will be skipped."
    )

    app, project, ensure_layer = initialize_qgis()

    try:

        os.chdir(BASE)

        for index, stage in enumerate(STAGES, start=1):

            if stage_is_complete(stage):

                print(
                    f"\n[SKIP] {stage['name']}"
                )

                continue

            print("\n" + "=" * 68)

            print(
                f"RUNNING STAGE {index}: {stage['name']}"
            )

            print("=" * 68)

            for layer_name, relative_path in stage["layers"]:

                ensure_layer(
                    layer_name,
                    relative_path
                )

            script_path = absolute(stage["script"])

            sys.path.insert(0, str(ML_PACKAGES))

            runpy.run_path(
                str(script_path),
                run_name="__main__"
            )

            missing_outputs = [
                item
                for item in stage["outputs"]
                if not absolute(item).is_file()
            ]

            if missing_outputs:

                raise RuntimeError(
                    "Stage did not create expected output(s): "
                    + ", ".join(missing_outputs)
                )

            print(
                f"[SUCCESS] {stage['name']}"
            )

        print("\n" + "=" * 68)
        print("GEOMINE MASTER PIPELINE FINISHED")
        print("=" * 68)

    finally:

        app.exitQgis()

    validate_application()


# ============================================================
# COMMAND-LINE OPTIONS
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="GeoMine Master Pipeline"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check required files and existing outputs"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate geological outputs, frontend and API"
    )

    args = parser.parse_args()

    check_project_files()

    if args.validate:

        print_status()
        validate_application()

    elif args.check:

        print_status()

        print(
            "\nCHECK ONLY: No processing was executed."
        )

    else:

        run_pipeline()
