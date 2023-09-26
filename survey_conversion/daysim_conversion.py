import os
import numpy as np
import datetime
import urllib
import pyodbc
import pandas as pd
import sqlalchemy
from sqlalchemy.engine import URL
from pymssql import connect
import logging
import logcontroller
pd.options.mode.chained_assignment = None  # default='warn'

# Import local module variables
from lookup import *

# Geolocated directory
input_dir = r'R:\e2projects_two\2023_base_year\2017_2019_survey'

# FIXME - which columns to use?:


# Output directory
output_dir = r'R:\e2projects_two\2018_base_year\survey\daysim_format\revised'

# Flexible column names, given that these may change in future surveys
### FIXME! put into the config file
hhno = 'household_id'
hownrent = 'rent_own'
hrestype = 'res_type'
hhincome = 'hhincome_detailed'
hhtaz = 'final_home_taz'
hhparcel = 'final_home_parcel'
hhexpfac = 'hh_wt_revised'
hhwkrs = 'numworkers'
hhvehs = 'vehicle_count'
pno = 'pernum'

# Heirarchy order for tour mode, per DaySim docs: https://www.psrc.org/sites/default/files/2015psrc-modechoiceautomodels.pdf
# Drive to Transit > Walk to Transit > School Bus > HOV3+ > HOV2 > SOV > Bike > Walk > Other
drive_transit_i = 0
walk_transit_i = 0
mode_heirarchy = [6,8,9,5,4,3,2,1,10]

# Start log file
logger = logcontroller.setup_custom_logger('main_logger')
logger.info('--------------------NEW RUN STARTING--------------------')
start_time = datetime.datetime.now()

def assign_tour_mode(_df, tour_dict, tour_id, mode_heirarchy=mode_heirarchy):
    """ Get a list of transit modes and identify primary mode
        Primary mode is the first one from a heirarchy list found in the tour.   """
    mode_list = _df['mode'].value_counts().index.astype('int').values
    
    for mode in mode_heirarchy:
        if mode in mode_list:
            # If transit, check whether access mode is walk to transit or drive to transit
            if mode==6:
                # Try to use the access mode field values to get access mode
                try: 
                    if len([i for i in _df['mode_acc'].values if i in [3,4,5,6,7]]):
                        print('mode_acc drive')
                        tour_mode = 7    # park and ride
                    else:
                        tour_mode = 6
                        print('mode_acc walk')
                    return tour_mode
                except:
                    # otherwise, assume walk to transit                    if len([i for i in mode_list if i in [3,4,5]]) > 0:
                    tour_mode = 6   # walk
                    return tour_mode 

            # For non-transit modes, add first mode from the heirarchical list
            #tour_dict[tour_id]['tmodetp'] = mode
            #break
            return mode

def process_person_file(person):
    """ Create Daysim-formatted person file from Survey Excel file. """

    # Full time worker
    person.loc[person['employment'] == employment_full_time, 'pptyp'] = 1

    # Part-time worker
    person.loc[person['employment'] == employment_part_time, 'pptyp'] = 2

    # Non-working adult age 65+
    person.loc[(person['worker'] == is_worker) &  (person['age'].isin([age_65_74,age_75_84,age_85_plus])), 'pptyp'] = 3

    # Non working adult age <65
    person.loc[(person['worker'] == is_worker) &  (person['age'].isin([age_18_24,age_25_34,age_35_44,age_45_54,age_55_64])), 'pptyp'] = 4

    # university student (full-time)
    person.loc[(person['schooltype'].isin([schooltype_college,schooltype_vocational])) & (person['student'] == student_full_time), 'pptyp'] = 5

    # High school student age 16+
    person.loc[(~person['age'].isin([age_under_5,age_5_11,age_12_15])) & (person['schooltype'].isin([schooltype_homeschool,schooltype_public_k12,schooltype_private_k12])), 'pptyp'] = 6

    # Child age 5-15
    person.loc[person['age'].isin([age_5_11,age_12_15]), 'pptyp'] = 7

    # child under 5
    person.loc[person['age']==age_under_5, 'pptyp'] = 8

    # 
    person.loc[person['pptyp'].isnull(), 'pptyp'] = -1

    # Person worker type
    person.loc[person['employment'].isin([employment_full_time]), 'pwtyp'] = 1
    person.loc[person['employment'].isin([employment_part_time]), 'pwtyp'] = 2
    person.loc[~person['employment'].isin([employment_full_time,employment_part_time]), 'pwtyp'] = 0
    person['pwtyp'].fillna(0,inplace=True)
    person['pwtyp'] = person['pwtyp'].astype('int')

    # Transit pass availability
    person['ptpass'] = 0
    person.loc[(person['tran_pass_12'].isin([transit_pass_yes_all_paid,transit_pass_yes_part_paid])) | (person['benefits_3'].isin([transit_benefits_offered_used])),'ptpass'] = 1

    # Paid parking at work (any level of subsidy counts as 'paid')
    person['ppaidprk'] = -1
    # person.loc[person['workpass'].isin([995]), 'ppaidprk'] = -1
    person.loc[person['workpass'].isin([work_parking_free,work_parking_na]), 'ppaidprk'] = 1
    person.loc[person['workpass'].isin([work_parking_employer_pays_all,work_parking_employer_pays_some,work_parking_worker_pays_all_pass,work_parking_worker_pays_all_daily]), 'ppaidprk'] = 1

    ### FIXME:
    # usual arrival/departure time to/from work
    # Derive this from the day record file and trip files 
    # typical_day = 1 (true) and look at the commute trip

    # Map other variables from lookup tables
    person['puwmode'] = person['commute_mode'].map(commute_mode_dict)   # Note that all HOV trips are lumped into HOV2 besides vanpool, should use occupancy to sort this out
    # person['age'] = person['age'].astype('int')
    person['pagey'] = person['age'].map(age_map)
    person['pgend'] = person['gender'].map(gender_map)
    person['pstyp'] = person['student'].map(pstyp_map)
    person['pstyp'].fillna(0,inplace=True)
    person['hhno'] = person['household_id']
    person['pno'] = person['person_id'].astype('str').apply(lambda x: x[-2:]).astype('int')
    person['psexpfac'] = person[person_weight_col]

    # Get the TAZ and parcel data from the survey (must be added from the locate_parcels.py script first!)
    person['pwtaz'] = person['work_taz']
    person['pstaz'] = person['school_loc_taz']
    person['pwpcl'] = person['work_parcel']
    person['pspcl'] = person['school_loc_parcel']

    daysim_cols = ['hhno', 'pno', 'pptyp', 'pagey', 'pgend', 'pwtyp', 'pwpcl', 'pwtaz', 'pwautime',
               'pwaudist', 'pstyp', 'pspcl', 'pstaz', 'psautime', 'psaudist', 'puwmode', 'puwarrp', 
               'puwdepp', 'ptpass', 'ppaidprk', 'pdiary', 'pproxy', 'psexpfac','person_id']

    # Add empty columns to fill in later with skims
    for col in daysim_cols:
        if col not in person.columns:
            person[col] = -1
        else:
            person[col] = person[col].fillna(-1)
        
    person = person[daysim_cols]

    return person

