import pandas as pd
import numpy as np

################################ Load Files
# Air quality output produced from Soundcast scripts\summarize\standard\air_quality script
aq_rates = pd.read_csv(r'R:\e2projects_two\SoundCast\Inputs\db_inputs\running_emission_rates_by_veh_type.csv')

# Activity results are at parcel level - aggregate to block level for now
block_parcel_lookup = pd.read_csv(r'R:\e2projects_two\aq\new_parcel_block_lookup.txt')

# Load intersection of blocks and network components (replace with parcel intersect in future)
# This was done in GIS, as an intersect between edges_0 and a layer of block centroids buffered at 500 ft.
# Ideally do this in code with geopandas
block_network = pd.read_csv(r'R:\e2projects_two\aq\block_network_intersect.txt')

# Use trip records to create activity patterns for each simulated person in the region
df = pd.read_csv(r'L:\RTP_2022\final_runs\sc_rtp_2018_final\soundcast\outputs\daysim\_trip.tsv', sep='\t')   # Daysim standard output

################################
# Start script

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
#     print i
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


# Write to CSV
activity.to_csv(r'activity.csv', index=False)

###############################
# Create pollution totals by assignment period
# Re-read if you want to skip the above munging
activity = pd.read_csv(r'activity.csv')


# Add census block field (GEOID10) to the activity records
# We use this to help filter out blocks that don't appear in the activity df
activity = pd.merge(activity, block_parcel_lookup[['parcelid','GEOID10']], left_on='parcel',right_on='parcelid', how='left')

# Remove unneeded columns and rename temporarily
df = block_network[['Shape_Length','GEOID10','NewINode','NewJNode']]

# Remove any block that doesn't exist in activity dataframe
df = df[df['GEOID10'].isin(pd.unique(activity['GEOID10']))]

# List of pollutant IDs; not sure which ones we will need in the future
pollutant_list = [1,2,3,5,6,79,87,90,91,98,100,106,107,110,112,115,116,117,118,119]

# Reduce column size to only include pollutant totals, nodes, volume, and hour
aq_rates = aq_rates[['inode_x','jnode_x','total_volume','hourId']+[str(i) for i in pollutant_list]]

# Merge the network/block intersection with the hourly rates
block_rates = pd.merge(df, aq_rates, left_on=['NewINode','NewJNode'], right_on=['inode_x','jnode_x'], how='left')

# Compute the total grams emitted within the time frame
# by multiplying total volume by miles of network link
for pollutant in pollutant_list:
    block_rates[str(pollutant)+'_total_grams'] = block_rates['total_volume']*(block_rates['Shape_Length']/5280)*block_rates[str(pollutant)]

# Take sum of hourly emissions within each census block
total_hourly_block_grams = block_rates.groupby(['GEOID10','hourId']).sum()[['100_total_grams','1_total_grams']]
total_hourly_block_grams = total_hourly_block_grams.reset_index()

def average_emissions_to_hours(df, hour_list):
    
    # First hour contains information summed for all time periods
    copy_df = df[df['hourId'] == hour_list[0]].copy()
    
    for hour in hour_list:
        _df = copy_df.copy()
#         print hour
        if hour == hour_list[0]:
            df = df[df['hourId'] != hour_list[0]]
        _df['hourId'] = hour
        _df[['100_total_grams','1_total_grams']]/(len(hour_list))
        df = df.append(_df)
        
    df = df.reset_index()
    df = df.drop('index', axis=1)
    return df


hourly_emissions_total = average_emissions_to_hours(total_hourly_block_grams, hour_list=[10,11,12,13])
hourly_emissions_total = average_emissions_to_hours(hourly_emissions_total, hour_list=[18,19])
hourly_emissions_total = average_emissions_to_hours(hourly_emissions_total, hour_list=[20,21,22,23,0,1,2,3,4])

# Write to file ?
hourly_emissions_total.to_csv(r'hourly_emissions_total.csv', index=False)

####################################################
# Calculate the total grams for a given block and time period

def total_activity_emissions(df, zone_num, emissions_type, begin_hour, begin_hour_share, end_hour, end_hour_share,
                            geography_field='GEOID10'):
    """Calculate the total grams per each activity"""
    
    df = hourly_emissions_total
    
    # Totals from first hour
    first_hour_total = df[(df[geography_field] == zone_num) & (df.hourId == begin_hour)][emissions_type].values[0]
    first_hour_total = first_hour_total*begin_hour_share    # Modify with % of hour at that location
    
    # Totals from last hour
    last_hour_total = df[(df[geography_field] == zone_num) & (df.hourId == end_hour)][emissions_type].values[0]
    last_hour_total = last_hour_total*end_hour_share    # Modify with % of hour at that location
    
    # Calculate totals for interim hours if necessary
    interim_total = 0
    if end_hour-begin_hour>1:
        for hour in range(begin_hour+1,end_hour):
            interim_total +=  df[(df[geography_field] == zone_num) & (df.hourId == hour)][emissions_type].values[0]
            
    activity_total = first_hour_total + interim_total + last_hour_total
    
    return activity_total

# I can't figure out how to use lambda functino for a full dataframe right now,
# so let's loop for now ...

# Only include activities that occur within areas that have pollution
df = activity[activity['GEOID10'].isin(pd.unique(hourly_emissions_total['GEOID10']))]

results = []
print(len(df))
for index, row in df.iterrows():
    print(index)
    tot_emissions = total_activity_emissions(df, zone_num=row['GEOID10'], emissions_type='1_total_grams', 
                                begin_hour=row['begin_hour'], begin_hour_share=row['begin_hour_fraction'], 
                                end_hour=row['end_hour'], end_hour_share=row['end_hour_fraction'])
    results.append(tot_emissions)
    

df['total_exposure'] = results
df.to_csv('final_final.csv')


# Alternative is to use multiprocessing...

#def compute_exposure(process_integer):
#    print "processing thread: " + str(process_integer)
#    results = []
#    person_list = pd.unique(df['person_id'])
#    #chunksize = len(person_list)/num_processes
#    chunksize = 10000
#    _df = df[df['person_id'].isin(person_list[(i-1)*chunksize:i*chunksize])]
#    for index, row in _df.iterrows():
#        #print index
#        tot_emissions = total_activity_emissions(_df, zone_num=row['GEOID10'], emissions_type='1_total_grams', 
#                                    begin_hour=row['begin_hour'], begin_hour_share=row['begin_hour_fraction'], 
#                                    end_hour=row['end_hour'], end_hour_share=row['end_hour_fraction'])
#        results.append(tot_emissions)

#    _df['total_exposure'] = results
#    _df.to_csv(str(process_integer)+'.csv')

# try it as a multiprocess
#if __name__ == '__main__':
#    from multiprocessing import Pool
#    num_processes = 12
#    p = Pool(processes=num_processes)
#    p.map(compute_exposure, [1,2,3,4,5,6,7,8,9,10,11,12])