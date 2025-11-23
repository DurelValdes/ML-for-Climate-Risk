import geopandas as gpd

LimitAdmin = r"ADE_4-0_GPKG_WGS84G_FRA-ED2025-10-15.gpkg"

import pyogrio

layers = pyogrio.list_layers(LimitAdmin)
print(layers)

gdf_commune = gpd.read_file(LimitAdmin, layer="commune")

print(gdf_commune.crs)
gdf_commune.head()

gdf_commune.to_file(r"limit_admin.geojson", driver="GeoJSON")