def total_persons_to_hh(hh, person, daysim_field, filter_field, 
                        filter_field_list, hhid_col='hhno', wt_col='hhexpfac'):
    
    """Use person field to calculate total number of person in a household for a given field
    e.g., total number of full-time workers"""
    
    df = person[person[filter_field].isin(filter_field_list)]
    df = df.groupby(hhid_col).count().reset_index()[[wt_col,hhid_col]]
    df.rename(columns={wt_col: daysim_field}, inplace=True)
    
    # Join to households
    hh = pd.merge(hh, df, how='left', on=hhid_col)
    hh[daysim_field].fillna(0, inplace=True)
    
    return hh

def process_household_file(hh, person):

    hh['hhno'] = hh['household_id']
    hh['hhexpfac'] = hh[hh_weight_col]

    # Workers in Household from Person File (hhwkrs)
    hh = total_persons_to_hh(hh, person, daysim_field='hhwkrs', 
                            filter_field='pwtyp', filter_field_list=[1,2],
                            hhid_col='hhno', wt_col='psexpfac')

    # Full-time workers
    hh = total_persons_to_hh(hh, person, daysim_field='hhftw', 
                             filter_field='pwtyp', filter_field_list=[1],
                             hhid_col='hhno', wt_col='psexpfac')

    # Part-time workers
    hh = total_persons_to_hh(hh, person, daysim_field='hhptw', 
                            filter_field='pwtyp', filter_field_list=[2],
                            hhid_col='hhno', wt_col='psexpfac')

    # Retirees
    hh = total_persons_to_hh(hh, person, daysim_field='hhret', 
                        filter_field='pptyp', filter_field_list=[3],
                        hhid_col='hhno', wt_col='psexpfac')
    
    # Other Adults
    hh = total_persons_to_hh(hh, person, daysim_field='hhoad', 
                        filter_field='pptyp', filter_field_list=[4],
                        hhid_col='hhno', wt_col='psexpfac')
    
    # University Students
    hh = total_persons_to_hh(hh, person, daysim_field='hhuni', 
                    filter_field='pptyp', filter_field_list=[5],
                    hhid_col='hhno', wt_col='psexpfac')

    # High school students
    hh = total_persons_to_hh(hh, person, daysim_field='hhhsc', 
                    filter_field='pptyp', filter_field_list=[6],
                    hhid_col='hhno', wt_col='psexpfac')

    # K12 age 5-15
    hh = total_persons_to_hh(hh, person, daysim_field='hh515', 
                    filter_field='pptyp', filter_field_list=[7],
                    hhid_col='hhno', wt_col='psexpfac')

    # age under 5
    hh = total_persons_to_hh(hh, person, daysim_field='hhcu5', 
                filter_field='pptyp', filter_field_list=[8],
                hhid_col='hhno', wt_col='psexpfac')

    hh['hownrent'] = hh[hownrent].map(hownrent_map) 
    hh['hrestype'] = hh[hrestype].map(hhrestype_map) 
    hh['hhincome'] = hh[hhincome].map(income_map) 
    hh['hhtaz'] = hh[hhtaz]
    hh['hhparcel'] = hh[hhparcel]
    hh['hhwkrs'] = hh[hhwkrs]
    hh['hhno'] = hh[hhno]
    hh['hhvehs'] = hh[hhvehs]
    hh['samptype'] = 1

    # Remove households without parcels
    _filter = -hh['hhparcel'].isnull()
    logger.info(f'Dropped {len(hh[~_filter])} households: missing parcels')
    hh = hh[_filter]

    daysim_fields = ['hhno','hhsize','hhvehs','hhwkrs','hhftw','hhptw','hhret','hhoad','hhuni','hhhsc','hh515',
                 'hhcu5','hhincome','hownrent','hrestype','hhtaz','hhparcel','hhexpfac','samptype']

    hh = hh[daysim_fields]

    return hh

