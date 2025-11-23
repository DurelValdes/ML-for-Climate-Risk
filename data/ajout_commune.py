import geopandas as gpd
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import numpy as np

def assign_by_knn_nearest_centroid_knn(polygons_path, points_csv_path, output_csv_path):
    # Charger polygones
    gdf_polygons = gpd.read_file(polygons_path)
    print(f"Polygones chargés : {len(gdf_polygons)}")

    # Projection uniforme en EPSG 2154
    if gdf_polygons.crs.to_epsg() != 2154:
        if gdf_polygons.crs.to_epsg() == 4326:
            gdf_polygons = gdf_polygons.to_crs(epsg=2154)
        else:
            raise ValueError(f"CRS inattendu: {gdf_polygons.crs}.")

    # Calculer les centroïdes des polygones
    gdf_polygons['centroid'] = gdf_polygons.geometry.centroid
    
    # Extraire coordonnées centroïdes dans un array numpy
    X_polygons = np.array([[pt.x, pt.y] for pt in gdf_polygons['centroid']])

    # Charger points dans DataFrame Pandas
    df_points = pd.read_csv(points_csv_path)
    
    # Extraire coordonnées points dans un array numpy (supposant colonnes LAMBX_right et LAMBY_right existantes)
    X_points = df_points[['LAMBX_right', 'LAMBY_right']].values

    # Instancier KNN (k=1, voisin le plus proche)
    nbrs = NearestNeighbors(n_neighbors=1, algorithm='auto').fit(X_polygons)
    
    # Trouver l'indice du centroïde le plus proche pour chaque point
    distances, indices = nbrs.kneighbors(X_points)
    
    # Récupérer attributs du polygone associé au plus proche voisin
    df_points['code_insee'] = gdf_polygons.iloc[indices.flatten()]['code_insee'].values
    df_points['nom_officiel'] = gdf_polygons.iloc[indices.flatten()]['nom_officiel'].values
    df_points['code_insee_de_la_region'] = gdf_polygons.iloc[indices.flatten()]['code_insee_de_la_region'].values
    # Dictionnaire de correspondance code INSEE -> nom de la région
    region_dict = {
        '11': "Île-de-France",
        '24': "Centre-Val de Loire",
        '27': "Bourgogne-Franche-Comté",
        '28': "Normandie",
        '32': "Hauts-de-France",
        '44': "Grand Est",
        '52': "Pays de la Loire",
        '53': "Bretagne",
        '75': "Nouvelle-Aquitaine",
        '76': "Occitanie",
        '84': "Auvergne-Rhône-Alpes",
        '93': "Provence-Alpes-Côte d'Azur",
        '94': "Corse"
    }

    # Création de la colonne 'nom_de_la_region' via la correspondance
    df_points['region'] = df_points['code_insee_de_la_region'].map(region_dict)

    # Fonction pour extraire le code département (prise en compte spécificités Corse)
    def extraire_code_departement(code_commune):
        if code_commune.startswith('2A') or code_commune.startswith('2B'):
            return code_commune[:2]
        return code_commune[:2]

    df_points['code_insee_departement'] = df_points['code_insee'].apply(extraire_code_departement)

    # Dictionnaire complet code département -> nom département
    departement_dict = {
        '01': "Ain", '02': "Aisne", '03': "Allier", '04': "Alpes-de-Haute-Provence", '05': "Hautes-Alpes",
        '06': "Alpes-Maritimes", '07': "Ardèche", '08': "Ardennes", '09': "Ariège", '10': "Aube",
        '11': "Aude", '12': "Aveyron", '13': "Bouches-du-Rhône", '14': "Calvados", '15': "Cantal",
        '16': "Charente", '17': "Charente-Maritime", '18': "Cher", '19': "Corrèze", '2A': "Corse-du-Sud",
        '2B': "Haute-Corse", '21': "Côte-d'Or", '22': "Côtes-d'Armor", '23': "Creuse", '24': "Dordogne",
        '25': "Doubs", '26': "Drôme", '27': "Eure", '28': "Eure-et-Loir", '29': "Finistère",
        '30': "Gard", '31': "Haute-Garonne", '32': "Gers", '33': "Gironde", '34': "Hérault",
        '35': "Ille-et-Vilaine", '36': "Indre", '37': "Indre-et-Loire", '38': "Isère", '39': "Jura",
        '40': "Landes", '41': "Loir-et-Cher", '42': "Loire", '43': "Haute-Loire", '44': "Loire-Atlantique",
        '45': "Loiret", '46': "Lot", '47': "Lot-et-Garonne", '48': "Lozère", '49': "Maine-et-Loire",
        '50': "Manche", '51': "Marne", '52': "Haute-Marne", '53': "Mayenne", '54': "Meurthe-et-Moselle",
        '55': "Meuse", '56': "Morbihan", '57': "Moselle", '58': "Nièvre", '59': "Nord",
        '60': "Oise", '61': "Orne", '62': "Pas-de-Calais", '63': "Puy-de-Dôme", '64': "Pyrénées-Atlantiques",
        '65': "Hautes-Pyrénées", '66': "Pyrénées-Orientales", '67': "Bas-Rhin", '68': "Haut-Rhin", '69': "Rhône",
        '70': "Haute-Saône", '71': "Saône-et-Loire", '72': "Sarthe", '73': "Savoie", '74': "Haute-Savoie",
        '75': "Paris", '76': "Seine-Maritime", '77': "Seine-et-Marne", '78': "Yvelines", '79': "Deux-Sèvres",
        '80': "Somme", '81': "Tarn", '82': "Tarn-et-Garonne", '83': "Var", '84': "Vaucluse",
        '85': "Vendée", '86': "Vienne", '87': "Haute-Vienne", '88': "Vosges", '89': "Yonne",
        '90': "Territoire de Belfort", '91': "Essonne", '92': "Hauts-de-Seine", '93': "Seine-Saint-Denis",
        '94': "Val-de-Marne", '95': "Val-d'Oise"
    }

    # Création de la colonne avec le nom du département
    df_points['departement'] = df_points['code_insee_departement'].map(departement_dict)





    # Sauvegarde
    df_points.to_csv(output_csv_path, index=False)
    print(f"Attribution par KNN terminée. Résultat sauvegardé dans {output_csv_path}.")

if __name__ == "__main__":
    assign_by_knn_nearest_centroid_knn(
        "limite_admin/ADMIN-EXPRESS_4-0__GPKG_WGS84G_FRA_2025-10-15/ADMIN-EXPRESS/1_DONNEES_LIVRAISON_2025-10-00141/ADE_4-0_GPKG_WGS84G_FRA-ED2025-10-15/limit_admin.geojson",
        "swi_with_niveau_dpt_knn.csv",
        "data.csv"
    )
