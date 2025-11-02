

# import streamlit as st
# import geopandas as gpd
# import leafmap.foliumap as leafmap
# import os

# # ----------------------------------------------------------
# # ⚙️ Configuration Streamlit
# # ----------------------------------------------------------
# st.set_page_config(page_title="Carte interactive France", layout="wide")
# st.title("🇫🇷 Carte interactive — Régions, Départements et Communes")

# # ----------------------------------------------------------
# # 📁 Chargement des fichiers GeoJSON
# # ----------------------------------------------------------
# path_regions = os.path.join("coordonnees", "a-reg2020-geojson.json")
# path_departements = os.path.join("coordonnees", "a-dep2020-geojson.json")
# path_communes = os.path.join("coordonnees", "p-com2020.json")

# for p in [path_regions, path_departements, path_communes]:
#     if not os.path.exists(p):
#         st.error(f"❌ Fichier manquant : {p}")
#         st.stop()

# gdf_regions = gpd.read_file(path_regions)
# gdf_departements = gpd.read_file(path_departements)
# gdf_communes = gpd.read_file(path_communes)

# # Harmonisation des projections
# for gdf in [gdf_regions, gdf_departements, gdf_communes]:
#     if gdf.crs is not None and gdf.crs.to_string() != "EPSG:4326":
#         gdf.to_crs(epsg=4326, inplace=True)

# # ----------------------------------------------------------
# # 🔍 Détection automatique des colonnes
# # ----------------------------------------------------------
# def detect_columns(gdf, keywords):
#     for k in keywords:
#         for c in gdf.columns:
#             if k.lower() in c.lower():
#                 return c
#     return None

# col_reg_code = detect_columns(gdf_regions, ["code", "reg"])
# col_reg_nom = detect_columns(gdf_regions, ["nom", "libgeo"])
# col_dep_code = detect_columns(gdf_departements, ["code", "dep"])
# col_dep_nom = detect_columns(gdf_departements, ["nom", "libgeo"])
# col_dep_code_reg = detect_columns(gdf_departements, ["reg"])
# col_com_code_dep = detect_columns(gdf_communes, ["code_dep", "dep", "departement"])
# col_com_nom = detect_columns(gdf_communes, ["nom", "commune", "libgeo"])

# # ----------------------------------------------------------
# # 🧠 Affichage latéral
# # ----------------------------------------------------------
# st.sidebar.header("🔍 Colonnes détectées")
# st.sidebar.json({
#     "Régions": list(gdf_regions.columns),
#     "Départements": list(gdf_departements.columns),
#     "Communes": list(gdf_communes.columns)
# })

# # ----------------------------------------------------------
# # 🗺️ Carte principale
# # ----------------------------------------------------------
# m = leafmap.Map(center=[46.7, 2.5], zoom=5, draw_control=False, measure_control=False)
# m.add_basemap("CartoDB.Positron")

# # ----------------------------------------------------------
# # 📍 Fonction de zoom dynamique
# # ----------------------------------------------------------
# def zoom_on_geometry(map_obj, gdf):
#     """Centre la carte sur la géométrie avec zoom adapté à sa taille."""
#     if gdf.empty:
#         return
#     bounds = gdf.total_bounds  # xmin, ymin, xmax, ymax
#     cx = (bounds[0] + bounds[2]) / 2
#     cy = (bounds[1] + bounds[3]) / 2

#     # Taille approximative du polygone pour ajuster le zoom
#     span = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
#     if span > 5:
#         zoom = 6  # grande région
#     elif span > 2:
#         zoom = 8  # département
#     else:
#         zoom = 10  # petite commune
#     map_obj.set_center(cx, cy, zoom=zoom)

# # ----------------------------------------------------------
# # 🧭 Navigation
# # ----------------------------------------------------------
# st.sidebar.subheader("🧭 Navigation")

# region_names = sorted(gdf_regions[col_reg_nom].unique()) if col_reg_nom else []
# selected_region = st.sidebar.selectbox("Choisir une région :", ["Toutes"] + region_names)

# if selected_region != "Toutes":
#     region_geom = gdf_regions[gdf_regions[col_reg_nom] == selected_region]
#     m.add_gdf(region_geom, layer_name=f"Région : {selected_region}",
#               style={"color": "#0044CC", "weight": 2, "fillColor": "#99CCFF", "fillOpacity": 0.25})
#     zoom_on_geometry(m, region_geom)

#     # Départements dans la région
#     if col_dep_code_reg and col_reg_code:
#         dep_region = gdf_departements[gdf_departements[col_dep_code_reg] == region_geom.iloc[0][col_reg_code]]
#     else:
#         dep_region = gpd.GeoDataFrame(columns=gdf_departements.columns)

