# GeoMine — IOCG Mineral Prospectivity Mapping

**GeoMine Geodata Scientist Take-Home Assessment | AI/ML Track**

## 1. Project Overview

GeoMine is an AI/ML-based mineral prospectivity mapping prototype developed for the GeoMine Geodata Scientist take-home assessment.

The project identifies prospective Iron Oxide Copper-Gold (IOCG) exploration areas across the Tennant Creek–Mount Isa investigation region, Australia.

It integrates geological evidence, expert-derived mineral-system indicators, and a Positive-Unlabelled (PU) Random Forest ensemble to generate prospectivity rankings and refined exploration targets.

The system combines geospatial data processing, machine learning, spatial validation, geological explanations, a REST API, an interactive web map, and a grounded geological analyst.

### Key Features

- Geological raster processing and feature extraction.
- 2 km × 2 km spatial analysis grid.
- Four mineral-system component scores.
- Expert-derived prospectivity baseline.
- Positive-Unlabelled Random Forest modelling.
- 50 km spatial block validation.
- Refined exploration target identification.
- Cell-level geological explanations.
- Flask REST API.
- React and Leaflet interactive dashboard.
- API-grounded geological analyst.
- Automated groundedness evaluation.
- Docker Compose deployment.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Geospatial processing | QGIS, GDAL, GeoPandas |
| Coordinate reference system | EPSG:3577 |
| Spatial data storage | GeoPackage, GeoJSON |
| Data processing | Python, Pandas, NumPy |
| Machine learning | Scikit-learn, Random Forest |
| Model persistence | Joblib |
| Backend | Flask |
| Frontend | React 19, Vite |
| Interactive mapping | Leaflet, React-Leaflet |
| Web server | Nginx |
| Containerisation | Docker, Docker Compose |
| Evaluation | Python-based groundedness tests |

## 3. Project Structure

```text
GeoMine/
│
├── api/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── app/
│   ├── public/
│   │   ├── deposits.geojson
│   │   ├── targets.geojson
│   │   ├── prospectivity.png
│   │   └── prospectivity_bounds.json
│   │
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── AnalystChat.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── config/
│   ├── predictor_config.csv
│   ├── predictor_config.json
│   └── pu_learning_config.json
│
├── data/
│   ├── raw/
│   └── processed/
│
├── eval/
│   ├── groundedness_questions.json
│   ├── groundedness_results.csv
│   ├── groundedness_transcripts.json
│   └── run_groundedness_tests.py
│
├── models/
│   └── final_pu_random_forest_ensemble.joblib
│
├── outputs/
│   ├── final_pu_prospectivity.csv
│   ├── pu_spatial_cv_predictions.csv
│   └── GeoMine_PU_Prospectivity.qgz
│
├── reports/
│   ├── cell_explanations.csv
│   ├── model_comparison_summary.csv
│   ├── pu_spatial_cv_evaluation.csv
│   ├── pu_refined_clusters_99.csv
│   └── spatial_block_summary.csv
│
├── src/
│   ├── extract_all_features.py
│   ├── calculate_component_scores.py
│   ├── calculate_final_prospectivity.py
│   ├── create_spatial_blocks.py
│   ├── prepare_ml_dataset.py
│   ├── run_pu_spatial_validation.py
│   ├── train_final_pu_model.py
│   ├── validate_final_pu_model.py
│   ├── create_final_pu_geopackage.py
│   ├── identify_refined_pu_clusters.py
│   ├── create_refined_target_polygons.py
│   ├── generate_cell_explanations.py
│   ├── create_prospectivity_map.py
│   └── run_pipeline.py
│
├── GeoMine.qgz
├── docker-compose.yml
├── .dockerignore
└── README.md
```

Additional diagnostic, inspection, styling, and validation scripts are also available under `src/`.

## 4. Data Preparation and Geospatial Processing

The project uses geological predictor rasters, known Australian mineral deposit records, an investigation area boundary, and expert-derived GA prospectivity baseline maps.

### Input Data

- 31 geological predictor rasters.
- Australian mineral deposit records.
- Tennant Creek–Mount Isa investigation area boundary.
- Expert-derived IOCG prospectivity baseline rasters.

### Data Processing Workflow