def process_trip_file(trip, person):
    """ Convert trip records to Daysim format."""

    trip['trexpfac'] = trip[trip_weight_col]

    # Filter out trips that have weight of zero or null
    _filter = (-trip['trexpfac'].isnull()) & (trip['trexpfac'] > 0)
    logger.info(f'Dropped {len(trip[~_filter])} trips: no or null weight ')
    trip = trip[_filter]

    # Filter out trips that started before 0 mam
    _filter = trip['depart_time_mam'] >= 0
    logger.info(f'Dropped {len(trip[~_filter])} trips: trips started before 0 mam ')
    trip = trip[_filter] 

    # Filter out rows with missing departure and arrival times
    _filter = (-trip['arrival_time_timestamp'].isnull()) & (-trip['depart_time_timestamp'].isnull())
    logger.info(f'Dropped {len(trip[~_filter])} trips: missing departure/arrival time ')
    trip = trip[_filter] 

    trip['hhno'] = trip['household_id']
    trip['tsvid'] = trip['trip_id']

    # Select only weekday trips (M-Th)
    # 1 is Monday, 2 T, 3 W, 4 Th
    trip = trip[trip['dayofweek'].isin(['Monday','Tuesday','Wednesday','Thursday'])] 
    trip['day'] = trip['dayofweek'].map(day_map)

    trip['opurp'] = trip['origin_purpose'].map(purpose_map)
    trip['dpurp'] = trip['dest_purpose'].map(purpose_map)

    trip['dorp'] = trip['driver'].map(dorp_map)

    # Dorp of N/A is 3 in daysim, fillna with this value
    trip['dorp'] = trip['dorp'].fillna(3)

    ##############################
    # Start and end time
    ##############################

    # The time_mam (minutes after midnight) data seems to be corrupted; recalculate from the timestamp
    trip['arrive_hour'] = trip['arrival_time_timestamp'].apply(lambda x: str(x).split(' ')[-1].split(':')[0]).astype('int')
    trip['arrive_min'] = trip['arrival_time_timestamp'].apply(lambda x: str(x).split(' ')[-1].split(':')[1]).astype('int')
    trip['arrtm'] = trip['arrive_hour']*60 + trip['arrive_min']
    
    trip['depart_hour'] = trip['depart_time_timestamp'].apply(lambda x: str(x).split(' ')[-1].split(':')[0]).astype('int')
    trip['depart_min'] = trip['depart_time_timestamp'].apply(lambda x: str(x).split(' ')[-1].split(':')[1]).astype('int')
    trip['deptm'] = trip['depart_hour']*60 + trip['depart_min']

    # trip['arrtm'] = trip['arrival_time_mam']
    # trip['deptm'] = trip['depart_time_mam']
    # if arrtm/deptm > 24*60, subtract that value to normalize to a single day
    # for some reason values can extend to a full day later
    for colname in ['arrtm','deptm']:
        for i in range(2,int(np.ceil(trip[colname]/(24*60)).max())+1):
            filter = (trip[colname] > (24*60)) & (trip[colname] < (24*60)*i)
            trip.loc[filter, colname] = trip.loc[filter, colname] - 24*60*(i-1)
    
    # Calculate start of next trip (ENDACTTM: trip destination activity end time)
    # FIXME: there are negative values in the activity_duration field
    trip['endacttm'] = trip['activity_duration'].abs() + trip['arrtm']

    ##############################
    # Mode
    ##############################
    trip['mode'] = 'Other'

    # Get HOV2/HOV3 based on total number of travelers
    trip.loc[(trip['travelers_total'] == 1) & (trip['mode_simple'] == 'Drive'),'mode'] = 'SOV'
    trip.loc[(trip['travelers_total'] == 2) & (trip['mode_simple'] == 'Drive'),'mode'] = 'HOV2'
    trip.loc[(trip['travelers_total'] > 2) & (trip['mode_simple'] == 'Drive'),'mode'] = 'HOV3+'
    # transit etc
    trip.loc[trip['mode_simple'] == 'Transit','mode'] = 'Transit'
    trip.loc[trip['mode_simple'] == 'Walk','mode'] = 'Walk'
    trip.loc[trip['mode_simple'] == 'Bike','mode'] = 'Bike'
    trip.loc[trip['mode_1'].isin(['School bus']),'mode'] = 'School_Bus'
    trip.loc[trip['mode_1'].isin(['Other hired service (Uber, Lyft, or other smartphone-app car service)',
                                  'Taxi (e.g., Yellow Cab)']),'mode'] = 'TNC' # Should this also include traditonal Taxi?
    trip['mode'] = trip['mode'].map(mode_dict)
    
    ##############################
    # Origin and Destination Types
    ##############################

    # Assume "other" by default
    trip.loc[:,'oadtyp'] = 4
    trip.loc[:,'dadtyp'] = 4

    # Trips with origin/destination purpose of "Home" (0) have a origin/destination address type of "Home" (1)
    trip.loc[trip['opurp'] == 0,'oadtyp'] = 1
    trip.loc[trip['dpurp'] == 0,'dadtyp'] = 1

    # Trips to/from work are considered "usual workplace" only if dtaz == workplace TAZ
    #### FIX ME: do not have PARCELS, only using TAZ
    # must join person records to get usual work and school location
    trip = trip.merge(person[['person_id','pwpcl','pspcl','pwtaz','pstaz']], how='left', on='person_id')

    # usual school
    trip.loc[(trip['opurp'] == 2) & (trip['opcl'] == trip['pspcl']),'oadtyp'] = 3
    trip.loc[(trip['dpurp'] == 2) & (trip['dpcl'] == trip['pspcl']),'dadtyp'] = 3

    # If trip is to/from TAZ of usual workplace and trip purpose is work
    # NOTE: Could use parcel here if geocoding was re-evaluated
    trip.loc[(trip['opurp'] == 1) & (trip['otaz'] == trip['pwtaz']),'oadtyp'] = 2
    trip.loc[(trip['dpurp'] == 1) & (trip['dtaz'] == trip['pwtaz']),'dadtyp'] = 2
    #trip.loc[(trip['opurp'] == 1) & (trip['opcl'] == trip['pwpcl']),'oadtyp'] = 2
    #trip.loc[(trip['dpurp'] == 1) & (trip['dpcl'] == trip['pwpcl']),'dadtyp'] = 2

    # Change mode
    trip.loc[trip['opurp'] == 10,'oadtyp'] = 6
    trip.loc[trip['dpurp'] == 10,'dadtyp'] = 6

    ##############################
    # Set Skim Values
    ##############################

    trip['travcost'] = -1
    trip['travtime'] = -1
    trip['travdist'] = -1

    # Add pathtype by analyzing transit submode
    # FIXME: Note that this field doesn't exist for some trips, should really be analyzed by grouping on the trip day or tour
    trip['pathtype'] = 1
    for index, row in trip.iterrows():
        if len([i for i in list(row[['mode_1','mode_2','mode_3','mode_4']].values) if i in transit_mode_list]):

            # ferry or water taxi
            if 'Ferry or water taxi' in row[['mode_1','mode_2','mode_3','mode_4']].values:
                trip.loc[index,'pathtype'] = 7
            # commuter rail
            elif 'Commuter rail (Sounder, Amtrak)' in row[['mode_1','mode_2','mode_3','mode_4']].values:
                trip.loc[index,'pathtype'] = 6
            # 'Urban rail (e.g., Link light rail, monorail)'
            elif ['Urban Rail (e.g., Link light rail, monorail)' or 'Other rail (e.g., streetcar)'] in row[['mode_1','mode_2','mode_3','mode_4']].values:
                trip.loc[index,'pathtype'] = 4
            else:
                trip.loc[index,'pathtype'] = 3

            # FIXME!!!
            # Note that we also need to include KnR and TNC
    
    trip_cols = ['hhno','pno','tsvid','day','mode','opurp','dpurp','deptm',
            'otaz','opcl','dtaz','dpcl','oadtyp','dadtyp',
            'arrtm','trexpfac','travcost','travtime','travdist',
        'pathtype','mode_acc','dorp','endacttm','trip_id','person_id']    # only include access mode temporarily

    # Filter bad trips
    for col in ['mode','opurp','dpurp','otaz','dtaz']:
        _filter = -trip[col].isnull()
        logger.info(f'Dropped {len(trip[~_filter])} trips: {col} is null')
        trip = trip[_filter]

    # Write to file
    trip = trip[trip_cols]

    return trip

