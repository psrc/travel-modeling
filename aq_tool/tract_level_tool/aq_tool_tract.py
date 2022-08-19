import os
import pandas as pd
import geopandas as gpd
import os.path
os.chdir(r'C:\Workspace\aq_tool')
from functions import read_from_sde, load_network_summary, intersect_geog
from emissions import *

# Set root of model run to analyze AND the model year
run_dir = r'L:\RTP_2022\final_runs\sc_rtp_2018_final\soundcast'
model_year = '2018'    # Make sure to update this since rates used are based on this value
# run_dir = r'\\modelstation1\c$\workspace\sc_rtp_2030_final\soundcast'
# model_year = '2030'    # Make sure to update this since rates used are based on this value
# run_dir = r'\\modelstation1\c$\workspace\sc_2040_rtp_final\soundcast'
# model_year = '2040'
# run_dir = r'\\modelstation1\c$\workspace\sc_rtp_2050_constrained_final\soundcast'
# model_year = '2050'

# Set output directory; results will be stored in a folder by model year 
output_dir = r'C:\Workspace\aq_tool\output_TRACT\\' + model_year

# Create outputs directory if needed
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Change working directory to run_dir
os.chdir(run_dir)

# Load the network
crs = 'EPSG:2285'
gdf_network = gpd.read_file(os.path.join(run_dir,r'inputs\scenario\networks\shapefiles\AM\AM_edges.shp'))
gdf_network.crs = crs

# Load  tract geographies from ElmerGeo
connection_string = 'mssql+pyodbc://AWS-PROD-SQL\Sockeye/ElmerGeo?driver=SQL Server?Trusted_Connection=yes'

version = "'DBO.Default'"
gdf_shp = read_from_sde(connection_string, 'tract2010_nowater', version, crs=crs, is_table=False)

# Load parcels as a geodataframe
parcel_df = pd.read_csv(os.path.join(run_dir,r'inputs/scenario/landuse/parcels_urbansim.txt'), delim_whitespace=True,
                            usecols=['PARCELID','XCOORD_P','YCOORD_P'])

parcel_gdf = gpd.GeoDataFrame(parcel_df,
        geometry=gpd.points_from_xy(parcel_df['XCOORD_P'], parcel_df['YCOORD_P']), crs=crs)

# Perform intersect to get the network within each city in a list
df_network = load_network_summary(os.path.join(run_dir, r'outputs\network\network_results.csv'))

def calculate_start_emissions_tract(df_veh, parcel_geog, df_hh, conn, intersect_gdf, model_year):
    """ Calculate start emissions based on vehicle population by county and year. """

    tot_veh = df_hh['hhvehs'].sum()
    # Scale total county vehicles owned to match model
    tot_veh_model_base_year = 3007056
    veh_scale = 1.0+(tot_veh - tot_veh_model_base_year)/tot_veh_model_base_year
    df_veh['vehicles'] = df_veh['vehicles']*veh_scale

    # Select total vehicles by county within the intersected geographies
    # This will indetify the shares of vehicles per county from the spatial joined data
    df_hh = df_hh.merge(parcel_geog, left_on='hhparcel', right_on='ParcelID')    # join hh data to parcels
    _df_hh = df_hh[df_hh['hhparcel'].isin(intersect_gdf['PARCELID'])]    # Intersect with filtered geographic data
    _hh_vehs = _df_hh.groupby('CountyName').sum()[['hhvehs']]    # Get total vehicles by county within filtered geog
    
    # Calculate percent of vehicles in each county for filtered geog versus full results by county
    county_tot_vehs = df_hh.groupby('CountyName').sum()[['hhvehs']].reset_index()
    subset_vehs = _df_hh.groupby('CountyName').sum()[['hhvehs']].reset_index()
    county_subset_shares = county_tot_vehs.merge(subset_vehs, on='CountyName', how='left', suffixes=['_tot', '_subset']).fillna(0)
    county_subset_shares['hhvehs_share'] = county_subset_shares['hhvehs_subset']/county_subset_shares['hhvehs_tot']
    county_subset_shares['CountyName'] = county_subset_shares['CountyName'].str.lower()

    # Apply shares to the total vehicles df; results are scaled # of vehicles from filtered geog within each county
    df_veh = df_veh.merge(county_subset_shares[['CountyName','hhvehs_share']], left_on='county', right_on='CountyName', how='left')
    df_veh['vehicles'] = df_veh['vehicles'] *df_veh['hhvehs_share']

    # Join with rates to calculate total emissions
    print(model_year)
    start_rates_df = pd.read_sql('SELECT * FROM start_emission_rates_by_veh_type WHERE year=='+model_year, con=conn)

    # Select winter rates for pollutants other than those listed in summer_list
    df_summer = start_rates_df[start_rates_df['pollutantID'].isin(summer_list)]
    df_summer = df_summer[df_summer['monthID'] == 7]
    df_winter = start_rates_df[~start_rates_df['pollutantID'].isin(summer_list)]
    df_winter = df_winter[df_winter['monthID'] == 1]
    start_rates_df = df_winter.append(df_summer)

    # Sum total emissions across all times of day, by county, for each pollutant
    start_rates_df = start_rates_df.groupby(['pollutantID','county','veh_type']).sum()[['ratePerVehicle']].reset_index()

    df = pd.merge(df_veh, start_rates_df, left_on=['type','county'],right_on=['veh_type','county'])
    df['start_grams'] = df['vehicles']*df['ratePerVehicle'] 
    df['start_tons'] = grams_to_tons(df['start_grams'])
    df = df.groupby(['pollutantID','veh_type','county']).sum().reset_index()

    return df

