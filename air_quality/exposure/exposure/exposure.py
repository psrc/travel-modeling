# Revisit exposure script
import os
import numpy as np
import pandas as pd
import pyodbc
import sqlalchemy
from shapely import wkt
import geopandas as gpd
import time

run_create_activity = False
run_join_shapefile = False
run_calculate_emissions = True
load_existing = False

# For each person, find out their time spent at different locations (activity pattern)

# Get this from inverse of trip records
start_time = time.time()

hour_map = {
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    11: 10,
    12: 10,
    13: 10,
    14: 14,
    15: 15,
    16: 16,
    17: 17,
    18: 18,
    19: 18,
    20: 20,
    21: 20,
    22: 20,
    23: 20,
    24: 20,
    0: 0,
    1: 5,
    2: 5,
    3: 5,
    4: 5}

facility_type_lookup = {
        1:'Freeway',   # Interstate
        2:'Freeway',   # Ohter Freeway
        3:'Freeway', # Expressway
        4:'Ramp',
        5:'Arterial',    # Principal arterial
        6:'Arterial',    # Minor Arterial
        7:'Collector',    # Major Collector
        8:'Collector',    # Minor Collector
        9:'Collector',   # Local
        10:'Busway',
        11:'Non-Motor',
        12:'Light Rail',
        13:'Commuter Rail',
        15:'Ferry',
        16:'Passenger Only Ferry',
        17:'Connector',    # centroid connector
        18:'Connector',    # facility connector
        19:'HOV',    # HOV Only Freeway
        20:'HOV'    # HOV Flag
        }

def create_activity():
    run_dir = r'L:\RTP_2022\final_runs\sc_rtp_2018_final\soundcast'

    df = pd.read_csv(os.path.join(run_dir,'outputs/daysim/_trip.tsv'), delim_whitespace=True,
                     usecols=['hhno','pno','opcl','dpcl','arrtm','deptm','trexpfac'])


    ################################
    # Start script
    ################################

    # Generate unique person ID field 
    df['person_id'] = df['hhno'].astype('str') + '_' + df['pno'].astype('str')

    # Attach the total number of trips per person, from the person records
    tot_trips = df[['person_id','trexpfac']].groupby('person_id').sum().reset_index()
    tot_trips.columns = ['person_id','total_trips']

    df = pd.merge(df,tot_trips,on='person_id',how='left')

    # first trip departure is the end of the first activity; first origin parcel is location of first activity
    first_trip = df.groupby(['person_id']).first()[['opcl','deptm']].reset_index()
    first_trip.columns = ['person_id','parcel','end_time']

    # Save this as the first activity for each person
    activity = first_trip.copy()
    activity['begin_time'] = 0
    activity['activity_index'] = 0

    # Group trips by person_id and iterate through each row of grouped results to get activities
    max_trips_per_person = df['total_trips'].max()    # There are some people with 32 trips per day, may want to limit this...

    for i in range(2,max_trips_per_person+1):    # Start with the second trip since we alreayd calculated the first
        print(i)
        current_trip = df.groupby(['person_id']).nth(n=i-1)[['opcl','dpcl','arrtm','deptm','total_trips']].reset_index()
        activity_row = current_trip[['person_id','opcl','deptm']]    
        activity_row.columns = ['person_id','parcel','end_time']    # activity ends when trip from current locations starts
    
        # Use previous trip record to define activity begingging
        previous_trip = df.groupby(['person_id']).nth(n=i-2)[['arrtm']].reset_index()    # nth function is 0-based
        previous_trip.columns = ['person_id','begin_time']    # activity starts when previous trip arrives at past location
    
        # Merge info from current and previous trips to produce a complete activity record
        merged = pd.merge(activity_row, previous_trip, on='person_id', how='left')
        merged['activity_index']=i-1    # use 0-based index
    
        # add this activity to the dataframe
        activity = activity.append(merged)
    
        # For records where the current trip is the final trip, add the last activity
        last_activity_row = current_trip[current_trip['total_trips'] == i]    # use num of total trips to identifiy last trip rows
        if len(last_activity_row) > 0:
            last_activity_row = last_activity_row[['person_id','dpcl','arrtm']]    
            last_activity_row.columns = ['person_id','parcel','begin_time'] # use the arrival time and dpcl to get final activity location and start time
            last_activity_row['end_time'] = 24*60    # End of last activity is 24 hours
            last_activity_row['activity_index'] = i    # Add the 0-bsaed index

            # add this last activity to the dataframe
            activity = activity.append(last_activity_row)

    # further separate each activity to 12 time periods to get hourly air quality estimates
    # use floor to define the hour bin
    activity['begin_hour'] = np.floor(activity['begin_time']/60.0).astype('int')
    activity['end_hour'] = np.floor(activity['end_time']/60.0).astype('int')

    # Keep track of what percent of activity occurred during this hour
    activity['begin_hour_fraction'] = (activity['begin_time']-(activity['begin_hour']*60))/60
    activity['end_hour_fraction'] = (activity['end_time']-((activity['end_hour'])*60))/60

    activity['begin_hour'] = activity['begin_hour'].map(hour_map)
    activity['end_hour'] = activity['end_hour'].map(hour_map)

    print("--- %s seconds ---" % (time.time() - start_time))

    print('test')

    # Write to CSV
    activity.to_csv(r'activity.csv', index=False)

    return activity


