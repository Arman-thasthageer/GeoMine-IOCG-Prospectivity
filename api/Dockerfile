FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV GEOMINE_BASE=/app
ENV PORT=5000

COPY api/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY reports/cell_explanations.csv ./reports/

RUN mkdir -p /app/data/processed

COPY data/processed/pu_refined_target_polygons.gpkg ./data/processed/
COPY data/processed/final_pu_prospectivity.gpkg ./data/processed/
COPY data/processed/iocg_prospectivity_v4.gpkg ./data/processed/
COPY data/processed/ga_baseline_grid.gpkg ./data/processed/

EXPOSE 5000

CMD ["python", "api/app.py"]