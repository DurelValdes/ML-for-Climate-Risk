import pandas as pd

df = pd.read_csv("C:/Users/HP/Desktop/ML for climate risk/ML-for-Climate-Risk/data/swi_uniforme/swi_unif_annee.csv", sep=';')

df['seuil_T1_of'] = df[['swi_unif_01', 'swi_unif_02', 'swi_unif_03']].mean(axis=1)
df['seuil_T2_of'] = df[['swi_unif_04', 'swi_unif_05', 'swi_unif_06']].mean(axis=1)
df['seuil_T3_of'] = df[['swi_unif_07', 'swi_unif_08', 'swi_unif_09']].mean(axis=1)
df['seuil_T4_of'] = df[['swi_unif_10', 'swi_unif_11', 'swi_unif_12']].mean(axis=1)

def seuil_secheresse(swi_series):
    sorted_vals = swi_series.nsmallest(2)
    seuil = sorted_vals.max()
    return swi_series <= seuil

def calc_binaires_par_trimestre(df, trimestre_col):
    results = []
    for num in df['NUMERO'].unique():
        df_subset = df[df['NUMERO'] == num].copy()
        df_subset = df_subset.sort_values('ANNEE').reset_index(drop=True)
        binaire = []
        for idx, row in df_subset.iterrows():
            annee = row['ANNEE']
            fenetre = df_subset[(df_subset['ANNEE'] >= annee - 49) & (df_subset['ANNEE'] <= annee)][trimestre_col]
            is_secheresse = seuil_secheresse(fenetre)
            index_in_fenetre = fenetre.index.get_loc(idx)
            binaire.append(int(is_secheresse.iloc[index_in_fenetre]))
        df_subset[trimestre_col + '_binaire'] = binaire
        results.append(df_subset)
    return pd.concat(results)

df_result = df.copy()
for t in ['seuil_T1_of', 'seuil_T2_of', 'seuil_T3_of', 'seuil_T4_of']:
    df_result = calc_binaires_par_trimestre(df_result, t)

# Sauvegarde du résultat dans un fichier CSV
df_result.to_csv("seuil_officiel.csv", sep=';', index=False)

print(df_result[['NUMERO', 'ANNEE', 'seuil_T1_of_binaire', 'seuil_T2_of_binaire', 'seuil_T3_of_binaire', 'seuil_T4_of_binaire']])