1. Inspect the source raster datasets and their spatial metadata.
2. Verify raster alignment, dimensions, resolution, and coordinate reference systems.
3. Project the investigation boundary and known deposit locations into EPSG:3577.
4. Generate a 2 km × 2 km analysis grid.
5. Clip the grid to the investigation boundary.
6. Join known IOCG deposit locations to grid cells.
7. Extract zonal mean statistics from the geological predictor rasters.
8. Prepare the geological feature dataset for component scoring and machine learning.

### Dataset Characteristics

| Attribute | Value |
|---|---:|
| Geological predictors | 31 |
| Grid resolution | 2 km × 2 km |
| Study-area grid cells | 112,179 |
| Known positive cells | 16 |
| Unlabelled cells | 112,163 |
| Confirmed negative cells | 0 |
| Coordinate reference system | EPSG:3577 |

All 31 geological predictors were aligned in the source dataset and used for feature extraction.

Unlabelled cells are not treated as confirmed negative examples.

## 5. Mineral-System Component Framework

The 31 geological predictors are organised into four mineral-system components.

| Component | Predictor Family | Number of Predictors |
|---|---|---:|
| Sources | S | 7 |
| Energy / Drivers | D | 8 |
| Pathways / Architecture | P | 5 |
| Deposition | T | 11 |
| **Total** | | **31** |

The component framework represents the geological requirements of an IOCG mineral system.

### Component Score Calculation

Official predictor weights are used to calculate weighted component scores.

Predictor values are normalised using the implementation's input scaling, and official weights are normalised within each component.

The resulting component scores range from 0 to 100.

### Expert-Derived Final Prospectivity Score

The four component scores are combined using a geometric mean:

\[
S_{\text{final}} =
100 \times
\left[
\left(\frac{S}{100}\right)
\left(\frac{E}{100}\right)
\left(\frac{P}{100}\right)
\left(\frac{D}{100}\right)
\right]^{1/4}
\]

Where:

- S = Sources score.
- E = Energy / Drivers score.
- P = Pathways / Architecture score.
- D = Deposition score.

A zero component score produces a zero final score.

This aggregation ensures that all four mineral-system components contribute to the final expert-derived prospectivity score.

The expert-derived map is kept separate from the machine-learning predictor features and labels.

## 6. Positive-Unlabelled Machine Learning

A Positive-Unlabelled Random Forest ensemble is implemented to identify geological patterns associated with known IOCG deposits.

### Why Positive-Unlabelled Learning?

The dataset contains known IOCG deposit locations but does not contain verified barren or negative exploration locations.

Therefore:

- Known deposit cells are treated as positive observations.
- Remaining cells are treated as unlabelled observations.
- Unlabelled observations are sampled during model training.
- Unlabelled observations are not interpreted as confirmed barren areas.

### Model Configuration

The Random Forest configuration includes:

| Parameter | Value |
|---|---:|
| Number of trees per model | 300 |
| Maximum tree depth | 12 |
| Minimum leaf size | 2 |
| Maximum features | sqrt |
| Class weights | Balanced |
| Ensemble models | 10 |
| Unlabelled samples per positive | 5 |

Repeated unlabelled sampling is used to train the ensemble.

The final model is trained using all 16 known positive cells and sampled unlabelled observations.

### Model Outputs

- `models/final_pu_random_forest_ensemble.joblib`
- `outputs/final_pu_prospectivity.csv`
- `data/processed/final_pu_prospectivity.gpkg`

### Score Interpretation

The model generates a PU ranking score between 0 and 1.

**Important:** The PU score is a relative ranking score, not a calibrated probability of discovering an IOCG deposit.

## 7. Spatial Validation

Spatial block validation is implemented using 50 km spatial blocks to investigate the model's performance under geographic separation.

The validation process:

1. Assign grid cells to 50 km spatial blocks.
2. Identify blocks containing known positive deposit cells.
3. Hold out positive-containing blocks for evaluation.
4. Train fold-specific models using training observations.
5. Sample unlabelled cells from the training region.
6. Generate predictions for held-out blocks.
7. Calculate positive capture rates at different area cutoffs.

### Positive Distribution

The 16 known positive cells occur in four adjacent spatial blocks.

This geographic clustering creates an important validation limitation.

Holding out one positive block still leaves neighbouring positive blocks available for training. A 50 km buffer could remove all available training positives.

Consequently, the current results are preliminary spatial holdout results rather than definitive independent geographic validation.

### Evaluation Metrics