##########################################################
# Create a network buffer intersection with parcels
# We want to identify volume (and emissions) for each parcel
# resulting from nearby emissions
# For now, assume that a parcel is exposed if it's within a 500 ft buffer of a roadway

def read_from_sde(connection_string, feature_class_name, version,
                  crs={'init': 'epsg:2285'}, is_table = False):
    """
    Returns the specified feature class as a geodataframe from ElmerGeo.
    
    Parameters
    ----------
    connection_string : SQL connection string that is read by geopandas 
                        read_sql function
    
    feature_class_name: the name of the featureclass in PSRC's ElmerGeo 
                        Geodatabase
    
    cs: cordinate system
    """


    engine = sqlalchemy.create_engine(connection_string)
    con=engine.connect()
    #con.execute("sde.set_current_version {0}".format(version))
    if is_table:
        gdf=pd.read_sql('select * from %s' % 
                   (feature_class_name), con=con)
        con.close()

    else:
        df=pd.read_sql('select *, Shape.STAsText() as geometry from %s' % 
                   (feature_class_name), con=con)
        con.close()

        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf=gpd.GeoDataFrame(df, geometry='geometry')
        gdf.crs = crs
        cols = [col for col in gdf.columns if col not in 
                ['Shape', 'GDB_GEOMATTR_DATA', 'SDE_STATE_ID']]
        gdf = gdf[cols]
    
    return gdf

def join_shapefile(activity):

    connection_string = 'mssql+pyodbc://AWS-PROD-SQL\Sockeye/ElmerGeo?driver=SQL Server?Trusted_Connection=yes'
    crs = {'init' : 'EPSG:2285'}
    version = "'DBO.Default'"
    gdf_shp = read_from_sde(connection_string, 'blockgrp2020', version, crs=crs, is_table=False)

    run_dir_18 = r'L:\RTP_2022\final_runs\sc_rtp_2018_final\soundcast'
    parcel_18 = pd.read_csv(os.path.join(run_dir_18,'inputs\scenario\landuse\parcels_urbansim.txt'), delim_whitespace=True)

    # Load parcel centroids as geodataframe
    parcel_18_gdf = gpd.GeoDataFrame(
        parcel_18, geometry=gpd.points_from_xy(parcel_18.XCOORD_P, parcel_18.YCOORD_P))
    crs = {'init' : 'EPSG:2285'}
    parcel_18_gdf.crs = crs

    # Select only parcels that contain activities
    parcel_18_gdf = parcel_18_gdf[parcel_18_gdf['PARCELID'].isin(activity['parcel'])]

    # Buffer parcels
    buffer_dist = 500
    parcel_18_gdf.geometry = parcel_18_gdf.buffer(buffer_dist)

    # Load network
    gdf_network = gpd.read_file(os.path.join(run_dir_18,r'inputs/scenario/networks/shapefiles/AM/AM_edges.shp'))

    

    # Remove connectors and other network elements
    gdf_network = gdf_network[gdf_network['FacilityTy'].isin([1,2,3,4,5,6,7,8,9,19,20])]
    gdf_network = gdf_network[['i','j','geometry']]

    # Intersect network with the buffered parcels
    # Any network within the buffer will be considered for emissions exposure
    # Recalcualte the length of the intersected network piece inside the buffer


    ############## FIXME:
    # this doesn't seem to be working like it should be
    # maybe we should be doing an intersect instead of a spatial join
    #gdf_joined = gpd.sjoin(gdf_network, parcel_18_gdf, how='inner')
    #df1.overlay(df2, how='intersection')
    gdf_joined = gpd.overlay(gdf_network, parcel_18_gdf, how='intersection')

    # Calculate new length of intersected links
    gdf_joined['new_length'] = gdf_joined.geometry.length/5280.0

    # Select only required columns
    gdf_joined = gdf_joined[['i','j','PARCELID','new_length','geometry']]

    # temp
    gdf_joined.to_file(r'gdf_joined.shp')

    return gdf_joined



