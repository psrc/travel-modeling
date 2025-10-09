import os, sys
import toml
import pandas as pd
from pathlib import Path
import geopandas as gpd
import os.path
import psrcelmerpy
from sqlalchemy import create_engine
from functions import load_network_summary, intersect_geog
from emissions import *

###############################################################
# Settings
###############################################################

# get toml config location as script argument
if len(sys.argv) > 1:
    config_path = sys.argv[1]
else:
    config_path = 'config.toml'

config = toml.load(config_path)

###############################################################
# Script Start
###############################################################

# # Create outputs directory if needed
output_dir = os.path.join(config['output_root'],'city')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
for vmt_dir in ['interzonal_vmt','intrazonal_vmt']:
    if not os.path.exists(os.path.join(output_dir,vmt_dir)):
        os.makedirs(os.path.join(output_dir,vmt_dir))

# Change working directory to run_dir
os.chdir(config["run_dir"])

# Load the network shapefile
crs = 'EPSG:2285'
gdf_network = gpd.read_file(os.path.join(config["run_dir"],r'inputs\scenario\networks\shapefiles\AM\AM_edges.shp'))
gdf_network.crs = crs

# Load city from ElmerGeo
eg_conn = psrcelmerpy.ElmerGeoConn()
gdf_shp = eg_conn.read_geolayer('regional_geographies_preferred_alternative')
gdf_shp = gdf_shp.to_crs(crs)

# Perform intersect to get the network within each city in a list
df_network = load_network_summary(os.path.join(config["run_dir"], r'outputs\network\network_results.csv'))


taz_gdf = eg_conn.read_geolayer('taz2010_no_water')
taz_gdf = taz_gdf.to_crs(crs)
# Get list of zones to include for intrazonal trips
# Include intrazonal trips for any TAZ centroids within city boundary

# Load TAZ centroids
_taz_gdf = gpd.GeoDataFrame(taz_gdf.centroid)
_taz_gdf.geometry = _taz_gdf[0]
_taz_gdf['taz'] = taz_gdf['taz'].astype('int')

# # Load run config toml files
input_settings = toml.load(os.path.join(config["run_dir"], 'configuration', 'input_configuration.toml'))
summary_settings = toml.load(os.path.join(config["run_dir"], 'configuration', 'summary_configuration.toml'))


def evaluate_emissions(_gdf_shp):
    """Compute emissions for a jurisdiction. 
    
        _gdf_shp: polygon geodataframe of a jurisidiction (should be complete coverage without holes over bodies of water, etc.)
        model_year: must be passed for clarity

    """

    # Intersect jurisdiction polygon with network shapefile and network CSV file
    _gdf_shp = intersect_geog(_gdf_shp, gdf_network)

    # Select links from network summary dataframe that are within the gdf_shp
    # The dataframe contains link-level model outputs
    _df = df_network[df_network['ij'].isin(_gdf_shp['link_id'])]

    # Replace length with length from _gdf_shp to ensure roads stop at city boundaries
    # Drop "length field from _gdf_shp, which is length in miles; 
    # use new_length field, which is calculated length of intersected links in feet
    _df.drop('length', axis=1, inplace=True)
    _df = _df.merge(_gdf_shp, how='left', left_on='ij', right_on='link_id')
    # _df.drop('length', axis=1, inplace=True)
    _df.rename(columns={'new_length': 'length',
                    'length': 'original_length'}, inplace=True)



    df_interzonal_vmt = calculate_interzonal_vmt(_df, input_settings, summary_settings)
    # df_interzonal = calculate_interzonal_emissions(df_interzonal_vmt, df_running_rates)

    city_gdf = gdf_shp[gdf_shp['juris'] == city]

    intersect_gdf = gpd.overlay(_taz_gdf, 
            city_gdf, 
            how="intersection")

    # Load intrazonal trips for zones in the area
    df_iz = pd.read_csv(os.path.join(config["run_dir"],r'outputs\network\iz_vol.csv'))

    # Filter for zone centroids within the jurisdiction
    _df_iz = df_iz[df_iz['taz'].isin(intersect_gdf.taz)]

    # If no zones centroids in a city, pass an empty df with 0 values for VMT;
    # Otherwise calculate intrazonal VMT for the associated TAZs only
    if len(_df_iz) > 0:
        df_intrazonal_vmt = calculate_intrazonal_vmt(summary_settings, _df_iz)
        
    else:
        # Load the regional results and fill VMT with 0
        df_intrazonal_vmt = pd.read_csv(os.path.join(config["run_dir"], r'outputs\emissions\intrazonal_vmt_grouped.csv'))
        df_intrazonal_vmt['VMT'] = 0

    return df_interzonal_vmt, df_intrazonal_vmt

# Select all cities and towns in King county
alt_city_list = []
if len(alt_city_list) == 0:
    city_list = gdf_shp[(gdf_shp['cnty_name'] == 'King') & (gdf_shp['rg_propose_pa'].isin(['CitiesTowns', 'Core',
                    'Metro','HCT']))]['juris'].to_list()
    # Exclude any PAA (potential annexation area from this list); we will consider that unincorporated King County
    for i in city_list:
        if 'PAA' in i:
            city_list.remove(i)

    # Manually remove some anomalies:
    city_list.remove('North Highline')

    # Also add in Bainbridge Island since they request this data
    # city_list += ['Bainbridge Island']

else:
    city_list = alt_city_list

missing_city_list = []

for city in city_list:
    if not os.path.isfile(os.path.join(config["output_root"],city+'.csv')):
        print(city)
        _gdf_shp = gdf_shp[gdf_shp['juris'] == city]
        df_interzonal_vmt, df_intrazonal_vmt = evaluate_emissions(_gdf_shp)
        df_interzonal_vmt.to_csv(os.path.join(output_dir,'interzonal_vmt',city+'.csv'), index=False)
        df_intrazonal_vmt.to_csv(os.path.join(output_dir,'intrazonal_vmt',city+'.csv'), index=False)
