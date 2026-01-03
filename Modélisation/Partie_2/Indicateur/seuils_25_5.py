import pandas as pd

# Chargement du CSV
df = pd.read_csv("C:/Users/HP/Desktop/ML for climate risk/ML-for-Climate-Risk/data/swi_uniforme/swi_unif_annee.csv", sep=';')

# Définition des trimestres
trimestres = {
    "T1": ["swi_unif_01", "swi_unif_02", "swi_unif_03"],
    "T2": ["swi_unif_04", "swi_unif_05", "swi_unif_06"],
    "T3": ["swi_unif_07", "swi_unif_08", "swi_unif_09"],
    "T4": ["swi_unif_10", "swi_unif_11", "swi_unif_12"],
}

# On crée une colonne trimestrielle pour chaque année
for t_name, mois in trimestres.items():
    df[t_name] = df[mois].mean(axis=1)   # moyenne des 3 mois du trimestre

# Résultat final par NUMERO
result = {"NUMERO": df["NUMERO"].unique()}

for t_name in trimestres.keys():
    result[f"seuil_{t_name}_25"] = []
    result[f"seuil_{t_name}_5"] = []

# On calcule les seuils pour chaque NUMERO
for numero in result["NUMERO"]:
    df_num = df[df["NUMERO"] == numero]  # toutes les années de ce NUMERO
    
    for t_name in trimestres.keys():
        values = df_num[t_name].dropna().values

        q25 = pd.Series(values).quantile(0.25)
        q05 = pd.Series(values).quantile(0.05)

        
        result[f"seuil_{t_name}_25"].append(q25)
        result[f"seuil_{t_name}_5"].append(q05)

# Construction de la nouvelle base
df_res = pd.DataFrame(result)

# Export CSV
df_res.to_csv("seuils_25_5.csv", index=False)

print("Nouvelle base générée : nouvelle_base_swi_seuils.csv")