######################################################
# Get total emissions for each of the intersecting links
######################################################

def calculate_emissions(activity, gdf_joined):

    # List of vehicle types to include in results; note that bus is included here but not for intrazonals
    vehicle_type_list = ['sov','hov2','hov3','bus','medium_truck','heavy_truck']

    # Load link-level volumes and join to intersected network links
    model_path =  r'L:\RTP_2022\final_runs\sc_rtp_2018_final\soundcast'
    df = pd.read_csv(os.path.join(model_path,r'outputs/network/network_results.csv'))


    # Pivot data so volumes are 

    ## Join volumnes to gdf_shp
    #gdf_joined.merge()

    # Apply county names
    county_id_lookup = {
	    33: 'king',
	    35: 'kitsap',
	    53: 'pierce',
	    61: 'snohomish'
    }

    tod_lookup = {'5to6' : 5, '6to7' : 6, '7to8' : 7, '8to9' : 8, '9to10' : 9, 
                  '10to14' : 10, '14to15' : 14, '15to16' : 15, '16to17' : 16, 
                  '17to18' : 17, '18to20' : 18, '20to5' : 20}

    fac_type_lookup = {0:0, 1:4, 2:4, 3:5, 4:5, 5:5, 6:3, 7:5, 8:0}

    speed_bins = [-999999, 2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5, 37.5, 42.5, 47.5, 52.5, 57.5, 62.5, 67.5, 72.5, 999999] 
    speed_bins_labels =  range(1, len(speed_bins))

    df['county'] = df['@countyid'].map(county_id_lookup)

    # Remove links with facility type = 0 from the calculation
    df['facility_type'] = df['data3']    # Rename for human readability
    df = df[df['facility_type'] > 0]

    # Calculate VMT by bus, SOV, HOV2, HOV3+, medium truck, heavy truck
    df['sov_vol'] = df['@sov_inc1']+df['@sov_inc2']+df['@sov_inc3']
    df['hov2_vol'] = df['@hov2_inc1']+df['@hov2_inc2']+df['@hov2_inc3']
    df['hov3_vol'] = df['@hov3_inc1']+df['@hov3_inc2']+df['@hov3_inc3']
    df['light_vol'] = df['sov_vol']+df['hov2_vol']+df['hov3_vol']

    # Convert TOD periods into hours used in emission rate files
    df['hourID'] = df['tod'].map(tod_lookup).astype('int')

    # Calculate congested speed to separate time-of-day link results into speed bins
    df['congested_speed'] = (df['length']/df['auto_time'])*60
    df['avgSpeedBinID'] = pd.cut(df['congested_speed'], speed_bins, labels=speed_bins_labels).astype('int')

    # Relate soundcast facility types to emission rate definitions (e.g., minor arterial, freeway)
    df['roadTypeID'] = df["facility_type"].map(fac_type_lookup).astype('int')

    # Rename truck volumes for consistency
    df.rename(columns={'@mveh': 'medium_truck_vol', '@hveh': 'heavy_truck_vol'}, inplace=True)

    col_list = ['light_vol','medium_truck_vol','heavy_truck_vol','avgSpeedBinID','roadTypeID','hourID','county','i_node','j_node']
    df = df[col_list]

    # Load rates files and join to the 
    from sqlalchemy import create_engine
    ############## FIXME: make model year and model run locaton configurable
    model_year = '2018'
    conn = create_engine('sqlite:///L:/RTP_2022/final_runs/sc_rtp_2018_final/soundcast/inputs/db/soundcast_inputs.db')
    ########################

    # Load running emission rates by vehicle type, for the model year
    df_rates = pd.read_sql('SELECT * FROM running_emission_rates_by_veh_type WHERE year=='+model_year, con=conn)
    df_rates.rename(columns={'ratePerDistance': 'grams_per_mile'}, inplace=True)
    df_rates['year'] = df_rates['year'].astype('str')
    df_rates = df_rates[df_rates['pollutantID'].isin([90,87])]
    # Simplify by taking winter rates
    df_rates = df_rates[df_rates['monthID'] == 1]
    df_rates.drop(['monthID','year','field1'], axis=1, inplace=True)

    df_rates = df_rates.pivot_table(index=['roadTypeID','avgSpeedBinID','hourID','county'], columns=['pollutantID','veh_type'],
                         values='grams_per_mile', aggfunc='sum').reset_index()

    df = df.merge(df_rates, how='left', on=['roadTypeID','avgSpeedBinID','hourID','county'])

    # join this to the parcel info

    df = gdf_joined.merge(df, left_on=['i','j'], right_on=['i_node','j_node'], how='left')

    # Calculate emissions totals
    df['light_grams_90'] = df['new_length']*df['light_vol']*df[90,'light']
    df['medium_grams_90'] = df['new_length']*df['medium_truck_vol']*df[90,'medium']
    df['heavy_grams_90'] = df['new_length']*df['heavy_truck_vol']*df[90,'heavy']

    ############## FIXME
    # Fill nan with 0, see why that's the case later
    df = df.fillna(0)

    # Group results by parcel and time of day
    parcel_tot_df = df.groupby(['PARCELID','hourID']).sum().reset_index()

    # Join this to activity records
    # Record activity to match  ours used for 

    #activity.merge(parcel_tot_df, left_on=['PARCELID'])



    parcel_tot_df['hourID'] = parcel_tot_df['hourID'].astype('int')

    # Create sum across vehicle types (?)
    parcel_tot_df['tot_90_grams'] = parcel_tot_df[['light_grams_90','medium_grams_90','heavy_grams_90']].sum(axis=1)

    parcel_tot_df = average_emissions_to_hours(parcel_tot_df, hour_list=[10,11,12,13])
    parcel_tot_df = average_emissions_to_hours(parcel_tot_df, hour_list=[18,19])
    parcel_tot_df = average_emissions_to_hours(parcel_tot_df, hour_list=[20,21,22,23,0,1,2,3,4])

    parcel_tot_df.to_csv('parcel_tot_df.csv')

    return parcel_tot_df


