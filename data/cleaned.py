import pandas as pd
df = pd.read_csv("data.csv")
colonnes_a_supprimer = ['LAMBX', 'LAMBY', 'ANNEE','DPT'] 
df = df.drop(columns=colonnes_a_supprimer)
colonnes_a_renommer = {
    'LAMBX_orig_swi': 'LAMBX_2',
    'LAMBY_orig_swi': 'LAMBY_2',
    'LAMBX_right': 'LAMBX_93',
    'LAMBY_right': 'LAMBY_93',
    'code_insee': 'code_insee_commune',
    'nom_officiel': 'commune',
    'NIVEAU': 'argile_niveau',
}
df = df.rename(columns=colonnes_a_renommer)

df.columns = [col[:-6] if col.endswith('_right') else col for col in df.columns]
df['code_insee_de_la_region'] = df['code_insee_de_la_region'].astype(str)

# Liste des colonnes que vous voulez en premier, dans l'ordre désiré
colonnes_prioritaires = [
    'NUMERO', 'LAMBX_93', 'LAMBY_93', 'LAMBX_2', 'LAMBY_2', 'ANNEE',
    'code_insee_commune', 'commune', 'code_insee_de_la_region', 'region',
    'code_insee_departement', 'departement', 'argile_niveau'
]

# Colonnes swi_unif_01 à swi_unif_12
swi_unif_cols = [f'swi_unif_{str(i).zfill(2)}' for i in range(1, 13)]

# Colonnes SWI_01 à SWI_12
swi_cols = [f'SWI_{str(i).zfill(2)}' for i in range(1, 13)]

# Construire la liste finale des colonnes dans l'ordre demandé
colonnes_ordonnees = colonnes_prioritaires + swi_unif_cols + swi_cols

# Récupérer les colonnes restantes (non listées)
autres_colonnes = [col for col in df.columns if col not in colonnes_ordonnees]

# Réordonner le DataFrame
df = df[colonnes_ordonnees + autres_colonnes]

df.to_csv("data_cleaned.csv", index=False)
