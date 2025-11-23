import pandas as pd
import glob

# Rechercher tous les fichiers CSV dont le nom commence par "swi." dans le dossier courant
file_list = glob.glob('swi.*.csv')

# Concaténer les fichiers
dfs = []
for file in file_list:
    df = pd.read_csv(file, sep=';', dtype={"DATE": str})
    dfs.append(df)

concat_df = pd.concat(dfs, ignore_index=True)

# Filtrer sur la colonne 'DATE' pour ne garder que les années de 2020 à 2025 inclus
# On suppose que 'DATE' est de la forme "YYYYMM" (par exemple "202201")
# concat_df['ANNEE'] = concat_df['DATE'].str[:4].astype(int)
# concat_df = concat_df[concat_df['ANNEE'].between(2020, 2025)]

# Optionnel : Réordonner les colonnes et supprimer la colonne ANNEE temporaire
# concat_df = concat_df.drop(columns=['ANNEE'])
concat_df['SWI_UNIF_MENS'] = concat_df['SWI_UNIF_MENS'].str.replace(',', '.').astype(float)



# Sauvegarder le résultat dans un nouveau CSV
concat_df.to_csv('swi_unif_concat.csv', sep=';', index=False)
