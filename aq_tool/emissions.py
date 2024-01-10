import os, sys, shutil
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
# from emme_configuration import *
from standard_summary_configuration import *
from input_configuration import base_year
pd.options.mode.chained_assignment = None

def grams_to_tons(value, metric_tons=False):
    """ Convert grams to tons."""
    if metric_tons:
        value = value/1000000
    else:
        value = value/453.592
        value = value/2000

    return value

def calculate_interzonal_vmt(df):
    """ Calcualte inter-zonal running emission rates from network outputs (df)
    """

    # List of vehicle types to include in results; note that bus is included here but not for intrazonals
    vehicle_type_list = ['sov','hov2','hov3','bus','medium_truck','heavy_truck']

    # Apply county names
    county_id_lookup = {
	    33: 'king',
	    35: 'kitsap',
	    53: 'pierce',
	    61: 'snohomish'
    }

    df['geog_name'] = df['@countyid'].map(county_id_lookup)

    # Remove links with facility type = 0 from the calculation
    df['facility_type'] = df['data3']    # Rename for human readability
    df = df[df['facility_type'] > 0]

    # Calculate VMT by bus, SOV, HOV2, HOV3+, medium truck, heavy truck
    df['sov_vol'] = df['@sov_inc1']+df['@sov_inc2']+df['@sov_inc3']
    df['sov_vmt'] = df['sov_vol']*df['length']
    df['hov2_vol'] = df['@hov2_inc1']+df['@hov2_inc2']+df['@hov2_inc3']
    df['hov2_vmt'] = df['hov2_vol']*df['length']
    df['hov3_vol'] = df['@hov3_inc1']+df['@hov3_inc2']+df['@hov3_inc3']
    df['hov3_vmt'] = df['hov3_vol']*df['length']
    df['tnc_vmt'] = df['@tnc_inc1']+df['@tnc_inc2']+df['@tnc_inc3']
    df['bus_vmt'] = df['@bveh']*df['length']
    df['medium_truck_vmt'] = df['@mveh']*df['length']
    df['heavy_truck_vmt'] = df['@hveh']*df['length']

    # Convert TOD periods into hours used in emission rate files
    df['hourId'] = df['tod'].map(tod_lookup).astype('int')

    # Calculate congested speed to separate time-of-day link results into speed bins
    df['congested_speed'] = (df['length']/df['auto_time'])*60
    df['avgspeedbinId'] = pd.cut(df['congested_speed'], speed_bins, labels=speed_bins_labels).astype('int')

    # Relate soundcast facility types to emission rate definitions (e.g., minor arterial, freeway)
    df['roadtypeId'] = df["facility_type"].map(fac_type_lookup).astype('int')

    # Take total across columns where distinct emission rate are available
    # This calculates total VMT, by vehicle type (e.g., HOV3 VMT for hour 8, freeway, King County, 55-59 mph)
    join_cols = ['avgspeedbinId','roadtypeId','hourId','geog_name']
    df = df.groupby(join_cols).sum()
    df = df[['sov_vmt','hov2_vmt','hov3_vmt','tnc_vmt','bus_vmt','medium_truck_vmt','heavy_truck_vmt']]
    df = df.reset_index()
    # Write this file for calculation with different emission rates
    # df.to_csv(r'outputs/emissions/interzonal_vmt_grouped.csv', index=False)

    return df

def finalize_emissions(df, col_suffix=""):
	""" 
	Compute PM10 and PM2.5 totals, sort index by pollutant value, and pollutant name.
	For total columns add col_suffix (e.g., col_suffix='intrazonal_tons')
	"""

	pm10 = df[df['pollutantID'].isin([100,106,107])].groupby('veh_type').sum().reset_index()
	pm10['pollutantID'] = 'PM10'
	pm25 = df[df['pollutantID'].isin([110,116,117])].groupby('veh_type').sum().reset_index()
	pm25['pollutantID'] = 'PM25'
	df = df.append(pm10)
	df = df.append(pm25)

	## Sort final output table by pollutant ID
	#df_a = df[(df['pollutantID'] != 'PM10') & (df['pollutantID'] != 'PM25')]
	#df_a['pollutantID'] = df_a['pollutantID'].astype('int')
	#df_a = df_a.sort_values('pollutantID')
	#df_a['pollutantID'] = df_a['pollutantID'].astype('str')
	#df_b = df[-((df['pollutantID'] != 'PM10') & (df['pollutantID'] != 'PM25'))]

	#df = pd.concat([df_a,df_b])
	#df['pollutant_name'] = df['pollutantID'].map(pollutant_map)

	#common_cols = ['pollutantID','pollutant_name']   # do not add suffix to these columns
	#df.columns = [i+col_suffix for i in df.columns if i not in common_cols]+common_cols

	return df

