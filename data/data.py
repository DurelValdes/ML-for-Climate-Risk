import pandas as pd
from sklearn.neighbors import NearestNeighbors
from pyproj import Transformer

def lambert2_to_lambert93(x, y):
    transformer = Transformer.from_crs("EPSG:27572", "EPSG:2154", always_xy=True)  # Lambert 2 étendu -> Lambert 93
    x2, y2 = transformer.transform(x, y)
    return x2, y2

def merge_nearest_left(df_left, df_right, left_coords=['LAMBX', 'LAMBY'], right_coords=['LAMBX', 'LAMBY'], key='ANNEE'):
    # Conversion hectomètres → mètres dans df_left
    df_left[left_coords] = df_left[left_coords] * 100

    # Convertir coordonnées df_left de Lambert 2 étendu vers Lambert 93
    x_l, y_l = lambert2_to_lambert93(df_left[left_coords[0]].values, df_left[left_coords[1]].values)
    df_left = df_left.copy()

    df_left['LAMBX_orig_swi'] = df_left[left_coords[0]]
    df_left['LAMBY_orig_swi'] = df_left[left_coords[1]]

    df_left[left_coords[0]] = x_l
    df_left[left_coords[1]] = y_l

    # Filtrer sur années
    df_left = df_left[(df_left[key] >= 2000) & (df_left[key] <= 2024)].reset_index(drop=True)
    df_right = df_right[(df_right[key] >= 2000) & (df_right[key] <= 2024)].reset_index(drop=True)

    merged_rows = []

    for annee in sorted(df_left[key].unique()):
        left_sub = df_left[df_left[key] == annee].reset_index(drop=True)
        right_sub = df_right[df_right[key] == annee].reset_index(drop=True)

        if right_sub.empty:
            left_sub = left_sub.assign(**{f"{col}_right": pd.NA for col in right_sub.columns if col not in [key]})
            merged_rows.append(left_sub)
            continue

        nbrs = NearestNeighbors(n_neighbors=1).fit(right_sub[right_coords].values)
        distances, indices = nbrs.kneighbors(left_sub[left_coords].values)

        right_matches = right_sub.loc[indices.flatten()].reset_index(drop=True)
        right_matches = right_matches.add_suffix('_right')

        combined = pd.concat([left_sub.reset_index(drop=True), right_matches], axis=1)
        merged_rows.append(combined)

    result = pd.concat(merged_rows, ignore_index=True)
    return result

def main():
    df_swi_annee = pd.read_csv('swi_daily_csv/swi_annee.csv', sep=';')
    df_swi_unif_annee = pd.read_csv('swi_uniforme/swi_unif_annee.csv', sep=';')

    df_merged = merge_nearest_left(df_swi_annee, df_swi_unif_annee)

    df_merged.to_csv('swi_merged_left_2000_2024.csv', sep=';', index=False)
    print("Merge gauche réalisé, fichier sauvegardé sous 'swi_merged_left_2000_2024.csv'")

if __name__ == "__main__":
    main()