def average_emissions_to_hours(df, hour_list):
    
    # First hour contains information summed for all time periods
    copy_df = df[df['hourID'] == hour_list[0]].copy()
    
    for hour in hour_list:
        _df = copy_df.copy()
#         print hour
        if hour == hour_list[0]:
            df = df[df['hourID'] != hour_list[0]]
        _df['hourID'] = hour
        _df[['tot_90_grams']] = _df[['tot_90_grams']]/(len(hour_list)*1.0)  
        df = df.append(_df)
        
    df = df.reset_index()
    df = df.drop('index', axis=1)
    return df

# For each activity, calculate the total emissions exposures, using hourly totals at each parcel
def total_activity_emissions(df, zone_num, emissions_type, begin_hour, begin_hour_share, end_hour, end_hour_share,
                            geography_field='PARCELID'):
    """Calculate the total grams per each activity"""
    
    #df = hourly_emissions_total
    
        # Totals from first hour
    first_hour_total = df[(df[geography_field] == zone_num) & (df.hourID == begin_hour)][emissions_type].values[0]
    first_hour_total = first_hour_total*begin_hour_share    # Modify with % of hour at that location
    
    # Totals from last hour
    last_hour_total = df[(df[geography_field] == zone_num) & (df.hourID == end_hour)][emissions_type].values[0]
    last_hour_total = last_hour_total*end_hour_share    # Modify with % of hour at that location
    
    # Calculate totals for interim hours if necessary
    interim_total = 0
    if end_hour-begin_hour>1:
        for hour in range(begin_hour+1,end_hour):
            interim_total +=  df[(df[geography_field] == zone_num) & (df.hourID == hour)][emissions_type].values[0]
            
    activity_total = first_hour_total + interim_total + last_hour_total
    
    return activity_total

