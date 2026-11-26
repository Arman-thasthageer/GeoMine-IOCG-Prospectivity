
import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange,
    QgsFillSymbol,
    QgsClassificationCustom,
    QgsStyle
)

from qgis.PyQt.QtGui import QColor

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

GPKG = os.path.join(
    BASE,
    "data",
    "processed",
    "final_pu_prospectivity.gpkg"
)

LAYER_NAME = "final_pu_prospectivity"

print("=" * 65)
print("STYLING FULL-AREA PU PROSPECTIVITY MAP")
print("=" * 65)

# --------------------------------------------------
# 1. GET OR LOAD LAYER
# --------------------------------------------------

project = QgsProject.instance()

layers = project.mapLayersByName(LAYER_NAME)

if layers:
    layer = layers[0]
else:
    layer = QgsVectorLayer(
        GPKG + "|layername=" + LAYER_NAME,
        LAYER_NAME,
        "ogr"
    )

    if not layer.isValid():
        raise RuntimeError("Could not load PU prospectivity layer.")

    project.addMapLayer(layer)

if not layer.isValid():
    raise RuntimeError("PU layer is invalid.")

if layer.featureCount() != 112179:
    raise ValueError("Unexpected feature count.")

if layer.crs().authid() != "EPSG:3577":
    raise ValueError("Expected EPSG:3577.")

if layer.fields().indexFromName("pu_percentile") == -1:
    raise ValueError("pu_percentile field not found.")

print("Layer:", layer.name())
print("Features:", layer.featureCount())
print("CRS:", layer.crs().authid())

# --------------------------------------------------
# 2. DEFINE FIVE PROSPECTIVITY CLASSES
# --------------------------------------------------

classes = [
    (0, 20, "Very Low", "#ffffcc"),
    (20, 40, "Low", "#a1dab4"),
    (40, 60, "Moderate", "#41b6c4"),
    (60, 80, "High", "#2c7fb8"),
    (80, 100, "Very High", "#253494")
]

ranges = []

for lower, upper, label, color in classes:

    symbol = QgsFillSymbol.createSimple({
        "color": color,
        "outline_style": "no"
    })

    renderer_range = QgsRendererRange(
        lower,
        upper,
        symbol,
        label
    )

    ranges.append(renderer_range)

# --------------------------------------------------
# 3. APPLY GRADUATED RENDERER
# --------------------------------------------------

renderer = QgsGraduatedSymbolRenderer(
    "pu_percentile",
    ranges
)

renderer.setClassificationMethod(
    QgsClassificationCustom()
)

layer.setRenderer(renderer)

layer.triggerRepaint()

# --------------------------------------------------
# 4. SET LAYER DISPLAY
# --------------------------------------------------

layer.setOpacity(0.90)

project.setTitle(
    "GeoMine - IOCG PU Prospectivity Map"
)

iface.setActiveLayer(layer)

# Zoom to study area
iface.mapCanvas().setExtent(layer.extent())
iface.mapCanvas().refresh()

# --------------------------------------------------
# 5. SAVE QGIS PROJECT
# --------------------------------------------------

PROJECT_FILE = os.path.join(
    BASE,
    "outputs",
    "GeoMine_PU_Prospectivity.qgz"
)

project.setFileName(PROJECT_FILE)

saved = project.write()

if not saved:
    raise RuntimeError("QGIS project could not be saved.")

# --------------------------------------------------
# 6. PRINT CLASSIFICATION SUMMARY
# --------------------------------------------------

print("\nPROSPECTIVITY CLASSES")
print("-" * 50)

for lower, upper, label, color in classes:
    print(
        label,
        "| Percentile:",
        str(lower) + "-" + str(upper),
        "| Color:",
        color
    )

print("\nQGIS PROJECT SAVED")
print(PROJECT_FILE)

print("\n" + "=" * 65)
print("PU PROSPECTIVITY MAP STYLING COMPLETED")
print("=" * 65)
