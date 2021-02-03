####################################
# Preprocess Daysim-formatted survey files for Activitysim
# The outputs of this script must be processed by infer.py to produce the final estimation input dataset for Activitysim
# The prefix 'survey_' refers to outputs from this script, which servers as input for infer.py
# The prefix 'override_' refers to the output of infer.py, which will be read by Activitysim in estimation mode.
####################################

import os
import pandas as pd
import numpy as np
from urlparse import urljoin

# Survey input files, in Daysim format
survey_input_dir = r'R:\e2projects_two\SoundCast\Inputs\dev\base_year\2018\survey'

output_dir = r'R:\e2projects_two\activitysim\data\psrc\one_zone\estimation\inputs'

# Example survey data for formatting template
example_survey_dir = r'https://raw.githubusercontent.com/ActivitySim/activitysim/master/activitysim/examples/example_estimation/data_sf/survey_data/'

def process_hh(df):

    df.rename(columns={'hhtaz': 'TAZ',
                        'hhincome': 'income',
                         'hhwkrs': 'num_workers',
                      'hhvehs': 'auto_ownership'}, inplace=True)
    df['household_id'] = df['hhno'].copy()

    # Set household type to 1 for now
    df['HHT'] = 1

    # Household type
    # Integer, 
    # 1 - family household: married-couple; 
    # 2 - family household: male householder, no wife present; 
    # 3 - family household: female householder, no husband present; 
    # 4 - non-family household: male householder living alone; 
    # 5 - non-family household: male householder, not living alone; 
    # 6 - non-family household female householder, living alone; 
    # 7 - non-family household: female householder, not living alone

    return df

# Person
def process_person(df):

    df.rename(columns={
        'hhno':'household_id',
        'pagey':'age',
        'pno': 'PNUM',
        'pgend': 'sex',
        'pwtaz': 'workplace_taz',
        'pstaz': 'school_taz'
    }, inplace=True)


    # Create new df id by concatenating household id and pno
    df['person_id'] = df['household_id'].astype('str') + df['PNUM'].astype('str')

    df.loc[df['pwtyp'] == 1,'pemploy'] = 1
    df.loc[df['pwtyp'] == 2,'pemploy'] = 2
    df.loc[df['pwtyp'] == 0,'pemploy'] = 3
    df.loc[df['age'] < 16,'pemploy'] = 4
    df['pemploy'] = df['pemploy'].astype('int')

    df['pstudent'] = 3
    df.loc[df['pptyp'].isin([7,6]),'pstudent'] = 1
    df.loc[df['pptyp']==5 ,'pstudent'] = 2

    # There are some people with -1 pptyp that should be corrected for
    # Reclassify
    _filter = df['pptyp'] == -1
    df.loc[(df['pptyp'] == -1) & (df['pwtyp'] == 0) & (df['age']>=65), 'pptyp'] = 3   # Non-worker over 65
    df.loc[(df['pptyp'] == -1) & (df['pstyp'] > 0) & (df['age']>18), 'pptyp'] = 5    # university student 
    df.loc[(df['pptyp'] == -1) & (df['pstyp'] > 0) & (df['age']<=18), 'pptyp'] = 6 # high school student
    df.loc[(df['pptyp'] == -1) & (df['pwtyp'] == 0) & (df['age']<65), 'pptyp'] = 4 # non-working adult under 65

    # assign values used in activitysim
    df['ptype'] = df['pptyp']
    df.loc[df['pptyp'] == 3, 'ptype'] = 5
    df.loc[df['pptyp'] == 5, 'ptype'] = 3

    # Free parking at work
    df.loc[df['ppaidprk'] == 1, 'free_parking_at_work'] = True
    df.loc[df['ppaidprk'] < 1, 'free_parking_at_work'] = False

    return df



def process_trip(df, template):


    # Create new person id by concatenating household id and pno
    df['person_id'] = df['hhno'].astype('str') + df['pno'].astype('str')

    df.rename(columns={
        'tour':'tour_id',
        'id':'trip_id',
        'hhno':'household_id',
    #     'dpurp':'purpose',
        'otaz':'origin',
        'dtaz':'destination',
    #     'mode':'trip_mode',
    #     'deptm': 'depart'
    }, inplace=True)
    # purpose
    #trip_template.groupby('purpose').count()[['trip_id']]
    purp_map = {
        0: 'Home',
    1: 'work',
    2:'school',
    3:'escort',
    4:'othmaint',
    5:'shopping',
    6:'eatout',
    7:'social'}

    df['purpose'] = df['dpurp'].map(purp_map)

    # assign some modes directly
    mode_map = {
        1: 'WALK',
        2: 'BIKE',
        3: 'DRIVEALONEPAY',
        4: 'SHARED2FREE',
        5: 'SHARED3FREE',
        10: 'TNC_SINGLE'
    }
    df['trip_mode'] = df['mode'].map(mode_map)

    # Assign transit submodes based on PATHTYPE field

    # all walk access assumed
    df.loc[df['pathtype']==3, 'trip_mode'] = 'WALK_LOC' # local bus, 
    df.loc[df['pathtype']==4, 'trip_mode'] = 'WALK_HVY' # Assign light rail as heavy rail (no such thing as light rail in MTC TM1)
    df.loc[df['pathtype']==6, 'trip_mode'] = 'WALK_COM'
    # Fix me!!!
    # NO FERRY MODE; use the EXP mode?
    df.loc[df['pathtype']==7, 'trip_mode'] = 'WALK_EXP'  # No ferry mode...

    # Fix me!!!
    # Drop the null trips (other and school bus) for now
    df = df[-df['trip_mode'].isnull()]

    # departure time departure hour
    df['depart'] = np.floor(df['deptm']/60)

    # outbound based on df half
    df['outbound'] = False
    df.loc[df['half']==1,'outbound'] = True

    return df


