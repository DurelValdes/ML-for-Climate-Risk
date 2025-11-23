import os
import requests
import gzip
import shutil
import pandas as pd

DATA_DIR = "swi_daily_csv"

def download_file(url, filename, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    local_path = os.path.join(dest_folder, filename)
    if os.path.exists(local_path):
        print(f"{local_path} déjà téléchargé.")
        return local_path
    print(f"Téléchargement de {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Téléchargé dans {local_path}")
    return local_path

def decompress_gz(gz_path, csv_path):
    print(f"Décompression de {gz_path} vers {csv_path}...")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(csv_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Décompression terminée.")

def main():
    url_to_filename = {
        "https://www.data.gouv.fr/api/1/datasets/r/da6cd598-498b-4e39-96ea-fae89a4a8a46": "swi_2010_2019.csv.gz",
        "https://www.data.gouv.fr/api/1/datasets/r/10d2ce77-5c3b-44f8-bb46-4df27ed48595": "swi_2000_2009.csv.gz",
    }

    downloaded_gz_files = []
    for url, gz_filename in url_to_filename.items():
        path = download_file(url, gz_filename, DATA_DIR)
        downloaded_gz_files.append(path)

    dfs = []
    for gz_path in downloaded_gz_files:
        csv_path = gz_path[:-3]  # enlever .gz à la fin
        decompress_gz(gz_path, csv_path)
        df = pd.read_csv(csv_path)
        dfs.append(df)

    return dfs

if __name__ == "__main__":
    dfs = main()
    print("Chargement terminé")
