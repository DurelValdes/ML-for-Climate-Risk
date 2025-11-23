import sys
import pandas as pd

def main():
    if len(sys.argv) < 3:
        print("Usage : python cumul.py fichier_final.csv fichier1.csv [fichier2.csv ...]")
        sys.exit(1)

    fichier_final = sys.argv[1]
    fichiers_concat = sys.argv[2:]

    dfs = []
    for fichier in fichiers_concat:
        df = pd.read_csv(fichier, sep=';')
        dfs.append(df)

    df_concat = pd.concat(dfs, ignore_index=True)

    if 'DATE' in df_concat.columns:
        df_concat = df_concat.drop(columns=['DATE'])

    df_concat.to_csv(fichier_final, index=False, sep=';')
    print(f"Fichier concaténé sauvegardé sous : {fichier_final}")

if __name__ == "__main__":
    main()
