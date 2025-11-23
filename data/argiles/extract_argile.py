
import subprocess

command = 'ogr2ogr -f GeoJSON ExpoArgile_Fxx_4326.geojson ExpoArgile_Fxx_4326.mbtiles'
result = subprocess.run(command, shell=True, capture_output=True, text=True)

if result.returncode != 0:
    print("Erreur lors de l'exécution:", result.stderr)
else:
    print("Conversion réussie :", result.stdout)
    print("Fichier GeoJSON créé avec succès : ExpoArgile_Fxx_4326.geojson")