if run_create_activity:
    activity = create_activity()
else:
    activity = pd.read_csv('activity.csv')

if run_join_shapefile:
    gdf_joined = join_shapefile(activity)
else:
    gdf_joined = gpd.read_file('gdf_joined.shp')

if run_calculate_emissions:
    parcel_tot_df = calculate_emissions(activity, gdf_joined)

if load_existing:
    parcel_tot_df = pd.read_csv(r'C:\workspace\travel-modeling\air_quality\exposure\exposure\parcel_tot_df.csv')
    activity = pd.read_csv(r'C:\workspace\travel-modeling\air_quality\exposure\exposure\activity.csv')

# The issue now is that we are joining multiple hours of activity
# Maybe have a function that gets applied for each activity

#_df = activity.iloc[0]

#_parcel_tot_df = parcel_tot_df[parcel_tot_df['PARCELID'] == _df['parcel']]


# Only include activities that occur within areas that have pollution
#df = activity[activity['GEOID10'].isin(pd.unique(hourly_emissions_total['GEOID10']))]
df = activity[activity['parcel'].isin(pd.unique(parcel_tot_df['PARCELID']))]

# 
#df.set_index(['parcel','begin_hour','end_hour'])

import timeit


results = []

############## FIXME: limited for testing
#########################
parcel_tot_df = parcel_tot_df.reset_index()
parcel_tot_df = parcel_tot_df.sort_values('PARCELID')
parcel_tot_df['tot_90_grams'] = parcel_tot_df['tot_90_grams'].astype('int')
df = df.reset_index(drop=True)
#df = df.iloc[0:10000]
missing = []
start = time.time()
counter = 1
for index, row in df.iterrows():
    #print(index)
    if counter%10:
        print(str(counter/int(len(df))*100)+'% complete')
    counter += 1
    try:
        tot_emissions = total_activity_emissions(parcel_tot_df, zone_num=row['parcel'], emissions_type='tot_90_grams', 
                                    begin_hour=row['begin_hour'], begin_hour_share=row['begin_hour_fraction'], 
                                    end_hour=row['end_hour'], end_hour_share=row['end_hour_fraction'])
        results.append(tot_emissions)
    except:
        missing.append(df.person_id)
        continue
    
end = time.time()
print(end - start)
# 0.12 s

df['total_exposure'] = results
df.to_csv('results.csv')

df_missing = pd.DataFrame(missing)
df_missing.to_csv('missing.csv')

print("--- %s seconds ---" % (time.time() - start_time))

######## Solution A
#parcel_tot_df = parcel_tot_df.reset_index(drop=True)
#parcel_sum_df = parcel_tot_df[['PARCELID','hourID','tot_90_grams']].sort_values(['PARCELID','hourID'])
#parcel_sum_df = parcel_sum_df.set_index(['PARCELID','hourID'])

#idx = pd.IndexSlice
## Retrieve emissions value for a Parcel (2) and times 4 to 7
#parcel_sum_df.loc[idx[2, 4:7], :].sum().values[0]

## Test with a subset of activities
#df = df.iloc[0:100]

## Make the indeces equal to the parcel, begin hour, and end hour
#import time
#start = time.time()
#df['grams'] = df.apply(lambda x: parcel_sum_df.loc[idx[int(x['parcel']), int(x['begin_hour']):int(x['end_hour'])], :].sum(), 
#                       axis=1)
#end = time.time()
#print(end - start)
###### 
#10.7 s