- Positive capture rate at 5% of evaluated area.
- Positive capture rate at 10% of evaluated area.
- Positive capture rate at 20% of evaluated area.
- Fold-wise positive capture.

The PU dataset contains no confirmed negative observations. Therefore, conventional AUC calculations that treat all unlabelled observations as negatives are not appropriate.

### Spatial Validation Results

| Held-out Block | Capture at 5% | Capture at 10% | Capture at 20% |
|---|---:|---:|---:|
| B_3_-42 | 0% | 100% | 100% |
| B_3_-43 | 0% | 0% | 0% |
| B_4_-42 | 0% | 20% | 100% |
| B_4_-43 | 33.33% | 66.67% | 66.67% |
| **Aggregate** | **18.75%** | **50%** | **75%** |

These aggregate figures represent fold-wise positive capture at the corresponding area cutoffs. They should not be compared directly with full-study-area in-sample capture rates.

## 8. Expert Baseline and GA Baseline Comparison

The project includes two reference prospectivity maps:

- Expert-derived geological component baseline.
- GA-derived prospectivity baseline.

These maps are evaluated separately from the machine-learning model.

### Full Study-Area Baseline Results

| Baseline | Top 5% Capture | Top 10% Capture | Top 20% Capture |
|---|---:|---:|---:|
| Expert-derived baseline | 93.75% | 93.75% | 94.20% |
| GA baseline | 87.50% | 93.75% | 100% |

These are full-study-area baseline comparisons using known deposit locations. They are not independent predictive validation results.

The GA baseline is not used as a machine-learning feature or training label.

## 9. Exploration Target Identification

The final PU ranking scores are used to identify high-ranking candidate exploration areas.

### Target Identification Workflow

1. Rank grid cells using the final PU model score.
2. Select cells in the 99th percentile.
3. Identify spatially connected high-ranking clusters.
4. Dissolve connected cells into target polygons.
5. Calculate target area and prospectivity statistics.
6. Count known deposit cells within each target.

The refined target dataset contains 11 target polygons.

### Refined Target Summary

| Target | Cells | Area (km²) | Mean PU Score | Maximum PU Score | Known Deposit Cells |
|---|---:|---:|---:|---:|---:|
| R1 | 623 | 2,492 | 0.9273 | 0.9973 | 15 |
| R2 | 23 | 92 | 0.8256 | 0.9652 | 0 |
| R3 | 3 | 12 | 0.8029 | 0.8029 | 0 |
| R4 | 6 | 24 | 0.7981 | 0.7981 | 0 |
| R5 | 87 | 348 | 0.7533 | 0.7533 | 0 |
| R6 | 3 | 12 | 0.7389 | 0.7389 | 0 |
| R7 | 179 | 716 | 0.7241 | 0.7241 | 0 |
| R8 | 5 | 20 | 0.7125 | 0.7125 | 0 |
| R9 | 155 | 620 | 0.6904 | 0.6904 | 0 |
| R10 | 23 | 92 | 0.6899 | 0.6899 | 0 |
| R11 | 5 | 20 | 0.5896 | 0.5896 | 0 |

### Important Geological Interpretation

R1 contains 15 known deposit cells because the final PU model was trained using the known positive observations.

It must not be presented as an independent discovery or independent validation result.

R2–R11 contain no known positive cells in the current dataset. They are unlabelled candidate exploration areas requiring independent geological review and field validation.

## 10. Cell-Level Geological Explanations

The project generates a cell-level explanation dataset containing:

- Grid cell identifier.
- PU ranking score.
- PU ranking percentile.
- Four mineral-system component scores.
- Top three geological drivers.
- Data completeness information.

### Explanation Method

The top geological drivers are calculated using weighted predictor contributions to their corresponding mineral-system component scores.

They provide geological evidence supporting the component scores.

They are not causal explanations of the Random Forest prediction.

### Example: Grid Cell 1

| Metric | Value |
|---|---:|
| PU Score | 0.9958 |
| PU Percentile | 99.9973% |
| Data Completeness | 100% |
| Sources | 49.1259 |
| Energy | 44.7102 |
| Pathways | 50.1290 |
| Deposition | 8.5163 |

Top three geological drivers:

1. P2a — Pathways: 32.4873
2. S4 — Sources: 19.5804
3. S5 — Sources: 18.3566

Primary explanation dataset:

`reports/cell_explanations.csv`

## 11. Backend REST API

