# Spatial join TAZ centroid to Census Tracts
# Use summary conda env to use pscrelmerpy
import os
import psrcelmerpy
import toml

config = toml.load('config.toml')

eg_conn = psrcelmerpy.ElmerGeoConn()
taz_gdf = eg_conn.read_geolayer('taz2010_no_water')
taz_gdf.to_crs(epsg=config["project_epsg"], inplace=True)

# Assume 2020 tract geography
tract_gdf = eg_conn.read_geolayer('tract2020_nowater')
tract_gdf.to_crs(epsg=config["project_epsg"], inplace=True)

# Get TAZ centroids and intersect with tract_gdf
taz_centroids = taz_gdf.copy()
taz_centroids['geometry'] = taz_centroids.centroid
taz_tract_intersection = taz_centroids.sjoin(tract_gdf, how='left', predicate='intersects')

taz_tract_intersection = taz_tract_intersection[["taz","geoid20"]]
taz_tract_intersection["taz"] = taz_tract_intersection["taz"].astype(int)

taz_tract_intersection.to_csv(os.path.join(config["working_dir"], "taz_tract_lookup.csv"), index=False)