def build_tour_file(trip, person):
    """ Generate tours from Daysim-formatted trip records. """

    # FIXME: create a way to log each excluded trip
    # Purpose is to create a way to measure how many trips were excluded by reason
    # Solutions: create a dictionary of categories and values
    # e.g. "same origin and destination": 0, increment that dict every time
    # write to log file when done with the script

    error_dict = {
        "first O and last D are not home": 0,
        "different number of tour starts and ends at home": 0
    }

    # Filter out trips that have the same origin and destination of home
    _filter = -((trip['opurp'] == trip['dpurp']) & (trip['opurp'] == 0))
    logger.info(f'Dropped {len(trip[~_filter])} trips: trips have same origin/destination of home')
    trip = trip[_filter]

    _filter = (((trip['dpurp'] >= 0)) | (trip['opurp'] >= 0))
    logger.info(f'Dropped {len(trip[~_filter])} trips: trips missing purpose')
    trip = trip[_filter]
    # trip = trip[(trip['dpurp'] >= 0)]
    # trip = trip[(trip['opurp'] >= 0)]

    trip['dpurp'] = trip['dpurp'].astype('int')

    # Reset the index
    trip = trip.reset_index()

    tour_dict = {}
    bad_trips = []
    tour_id = 0

    for person_id in trip['person_id'].value_counts().index.values:
    # for person_id in [19101730201]:
        print(person_id)
        person_df = trip.loc[trip['person_id'] == person_id]

        # Loop through each day
        for day in person_df['day'].unique():

            df = person_df.loc[person_df['day'] == day]

            # First o and last d of person's travel day should be home; if not, skip this trip set
            # FIXME : just remove all trips after the last home return trip?
            # !!!!!!!!!!!
            if (df.groupby('person_id').first()['opurp'].values[0] != 0) or df.groupby('person_id').last()['dpurp'].values[0] != 0:
                bad_trips += df['trip_id'].tolist()
                error_dict["first O and last D are not home"] += 1
                continue

            # Some people do not report sequential trips. 
            # If the dpurp of the previous trip does not match the opurp of the next trip, skip
            # similarly for activity type
            df['next_opurp'] = df.shift(-1)[['opurp']]
            df['prev_opurp'] = df.shift(1)[['opurp']]
            df['next_oadtyp'] = df.shift(-1)[['oadtyp']]
            if len(df.iloc[:-1][(df.iloc[:-1]['next_opurp'] != df.iloc[:-1]['dpurp'])]) > 0:
                bad_trips += df['trip_id'].tolist()
                continue
            # FIXME: add to logger!
            if len(df.iloc[:-1][(df.iloc[:-1]['next_oadtyp'] != df.iloc[:-1]['dadtyp'])]) > 0:
                bad_trips += df['trip_id'].tolist()
                continue
            # FIXME: add to logger!

            # identify home-based tours 
            home_tours_start = df[df['opurp'] == 0]
            home_tours_end = df[df['dpurp'] == 0]

            # skip person if they have a different number of tour starts/ends at home
            if len(home_tours_start) != len(home_tours_end):
                bad_trips += df['trip_id'].tolist()
                continue

            local_tour_id = 1
            # Loop through each set of home-based tours
            for tour_start_index in range(len(home_tours_start)):

                tour_dict[tour_id] = {}       
    
                # start row for this set
                start_row_id = home_tours_start.index[tour_start_index]
                end_row_id = home_tours_end.index[tour_start_index]
                # iterate between the start row id and the end row id to build the tour

                # Select slice of trips that correspond to a trip set
                _df = df.loc[start_row_id:end_row_id]

                #####################################################
                # Skip this trip set under certain conditions
                #####################################################

                if len(_df) == 0:
                    bad_trips += _df['trip_id'].tolist()
                    continue
               
                # calculate duration at location, as difference between arrival at a place and start of next tripi
                _df['duration'] = _df.shift(-1).iloc[:-1]['deptm']-_df.iloc[:-1]['arrtm']

                # First row contains origin information for the primary tour
                tour_dict[tour_id]['tlvorig'] = _df.iloc[0]['deptm']                
                tour_dict[tour_id]['totaz'] = _df.iloc[0]['otaz']
                tour_dict[tour_id]['topcl'] = _df.iloc[0]['opcl']
                tour_dict[tour_id]['toadtyp'] = _df.iloc[0]['oadtyp']

                # Last row contains return information
                tour_dict[tour_id]['tarorig'] = _df.iloc[-1]['arrtm'] 

                # Household and person info
                tour_dict[tour_id]['hhno'] = _df.iloc[0]['hhno']
                tour_dict[tour_id]['pno'] = _df.iloc[0]['pno']
                tour_dict[tour_id]['day'] = day
                tour_dict[tour_id]['tour'] = local_tour_id
                tour_dict[tour_id]['person_id'] = _df.iloc[0]['person_id']

                # For sets with only 2 trips, the halves are simply the first and second trips
                if len(_df) == 2:
                    tour_dict[tour_id]['pdpurp'] = _df.iloc[0]['dpurp']
                    tour_dict[tour_id]['tripsh1'] = 1
                    tour_dict[tour_id]['tripsh2'] = 1
                    tour_dict[tour_id]['tdadtyp'] =  _df.iloc[0]['dadtyp']
                    tour_dict[tour_id]['toadtyp'] =  _df.iloc[0]['oadtyp']
                    tour_dict[tour_id]['tpathtp'] = _df.iloc[0]['pathtype']
                    tour_dict[tour_id]['tdtaz'] = _df.iloc[0]['dtaz']
                    tour_dict[tour_id]['tdpcl'] = _df.iloc[0]['dpcl']
                    tour_dict[tour_id]['tardest'] = _df.iloc[0]['arrtm']
                    tour_dict[tour_id]['tlvdest'] = _df.iloc[-1]['deptm']
                    tour_dict[tour_id]['tarorig'] = _df.iloc[-1]['arrtm']
                    tour_dict[tour_id]['parent'] = 0    # No subtours for 2-leg trips
                    tour_dict[tour_id]['subtrs'] = 0    # No subtours for 2-leg trips

                    # Set tour half and tseg within half tour for trips
                    # for tour with only two records, there will always be two halves with tseg = 1 for both
                    trip.loc[trip['trip_id'] == _df.iloc[0]['trip_id'], 'half'] = 1
                    trip.loc[trip['trip_id'] == _df.iloc[-1]['trip_id'], 'half'] = 2
                    trip.loc[trip['trip_id'].isin(_df['trip_id']),'tseg'] = 1

                    tour_dict[tour_id]['tmodetp'] = assign_tour_mode(_df, tour_dict, tour_id)
                    
                    trip.loc[trip['trip_id'].isin(_df['trip_id'].values),'tour'] = local_tour_id

                # For tour groups with > 2 trips, calculate primary purpose and halves
                else: 
                    # Could be dealing with work-based subtours
                    # subtours exist if usual_workplace_dest==1 more than 2 times

                    # FIXME: maybe calculate whether or not this is overall a work tour based on longer duration? 
                    if (len(_df) >= 4) & (len(_df[_df['oadtyp'] == 2]) >= 2) & (len(_df[_df['opurp'] == 1]) >= 2) & (len(_df[(_df['oadtyp'] == 2) & (_df['dadtyp'] > 2)]) >= 1):


                        #subtour_index_start_values = _df[(_df['oadtyp'] == 2) & (_df['dadtyp'] > 2)].index.values
                        subtour_index_start_values = _df[(((_df['oadtyp'] == 2) & (_df['dadtyp'] > 2)) | 
                                                          ((_df['opurp'] == 1) & (_df['dpurp'] > 1)))].index.values
                        print('subtour --------------- :)')
                        subtours_df = pd.DataFrame()

                        # Loop through each potential subtour
                        # the following trips must eventually return to work for this to qualify as a subtour
                        subtour_id = tour_id + 1
                        
                        local_tour_id_placeholder = local_tour_id
                        subtour_count = 0

                        for subtour_start_value in subtour_index_start_values:
                            #print(subtour_start_value)
                            # Potential subtour
                            # Loop through the index from subtour start 
                            next_row_index_start = np.where(_df.index.values == subtour_start_value)[0][0]+1
                            for i in _df.index.values[next_row_index_start:]:
                            #for i in _df.loc[subtour_start_value:].index.values:
                                next_row = _df.loc[i]
                                if next_row['dadtyp'] == 2:
                                    subtour_df = _df.loc[subtour_start_value:i]

                                    local_tour_id +=1

                                    tour_dict[subtour_id] = {}
                                    # Process this subtour
                                    # Create a new tour record for the subtour
                                    subtour_df['subtour_id'] = subtour_start_value
                                    subtours_df = subtours_df.append(subtour_df)

                                    # add this as a tour
                                    tour_dict[subtour_id]['tour'] = local_tour_id
                                    tour_dict[subtour_id]['hhno'] = subtour_df.iloc[0]['hhno']
                                    tour_dict[subtour_id]['pno'] = subtour_df.iloc[0]['pno']
                                    tour_dict[subtour_id]['day'] = day
                                    tour_dict[subtour_id]['tlvorig'] = subtour_df.iloc[0]['deptm']
                                    tour_dict[subtour_id]['tarorig'] = subtour_df.iloc[-1]['arrtm']
                                    tour_dict[subtour_id]['totaz'] = subtour_df.iloc[0]['otaz']
                                    tour_dict[subtour_id]['topcl'] = subtour_df.iloc[0]['opcl']
                                    tour_dict[subtour_id]['toadtyp'] = subtour_df.iloc[0]['oadtyp']
                                    tour_dict[subtour_id]['parent'] = local_tour_id_placeholder    # Parent is the main tour ID
                                    tour_dict[subtour_id]['subtrs'] = 0    # No subtours for subtours

                                    trip.loc[trip['trip_id'].isin(subtour_df['trip_id'].values),'tour'] = local_tour_id

                                    if len(subtour_df) == 2:
                                        #if subtour_df.iloc[0]['dpurp'] in [0,10]:   # ignore tours that have purposes to home or changemode
                                        #    bad_trips += _df['trip_id'].to_list()
                                        #    continue
                                        tour_dict[subtour_id]['pdpurp'] = subtour_df.iloc[0]['dpurp']
                                        tour_dict[subtour_id]['tripsh1'] = 1
                                        tour_dict[subtour_id]['tripsh2'] = 1
                                        tour_dict[subtour_id]['tdadtyp'] =  subtour_df.iloc[0]['dadtyp']
                                        tour_dict[subtour_id]['toadtyp'] =  subtour_df.iloc[0]['oadtyp']
                                        tour_dict[subtour_id]['tpathtp'] = subtour_df.iloc[0]['pathtype']
                                        tour_dict[subtour_id]['tdtaz'] = subtour_df.iloc[0]['dtaz']
                                        tour_dict[subtour_id]['tdpcl'] = subtour_df.iloc[0]['dpcl']
                                        tour_dict[subtour_id]['tlvdest'] = subtour_df.iloc[-1]['deptm']
                                        tour_dict[subtour_id]['tardest'] = subtour_df.iloc[0]['arrtm']

                                        tour_dict[subtour_id]['tmodetp'] = assign_tour_mode(subtour_df, tour_dict, subtour_id)

                                        # Set tour half and tseg within half tour for trips
                                        # for tour with only two records, there will always be two halves with tseg = 1 for both
                                        trip.loc[trip['trip_id'] == subtour_df.iloc[0]['trip_id'], 'half'] = 1
                                        trip.loc[trip['trip_id'] == subtour_df.iloc[-1]['trip_id'], 'half'] = 2
                                        trip.loc[trip['trip_id'].isin(_df['trip_id']),'tseg'] = 1

                                    # If subtour length > 2, find the primary purpose
                                    else:
                                        subtour_df['duration'] = subtour_df.shift(-1).iloc[:-1]['deptm']-subtour_df.iloc[:-1]['arrtm']
                                        primary_subtour_purp_index = subtour_df[subtour_df['dpurp']!=10]['duration'].idxmax()

                                        tour_dict[subtour_id]['pdpurp'] = subtour_df.loc[primary_subtour_purp_index]['dpurp']

                
                                        # Get the data based on the primary destination trip
                                        # We know the tour destination parcel/TAZ field from that primary trip, as well as destination type
                                        tour_dict[subtour_id]['tdtaz'] = subtour_df.loc[primary_subtour_purp_index]['dtaz']
                                        tour_dict[subtour_id]['tdpcl'] = subtour_df.loc[primary_subtour_purp_index]['dpcl']
                                        tour_dict[subtour_id]['tdadtyp'] = subtour_df.loc[primary_subtour_purp_index]['dadtyp']
                
                                        # Pathtype is defined by a heirarchy, where highest number is chosen first
                                        # Ferry > Commuter rail > Light Rail > Bus > Auto Network
                                        # Note that tour pathtype is different from trip path type (?)
                                        tour_dict[subtour_id]['tpathtp'] = subtour_df.loc[subtour_df['mode'].idxmax()]['pathtype']

                                        # Calculate tour halves, etc
                                        tour_dict[subtour_id]['tripsh1'] = len(subtour_df.loc[0:primary_subtour_purp_index])
                                        tour_dict[subtour_id]['tripsh2'] = len(subtour_df.loc[primary_subtour_purp_index+1:])

                                        # Set tour halves on trip records
                                        trip.loc[trip['trip_id'].isin(subtour_df.loc[0:primary_subtour_purp_index].trip_id),'half'] = 1
                                        trip.loc[trip['trip_id'].isin(subtour_df.loc[primary_subtour_purp_index+1:].trip_id),'half'] = 2

                                        # set trip segment within half tours
                                        trip.loc[trip['trip_id'].isin(subtour_df.loc[0:primary_subtour_purp_index].trip_id),'tseg'] = range(1,len(subtour_df.loc[0:primary_subtour_purp_index])+1)
                                        trip.loc[trip['trip_id'].isin(subtour_df.loc[primary_subtour_purp_index+1:].trip_id),'tseg'] = range(1,len(subtour_df.loc[primary_subtour_purp_index+1:])+1)

                                        # Departure/arrival times
                                        tour_dict[subtour_id]['tlvdest'] = subtour_df.loc[primary_subtour_purp_index]['deptm']
                                        tour_dict[subtour_id]['tardest'] = subtour_df.loc[primary_subtour_purp_index]['arrtm']
                                        
                                        tour_dict[subtour_id]['tmodetp'] = assign_tour_mode(subtour_df, tour_dict, subtour_id)

                                    # Done with this subtour 
                                    subtour_count += 1
                                    subtour_id += 1
                                    break
                                else:
                                    continue
                        
                        if len(subtours_df) < 1:
                            # No subtours actually found
                            # FIXME: make this a function, because it's called multiple times
                            tour_dict[tour_id]['subtrs'] = 0
                            tour_dict[tour_id]['parent'] = 0

                            # Identify the primary purpose
                            primary_purp_index = _df[-_df['dpurp'].isin([0,10])]['duration'].idxmax()

                            tour_dict[tour_id]['pdpurp'] = _df.loc[primary_purp_index]['dpurp']
                            tour_dict[tour_id]['tlvdest'] = _df.loc[primary_purp_index]['deptm']
                            tour_dict[tour_id]['tdtaz'] = _df.loc[primary_purp_index]['dtaz']
                            tour_dict[tour_id]['tdpcl'] = _df.loc[primary_purp_index]['dpcl']
                            tour_dict[tour_id]['tdadtyp'] = _df.loc[primary_purp_index]['dadtyp']

                            tour_dict[tour_id]['tardest'] = _df.iloc[-1]['arrtm']
                   
                            tour_dict[tour_id]['tripsh1'] = len(_df.loc[0:primary_purp_index])
                            tour_dict[tour_id]['tripsh2'] = len(_df.loc[primary_purp_index+1:])
                        
                            # path type
                            # Pathtype is defined by a heirarchy, where highest number is chosen first
                            # Ferry > Commuter rail > Light Rail > Bus > Auto Network
                            # Note that tour pathtype is different from trip path type (?)
                            tour_dict[tour_id]['tpathtp'] = _df.loc[_df['mode'].idxmax()]['pathtype']

                            # Set tour halves on trip records
                            trip.loc[trip['trip_id'].isin(_df.loc[0:primary_purp_index].trip_id),'half'] = 1
                            trip.loc[trip['trip_id'].isin(_df.loc[primary_purp_index+1:].trip_id),'half'] = 2

                            # set trip segment within half tours
                            trip.loc[trip['trip_id'].isin(_df.loc[0:primary_purp_index].trip_id),'tseg'] = range(1,len(_df.loc[0:primary_purp_index])+1)
                            trip.loc[trip['trip_id'].isin(_df.loc[primary_purp_index+1:].trip_id),'tseg'] = range(1,len(_df.loc[primary_purp_index+1:])+1)

                            trip.loc[trip['trip_id'].isin(_df['trip_id'].values),'tour'] = local_tour_id

                            # Extract main mode 
                            tour_dict[tour_id]['tmodetp'] = assign_tour_mode(_df, tour_dict, tour_id)    
                        
                        else:
                            # The main tour destination arrival will be the trip before subtours
                            # the main tour destination departure will be the trip after subtours
                            # trip when they arrive to work -> always the previous trip before subtours_df index begins
                            main_tour_start_index = _df.index.values[np.where(_df.index.values == subtours_df.index[0])[0][0]-1]   
                            # trip when leave work -> always the next trip after the end of the subtours_df
                            main_tour_end_index = _df.index.values[np.where(_df.index.values == subtours_df.index[-1])[0][0]+1]    
                            # If there were subtours, this is a work tour
                            tour_dict[tour_id]['pdpurp'] = 1
                            tour_dict[tour_id]['tdtaz'] = _df.loc[main_tour_start_index]['dtaz']
                            tour_dict[tour_id]['tdpcl'] = _df.loc[main_tour_start_index]['dpcl']
                            tour_dict[tour_id]['tdadtyp'] = _df.loc[main_tour_start_index]['dadtyp']

                            # Pathtype is defined by a heirarchy, where highest number is chosen first
                            # Ferry > Commuter rail > Light Rail > Bus > Auto Network
                            # Note that tour pathtype is different from trip path type (?)
                            subtours_excluded_df = pd.concat([df.loc[start_row_id:main_tour_start_index], df.loc[main_tour_end_index:end_row_id]])
                            tour_dict[tour_id]['tpathtp'] = subtours_excluded_df.loc[subtours_excluded_df['mode'].idxmax()]['pathtype']

                            # Calculate tour halves, etc
                            tour_dict[tour_id]['tripsh1'] = len(_df.loc[0:main_tour_start_index])
                            tour_dict[tour_id]['tripsh2'] = len(_df.loc[main_tour_end_index:])

                            # Set tour halves on trip records
                            trip.loc[trip['trip_id'].isin(_df.loc[0:main_tour_start_index].trip_id),'half'] = 1
                            trip.loc[trip['trip_id'].isin(_df.loc[main_tour_end_index:].trip_id),'half'] = 2

                            # set trip segment within half tours
                            trip.loc[trip['trip_id'].isin(_df.loc[0:main_tour_start_index].trip_id),'tseg'] = range(1,len(_df.loc[0:main_tour_start_index])+1)
                            trip.loc[trip['trip_id'].isin(_df.loc[main_tour_end_index:].trip_id),'tseg'] = range(1,len(_df.loc[main_tour_end_index:])+1)

                            # Departure/arrival times
                            tour_dict[tour_id]['tlvdest'] = _df.loc[main_tour_end_index]['deptm']
                            tour_dict[tour_id]['tardest'] = _df.loc[main_tour_start_index]['arrtm']

                            # Number of subtours 
                            tour_dict[tour_id]['subtrs'] = subtour_count
                            tour_dict[tour_id]['parent'] = 0

                            # Mode
                            tour_dict[tour_id]['tmodetp'] = assign_tour_mode(_df, tour_dict, tour_id)
                        
                             # add tour ID to the trip records (for trips not in the subtour_df)
                            df_unique_no_subtours = [i for i in _df['trip_id'].values if i not in subtours_df['trip_id'].values]
                            df_unique_no_subtours = _df[_df['trip_id'].isin(df_unique_no_subtours)]
                            trip.loc[trip['trip_id'].isin(df_unique_no_subtours['trip_id'].values),'tour'] = local_tour_id_placeholder

                    else:
                        # No subtours
                        tour_dict[tour_id]['subtrs'] = 0
                        tour_dict[tour_id]['parent'] = 0

                        # Identify the primary purpose
                        primary_purp_index = _df[-_df['dpurp'].isin([0,10])]['duration'].idxmax()

                        tour_dict[tour_id]['pdpurp'] = _df.loc[primary_purp_index]['dpurp']
                        tour_dict[tour_id]['tlvdest'] = _df.loc[primary_purp_index]['deptm']
                        tour_dict[tour_id]['tdtaz'] = _df.loc[primary_purp_index]['dtaz']
                        tour_dict[tour_id]['tdpcl'] = _df.loc[primary_purp_index]['dpcl']
                        tour_dict[tour_id]['tdadtyp'] = _df.loc[primary_purp_index]['dadtyp']

                        tour_dict[tour_id]['tardest'] = _df.iloc[-1]['arrtm']
                   
                        tour_dict[tour_id]['tripsh1'] = len(_df.loc[0:primary_purp_index])
                        tour_dict[tour_id]['tripsh2'] = len(_df.loc[primary_purp_index+1:])
                        
                        # path type
                        # Pathtype is defined by a heirarchy, where highest number is chosen first
                        # Ferry > Commuter rail > Light Rail > Bus > Auto Network
                        # Note that tour pathtype is different from trip path type (?)
                        tour_dict[tour_id]['tpathtp'] = _df.loc[_df['mode'].idxmax()]['pathtype']

                        # Set tour halves on trip records
                        trip.loc[trip['trip_id'].isin(_df.loc[0:primary_purp_index].trip_id),'half'] = 1
                        trip.loc[trip['trip_id'].isin(_df.loc[primary_purp_index+1:].trip_id),'half'] = 2

                        # set trip segment within half tours
                        trip.loc[trip['trip_id'].isin(_df.loc[0:primary_purp_index].trip_id),'tseg'] = range(1,len(_df.loc[0:primary_purp_index])+1)
                        trip.loc[trip['trip_id'].isin(_df.loc[primary_purp_index+1:].trip_id),'tseg'] = range(1,len(_df.loc[primary_purp_index+1:])+1)

                        trip.loc[trip['trip_id'].isin(_df['trip_id'].values),'tour'] = local_tour_id

                        # Extract main mode 
                        tour_dict[tour_id]['tmodetp'] = assign_tour_mode(_df, tour_dict, tour_id)                
                            
                # Increment the tour ID
                if (len(_df) >= 4) & (len(_df[_df['oadtyp'] == 2]) >= 2) & (len(_df[_df['opurp'] == 1]) >= 2) & (len(_df[(_df['oadtyp'] == 2) & (_df['dadtyp'] > 2)]) >= 1):
                    tour_id = subtour_id + tour_id
                else:
                    tour_id += 1     
                    
                local_tour_id += 1

    tour = pd.DataFrame.from_dict(tour_dict, orient='index')


    for col in ['jtindex', 'phtindx1', 'phtindx2', 'fhtindx1', 'fhtindx2']:
        tour[col] = 0

    for col in ['tautotime', 'tautocost', 'tautodist']:
        tour[col] = -1

    # Assign weight toexpfac as hhexpfac (getting it from psexpfac, which is the same as hhexpfac)
    # tour['person_id'] = tour['hhno'].astype('int').astype('str') + tour['pno'].astype('int').astype('str')
    tour = tour.merge(person[['person_id','psexpfac']], on='person_id', how='left')
    tour.rename(columns={'psexpfac':'toexpfac'}, inplace=True)

    # remove the trips that weren't included in the tour file
    trip = trip[-trip['trip_id'].isin(bad_trips)]
    pd.DataFrame(bad_trips).T.to_csv(os.path.join(output_dir,'bad_trips.csv'))

    # Export columns in proper order
    tour_cols = ['hhno','pno','day','tour','jtindex','parent','subtrs','pdpurp','tlvorig',
                 'tardest','tlvdest','tarorig','toadtyp','tdadtyp','topcl','totaz','tdpcl',
                 'tdtaz','tmodetp','tpathtp','tautotime','tautocost','tautodist','tripsh1',
                 'tripsh2','phtindx1','phtindx2','fhtindx1','fhtindx2','toexpfac','person_id']
    tour = tour[tour_cols]

    trip_cols = ['hhno','pno','day','tour','half','tseg','tsvid','opurp','dpurp','oadtyp','dadtyp',
                 'opcl','dpcl','otaz','dtaz','mode','pathtype','dorp','deptm','arrtm','endacttm','travtime',
                 'travcost','travdist','trexpfac','person_id']
    trip = trip[trip_cols]

    return tour, trip