def calculate_interzonal_emissions(df, df_rates, group_light_vehs=True):
    """ Calculate link emissions using rates unique to speed, road type, hour, county, and vehicle type. """

    df.rename(columns={'geog_name':'county', 'avgspeedbinId': 'avgSpeedBinID', 'roadtypeId': 'roadTypeID', 'hourId': 'hourID'}, inplace=True)

    # Calculate total VMT by vehicle group
    if group_light_vehs:
        df['light'] = df['sov_vmt']+df['hov2_vmt']+df['hov3_vmt']+df['tnc_vmt'] # Include for cities?
        df['medium'] = df['medium_truck_vmt']
        df['heavy'] = df['heavy_truck_vmt']
        df['transit'] = df['bus_vmt']        
    else:
        # group TNC in HOV2
        df['sov'] = df['sov_vmt']
        df['hov2'] = df['hov2_vmt'] # Note: excluding TNC for consitency with inventories
        df['hov3'] = df['hov3_vmt']
        df['medium'] = df['medium_truck_vmt']
        df['heavy'] = df['heavy_truck_vmt']
        df['transit'] = df['bus_vmt']
        
    df.drop(['sov_vmt','hov2_vmt','hov3_vmt','tnc_vmt','medium_truck_vmt','heavy_truck_vmt','bus_vmt'], inplace=True, axis=1)

    # Melt to pivot vmt by vehicle type columns as rows
    df = pd.melt(df, id_vars=['avgSpeedBinID','roadTypeID','hourID','county'], var_name='detailed_veh_type', value_name='vmt')

    # Join rates based on vehicle type but retain the light duty distinction
    veh_type_map = {'sov': 'light',
                    'hov2': 'light',
                    'hov3': 'light',
                    'medium': 'medium',
                    'heavy': 'heavy',
                    'transit': 'transit'}
    df['veh_type'] = df['detailed_veh_type'].map(veh_type_map)

    df = pd.merge(df, df_rates, on=['avgSpeedBinID','roadTypeID','hourID','county','veh_type'],
                  how='left', left_index=False)
    # Calculate total grams of emission 
    df['grams_tot'] = df['grams_per_mile']*df['vmt']
    df['tons_tot'] = grams_to_tons(df['grams_tot'], metric_tons=True)
    # df.to_csv(r'outputs\emissions\interzonal_emissions.csv', index=False)

    return df

def calculate_intrazonal_vmt(df_iz, conn):

    # df_iz = pd.read_csv(r'outputs/network/iz_vol.csv')

    # Map each zone to county
    county_df = pd.read_sql('SELECT * FROM taz_geography', con=conn)
    df_iz = pd.merge(df_iz, county_df, how='left', on='taz')

    # Sum up SOV, HOV2, and HOV3 volumes across user classes 1, 2, and 3 by time of day
    # Calcualte VMT for these trips too; rename truck volumes for clarity
    for tod in tod_lookup.keys():
        df_iz['sov_'+tod+'_vol'] = df_iz['sov_inc1_'+tod]+df_iz['sov_inc2_'+tod]+df_iz['sov_inc3_'+tod]
        df_iz['hov2_'+tod+'_vol'] = df_iz['hov2_inc1_'+tod]+df_iz['hov2_inc2_'+tod]+df_iz['hov2_inc3_'+tod]
        df_iz['hov3_'+tod+'_vol'] = df_iz['hov3_inc1_'+tod]+df_iz['hov3_inc2_'+tod]+df_iz['hov3_inc3_'+tod]
        df_iz['mediumtruck_'+tod+'_vol'] = df_iz['medium_truck_'+tod]
        df_iz['heavytruck_'+tod+'_vol'] = df_iz['heavy_truck_'+tod]

	    # Calculate VMT as intrazonal distance times volumes 
        df_iz['sov_'+tod+'_vmt'] = df_iz['sov_'+tod+'_vol']*df_iz['izdist']
        df_iz['hov2_'+tod+'_vmt'] = df_iz['hov2_'+tod+'_vol']*df_iz['izdist']
        df_iz['hov3_'+tod+'_vmt'] = df_iz['hov3_'+tod+'_vol']*df_iz['izdist']
        df_iz['mediumtruck_'+tod+'_vmt'] = df_iz['mediumtruck_'+tod+'_vol']*df_iz['izdist']
        df_iz['heavytruck_'+tod+'_vmt'] = df_iz['heavytruck_'+tod+'_vol']*df_iz['izdist']
	
    # Group totals by vehicle type, time-of-day, and county
    df = df_iz.groupby('geog_name').sum().T
    df.reset_index(inplace=True)
    df = df[df['index'].apply(lambda row: 'vmt' in row)]
    # df.columns = ['index','King','Kitsap','Pierce','Snohomish']
    df.rename(columns={'King County': 'King',
                        'Kitsap County': 'Kitsap',
                        'Pierce County': 'Pierce',
                        'Snohomish County': 'Snohomish'}, inplace=True)

    # Calculate total VMT by time of day and vehicle type
    # Ugly dataframe reformatting to unstack data
    df['tod'] = df['index'].apply(lambda row: row.split('_')[1])
    df['vehicle_type'] = df['index'].apply(lambda row: row.split('_')[0])
    df.drop('index', axis=1,inplace=True)
    df.index = df[['tod','vehicle_type']]
    df.drop(['tod','vehicle_type'],axis=1,inplace=True)
    df = pd.DataFrame(df.unstack()).reset_index()
    df['tod'] = df['level_1'].apply(lambda row: row[0])
    df['vehicle_type'] = df['level_1'].apply(lambda row: row[1])
    df.drop('level_1', axis=1, inplace=True)
    df.columns = ['geog_name','VMT','tod','vehicle_type']

    # Use hourly periods from emission rate files
    df['hourId'] = df['tod'].map(tod_lookup).astype('int')

    return df