#     if not dep_region.empty:
#         dep_names = sorted(dep_region[col_dep_nom].unique())
#         selected_dep = st.sidebar.selectbox("Choisir un département :", ["Aucun"] + dep_names)

#         if selected_dep != "Aucun":
#             dep_geom = dep_region[dep_region[col_dep_nom] == selected_dep]
#             m.add_gdf(dep_geom, layer_name=f"Département : {selected_dep}",
#                       style={"color": "#008000", "weight": 2, "fillColor": "#A7F3A0", "fillOpacity": 0.4})
#             zoom_on_geometry(m, dep_geom)

#             # Communes dans le département
#             if col_com_code_dep and col_dep_code:
#                 dep_code = str(dep_geom.iloc[0][col_dep_code])
#                 comm_dep = gdf_communes[gdf_communes[col_com_code_dep].astype(str) == dep_code]
#                 if not comm_dep.empty:
#                     comm_names = sorted(comm_dep[col_com_nom].unique())
#                     selected_com = st.sidebar.selectbox("Choisir une commune :", ["Aucune"] + comm_names)
#                     if selected_com != "Aucune":
#                         com_geom = comm_dep[comm_dep[col_com_nom] == selected_com]
#                         m.add_gdf(com_geom, layer_name=f"Commune : {selected_com}",
#                                   style={"color": "#FFA500", "weight": 1, "fillColor": "#FFF2CC", "fillOpacity": 0.6})
#                         zoom_on_geometry(m, com_geom)
#             else:
#                 st.warning("⚠️ Impossible d'associer les communes (clé manquante).")

# else:
#     m.add_gdf(gdf_regions, layer_name="Régions françaises",
#               style={"color": "#0044AA", "weight": 1.5, "fillColor": "#FFFFFF", "fillOpacity": 0.2})
#     zoom_on_geometry(m, gdf_regions)

# # ----------------------------------------------------------
# # 🚀 Affichage Streamlit
# # ----------------------------------------------------------
# st.markdown("---")
# m.to_streamlit(height=750, width=1200)







import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import folium
import os

# ----------------------------------------------------------
# ⚙️ Configuration Streamlit
# ----------------------------------------------------------
st.set_page_config(page_title="Carte interactive France", layout="wide")
st.title("🇫🇷 Carte interactive — Régions, Départements et Communes (Centroïdes corrigés)")

# ----------------------------------------------------------
# 📁 Chargement des fichiers GeoJSON
# ----------------------------------------------------------
path_regions = os.path.join("coordonnees", "a-reg2020-geojson.json")
path_departements = os.path.join("coordonnees", "a-dep2020-geojson.json")
path_communes = os.path.join("coordonnees", "p-com2020.json")

for p in [path_regions, path_departements, path_communes]:
    if not os.path.exists(p):
        st.error(f"❌ Fichier manquant : {p}")
        st.stop()

gdf_regions = gpd.read_file(path_regions)
gdf_departements = gpd.read_file(path_departements)
gdf_communes = gpd.read_file(path_communes)

# Harmoniser CRS
for gdf in [gdf_regions, gdf_departements, gdf_communes]:
    if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
        gdf.to_crs(epsg=4326, inplace=True)

# ----------------------------------------------------------
# 🔍 Détection automatique des colonnes
# ----------------------------------------------------------
def detect_columns(gdf, keywords):
    for k in keywords:
        for c in gdf.columns:
            if k.lower() in c.lower():
                return c
    return None

col_reg_code = detect_columns(gdf_regions, ["code", "reg"])
col_reg_nom = detect_columns(gdf_regions, ["nom", "libgeo"])
col_dep_code = detect_columns(gdf_departements, ["code", "dep"])
col_dep_nom = detect_columns(gdf_departements, ["nom", "libgeo"])
col_dep_code_reg = detect_columns(gdf_departements, ["reg"])
col_com_code_dep = detect_columns(gdf_communes, ["code_dep", "dep", "departement"])
col_com_nom = detect_columns(gdf_communes, ["nom", "commune", "libgeo"])

# ----------------------------------------------------------
# 🧠 Colonnes détectées
# ----------------------------------------------------------
st.sidebar.header("🔍 Colonnes détectées")
st.sidebar.json({
    "Régions": list(gdf_regions.columns),
    "Départements": list(gdf_departements.columns),
    "Communes": list(gdf_communes.columns)
})