The backend is implemented using Flask.

Main source file:

`api/app.py`

### API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | API health check |
| `/meta` | GET | Dataset and model metadata |
| `/cell` | GET | Retrieve cell prospectivity information |
| `/explain` | GET | Retrieve cell-level geological explanations |
| `/targets` | GET | Retrieve refined exploration targets |
| `/layers` | GET | Retrieve available map layers |
| `/ask` | GET / POST | Submit a question to the analyst |

### Example API Requests

```text
/health

/meta

/targets

/cell?grid_fid=1

/explain?grid_fid=1
```

### API Health Response

```json
{
  "explanation_records": 112179,
  "service": "GeoMine IOCG Prospectivity API",
  "status": "healthy"
}
```

The API loads the cell explanation dataset and provides structured responses for the frontend.

## 12. Frontend Dashboard

The frontend is developed using React, Vite, and Leaflet.

### Dashboard Features

- Interactive IOCG prospectivity map.
- PU prospectivity raster overlay.
- Known IOCG deposit overlay.
- Refined exploration target polygons.
- Exploration target ranking list.
- Target selection and summary.
- Cell-level geological explanation.
- Mineral-system component visualisation.
- Top three geological drivers.
- Grounded geological analyst interface.
- Map layer controls.

### Dashboard Statistics

The application displays:

| Metric | Value |
|---|---:|
| Grid cells | 112,179 |
| Predictors | 31 |
| Known deposits | 16 |
| Refined targets | 11 |

The frontend communicates with the Flask backend through Nginx reverse proxy configuration.

## 13. Grounded Geological Analyst

The GeoMine Analyst interface allows users to ask questions about the prospectivity dataset.

It currently uses deterministic, rule-based responses grounded in API data.

It is not a deployed large language model or autonomous LLM agent.

### Supported Query Examples

- Which exploration target has the highest prospectivity score?
- Explain the prospectivity of grid cell 1.
- What are the component scores of a particular cell?
- How many refined exploration targets are available?
- Which target contains known deposit cells?

### Groundedness Behaviour

The analyst returns:

- A structured answer.
- Groundedness status.
- Supporting data source references.

Questions that cannot be answered using the available project data are not presented as verified facts.

## 14. Groundedness Evaluation

The analyst evaluation is implemented in:

`eval/run_groundedness_tests.py`

### Evaluation Files

Input:

- `eval/groundedness_questions.json`

Outputs:

- `eval/groundedness_results.csv`
- `eval/groundedness_transcripts.json`

### Latest Evaluation Results

| Metric | Result |
|---|---:|
| Questions evaluated | 10 |
| Automatic checks passed | 10 |
| Automatic checks failed | 0 |

The automatic checks verify expected answers and grounding indicators.

These checks do not replace manual review of answer correctness, geological interpretation, and source attribution.

## 15. Docker Deployment

GeoMine supports containerised deployment using Docker and Docker Compose.

### Container Architecture

| Service | Technology | Container Port |
|---|---|---:|
| API | Python 3.12 + Flask | 5000 |
| Frontend | React + Nginx | 80 |

The frontend is exposed through host port 8081.

Nginx reverse-proxies `/api/` requests to the Flask API container.

### Prerequisites

- Windows 10/11 or a compatible operating system.
- Docker Desktop.
- Docker Engine.
- Docker Compose.
- WSL 2 for Windows Linux-container deployment.

### Build Docker Images

Open PowerShell in the project root:

```powershell
cd C:\Users\Ermus\Desktop\GeoMine

docker compose build
```

### Start the Application

```powershell
docker compose up -d
```

### Verify Container Status

```powershell
docker compose ps
```

Both services should show a running status:

- `geomine-api`
- `geomine-frontend`

### Access the Application

Frontend:

`http://localhost:8081`

API health check through Nginx:

`http://localhost:8081/api/health`

### View Container Logs

```powershell
docker compose logs -f
```

View only API logs:

```powershell
docker compose logs -f api
```

View only frontend logs:

```powershell
docker compose logs -f frontend
```

### Stop the Application

```powershell
docker compose down
```

### Docker Configuration Files

- `docker-compose.yml`
- `api/Dockerfile`
- `api/requirements.txt`
- `app/Dockerfile`
- `app/nginx.conf`
- `.dockerignore`

## 16. Reproducibility and Pipeline Execution