def calculate_intrazonal_vmt(df_iz, conn):

    # Map each zone to county
    county_df = pd.read_sql('SELECT * FROM taz_geography', con=conn)
    df_iz = pd.merge(df_iz, county_df, how='left', on='taz')

    # Sum up SOV, HOV2, and HOV3 volumes across user classes 1, 2, and 3 by time of day
    # Calculate VMT for these trips too; rename truck volumes for clarity
    for tod in tod_lookup.keys():
        df_iz['sov_'+tod+'_vol'] = df_iz['sov_inc1_'+tod]+df_iz['sov_inc2_'+tod]+df_iz['sov_inc3_'+tod]
        df_iz['hov2_'+tod+'_vol'] = df_iz['hov2_inc1_'+tod]+df_iz['hov2_inc2_'+tod]+df_iz['hov2_inc3_'+tod]
        df_iz['hov3_'+tod+'_vol'] = df_iz['hov3_inc1_'+tod]+df_iz['hov3_inc2_'+tod]+df_iz['hov3_inc3_'+tod]
        df_iz['mediumtruck_'+tod+'_vol'] = df_iz['medium_truck_'+tod]
        df_iz['heavytruck_'+tod+'_vol'] = df_iz['heavy_truck_'+tod]

	    # Calculate VMT as intrazonal distance times volumes 
        df_iz['sov_'+tod+'_vmt'] = df_iz['sov_'+tod+'_vol']*df_iz['izdist']
        df_iz['hov2_'+tod+'_vmt'] = df_iz['hov2_'+tod+'_vol']*df_iz['izdist']
        df_iz['hov3_'+tod+'_vmt'] = df_iz['hov3_'+tod+'_vol']*df_iz['izdist']
        df_iz['mediumtruck_'+tod+'_vmt'] = df_iz['mediumtruck_'+tod+'_vol']*df_iz['izdist']
        df_iz['heavytruck_'+tod+'_vmt'] = df_iz['heavytruck_'+tod+'_vol']*df_iz['izdist']
	
    # Group totals by vehicle type, time-of-day, and county
    df = df_iz.groupby('geog_name').sum().T
    df.reset_index(inplace=True)
    df = df[df['index'].apply(lambda row: 'vmt' in row)]
    # df.columns = ['index','King','Kitsap','Pierce','Snohomish']
    df.rename(columns={'King County': 'King',
                        'Kitsap County': 'Kitsap',
                        'Pierce County': 'Pierce',
                        'Snohomish County': 'Snohomish'}, inplace=True)

    # Calculate total VMT by time of day and vehicle type
    # Ugly dataframe reformatting to unstack data
    df['tod'] = df['index'].apply(lambda row: row.split('_')[1])
    df['vehicle_type'] = df['index'].apply(lambda row: row.split('_')[0])
    df.drop('index', axis=1,inplace=True)
    df.index = df[['tod','vehicle_type']]
    df.drop(['tod','vehicle_type'],axis=1,inplace=True)
    df = pd.DataFrame(df.unstack()).reset_index()
    df['tod'] = df['level_1'].apply(lambda row: row[0])
    df['vehicle_type'] = df['level_1'].apply(lambda row: row[1])
    df.drop('level_1', axis=1, inplace=True)
    df.columns = ['geog_name','VMT','tod','vehicle_type']

    # Use hourly periods from emission rate files
    df['hourId'] = df['tod'].map(tod_lookup).astype('int')

    # Export this file for use with other rate calculations
    # Includes total VMT for each group for which rates are available
    # df.to_csv(r'outputs/emissions/intrazonal_vmt_grouped.csv', index=False)

    return df