# ----------------------------------------------------------
# 🗺️ Carte
# ----------------------------------------------------------
m = leafmap.Map(center=[46.7, 2.5], zoom=5, draw_control=False, measure_control=False)
m.add_basemap("CartoDB.Positron")

def fit_to_gdf(map_obj, gdf, pad=0.08):
    """Zoom cadré (pas trop profond)"""
    if gdf.empty:
        return
    minx, miny, maxx, maxy = gdf.total_bounds
    dx, dy = (maxx - minx), (maxy - miny)
    if dx == 0 or dy == 0:
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        map_obj.set_center(cx, cy, zoom=12)
    else:
        minx -= dx * pad
        maxx += dx * pad
        miny -= dy * pad
        maxy += dy * pad
        map_obj.fit_bounds([[miny, minx], [maxy, maxx]])

# ----------------------------------------------------------
# 🧭 Navigation
# ----------------------------------------------------------
st.sidebar.subheader("🧭 Navigation")
region_names = sorted(gdf_regions[col_reg_nom].unique()) if col_reg_nom else []
selected_region = st.sidebar.selectbox("Région :", ["Toutes"] + region_names)

# ----------------------------------------------------------
# 🗺️ Logique d'affichage
# ----------------------------------------------------------
if selected_region != "Toutes":
    region_geom = gdf_regions[gdf_regions[col_reg_nom] == selected_region]
    m.add_gdf(
        region_geom,
        layer_name=f"Région : {selected_region}",
        style={"color": "#1e40af", "weight": 2.5, "fillColor": "#93c5fd", "fillOpacity": 0.25},
    )
    fit_to_gdf(m, region_geom)

    # --- Départements
    if col_dep_code_reg and col_reg_code:
        dep_region = gdf_departements[gdf_departements[col_dep_code_reg] == region_geom.iloc[0][col_reg_code]]
    else:
        dep_region = gpd.GeoDataFrame(columns=gdf_departements.columns)

    if not dep_region.empty:
        dep_names = sorted(dep_region[col_dep_nom].unique())
        selected_dep = st.sidebar.selectbox("Département :", ["Aucun"] + dep_names)

        if selected_dep != "Aucun":
            dep_geom = dep_region[dep_region[col_dep_nom] == selected_dep]
            m.add_gdf(
                dep_geom,
                layer_name=f"Département : {selected_dep}",
                style={"color": "#047857", "weight": 2.5, "fillColor": "#a7f3d0", "fillOpacity": 0.35},
            )
            fit_to_gdf(m, dep_geom)

            # --- Filtrer communes du département
            gdf_communes["_dep"] = gdf_communes[col_com_code_dep].astype(str).str.zfill(2)
            dep_code = str(dep_geom.iloc[0][col_dep_code]).zfill(2)
            comm_dep = gdf_communes[gdf_communes["_dep"] == dep_code]

            if not comm_dep.empty:
                # ✅ Afficher les centroïdes en orange
                for _, row in comm_dep.iterrows():
                    if row.geometry is None:
                        continue
                    c = row.geometry.centroid
                    folium.CircleMarker(
                        location=[c.y, c.x],
                        radius=3,
                        color="orange",
                        fill=True,
                        fill_opacity=0.8,
                        popup=row[col_com_nom],
                    ).add_to(m)

                # --- Sélecteur de commune
                com_names = sorted(comm_dep[col_com_nom].unique())
                selected_com = st.sidebar.selectbox("Commune :", ["Aucune"] + com_names)

                if selected_com != "Aucune":
                    com_geom = comm_dep[comm_dep[col_com_nom] == selected_com]
                    m.add_gdf(
                        com_geom,
                        layer_name=f"Commune : {selected_com}",
                        style={"color": "#b45309", "weight": 2, "fillColor": "#fde68a", "fillOpacity": 0.55},
                    )

                    # 🔴 Centroïde rouge
                    c = com_geom.geometry.centroid.iloc[0]
                    folium.CircleMarker(
                        location=[c.y, c.x],
                        radius=6,
                        color="red",
                        fill=True,
                        fill_opacity=1,
                        popup=selected_com,
                    ).add_to(m)

                    fit_to_gdf(m, com_geom)

else:
    m.add_gdf(
        gdf_regions,
        layer_name="Régions françaises",
        style={"color": "#1d4ed8", "weight": 1.6, "fillColor": "#ffffff", "fillOpacity": 0.15},
    )
    fit_to_gdf(m, gdf_regions)

# ----------------------------------------------------------
# 🚀 Affichage Streamlit
# ----------------------------------------------------------
st.markdown("---")
m.to_streamlit(height=750, width=1200)
