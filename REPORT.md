# GeoMine: IOCG Mineral Prospectivity Mapping
**GeoMine Geodata Scientist Take-Home Assessment | AI/ML Track**

## 1. Executive Summary

This project presents an AI/ML-based mineral prospectivity mapping prototype for Iron Oxide Copper-Gold (IOCG) exploration across the Tennant Creek–Mount Isa investigation region, Australia.

The objective is to integrate geological evidence, expert-derived mineral-system indicators, and machine learning to rank prospective exploration areas.

A 2 km × 2 km spatial grid was generated using EPSG:3577. Thirty-one geological predictors were extracted and organised into four mineral-system components: Sources, Energy/Drivers, Pathways/Architecture, and Deposition.

A Positive-Unlabelled (PU) Random Forest ensemble was implemented to generate relative prospectivity rankings. Spatial holdout evaluation was conducted using 50 km blocks. High-ranking cells were grouped into 11 refined exploration targets.

The final prototype includes cell-level geological explanations, a Flask REST API, a React and Leaflet dashboard, and a deterministic API-grounded geological analyst. The complete application was successfully deployed using Docker Compose.

## 2. Geological Data and Methodology

### 2.1 Data Preparation

The project uses geological predictor rasters, Australian mineral deposit records, an investigation-area boundary, and expert-derived GA prospectivity baseline maps.

The source rasters were verified for alignment and spatial consistency. The investigation boundary and deposit locations were projected into EPSG:3577, and a 2 km analysis grid was generated and clipped to the study area.

Zonal mean statistics were extracted from 31 geological predictor rasters.

**Dataset summary:**

| Attribute | Value |
|---|---:|
| Geological predictors | 31 |
| Grid resolution | 2 km × 2 km |
| Study-area grid cells | 112,179 |
| Known positive cells | 16 |
| Unlabelled cells | 112,163 |
| Confirmed negative cells | 0 |

### 2.2 Mineral-System Components

The geological predictors were grouped into four mineral-system components:

| Component | Predictors | Count |
|---|---|---:|
| Sources | S | 7 |
| Energy / Drivers | D | 8 |
| Pathways / Architecture | P | 5 |
| Deposition | T | 11 |

Official predictor weights were normalised within each component to calculate component scores ranging from 0 to 100.

The expert-derived final prospectivity score was calculated using a geometric mean:

\[
S_{\mathrm{final}} =
100\left[
\frac{S}{100}
\frac{E}{100}
\frac{P}{100}
\frac{D}{100}
\right]^{1/4}
\]

This formulation ensures that all four mineral-system components contribute to the final expert-derived score. A zero component score produces a zero final score.

The expert-derived baseline and GA baseline were kept separate from machine-learning predictors and labels.

## 3. Machine Learning and Spatial Validation

### 3.1 Positive-Unlabelled Random Forest

The study area contains known deposit locations but no verified negative exploration observations. Therefore, a Positive-Unlabelled learning approach was adopted.

Known deposit cells were treated as positive observations, while the remaining cells were treated as unlabelled observations. Unlabelled observations were sampled during training rather than interpreted as confirmed barren locations.

The final ensemble configuration included:

- Random Forest classifier with 300 trees per model.
- Maximum tree depth of 12.
- Minimum leaf size of 2.
- Square-root feature selection.
- Balanced class weights.
- Ten ensemble models.
- Repeated unlabelled sampling at five times the positive count.

The final model was trained using all 16 known positive cells and sampled unlabelled observations.

The model produces a PU ranking score between 0 and 1. These scores are relative ranking values, not calibrated probabilities of discovering IOCG deposits.

### 3.2 Spatial Validation

Spatial block validation used 50 km blocks. Four adjacent blocks contained all 16 known positive cells.

The held-out block capture results were:

| Held-out block | Top 5% | Top 10% | Top 20% |
|---|---:|---:|---:|
| B_3_-42 | 0% | 100% | 100% |
| B_3_-43 | 0% | 0% | 0% |
| B_4_-42 | 0% | 20% | 100% |
| B_4_-43 | 33.33% | 66.67% | 66.67% |
| **Aggregate** | **18.75%** | **50%** | **75%** |

These aggregate results represent fold-wise positive capture at the respective area cutoffs.

The validation has an important limitation: the positive blocks are geographically clustered. Holding out one block leaves neighbouring positive blocks in the training dataset, while a 50 km buffer could remove all available training positives.

Consequently, these results are preliminary spatial holdout results, not definitive independent geographic validation. Conventional AUC interpretation was not used because unlabelled cells are not confirmed negatives.

## 4. Exploration Targets and Geological Explanations