def calculate_start_emissions(conn, intersect_gdf, model_year, df_veh, parcel_geog, df_hh, start_rates_df, df_bus_veh):
    """ Calculate start emissions based on vehicle population by county and year. """
    
    # We were also scaling all types of vehicles based on household vehicle ownership (light)
    # FIXME: find a way to scale trucks based on truck trips

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

    df = pd.merge(df_veh, start_rates_df, left_on=['type','county'],right_on=['veh_type','county'])
    df['start_grams'] = df['vehicles']*df['ratePerVehicle'] 
    df['start_tons'] = grams_to_tons(df['start_grams'], metric_tons=True)
    df = df.groupby(['pollutantID','veh_type','county']).sum().reset_index()

    # Calculate bus start emissions
    # Load data taken from NTD that reports number of bus vehicles "operated in maximum service"
    tot_buses = df_bus_veh['bus_vehicles_in_service'].sum()

    df_bus = start_rates_df[start_rates_df['veh_type'] == 'transit']
  
    # Scale start emissions by total households in study area
    # Very hard to determine starting impact of buses
    bus_scale = len(_df_hh)/len(df_hh)
    df_bus['start_grams'] = df_bus['ratePerVehicle']*tot_buses*bus_scale
    df_bus['start_tons'] = grams_to_tons(df_bus['start_grams'], metric_tons=True)
    df_bus = df_bus.groupby(['pollutantID','county']).sum().reset_index()
    df_bus['veh_type'] = 'transit'

    df = df.append(df_bus)
    return df

def calculate_intrazonal_emissions(df_intra, df_running_rates):
    """ Summarize intrazonal emissions by vehicle type. """

    # df_intra = pd.read_csv(r'outputs/emissions/intrazonal_vmt_grouped.csv')
    df_intra.rename(columns={'vehicle_type':'veh_type', 'VMT': 'vmt', 'hourId': 'hourID', 'geog_name': 'county'},inplace=True)
    # df_intra.drop('tod', axis=1, inplace=True)
    df_intra['county'] = df_intra['county'].apply(lambda row: row.lower())
    df_intra.rename(columns={'veh_type': 'detailed_veh_type'}, inplace=True)

    df_intra_light = df_intra[df_intra['detailed_veh_type'].isin(['sov','hov2','hov3'])]
    df_intra_light.loc[:,'veh_type'] = 'light'

    df_intra_medium = df_intra[df_intra['detailed_veh_type'] == 'mediumtruck']
    df_intra_medium.loc[:,'veh_type'] = 'medium'
    df_intra_medium.loc[:,'detailed_veh_type'] = 'medium'   
    df_intra_heavy = df_intra[df_intra['detailed_veh_type'] == 'heavytruck']
    df_intra_heavy.loc[:,'veh_type'] = 'heavy'
    df_intra_heavy.loc[:,'detailed_veh_type'] = 'heavy'

    df_intra = df_intra_light.append(df_intra_medium)
    df_intra = df_intra.append(df_intra_heavy)

    # For intrazonals, assume standard speed bin and roadway type for all intrazonal trips
    speedbin = 4
    roadtype = 5

    iz_rates = df_running_rates[(df_running_rates['avgSpeedBinID'] == speedbin) &
                        (df_running_rates['roadTypeID'] == roadtype)]

    df_intra = pd.merge(df_intra, iz_rates, on=['hourID','county','veh_type'], how='left', left_index=False)

    # Calculate total grams of emission 
    df_intra['grams_tot'] = df_intra['grams_per_mile']*df_intra['vmt']
    df_intra['tons_tot'] = grams_to_tons(df_intra['grams_tot'], metric_tons=True)

    df_intra['veh_type']

    return df_intra