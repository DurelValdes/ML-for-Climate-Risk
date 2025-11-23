import pandas as pd
import numpy as np

# Lire le CSV
df = pd.read_csv("swi_unif_concat.csv", sep=';')

# Convertir la colonne DATE en string
df['DATE'] = df['DATE'].astype(str)

# Extraire l'année et le mois de la date
df['ANNEE'] = df['DATE'].str[:4]
df['MOIS'] = df['DATE'].str[4:6].astype(int)

# Assurer que SWI_UNIF_MENS est une string puis remplacer ',' par '.' pour convertir en float
df['SWI_UNIF_MENS'] = df['SWI_UNIF_MENS'].astype(str).str.replace(',', '.').astype(float)

# Pivot du dataframe pour avoir une colonne par mois
df_pivot = df.pivot_table(index=['NUMERO','LAMBX', 'LAMBY', 'ANNEE'],
                          columns='MOIS',
                          values='SWI_UNIF_MENS').reset_index()

# Renommer les colonnes mois en format swi_unif_01, swi_unif_02 ...
df_pivot.columns = ['NUMERO','LAMBX', 'LAMBY', 'ANNEE'] + [f'swi_unif_{i:02d}' for i in range(1, 13)]

# Sauvegarder en CSV
df_pivot.to_csv("swi_unif_annee.csv", sep=';', index=False)
