# AI_USAGE.md

# AI Usage Disclosure — GeoMine IOCG Prospectivity Prototype

## 1. Purpose

AI assistance was used during the development of the GeoMine IOCG mineral prospectivity prototype to support technical planning, implementation, debugging, documentation, and testing.

AI-generated suggestions were reviewed and adapted to the project requirements. Project outputs, implementation decisions, and reported metrics were checked against the actual datasets and execution results.

## 2. Areas Where AI Assistance Was Used

### 2.1 Project Planning and Architecture
AI assistance supported:
- Breaking the assessment requirements into implementation stages.
- Planning the geospatial data-processing workflow.
- Organising geological predictors into Sources, Energy/Drivers, Pathways/Architecture, and Deposition.
- Planning the API, frontend, machine-learning workflow, and Docker deployment.

### 2.2 Geospatial Data Processing
AI assistance supported:
- Writing and debugging Python and QGIS processing scripts.
- Working with raster and vector datasets.
- Preparing the 2 km analysis grid in EPSG:3577.
- Extracting zonal statistics for geological predictor rasters.
- Joining deposit locations to grid cells.
- Checking coordinate reference systems, raster alignment, and output datasets.

### 2.3 Machine Learning
AI assistance supported:
- Designing the Positive-Unlabelled learning workflow.
- Implementing Random Forest training and repeated unlabelled sampling.
- Preparing spatial block validation.
- Calculating capture rates at different area cutoffs.
- Generating final prospectivity rankings and refined target clusters.
- Explaining validation limitations and the distinction between unlabelled and confirmed negative observations.

The final implementation and reported model results were obtained by executing the project scripts against the project datasets.

### 2.4 API and Frontend Development
AI assistance supported:
- Implementing and debugging Flask API endpoints.
- Connecting the frontend to the backend API.
- Developing interactive prospectivity maps and target selection.
- Displaying cell-level geological explanations.
- Implementing deterministic, API-grounded analyst responses.

### 2.5 Docker and Deployment
AI assistance supported:
- Preparing Dockerfiles and Docker Compose configuration.
- Configuring Nginx as a frontend reverse proxy.
- Troubleshooting container builds and service connectivity.
- Verifying the deployed frontend and API endpoints.

### 2.6 Documentation and Testing
AI assistance supported:
- Preparing the README.md and REPORT.md documentation.
- Preparing project validation and testing procedures.
- Reviewing evaluation results and documenting known limitations.

## 3. AI Analyst Disclosure

The current GeoMine analyst is a deterministic, rule-based implementation that retrieves information from the project API.

It does not currently use a deployed Large Language Model (LLM). Its responses are grounded in available API data and include source information and grounding indicators.

An LLM-based analyst with API tool calling is identified as future work.

## 4. Human Review and Verification

AI assistance was not treated as a substitute for technical verification.

The following checks were performed during project development:

- Geological raster alignment and coordinate reference system checks.
- Verification of the study-area grid and known deposit labels.
- Inspection of geological component scores and final prospectivity scores.
- Execution of spatial block validation.
- Verification of refined target polygons.
- Testing of cell-level explanation records.
- Flask API endpoint testing.
- Automated groundedness evaluation.
- Docker Compose build and deployment verification.
- Frontend interaction and API connectivity testing.

## 5. Limitations and Responsible Use

AI-generated code and recommendations may contain errors. Outputs were therefore checked against actual execution results wherever possible.

The project does not interpret unlabelled cells as confirmed negative locations. PU ranking scores are not calibrated probabilities, and the current spatial validation has limitations due to the geographic concentration of known positive observations.

Candidate exploration targets require independent geological assessment and field validation.

## 6. Summary

AI tools were used as development assistants for planning, coding, debugging, explanation, and documentation. The GeoMine implementation, datasets, model outputs, validation results, and deployed application were produced and tested through the project workflow.

**Project:** GeoMine — IOCG Mineral Prospectivity Mapping  
**Assessment:** GeoMine Geodata Scientist Take-Home Assessment  
**Track:** AI/ML