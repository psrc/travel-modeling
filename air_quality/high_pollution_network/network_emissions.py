import os, sys
import pandas as pd
import geopandas as gpd
import emissions
import json
import toml
from sqlalchemy import create_engine

# get toml config location as script argument
if len(sys.argv) > 1:
    config_path = sys.argv[1]
else:
    config_path = 'config.toml'

config = toml.load(config_path)

# Load run config toml files
input_settings = toml.load(os.path.join(config["run_dir"], 'configuration', 'input_configuration.toml'))
summary_settings = toml.load(os.path.join(config["run_dir"], 'configuration', 'summary_configuration.toml'))

db_dir = "sqlite:///"+config["run_dir"]+'/inputs/db/'+input_settings["db_name"]
conn = create_engine(db_dir)


# Perform intersect to get the network within each city in a list
df_network = emissions.load_network_summary(os.path.join(config["run_dir"], r'outputs\network\network_results.csv'))

df_running_rates = emissions.load_running_rates(config["model_year"], summary_settings, conn)

df_interzonal_vmt = emissions.calculate_interzonal_vmt(df_network, input_settings, summary_settings)

# Calculate per-network-link emissions (totals by pollutant for each link)
df_network_emissions = emissions.calculate_network_emissions(
    df_network, df_running_rates, summary_settings, config.get("include_light_modes", False)
)

# How to identify the high pollution network?
# Let's use the base year VMT as the starting point
# Get the grams/mile for any roadway with more than 20,000 AADT or something
# Use that threshold to evaluate how many future roadways fit in that criteria

# Calculate 

gdf = gpd.read_file(os.path.join(config["run_dir"], r'inputs\scenario\networks\shapefiles\AM\AM_edges.shp'))
gdf = gdf.merge(df_network_emissions, left_on="link_id", right_on="ij", how="left")

gdf_pm25 = gdf[gdf["pollutantID"] == 110].copy()

# Ensure there's an identifier column to match GeoJSON features
gdf_pm25 = gdf_pm25.reset_index(drop=True)
gdf_pm25["link_id_str"] = gdf_pm25["link_id"].astype(str)

# Convert to GeoJSON and use featureidkey to match locations to properties.link_id_str
geojson = json.loads(gdf_pm25.to_json())

import plotly.express as px
# choose a valid color column (use tons_tot if available)
color_col = "tons_tot" if "tons_tot" in gdf_pm25.columns else ("grams_tot" if "grams_tot" in gdf_pm25.columns else None)
if color_col is None:
    raise RuntimeError("No emissions column (tons_tot or grams_tot) available to color the map.")

fig = px.choropleth_mapbox(
    gdf_pm25,
    geojson=geojson,
    locations="link_id_str",
    featureidkey="properties.link_id_str",
    color=color_col,
    color_continuous_scale="Viridis",
    mapbox_style="carto-positron",
    zoom=10,
    center={"lat": gdf_pm25.geometry.centroid.y.mean(), "lon": gdf_pm25.geometry.centroid.x.mean()},
    opacity=0.8,
)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.show()

# export to shapefile


# Identify areas of highest pollution 
print(df_network_emissions.head())