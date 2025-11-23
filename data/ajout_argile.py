import geopandas as gpd
import pandas as pd

def format_dpt(val):
    val = str(val).upper()
    if val.isdigit():
        return val.zfill(2)
    return val

def assign_by_knn_nearest_centroid(polygons_path, points_csv_path, output_csv_path):
    # Charger polygones
    gdf_polygons = gpd.read_file(polygons_path)
    print(f"Polygones chargés : {len(gdf_polygons)}")
    # Projection uniforme en EPSG 2154
    if gdf_polygons.crs.to_epsg() != 2154:
        if gdf_polygons.crs.to_epsg() == 3857:
            gdf_polygons = gdf_polygons.to_crs(epsg=2154)
        else:
            raise ValueError(f"CRS inattendu: {gdf_polygons.crs}.")
    
    # Calculer les centroïdes des polygones
    gdf_polygons['centroid'] = gdf_polygons.geometry.centroid
    gdf_centroids = gpd.GeoDataFrame(
        gdf_polygons[['NIVEAU', 'DPT']],
        geometry=gdf_polygons['centroid'],
        crs=gdf_polygons.crs
    )

    print("Début jointure nearest")
    # Charger les points
    df_points = pd.read_csv(points_csv_path, sep=';')
    gdf_points = gpd.GeoDataFrame(
        df_points,
        geometry=gpd.points_from_xy(df_points['LAMBX_right'], df_points['LAMBY_right']),
        crs='EPSG:2154'
    )

    # Réaliser la jointure nearest
    joined = gpd.sjoin_nearest(gdf_points, gdf_centroids, how='left', distance_col='dist')

    print('Fin jointure')


    # Ajouter NIVEAU et DPT au DataFrame points
    df_points['NIVEAU'] = joined['NIVEAU']
    df_points['DPT'] = joined['DPT']
    #df_points['DPT'] = df_points['DPT'].astype(str).str.zfill(2)
    # Sauvegarder
    df_points.to_csv(output_csv_path, index=False)
    print(f"Attribution par KNN terminée. Résultat sauvegardé dans {output_csv_path}.")

if __name__ == "__main__":
    assign_by_knn_nearest_centroid(
        "argiles/ExpoArgile_Fxx_4326.geojson",
        "swi_merged_left_2000_2024.csv",
        "swi_with_niveau_dpt_knn.csv"
    )
