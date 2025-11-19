import pandas as pd
from pyproj import Transformer
import sys
import pandas as pd
from pyproj import Transformer
import sys


def convert_lambert2hm_to_lambert93m(input_csv, output_csv):
    df = pd.read_csv(input_csv, sep=';')

    # Conversion de hectomètres en mètres
    df['LAMBX_m'] = df['LAMBX'] * 100
    df['LAMBY_m'] = df['LAMBY'] * 100

    # Initialiser la transformation (Lambert 2 étendu en mètres vers Lambert 93)
    transformer = Transformer.from_crs("EPSG:27572", "EPSG:2154", always_xy=True)

    # Transformer les coordonnées converties en mètres
    x93, y93 = transformer.transform(df['LAMBX_m'].values, df['LAMBY_m'].values)

    df['LAMBX_93'] = x93
    df['LAMBY_93'] = y93

    # Enregistrer dans le CSV de sortie
    df.to_csv(output_csv, sep=';', index=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_lambert.py input.csv output.csv")
    else:
        convert_lambert2hm_to_lambert93m(sys.argv[1], sys.argv[2])
