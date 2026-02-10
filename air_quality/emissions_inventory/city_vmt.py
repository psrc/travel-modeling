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

def calculate_city_vmt(city_polygon_gdf, gdf_network, taz_centroid_gdf):
    """Compute VMT for a jurisdiction. 
    
        city_polygon_gdf: polygon geodataframe of a jurisidiction (should be complete coverage without holes over bodies of water, etc.)
        model_year: must be passed for clarity
        gdf_network: geodataframe of all Soundcast network links with VMT attributes
        taz_centroid_gdf: point geodataframe of all TAZ centroids

    """

    # Intersect jurisdiction polygon with network shapefile and network CSV file
    city_network_gdf = intersect_geog(city_polygon_gdf, gdf_network)

    # Select links from network summary dataframe that are within the gdf_shp
    # The dataframe contains link-level model outputs
    df_city_network = df_network[df_network['ij'].isin(city_network_gdf['link_id'])]

    # Replace length with length from _gdf_shp to ensure roads stop at city boundaries
    # Drop "length field from city_network_gdf, which is length in miles; 
    # use new_length field, which is calculated length of intersected links in feet
    df_city_network.drop('length', axis=1, inplace=True)
    df_city_network = df_city_network.merge(city_network_gdf, how='left', left_on='ij', right_on='link_id')
    df_city_network.rename(columns={'new_length': 'length',
                    'length': 'original_length'}, inplace=True)



    df_interzonal_vmt = calculate_interzonal_vmt(df_city_network, input_settings, summary_settings)

    city_taz_gdf = gpd.overlay(taz_centroid_gdf, 
            city_polygon_gdf, 
            how="intersection")

    # Load intrazonal trips for zones in the area
    df_iz = pd.read_csv(os.path.join(config["run_dir"],r'outputs\network\iz_vol.csv'))
    # Filter for zone centroids within the jurisdiction
    df_iz = df_iz[df_iz['taz'].isin(city_taz_gdf.taz)]

    # If no zones centroids in a city, pass an empty df with 0 values for VMT;
    # Otherwise calculate intrazonal VMT for the associated TAZs only
    if len(df_iz) > 0:
        df_intrazonal_vmt = calculate_intrazonal_vmt(summary_settings, df_iz)
        
    else:
        # Load the regional results and fill VMT with 0
        df_intrazonal_vmt = pd.read_csv(os.path.join(config["run_dir"], r'outputs\emissions\intrazonal_vmt_grouped.csv'))
        df_intrazonal_vmt['VMT'] = 0

    return df_interzonal_vmt, df_intrazonal_vmt

###############################################################
# Script Start
###############################################################

for county in ["King", "Kitsap"]:
    # Create outputs directory if needed
    output_dir = os.path.join(config['output_root'],'data','city', county)
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

# Get list of zones to include for intrazonal trips
# Include intrazonal trips for any TAZ centroids within city boundary
taz_gdf = eg_conn.read_geolayer('taz2010_no_water')
taz_gdf = taz_gdf.to_crs(crs)

# Load TAZ centroids
taz_centroid_gdf = gpd.GeoDataFrame(taz_gdf.centroid)
taz_centroid_gdf.geometry = taz_centroid_gdf[0]
taz_centroid_gdf['taz'] = taz_gdf['taz'].astype('int')

# Load run config toml files
input_settings = toml.load(os.path.join(config["run_dir"], 'configuration', 'input_configuration.toml'))
summary_settings = toml.load(os.path.join(config["run_dir"], 'configuration', 'summary_configuration.toml'))


####################
# King County
####################

# Select all cities and towns in King County
county = "King"
city_list = gdf_shp[(gdf_shp['cnty_name'] == county) & (gdf_shp['rg_propose_pa'].isin(['CitiesTowns', 'Core',
                'Metro','HCT']))]['juris'].to_list()
# Exclude any PAA (potential annexation area from this list); we will consider that unincorporated King County
for i in city_list:
    if 'PAA' in i:
        city_list.remove(i)

# Manually remove some anomalies in King County that should be considered unincorporated:
city_list.remove('North Highline')

for city in city_list:
    if not os.path.isfile(os.path.join(config["output_root"],'data','city',county,city+'.csv')):
        print(city)
        city_polygon_gdf = gdf_shp[gdf_shp['juris'] == city]

        df_interzonal_vmt, df_intrazonal_vmt = calculate_city_vmt(city_polygon_gdf, gdf_network, taz_centroid_gdf)
        
        # Write file as CSVs for each city
        df_interzonal_vmt.to_csv(os.path.join(config["output_root"],'data','city',county,'interzonal_vmt',city+'.csv'), index=False)
        df_intrazonal_vmt.to_csv(os.path.join(config["output_root"],'data','city',county,'intrazonal_vmt',city+'.csv'), index=False)


####################
# Kitsap, Pierce, and Snohomish Counties
####################

# Only Bainbridge has requested VMT data in the past, but we will set the process up for other counties to be added as needed
county = "Kitsap"
for county in ["Kitsap", "Pierce", "Snohomish"]:
    city_list = gdf_shp[(gdf_shp['cnty_name'] == county) & (gdf_shp['rg_propose_pa'].isin(['CitiesTowns', 'Core',
                    'Metro','HCT']))]['juris'].to_list()

    for city in city_list:
        if not os.path.isfile(os.path.join(config["output_root"],'data','city',county,city+'.csv')):
            print(city)
            city_polygon_gdf = gdf_shp[gdf_shp['juris'] == city]

            df_interzonal_vmt, df_intrazonal_vmt = calculate_city_vmt(city_polygon_gdf, gdf_network, taz_centroid_gdf)
            
            # Write file as CSVs for each city
            df_interzonal_vmt.to_csv(os.path.join(config["output_root"],'data','city',county,'interzonal_vmt',city+'.csv'), index=False)
            df_intrazonal_vmt.to_csv(os.path.join(config["output_root"],'data','city',county,'intrazonal_vmt',city+'.csv'), index=False)