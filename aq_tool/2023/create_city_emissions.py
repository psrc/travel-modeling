import os
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

# Set root of model run to analyze AND the model year
run_dir = r'\\modelstation2\c$\Workspace\sc_2023_07_25_25'
model_year = '2023'    # Make sure to update this since rates used are based on this value

# Set output directory; results will be stored in a folder by model year 
output_dir = Path(os.getcwd(),'output', model_year)

# Script will process a standard set of cities unless otherwise specified
alt_city_list = []
create_county_total = True

###############################################################
# Script Start
###############################################################

# Create outputs directory if needed
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Change working directory to run_dir
os.chdir(run_dir)

# Load the network
crs = 'EPSG:2285'
gdf_network = gpd.read_file(os.path.join(run_dir,r'inputs\scenario\networks\shapefiles\AM\AM_edges.shp'))
gdf_network.crs = crs

# Load tract geographies from ElmerGeo
eg_conn = psrcelmerpy.ElmerGeoConn()
gdf_shp = eg_conn.read_geolayer('regional_geographies_preferred_alternative')
gdf_shp = gdf_shp.to_crs(crs)

# Load parcels as a geodataframe
parcel_df = pd.read_csv(os.path.join(run_dir,r'inputs/scenario/landuse/parcels_urbansim.txt'), sep='\s+',
                            usecols=['parcelid','xcoord_p','ycoord_p','hh_p'])
parcel_gdf = gpd.GeoDataFrame(parcel_df,
        geometry=gpd.points_from_xy(parcel_df['xcoord_p'], parcel_df['ycoord_p']), crs=crs)
parcel_gdf.crs = crs

# Perform intersect to get the network within each city in a list
df_network = load_network_summary(os.path.join(run_dir, r'outputs\network\network_results.csv'))

# connection_string = 'mssql+pyodbc://AWS-PROD-SQL\Sockeye/ElmerGeo?driver=SQL Server?Trusted_Connection=yes'

# version = "'DBO.Default'"
# taz_gdf = read_from_sde(connection_string, 'taz2010_no_water', version, crs=crs, is_table=False)
taz_gdf = eg_conn.read_geolayer('taz2010_no_water')
taz_gdf = taz_gdf.to_crs(crs)
# Get list of zones to include for intrazonal trips
# Include intrazonal trips for any TAZ centroids within city boundary

# Load TAZ centroids
_taz_gdf = gpd.GeoDataFrame(taz_gdf.centroid)
_taz_gdf.geometry = _taz_gdf[0]
_taz_gdf['taz'] = taz_gdf['taz'].astype('int')

# Calculate interzonal emissions using same approach as for regional/county emissions
os.chdir(run_dir)
conn = create_engine('sqlite:///inputs/db/soundcast_inputs_2023.db')

# Load run config toml files
input_settings = toml.load(os.path.join(run_dir, 'configuration', 'input_configuration.toml'))
summary_settings = toml.load(os.path.join(run_dir, 'configuration', 'summary_configuration.toml'))

df_running_rates = load_running_rates(input_settings, summary_settings, conn)

# Select the month to use for each pollutant; some rates are used for winter or summer depending
# on when the impacts are at a maximum due to temperature.
df_summer = df_running_rates[
    df_running_rates["pollutantID"].isin(summary_settings["summer_list"])
]
df_summer = df_summer[df_summer["monthID"] == 7]
df_winter = df_running_rates[
    ~df_running_rates["pollutantID"].isin(summary_settings["summer_list"])
]
df_winter = df_winter[df_winter["monthID"] == 1]
df_running_rates = pd.concat([df_winter, df_summer])

start_rates_df = load_starting_rates(input_settings, summary_settings, conn)

# # Load observed base year vehicle populations by county
# df_veh = pd.read_sql('SELECT * FROM vehicle_population WHERE year=='+input_settings['base_year'], con=conn)
# # Load parcel to county geographic lookup
# parcel_geog = pd.read_sql("SELECT ParcelID, CountyName FROM parcel_"+str(input_settings['base_year'])+"_geography", con=conn) 

# # Scale all vehicles by difference between base year and modeled total vehicles owned from auto onwership model
# df_hh = pd.read_csv(r'outputs/daysim/_household.tsv', delim_whitespace=True, usecols=['hhvehs','hhparcel'])

# start_rates_df = pd.read_sql('SELECT * FROM start_emission_rates_by_veh_type WHERE year=='+model_year, con=conn)

# # Select winter rates for pollutants other than those listed in summer_list
# df_summer = start_rates_df[start_rates_df['pollutantID'].isin(summary_settings['summer_list'])]
# df_summer = df_summer[df_summer['monthID'] == 7]
# df_winter = start_rates_df[~start_rates_df['pollutantID'].isin(summary_settings['summer_list'])]
# df_winter = df_winter[df_winter['monthID'] == 1]
# start_rates_df = pd.concat([df_winter,df_summer])

# # Sum total emissions across all times of day, by county, for each pollutant
# start_rates_df = start_rates_df.groupby(['pollutantID','county','veh_type']).sum()[['ratePerVehicle']].reset_index()

# df_bus_veh = pd.read_sql('SELECT * FROM bus_vehicles WHERE year=='+input_settings['base_year'], con=conn)