### One time load and process!!
###
conn = create_engine('sqlite:///inputs/db/soundcast_inputs.db')
# Load running emission rates by vehicle type, for the model year
os.chdir(run_dir)
df_running_rates = pd.read_sql('SELECT * FROM running_emission_rates_by_veh_type WHERE year=='+model_year, con=conn)
df_running_rates.rename(columns={'ratePerDistance': 'grams_per_mile'}, inplace=True)
df_running_rates['year'] = df_running_rates['year'].astype('str')
# Select the month to use for each pollutant; some rates are used for winter or summer depending
# on when the impacts are at a maximum due to temperature.
df_summer = df_running_rates[df_running_rates['pollutantID'].isin(summer_list)]
df_summer = df_summer[df_summer['monthID'] == 7]
df_winter = df_running_rates[~df_running_rates['pollutantID'].isin(summer_list)]
df_winter = df_winter[df_winter['monthID'] == 1]
df_running_rates = df_winter.append(df_summer)

# Get list of zones to include for intrazonal trips
# Include intrazonal trips for any TAZ centroids within city boundary

# Load TAZ centroids
connection_string = 'mssql+pyodbc://AWS-PROD-SQL\Sockeye/ElmerGeo?driver=SQL Server?Trusted_Connection=yes'
version = "'DBO.Default'"
taz_gdf = read_from_sde(connection_string, 'taz2010_no_water', version, crs=crs, is_table=False)

_taz_gdf = gpd.GeoDataFrame(taz_gdf.centroid)
_taz_gdf.geometry = _taz_gdf[0]
_taz_gdf['taz'] = taz_gdf['taz'].astype('int')

# Load intrazonal trips for zones in the area
df_iz = pd.read_csv(os.path.join(run_dir,r'outputs\network\iz_vol.csv'))


# Intersect parcels with the city gdf to get number of household to adjust vehicle starts
parcel_intersect_gdf = gpd.overlay(parcel_gdf,  
            gdf_shp, 
            how="intersection")

# Load observed base year vehicle populations by county
df_veh = pd.read_sql('SELECT * FROM vehicle_population WHERE year=='+base_year, con=conn)
# Load parcel to county geographic lookup
parcel_geog = pd.read_sql("SELECT ParcelID, CountyName FROM parcel_"+str(base_year)+"_geography", con=conn) 

# Scale all vehicles by difference between base year and modeled total vehicles owned from auto onwership model
df_hh = pd.read_csv(r'outputs/daysim/_household.tsv', delim_whitespace=True, usecols=['hhvehs','hhparcel'])