def process_household_day(tour, hh):

    household_day = tour.groupby(['hhno','day']).count().reset_index()[['hhno','day']]
    
    # add day of week lookup
    household_day['dow'] = household_day['day']

    # Set number of joint tours to 0 for this version of Daysim
    for col in ['jttours','phtours','fhtours']:
        household_day[col] = 0

    # Add expansion factor
    household_day = household_day.merge(hh[['hhno','hhexpfac']], on='hhno', how='left')
    household_day.rename(columns={'hhexpfac': 'hdexpfac'}, inplace=True)

    return household_day

def process_person_day(tour, person, trip, hh):

    # Get the usual workplace column from person records
    tour = tour.merge(person[['hhno','pno','pwpcl']], on=['hhno','pno'], how='left')
    
    pday = pd.DataFrame()
    for person_rec in person['person_id'].unique():

        # get this person's tours
        _tour = tour[tour['person_id'] == person_rec]
    
        # Loop through each day
        for day in _tour['day'].unique():
    
            day_tour = _tour[_tour['day'] == day]
        
            prec_id = str(person_rec) + str(day)
            pday.loc[prec_id,'hhno'] = day_tour['hhno'].iloc[0]
            pday.loc[prec_id,'pno'] = day_tour['pno'].iloc[0]
            pday.loc[prec_id,'day'] = day
        
            # Begin/End at home-
            # need to get from first and last trips of tour days 
            pday.loc[prec_id,'beghom'] = 0
            pday.loc[prec_id,'endhom'] = 0
            _trip = trip[(trip['person_id'] == person_rec) & (trip['day'] == day)]
            if _trip.iloc[0]['opurp'] == 0:
                pday.loc[prec_id,'beghom'] = 1
            if _trip.iloc[-1]['dpurp'] == 0:
                pday.loc[prec_id,'endhom'] = 1
        
            # Number of tours by purpose
            purp_dict = {
                'wk': 1,    
                'sc': 2,
                'es': 3,
                'pb': 4,
                'sh': 5,
                'ml': 6,
                'so': 7,
                're': 8,
                'me': 9
            }
            for purp_name, purp_val in purp_dict.items():
                # Number of tours
                pday.loc[prec_id,purp_name+'tours'] = len(day_tour[day_tour['pdpurp'] == purp_val])
        
                # Number of stops
                day_tour_purp = day_tour[day_tour['pdpurp'] == purp_val]
                if len(day_tour_purp) > 0:
                    nstops = day_tour_purp[['tripsh1','tripsh2']].sum().sum() - 2
                else:
                    nstops = 0
                pday.loc[prec_id,purp_name+'stops'] = nstops
        
            # Home based tours
            pday.loc[prec_id,'hbtours'] = len(day_tour)

            # Work-based tours (subtours)
            pday.loc[prec_id,'wbtours'] = day_tour['subtrs'].sum()

            # Work trips to usual workplace
            pday.loc[prec_id,'uwtours'] = len(day_tour[day_tour['tdpcl'] == day_tour['pwpcl']])

            # Fill in these fields for now:
            for col in ['wkathome']:
                pday[col] = -1

    # Add expansion factor
    pday = pday.merge(hh[['hhno','hhexpfac']], on='hhno', how='left')
    pday.rename(columns={'hhexpfac': 'pdexpfac'}, inplace=True)

    return pday