### 4.1 Refined Exploration Targets

The final PU scores were ranked, and cells in the 99th percentile were grouped into spatially connected clusters. The resulting dataset contains 11 refined target polygons.

| Target | Cells | Area (km²) | Mean PU score | Known deposit cells |
|---|---:|---:|---:|---:|
| R1 | 623 | 2,492 | 0.9273 | 15 |
| R2 | 23 | 92 | 0.8256 | 0 |
| R3 | 3 | 12 | 0.8029 | 0 |
| R4 | 6 | 24 | 0.7981 | 0 |
| R5 | 87 | 348 | 0.7533 | 0 |
| R6 | 3 | 12 | 0.7389 | 0 |
| R7 | 179 | 716 | 0.7241 | 0 |
| R8 | 5 | 20 | 0.7125 | 0 |
| R9 | 155 | 620 | 0.6904 | 0 |
| R10 | 23 | 92 | 0.6899 | 0 |
| R11 | 5 | 20 | 0.5896 | 0 |

R1 contains 15 known deposit cells because the final model was trained using the known positive observations. It is not independent predictive evidence.

R2–R11 contain no known positive cells in the current dataset. They are unlabelled candidate areas requiring independent geological review and field validation.

### 4.2 Cell-Level Explanations

The system provides PU scores, ranking percentiles, component scores, top geological drivers, and data completeness for individual grid cells.

For example, grid cell 1 has:

- PU score: 0.9958.
- PU percentile: 99.9973%.
- Sources: 49.1259.
- Energy: 44.7102.
- Pathways: 50.1290.
- Deposition: 8.5163.
- Data completeness: 100%.

Its leading geological drivers are P2a (Pathways), S4 (Sources), and S5 (Sources).

These drivers represent weighted contributions to geological component scores, not causal explanations of the Random Forest prediction.

## 5. Application Engineering and Grounded Analyst

The prototype includes a Flask REST API with endpoints for health checks, metadata, cell information, geological explanations, targets, map layers, and analyst queries.

A React 19, Vite, and Leaflet frontend provides an interactive prospectivity map, known deposit overlays, refined target polygons, target selection, cell-level explanations, and an analyst interface.

The geological analyst currently uses deterministic, rule-based responses grounded in the project API. It is not a deployed LLM.

The initial automated groundedness evaluation achieved:

| Evaluation metric | Result |
|---|---:|
| Questions evaluated | 10 |
| Automatic checks passed | 10 |
| Automatic checks failed | 0 |

The evaluation checks expected responses and grounding indicators; manual review remains necessary.

### Docker Deployment

The application was successfully containerised using Docker Compose with two services:

- `geomine-api`: Python 3.12 and Flask.
- `geomine-frontend`: React production build served through Nginx.

Both containers were verified as running.

**Application URL:** `http://localhost:8081`

**API health check:** `http://localhost:8081/api/health`

The deployed application was tested for API connectivity, target selection, cell explanations, and analyst responses.

## 6. Limitations and Future Work

The primary limitation is the small number of known positive cells (16), with no confirmed negative observations. Positive locations are concentrated in four adjacent spatial blocks, limiting the strength of geographic validation.

Additional limitations include sparse deposition predictor coverage, uncalibrated PU ranking scores, and the need for independent geological assessment of candidate targets.

Future improvements include:

1. Incorporating additional verified IOCG deposits and reliable barren-area observations.
2. Improving spatial validation using geographically independent positive datasets.
3. Evaluating additional PU learning and machine-learning approaches.
4. Integrating further geochemical and geophysical evidence.
5. Improving model-level explanation methods.
6. Introducing an LLM-based analyst with API tool calling and strict groundedness evaluation.
7. Conducting independent geological review and field validation of candidate targets.

## 7. Conclusion

GeoMine demonstrates an end-to-end IOCG mineral prospectivity prototype integrating geospatial processing, expert-derived mineral-system scoring, Positive-Unlabelled Random Forest modelling, spatial holdout evaluation, exploration target identification, geological explanations, REST API development, and interactive mapping.

The system produces ranked candidate exploration areas while explicitly communicating the limitations of the available positive-unlabelled dataset.

The Docker deployment provides an operational frontend and backend application, establishing a foundation for further geological assessment and future model improvements.

---

**Project:** GeoMine — IOCG Mineral Prospectivity Mapping  
**Assessment:** GeoMine Geodata Scientist Take-Home Assessment  
**Track:** AI/ML  
**Study Area:** Tennant Creek–Mount Isa, Australia  
**Grid Resolution:** 2 km × 2 km  
**CRS:** EPSG:3577