The repository contains the individual data preparation scripts, modelling workflow, trained PU Random Forest ensemble, generated spatial datasets, backend API, frontend application, and Docker configuration.

### Master Pipeline

The orchestration script is:

`src/run_pipeline.py`

It supports project preflight checks, pipeline execution, and application validation.

### Run Preflight Checks

Use the QGIS Python interpreter:

```powershell
cd C:\Users\Ermus\Desktop\GeoMine

& "C:\Program Files\QGIS 3.44.15\apps\Python312\python.exe" src/run_pipeline.py --check
```

### Validate Existing Outputs and Application

```powershell
& "C:\Program Files\QGIS 3.44.15\apps\Python312\python.exe" src/run_pipeline.py --validate
```

The validation mode checks existing project outputs and application functionality. It does not retrain the model.

The pipeline supports resuming from existing outputs. Existing files are checked for presence; this should not be interpreted as a complete clean-room reproducibility guarantee.

### Input Data Requirement

Original input datasets must be available under `data/raw/` before rerunning the complete data preparation workflow.

## 17. Limitations and Future Improvements

The current prototype has the following limitations:

1. Only 16 known positive IOCG grid cells are available within the investigation area.
2. No confirmed negative exploration observations are available.
3. Positive observations are concentrated in four adjacent spatial blocks.
4. Spatial validation has limitations due to geographic clustering.
5. PU scores are ranking scores and are not calibrated discovery probabilities.
6. Sparse deposition predictor coverage contributes to zero deposition component scores in many cells.
7. Geological driver contributions are not causal explanations of the Random Forest prediction.
8. R1 contains known deposits used during model training and is not independent predictive evidence.
9. Candidate exploration targets require independent geological assessment and field validation.
10. The analyst currently uses deterministic, API-grounded responses rather than a deployed LLM.

### Future Improvements

- Incorporate additional verified IOCG deposit observations.
- Obtain reliable barren-area or negative exploration evidence.
- Improve spatial validation using geographically independent positive datasets.
- Investigate PU learning methods suitable for small positive datasets.
- Evaluate additional machine-learning models.
- Improve geological feature interpretability.
- Integrate additional geochemical and geophysical evidence.
- Introduce an LLM-based analyst with API tool calling and strict groundedness checks.
- Conduct independent geological review of candidate exploration targets.

## 18. Key Project Outputs

| Output | Location |
|---|---|
| Final PU Random Forest ensemble | `models/final_pu_random_forest_ensemble.joblib` |
| Final PU scores | `outputs/final_pu_prospectivity.csv` |
| Final PU GeoPackage | `data/processed/final_pu_prospectivity.gpkg` |
| Refined target polygons | `data/processed/pu_refined_target_polygons.gpkg` |
| Geological component scores | `data/processed/geological_component_scores.gpkg` |
| Expert prospectivity map | `data/processed/iocg_prospectivity_v4.gpkg` |
| GA baseline | `data/processed/ga_baseline_grid.gpkg` |
| Cell explanations | `reports/cell_explanations.csv` |
| Spatial validation predictions | `outputs/pu_spatial_cv_predictions.csv` |
| Spatial validation evaluation | `reports/pu_spatial_cv_evaluation.csv` |
| Refined target summary | `reports/pu_refined_clusters_99.csv` |
| Groundedness results | `eval/groundedness_results.csv` |
| Interactive QGIS project | `GeoMine.qgz` |

## 19. Conclusion

GeoMine demonstrates an end-to-end IOCG mineral prospectivity mapping prototype integrating geospatial processing, expert-derived mineral-system scoring, Positive-Unlabelled machine learning, spatial holdout evaluation, geological explanations, REST API development, and interactive visualisation.

The system produces ranked exploration candidate areas and cell-level geological evidence while explicitly acknowledging the limitations of the available positive-unlabelled dataset.

The Docker deployment provides a reproducible way to launch the frontend and backend application services together.

The resulting prototype provides a foundation for further geological assessment, improved machine-learning validation, and future integration of additional mineral-system evidence.

---

**Project:** GeoMine — IOCG Mineral Prospectivity Mapping  
**Assessment:** GeoMine Geodata Scientist Take-Home Assessment  
**Track:** AI/ML  
**Study Area:** Tennant Creek–Mount Isa, Australia  
**Grid Resolution:** 2 km × 2 km  
**Coordinate Reference System:** EPSG:3577