# Get subtours

def main():
    
    debug_tours = False
    write_debug_files = True

    if not debug_tours:
        # Load geolocated survey data
        trip_original_df = pd.read_csv(os.path.join(input_dir,'geolocated_trip.csv'))
        hh_original_df = pd.read_csv(os.path.join(input_dir,'geolocated_hh.csv'))
        person_original_df = pd.read_csv(os.path.join(input_dir,'geolocated_person.csv'))

        person = process_person_file(person_original_df)
        hh = process_household_file(hh_original_df, person)
        trip = process_trip_file(trip_original_df, person)

        if write_debug_files == True:
        # Temporarily write file to disk so we can reload for debugging
            person.to_csv(os.path.join(output_dir,'daysim_person.csv'))
            hh.to_csv(os.path.join(output_dir,'daysim_hh.csv'))
            trip.to_csv(os.path.join(output_dir,'daysim_trip.csv'))
    else:
        person = pd.read_csv(os.path.join(output_dir,'daysim_person.csv'))
        hh = pd.read_csv(os.path.join(output_dir,'daysim_hh.csv'))
        trip = pd.read_csv(os.path.join(output_dir,'daysim_trip.csv'))

    # 
    #tour['person_id'] = tour['hhno'].astype('int').astype('str') + tour['pno'].astype('int').astype('str')
    # trip['person_id'] = trip['hhno'].astype('int').astype('str') + trip['pno'].astype('int').astype('str')
    # person['person_id'] = person['hhno'].astype('int').astype('str') + person['pno'].astype('int').astype('str')

    # Make sure trips are properly ordered, where deptm is increasing for each person's travel day
    trip['person_id_int'] = trip['person_id'].astype('int')
    trip = trip.sort_values(['person_id_int','day','deptm'])
    trip = trip.reset_index()

    # Create tour file and update the trip file with tour info
    tour, trip = build_tour_file(trip, person)

    household_day = process_household_day(tour, hh)

    # person day
    person_day = process_person_day(tour, person, trip, hh)

    trip[['travdist','travcost','travtime']] = "-1.00"

    for df_name, df in {'prec': person, 'trip': trip, 'tour': tour, 'hrec': hh,
                        'hday': household_day, 'pday': person_day}.items():
        print(df_name)
        #print(df)
        expcol = [col for col in df.columns if 'expfac' in col][0]
        col_list = df.columns.tolist()
        col_list.remove(expcol)
        if df_name == 'trip':
            for col in ['travcost','travdist','travtime']:
                col_list.remove(col)
        df[expcol] = df[expcol].astype('str').apply(lambda row: row.split('.')[0] + "." + row.split('.')[-1][0:2])
        df[col_list] = df[col_list].fillna(-1).astype(dtype='int', errors='ignore')
        df.to_csv(os.path.join(output_dir,df_name+'P14.dat'), index=False, sep=' ')
        df.to_csv(os.path.join(output_dir,df_name+'P17.csv'), index=False, sep=',')

    # Conclude log
    end_time = datetime.datetime.now()
    elapsed_total = end_time - start_time
    logger.info('--------------------RUN ENDING--------------------')
    logger.info('TOTAL RUN TIME %s'  % str(elapsed_total))

if __name__ == '__main__':
    main()