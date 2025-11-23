import pandas as pd

# Lire le CSV
df = pd.read_csv("swi_2000_2024.csv", sep=';')



# Extraire l'année à partir de MOIS (format YYYYMM)
df['ANNEE'] = df['MOIS'].astype(str).str[:4]

# Colonnes à pivoter (exclure LAMBX, LAMBY, MOIS, ANNEE)
cols_to_pivot = df.columns.difference(['LAMBX', 'LAMBY', 'MOIS', 'ANNEE'])

# Fonction pour pivoter chaque colonne en colonnes mensuelles
def pivot_monthly(df, col):
    df_pivot = df.pivot_table(index=['LAMBX', 'LAMBY', 'ANNEE'],
                              columns=df['MOIS'].astype(str).str[-2:].astype(int),
                              values=col)
    # Renommer colonnes comme COL_01 ... COL_12
    df_pivot.columns = [f"{col}_{i:02d}" for i in df_pivot.columns]
    return df_pivot

# Appliquer le pivot sur toutes les colonnes à pivoter
dfs = [pivot_monthly(df, col) for col in cols_to_pivot]

# Fusionner tous les résultats sur index commun
from functools import reduce
df_final = reduce(lambda left, right: left.join(right), dfs).reset_index()

# Sauvegarder le résultat
df_final.to_csv("swi_annee.csv", sep=';', index=False)