def evaluate_emissions(_gdf_shp, df_running_rates):
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
    df_interzonal = calculate_interzonal_emissions(df_interzonal_vmt, df_running_rates)

    city_gdf = gdf_shp[gdf_shp['juris'] == city]

    intersect_gdf = gpd.overlay(_taz_gdf, 
            city_gdf, 
            how="intersection")

    # Load intrazonal trips for zones in the area
    df_iz = pd.read_csv(os.path.join(run_dir,r'outputs\network\iz_vol.csv'))

    # Filter for zone centroids within the jurisdiction
    _df_iz = df_iz[df_iz['taz'].isin(intersect_gdf.taz)]

    # If no zones centroids in a city, pass an empty df with 0 values for VMT;
    # Otherwise calculate intrazonal VMT for the associated TAZs only
    if len(_df_iz) > 0:
        df_intrazonal_vmt = calculate_intrazonal_vmt(summary_settings, _df_iz)
        
    else:
        # Load the regional results and fill VMT with 0
        df_intrazonal_vmt = pd.read_csv(os.path.join(run_dir, r'outputs\emissions\intrazonal_vmt_grouped.csv'))
        df_intrazonal_vmt['VMT'] = 0
    df_intrazonal = calculate_intrazonal_emissions(df_intrazonal_vmt, df_running_rates)

    # Intersect parcels with the city gdf to get number of household to adjust vehicle starts
    parcel_intersect_gdf = gpd.overlay(parcel_gdf,  
                city_gdf, 
                how="intersection")
    start_emissions_df = calculate_start_emissions_city(conn, parcel_intersect_gdf, model_year, input_settings, summary_settings)

    df_inter_group = df_interzonal.groupby(['pollutantID','veh_type']).sum()[['tons_tot','vmt']].reset_index()
    df_inter_group.rename(columns={'tons_tot': 'interzonal_tons', 'vmt': 'interzonal_vmt'}, inplace=True)
    df_intra_group = df_intrazonal.groupby(['pollutantID','veh_type']).sum()[['tons_tot','vmt']].reset_index()
    df_intra_group.rename(columns={'tons_tot': 'intrazonal_tons', 'vmt': 'intrazonal_vmt'}, inplace=True)
    df_start_group = start_emissions_df.groupby(['pollutantID','veh_type']).sum()[['start_tons']].reset_index()

    summary_df = pd.merge(df_inter_group, df_intra_group, how='left').fillna(0)
    summary_df = pd.merge(summary_df, df_start_group, how='left')
    summary_df = finalize_emissions(summary_df, col_suffix="")
    summary_df = summary_df.fillna(0)
    summary_df.loc[~summary_df['pollutantID'].isin(['PM','PM10','PM25']),'pollutantID'] = summary_df[~summary_df['pollutantID'].isin(['PM','PM10','PM25'])]['pollutantID'].astype('int')
    summary_df['pollutant_name'] = summary_df['pollutantID'].astype('int', errors='ignore').astype('str').map(summary_settings["pollutant_map"])
    summary_df['total_daily_tons'] = summary_df['start_tons']+summary_df['interzonal_tons']+summary_df['intrazonal_tons']
    summary_df = summary_df[['pollutantID','pollutant_name','veh_type','intrazonal_vmt','interzonal_vmt','start_tons','intrazonal_tons','interzonal_tons','total_daily_tons']]

    return summary_df

# Select all cities and towns in King county
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
    city_list += ['Bainbridge Island']

else:
    city_list = alt_city_list

missing_city_list = []

for city in city_list:
    if not os.path.isfile(os.path.join(output_dir,city+'.csv')):
        print(city)
        _gdf_shp = gdf_shp[gdf_shp['juris'] == city]
        df = evaluate_emissions(_gdf_shp, df_running_rates)
        df.to_csv(os.path.join(output_dir,city+'.csv'), index=False)
        #try:
            #_gdf_shp = gdf_shp[gdf_shp['juris'] == city]
            #df = evaluate_emissions(_gdf_shp, df_running_rates)
            #df.to_csv(os.path.join(output_dir,city+'.csv'), index=False)
        #except:
        #    print('ERROR for: ' +city)
        #    missing_city_list.append(city)
        #    continue
    
# Sometimes there are database issues when loading data;
# If the initial pass did not work for all cities, try a second pass
# Usually this will catch any city that did not work on the first attempt

for city in missing_city_list:
    try:
        _gdf_shp = gdf_shp[gdf_shp['juris'] == city]
        df = evaluate_emissions(_gdf_shp, df_running_rates)
        df.to_csv(os.path.join(output_dir,city+'.csv'), index=False)
    except:
        print('ERROR for: ' +city)
        continue


# Optionally calculate King County totals
# The shapefile used for this exercise covers the entirity of King County
# any location in the inverse of the previously calculated cities will be considered unincorporated King County
if create_county_total:
    _gdf_shp = gdf_shp[(gdf_shp['cnty_name'] == 'King')]
    df = evaluate_emissions(_gdf_shp, df_running_rates)
    df.to_csv(os.path.join(output_dir,'King County Total.csv'), index=False)
    df = pd.read_csv(os.path.join(output_dir,'King County Total.csv'))
    df['vmt'] = df['interzonal_vmt'] + df['intrazonal_vmt']
    df = df.groupby(['pollutant_name','veh_type']).sum()[['total_daily_tons','vmt']].reset_index()
    df.to_csv(os.path.join(output_dir,model_year+'_county_summary.csv'), index=False)


# Summarize total emissions by each city
# Note that VMT will be listed for the same city and vehicle type combination multiple times (for each pollutant)


#df = pd.DataFrame()

##for city in city_list:
##    _df = pd.read_csv(os.path.join(output_dir,city+'.csv'))
##    _df['vmt'] = _df['interzonal_vmt'] + _df['intrazonal_vmt']
##    _df = _df.groupby(['pollutant_name','veh_type']).sum()[['total_daily_tons','vmt']].reset_index()
##    _df['city'] = city
##    df = df.append(_df)
##df.to_csv(os.path.join(output_dir,summary,model_year+'_summary.csv'))