import pandas as pd

# ------------------------------
# 1. Charger les bases
# ------------------------------
data = pd.read_csv("C:/Users/HP/Desktop/ML for climate risk/ML-for-Climate-Risk/data/data_cleaned.csv")
seuils = pd.read_csv("seuils_25_5.csv")
seuil_off = pd.read_csv("seuil_officiel.csv", sep=";")

# ------------------------------
# 2. Définition des trimestres
# ------------------------------
trimestres = {
    "T1": ["swi_unif_01", "swi_unif_02", "swi_unif_03"],
    "T2": ["swi_unif_04", "swi_unif_05", "swi_unif_06"],
    "T3": ["swi_unif_07", "swi_unif_08", "swi_unif_09"],
    "T4": ["swi_unif_10", "swi_unif_11", "swi_unif_12"],
}

# ------------------------------
# 3. Fusion avec seuils 25/5
# ------------------------------
data = data.merge(seuils, on="NUMERO", how="left")

# ------------------------------
# 4. Création des indicateurs trimestriels
# ------------------------------
for tri, cols in trimestres.items():

    # moyenne du trimestre
    data[f"swi_mean_{tri}"] = data[cols].mean(axis=1)

    # indicateurs 25% et 5%
    data[f"ind_sec_{tri}_25"] = (data[f"swi_mean_{tri}"] < data[f"seuil_{tri}_25"]).astype(int)
    data[f"ind_sec_{tri}_5"] = (data[f"swi_mean_{tri}"] <= data[f"seuil_{tri}_5"]).astype(int)

# ------------------------------
# 5. Fusion avec la base officielle
# ------------------------------
seuil_off_small = seuil_off[
    ["NUMERO", "ANNEE",
     "seuil_T1_of_binaire",
     "seuil_T2_of_binaire",
     "seuil_T3_of_binaire",
     "seuil_T4_of_binaire"]
].copy()

# Renommage
seuil_off_small = seuil_off_small.rename(columns={
    "seuil_T1_of_binaire": "ind_sec_T1_off",
    "seuil_T2_of_binaire": "ind_sec_T2_off",
    "seuil_T3_of_binaire": "ind_sec_T3_off",
    "seuil_T4_of_binaire": "ind_sec_T4_off",
})

data = data.merge(seuil_off_small, on=["NUMERO", "ANNEE"], how="left")

# ------------------------------
# 6. Suppression colonnes intermédiaires
# ------------------------------
cols_to_drop = []

# colonnes seuils importées
cols_to_drop += [
    f"seuil_{tri}_25" for tri in ["T1", "T2", "T3", "T4"]
]
cols_to_drop += [
    f"seuil_{tri}_5" for tri in ["T1", "T2", "T3", "T4"]
]

# colonnes moyennes trimestrielles
cols_to_drop += [
    f"swi_mean_{tri}" for tri in ["T1", "T2", "T3", "T4"]
]

data = data.drop(columns=cols_to_drop, errors="ignore")

# ------------------------------
# 7. Export final propre
# ------------------------------
data.to_csv("base_indic_complete.csv", index=False)

print("✔ Base propre enregistrée : base_indic_complete.csv")