def evaluate_emissions(_gdf_shp, model_year, tract):
    # Intersect jurisdiction polygon with network shapefile and network CSV file
    _gdf_shp = intersect_geog(_gdf_shp, gdf_network, df_network)

    # Select links from network summary dataframe that are within the gdf_shp
    # The dataframe contains link-level model outputs
    _df = df_network[df_network['ij'].isin(_gdf_shp['id'])]

    # Replace length with length from _gdf_shp to ensure roads stop at city boundaries
    # Drop "length field from _gdf_shp, which is length in miles; 
    # use new_length field, which is calculated length of intersected links in feet
    _df.drop('length', axis=1, inplace=True)
    _df = _df.merge(_gdf_shp, how='left', left_on='ij', right_on='id')
    # _df.drop('length', axis=1, inplace=True)
    _df.rename(columns={'new_length': 'length',
                    'length': 'original_length'}, inplace=True)

    # Calculate interzonal emissions using same approach as for regional/county emissions
    df_interzonal_vmt = calculate_interzonal_vmt(_df)
    df_interzonal = calculate_interzonal_emissions(df_interzonal_vmt, df_running_rates)

    intersect_gdf = gpd.overlay(_taz_gdf, 
            _gdf_shp, 
            how="intersection")

    # Filter for zone centroids within the jurisdiction
    _df_iz = df_iz[df_iz['taz'].isin(intersect_gdf.taz)]

    # If no zones centroids in a city, pass an empty df with 0 values for VMT;
    # Otherwise calculate intrazonal VMT for the associated TAZs only
    if len(_df_iz) > 0:
        df_intrazonal_vmt = calculate_intrazonal_vmt(_df_iz, conn)

    else:
        # Load the regional results and fill VMT with 0
        df_intrazonal_vmt = pd.read_csv(os.path.join(run_dir, r'outputs\emissions\intrazonal_vmt_grouped.csv'))
        df_intrazonal_vmt['VMT'] = 0

    df_intrazonal = calculate_intrazonal_emissions(df_intrazonal_vmt, df_running_rates)
    _parcel_intersect_gdf = parcel_intersect_gdf[parcel_intersect_gdf['tractce10'] == tract]

    start_emissions_df = calculate_start_emissions_tract(df_veh, parcel_geog, df_hh, conn, _parcel_intersect_gdf, model_year)

    df_inter_group = df_interzonal.groupby(['pollutantID','veh_type']).sum()[['tons_tot','vmt']].reset_index()
    df_inter_group.rename(columns={'tons_tot': 'interzonal_tons', 'vmt': 'interzonal_vmt'}, inplace=True)
    df_intra_group = df_intrazonal.groupby(['pollutantID','veh_type']).sum()[['tons_tot','vmt']].reset_index()
    df_intra_group.rename(columns={'tons_tot': 'intrazonal_tons', 'vmt': 'intrazonal_vmt'}, inplace=True)
    df_start_group = start_emissions_df.groupby(['pollutantID','veh_type']).sum()[['start_tons']].reset_index()

    summary_df = pd.merge(df_inter_group, df_intra_group)
    summary_df = pd.merge(summary_df, df_start_group, how='left')
    summary_df = finalize_emissions(summary_df, col_suffix="")
    summary_df.loc[~summary_df['pollutantID'].isin(['PM','PM10','PM25']),'pollutantID'] = summary_df[~summary_df['pollutantID'].isin(['PM','PM10','PM25'])]['pollutantID'].astype('int')
    summary_df['pollutant_name'] = summary_df['pollutantID'].astype('int', errors='ignore').astype('str').map(pollutant_map)
    summary_df['total_daily_tons'] = summary_df['start_tons']+summary_df['interzonal_tons']+summary_df['intrazonal_tons']
    summary_df = summary_df[['pollutantID','pollutant_name','veh_type','intrazonal_vmt','interzonal_vmt','start_tons','intrazonal_tons','interzonal_tons','total_daily_tons']]

    return summary_df

# intersect tract with city layer to get list of tracts in seattle
# Use the nowater version to get more accurate centroid locations
gdf_tract = read_from_sde(connection_string, 'tract2010_nowater', version, crs=crs, is_table=False)
# Select only tracts with centroids fully inside city limits
_gdf_tract = gdf_tract.copy()
_gdf_tract['geometry'] = _gdf_tract['geometry'].centroid

gdf_cities = read_from_sde(connection_string, 'cities', version, crs=crs, is_table=False)
gdf_seattle = gdf_cities[gdf_cities['city_name'] == 'Seattle']
gdf_intersect = gpd.overlay(_gdf_tract, gdf_seattle, how='intersection')

# Process multiple census tracts
# Select all tracts in Seattle

tract_list = gdf_intersect[gdf_intersect['city_name'] == 'Seattle']['tractce10'].unique()
missing_city_list = []

for tract in tract_list:
    if not os.path.isfile(os.path.join(output_dir,tract+'.csv')):
        print(tract)
        try:
            _gdf_shp = gdf_shp[gdf_shp['tractce10'] == tract]
            df = evaluate_emissions(_gdf_shp, model_year, tract)
            df.to_csv(os.path.join(output_dir,tract+'.csv'), index=False)
        except:
            print('ERROR for: ' +tract)
            missing_city_list.append(tract)
            continue
    
