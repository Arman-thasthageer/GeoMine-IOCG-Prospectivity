
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsFillSymbol,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling
)
from qgis.PyQt.QtGui import QColor, QFont

import os

BASE = r"C:\Users\Ermus\Desktop\GeoMine"

GPKG = os.path.join(
    BASE, "data", "processed",
    "pu_refined_target_polygons.gpkg"
)

PROJECT_OUTPUT = os.path.join(
    BASE, "outputs",
    "GeoMine_PU_Prospectivity.qgz"
)

print("=" * 65)
print("STYLING REFINED IOCG TARGET POLYGONS")
print("=" * 65)

project = QgsProject.instance()

# Find the existing layer or load it
layers = project.mapLayersByName("pu_refined_target_polygons")

if layers:
    layer = layers[0]
else:
    layer = QgsVectorLayer(
        GPKG + "|layername=pu_refined_target_polygons",
        "pu_refined_target_polygons",
        "ogr"
    )
    if not layer.isValid():
        raise RuntimeError("Target polygon layer could not be loaded.")
    project.addMapLayer(layer)

# Colour palette for the 11 targets
palette = [
    "#d73027",
    "#4575b4",
    "#1a9850",
    "#984ea3",
    "#ff7f00",
    "#a6d854",
    "#e7298a",
    "#66c2a5",
    "#e6ab02",
    "#a6761d",
    "#7570b3"
]

categories = []

for index in range(1, 12):

    target_id = "R" + str(index)

    symbol = QgsFillSymbol.createSimple({
        "color": QColor(palette[index - 1]).name(),
        "outline_color": "#222222",
        "outline_width": "0.35",
        "outline_width_unit": "MM",
        "style": "solid"
    })

    category = QgsRendererCategory(
        target_id,
        symbol,
        target_id
    )

    categories.append(category)

renderer = QgsCategorizedSymbolRenderer(
    "target_id",
    categories
)

layer.setRenderer(renderer)

# Label each target with its ID
settings = QgsPalLayerSettings()
settings.fieldName = "target_id"
settings.enabled = True

text_format = QgsTextFormat()
font = QFont("Arial", 10)
font.setBold(True)

text_format.setFont(font)
text_format.setSize(10)
text_format.setColor(QColor("#111111"))

settings.setFormat(text_format)

layer.setLabeling(
    QgsVectorLayerSimpleLabeling(settings)
)

layer.setLabelsEnabled(True)

layer.triggerRepaint()

# Set layer order
root = project.layerTreeRoot()

target_node = root.findLayer(layer.id())

if target_node:
    target_node.setItemVisibilityChecked(True)

for name in [
    "grid_labeled",
    "grid_deposit_join",
    "grid_2km_clipped"
]:
    for old_layer in project.mapLayersByName(name):
        node = root.findLayer(old_layer.id())
        if node:
            node.setItemVisibilityChecked(False)

# Keep the deposit overlay and boundary visible
for name in [
    "iocg_deposits_projected",
    "study_boundary_3577",
    "final_pu_prospectivity"
]:
    for overlay in project.mapLayersByName(name):
        node = root.findLayer(overlay.id())
        if node:
            node.setItemVisibilityChecked(True)

# Put target polygons above the prospectivity grid
if target_node:
    clone = target_node.clone()
    root.insertChildNode(0, clone)
    root.removeChildNode(target_node)

# Save project
result = project.write(PROJECT_OUTPUT)

if not result:
    raise RuntimeError("Could not save QGIS project.")

print("\nTarget polygon styling applied.")
print("Target categories:", len(categories))
print("Labels enabled: Yes")
print("Project saved:", PROJECT_OUTPUT)
print("\nSTYLING COMPLETED")