def process_tour(df, template):
    # concatentate tour ID
    df['tour_id'] = df['hhno'].astype('str') + df['pno'].astype('str') + df['tour'].astype('str')
    df['person_id'] = df['hhno'].astype('str') + df['pno'].astype('str')
    df['household_id'] = df['hhno']

    # tour purpose type
    purp_map = {
        0: 'Home',
    1: 'Work',
    2:'school',
    3:'escort',
    4:'othmaint',
    5:'shopping',
    6:'eatout',
    7:'social',
    10: 'othmaint'}

    df['tour_type'] = df['pdpurp'].map(purp_map)

    # Tour category based on tour type
    df['tour_category'] = 'non_mandatory'
    df.loc[df['tour_type'].isin(['Work','school']),'tour_category'] = 'mandatory'

    df.rename(columns={
        'totaz': 'origin',
        'tdtaz': 'destination'
    }, inplace=True)

    df['start'] = np.floor(df['tlvorig']/60)
    df['end'] = np.floor(df['tardest']/60)

    # assign some modes directly
    mode_map = {
        1: 'WALK',
        2: 'BIKE',
        3: 'DRIVEALONEPAY',
        4: 'SHARED2FREE',
        5: 'SHARED3FREE',
        10: 'TNC_SINGLE'
    }
    df['tour_mode'] = df['tmodetp'].map(mode_map)

    # Assign transit submodes based on PATHTYPE field

    # all walk access assumed
    df.loc[df['tpathtp']==3, 'tour_mode'] = 'WALK_LOC' # local bus, 
    df.loc[df['tpathtp']==4, 'tour_mode'] = 'WALK_HVY' # Assign light rail as heavy rail (no such thing as light rail in MTC TM1)
    df.loc[df['tpathtp']==6, 'tour_mode'] = 'WALK_COM'
    # Fix me!!!
    # NO FERRY MODE; use the EXP mode?
    df.loc[df['tpathtp']==7, 'tour_mode'] = 'WALK_EXP'  # No ferry mode...

    # Fix me!!!
    # Drop the null trips (other and school bus) for now
    df = df[-df['tour_mode'].isnull()]

    # Need to find some way to identify joint tours
    df['parent_tour_id'] = np.nan

    return df

def process_joint_tour(df, template):

    # Joint Tour
    # Find the joint tours
    # each of these tours occur more than once (assuming more than 1 person is on this same tour)
    joint_tour = 1
    for index, row in _df.iterrows():
        filter = (tour.day==row.day)&(tour.pdpurp==row.pdpurp)&(tour.topcl==row.topcl)&\
                      (tour.tdpcl==row.tdpcl)&(tour.origin==row.origin)&(tour.destination==row.destination)&\
                      (tour.tmodetp==row.tmodetp)&(tour.tpathtp==row.tpathtp)&(tour.start==row.start)&\
                      (tour.end==row.end)
        # Get total number of participatns (total number of matching tours) and assign a participant number
        # NOTE: this may need to be given a heirarchy of primary tour maker?
        participants = len(tour[filter])
        tour.loc[filter,'joint_tour'] = joint_tour
        tour.loc[filter,'participant_num'] = xrange(1,participants+1)
        joint_tour += 1

    # Use the joint_tour field to identify joint tour participants
    df = tour[-tour['joint_tour'].isnull()]
    # FIXME: not sure how participant ID varies from person ID, so just duplicate that for now
    df['participant_id'] = df['person_id']
    df = df[['person_id','tour_id','household_id','participant_num','participant_id']]

    return df


results_dict = {}
template_dict = {}

# Note: trip and joint tour files not yet available for estimation; add to this list later
for table in ['household','person','tour']:
    results_dict[table] = pd.read_csv(os.path.join(survey_input_dir,'_'+table+'.tsv'), delim_whitespace=True)
    template_dict[table] = pd.read_csv(urljoin(example_survey_dir, 'survey_'+table+'s.csv'))

####################
# Household
####################
hh = process_hh(results_dict['household'])
hh[template_dict['household'].columns].to_csv(os.path.join(output_dir,'survey_households.csv'), index=False)

####################
# Person
####################
person = process_person(results_dict['person'])
person[template_dict['person'].columns].to_csv(os.path.join(output_dir,'survey_persons.csv'), index=False)

####################
# Trip
####################
#trip = process_trip(results_dict['trip'], template_dict['trip'])
#trip[template_dict['trip'].columns].to_csv(os.path.join(output_dir,'survey_trips.csv'), index=False)

####################
# Tour
####################
tour = process_tour(results_dict['tour'], template_dict['tour'])
tour[template_dict['tour'].columns].to_csv(os.path.join(output_dir,'survey_tours.csv'), index=False)

####################
# Joint Tour
####################
#joint_tour = process_joint_tour(results_dict['joint_tour'], template_dict['joint_tour'])
#joint_tour[template_dict['joint_tour'].columns].to_csv(os.path.join(output_dir,'survey_joint_tour_participants.csv'), index=False)