# SOlution A 1/2
## Apply is a loop too, need to vectorize
# convert parcel_sum_df to an array of parcelID as index and col as hour
# first convert to series to simplify that data type
#parcel_sum_df = pd.Series(parcel_sum_df['tot_90_grams'])
#parcel_sum_df = parcel_sum_df.astype('int32')

#df = df.iloc[0:100000]
#df['grams'] = df.apply(lambda x: parcel_sum_df.loc[idx[int(x['parcel']), int(x['begin_hour']):int(x['end_hour'])], :].sum(), 
#                       axis=1)

# Solution B

#def lambda_test(parcel, begin_hour, begin_hour_share, end_hour, end_hour_share):
#        # Totals from first hour
#    first_hour_total = parcel_tot_df[(parcel_tot_df['PARCELID'] == parcel) & (parcel_tot_df['hourID'] == begin_hour)]['tot_90_grams'].values[0]
#    first_hour_total = first_hour_total*begin_hour_share    # Modify with % of hour at that location
    
    
#    ### Totals from last hour
#    #last_hour_total = df[(df[geography_field] == parcel) & (df.hourID == end_hour)][emissions_type].values[0]
#    last_hour_total = parcel_tot_df[(parcel_tot_df['PARCELID'] == parcel) & (parcel_tot_df['hourID'] == end_hour)]['tot_90_grams'].values[0]
#    last_hour_total = last_hour_total*end_hour_share    # Modify with % of hour at that location
    
#    ### Calculate totals for interim hours if necessary
#    interim_total = 0
#    if end_hour-begin_hour>1:
#        for hour in range(begin_hour+1,end_hour):
#            interim_total +=  parcel_tot_df[(parcel_tot_df[geography_field] == parcel) & (parcel_tot_df.hourID == hour)]['tot_90_grams'].values[0]
            
#    activity_total = first_hour_total + interim_total + last_hour_total

    
#    return activity_total

#start = time.time()
##df_test = df.set_index(['parcel','begin_hour','end_hour'])
#df['test'] = df.apply(lambda x: lambda_test(x['parcel'], x['begin_hour'], x['begin_hour_fraction'], 
#                                                      x['end_hour'], x['end_hour_fraction']), axis=1)
#end = time.time()
#print(end - start)

# 0.26 sec

############## FIXME: limited for testing
#########################
#parcel_tot_df['tot_90_grams'] = parcel_tot_df['tot_90_grams'].astype('int')
#parcel_sum_df = parcel_sum_df.astype('int')
##df = df.iloc[0:100]
#missing = []
#start = time.time()
#counter = 1
#for index, row in df.iterrows():
#    #print(index)
#    counter += 1
#    try:
#        tot_emissions = total_activity_emissions2(parcel_sum_df, zone_num=row['parcel'], emissions_type='tot_90_grams', 
#                                    begin_hour=row['begin_hour'], begin_hour_share=row['begin_hour_fraction'], 
#                                    end_hour=row['end_hour'], end_hour_share=row['end_hour_fraction'])
#        results.append(tot_emissions)
#    except:
#        missing.append(df.person_id)
#        continue
    
#end = time.time()
#print(end - start)

# It might be faster to create a row for each hour for each activity and join the emissions totals for those rows
# 
#activity = pd.read_csv(r'C:\workspace\travel-modeling\air_quality\exposure\exposure\activity.csv')

# Will still require looping...
# Process each person's daily activity

# for each person, they need one array of length 24 that contains their parcel location
# Another array can constrain their fraction of the hour spent there

#df = activity[activity['person_id'] == '1000000_1']
#day_array = np.repeat(0, 24)
#fraction_array = np.repeat(1.0, 24)
#for index, row in df.iterrows():
#    print(row)
#    day_array[row['begin_hour']:row['end_hour']] = np.repeat(row['parcel'],row['end_hour']-row['begin_hour'])
#    fraction_array[row['begin_hour']] = row['begin_hour_fraction']
#    fraction_array[row['end_hour']-1] = row['end_hour_fraction']

#parcel_tot_df.index = parcel_tot_df['PARCELID']
#_df = parcel_tot_df[parcel_tot_df['PARCELID'] == 2]
#_df = _df.sort_values('hourID')
#_

#_df['tot_90_grams']*day_array