import os
import requests
import gzip
import shutil
import zipfile
import py7zr
import pandas as pd
import geopandas as gpd

DATA_DIR = "data"
SWI_DAILY_CSV_DIR = os.path.join(DATA_DIR, "swi_daily_csv")
LIMITE_ADMIN_DIR = os.path.join(DATA_DIR, "limite_admin")

def download_file(url, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    local_filename = os.path.join(dest_folder, url.split("/")[-1])
    if os.path.exists(local_filename):
        print(f"{local_filename} déjà téléchargé.")
        return local_filename
    print(f"Téléchargement de {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Téléchargé dans {local_filename}")
    return local_filename

def extract_zip(zip_path, extract_folder):
    if os.path.isdir(extract_folder) and os.listdir(extract_folder):
        print(f"Le dossier {extract_folder} existe déjà et n'est pas vide, extraction ignorée.")
        return
    print(f"Extraction de {zip_path} ...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)
    print("Extraction terminée.")

def extract_7z(archive_path, extract_folder):
    if os.path.isdir(extract_folder) and os.listdir(extract_folder):
        print(f"Le dossier {extract_folder} existe déjà et n'est pas vide, extraction ignorée.")
        return
    print(f"Extraction de {archive_path} ...")
    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        archive.extractall(path=extract_folder)
    print("Extraction terminée.")

def convert_gz_to_csv(gz_path, csv_path):
    if os.path.exists(csv_path):
        print(f"{csv_path} existe déjà, conversion ignorée.")
        return
    print(f"Conversion de {gz_path} en {csv_path} ...")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(csv_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Conversion terminée.")

def load_csv(file_path, **kwargs):
    print(f"Chargement du fichier CSV {file_path} ...")
    df = pd.read_csv(file_path, **kwargs)
    print(f"Données chargées : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    return df

def generate_dynamic_name(gz_filename):
    base = os.path.splitext(gz_filename)[0]
    if "92065ec0" in base:
        return "swi_daily_2020-2024.csv"
    elif "adcca99a" in base:
        return "swi_daily_2025.csv"
    elif "da6cd598" in base:
        return "swi_daily_2010-2019.csv"
    elif "10d2ce77" in base:
        return "swi_daily_2000-2009.csv"
    else:
        return f"{base}.csv"

def load_swi_daily_files(gz_paths):
    os.makedirs(SWI_DAILY_CSV_DIR, exist_ok=True)
    dfs = []
    for gz_path in gz_paths:
        gz_filename = os.path.basename(gz_path)
        csv_filename = generate_dynamic_name(gz_filename)
        csv_path = os.path.join(SWI_DAILY_CSV_DIR, csv_filename)
        convert_gz_to_csv(gz_path, csv_path)
        df = load_csv(csv_path, sep=';', decimal=',', encoding='utf-8', low_memory=False)
        dfs.append(df)
    return dfs

def load_swi_uniforme(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.csv') or file.endswith('.txt'):
                path = os.path.join(root, file)
                return load_csv(path, sep=';', decimal=',', encoding='utf-8', low_memory=False)
    print("Aucun fichier SWI uniforme chargé.")
    return None

def load_argile(folder_path):
    print(f"Le dossier Argiles contient un fichier .mbtiles non compatible avec pandas. Chargement ignoré.")
    return None

def load_limite_admin(folder_path):
    # Cherche un fichier geopackage (.gpkg) dans le répertoire extrait
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".gpkg"):
                gpkg_path = os.path.join(root, file)
                print(f"Chargement du GeoPackage {gpkg_path}")
                gdf = gpd.read_file(gpkg_path)
                print(f"Données limite admin chargées : {len(gdf)} entités")
                return gdf
    print("Aucun fichier limite admin (GPKG) chargé.")
    return None

def main():
    urls_swi_daily = [
        "https://www.data.gouv.fr/api/1/datasets/r/92065ec0-ea6f-4f5e-8827-4344179c0a7f",
        "https://www.data.gouv.fr/api/1/datasets/r/adcca99a-6db0-495a-869f-40c888174a57",
        "https://www.data.gouv.fr/api/1/datasets/r/da6cd598-498b-4e39-96ea-fae89a4a8a46",
        "https://www.data.gouv.fr/api/1/datasets/r/10d2ce77-5c3b-44f8-bb46-4df27ed48595"
    ]
    urls = {
        "swi_uniforme": "https://donneespubliques.meteofrance.fr/donnees_libres/Txt/Swi/SWI_Package_1969-2024.zip",
        "argiles": "https://www.data.gouv.fr/api/1/datasets/r/c944be1e-06d6-46be-bf7d-9f9ad2b8ced9",
        "limite_admin": "https://data.geopf.fr/telechargement/download/ADMIN-EXPRESS/ADMIN-EXPRESS_4-0__GPKG_WGS84G_FRA_2025-10-15/ADMIN-EXPRESS_4-0__GPKG_WGS84G_FRA_2025-10-15.7z"
    }

    swi_daily_gz_files = [download_file(url, DATA_DIR) for url in urls_swi_daily]

    dfs_swi_daily = load_swi_daily_files(swi_daily_gz_files)

    swi_uniforme_zip = download_file(urls["swi_uniforme"], DATA_DIR)
    argiles_7z = download_file(urls["argiles"], DATA_DIR)
    limite_admin_7z = download_file(urls["limite_admin"], DATA_DIR)

    extract_zip(swi_uniforme_zip, os.path.join(DATA_DIR, "swi_uniforme"))
    extract_7z(argiles_7z, os.path.join(DATA_DIR, "argiles"))
    extract_7z(limite_admin_7z, LIMITE_ADMIN_DIR)

    df_swi_uniforme = load_swi_uniforme(os.path.join(DATA_DIR, "swi_uniforme"))
    df_argiles = load_argile(os.path.join(DATA_DIR, "argiles"))
    gdf_limite_admin = load_limite_admin(LIMITE_ADMIN_DIR)

    return dfs_swi_daily, df_swi_uniforme, df_argiles, gdf_limite_admin


if __name__ == "__main__":
    dfs_swi_daily, df_swi_uniforme, df_argiles, gdf_limite_admin = main()
    print(f"Nombre de fichiers SWI quotidien chargés : {len(dfs_swi_daily)}")
    print(df_swi_uniforme.head() if df_swi_uniforme is not None else "Pas de données SWI uniforme.")
    print("Pas de chargement des données argile car fichier .mbtiles non compatible.")
    if gdf_limite_admin is not None:
        print(gdf_limite_admin.head())
    else:
        print("Pas de données Limite administrative chargées.")
