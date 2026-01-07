import pandas as pd
import sys

def aggregate_monthly(input_csv, output_csv):
    # Lire le CSV
    df = pd.read_csv(input_csv, sep=';')
    
    # Nettoyer les colonnes (si espaces)
    df.columns = [col.strip() for col in df.columns]
    
    # Extraire les informations de mois (format AAAAMM)
    df['MOIS'] = df['DATE'].astype(str).str[:6]
    
    # Colonnes à regrouper
    group_cols = ['LAMBX', 'LAMBY', 'MOIS']
    
    # Trouver les colonnes numériques à agréger (sauf celles de groupage)
    num_cols = df.select_dtypes(include='number').columns.difference(['LAMBX', 'LAMBY'])
    # Ajouter les colonnes non numériques mais pertinentes à la liste si besoin

    # Agréger par la moyenne
    agg_df = df.groupby(group_cols)[num_cols].mean().reset_index().round(2)
    
    # Enregistrer le nouveau CSV
    agg_df.to_csv(output_csv, sep=';', index=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python aggregate_monthly.py input.csv output.csv")
    else:
        aggregate_monthly(sys.argv[1], sys.argv[2])

# commande python agreg.py mon_fichier_source.csv mon_fichier_destination.csv
# python agreg.py swi_daily_2020-2024.csv swi_monthly.csv
