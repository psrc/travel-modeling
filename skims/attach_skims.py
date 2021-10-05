import os, sys
import collections
import h5py
import re
import time
import pandas as pd
import numpy as np 
import pandana as pdna
import inro.emme.database.emmebank as _eb
from pyproj import Proj, transform
#from input_configuration import base_year

start_time = time.time()
model_path = r'C:\Workspace\sc_2018_rtp\soundcast'

#### FIXME: remove nrows for full runs!

# Get trip list
df = pd.read_csv(r'C:\Workspace\sc_2018_rtp\soundcast\outputs\daysim\_trip.tsv', delim_whitespace=True)
df['id'] = range(1,len(df)+1)
#df[df['id'] == 109]

# Drop the existing skim columns
#df.drop(['travcost','travdist','travtime'], axis=1, inplace=True)
for col in ['cost','dist','time']:
    df['trav'+col] = -1

df['od'] = df['otaz'].astype('str')+'-'+df['dtaz'].astype('str')
df.index = df['od']

df['departure_hour'] = (df['deptm']).floordiv(60)

tod_dict = {
    0: '20to5',
    1: '20to5',
    2: '20to5',
    3: '20to5',
    4: '20to5',
    5: '5to6',
    6: '6to7',
    7: '7to8',
    8: '8to9',
    9: '9to10',
    10:'10to14',
    11: '10to14',
    12: '10to14',
    13: '10to14',
    14: '10to14',
    15: '15to16',
    16: '16to17',
    16: '16to17',
    17: '17to18',
    18: '18to20',
    19: '18to20',
    20: '20to5',
    21: '20to5',
    22: '20to5',
    23: '20to5',
    24: '20to5'}

df['departure_hour']= df['departure_hour'].replace(tod_dict)

results_df = pd.DataFrame()


# Import from emme_config
vot_1_max = 14.32    # VOT for User Class 1 < vot_1_max
vot_2_max = 26.64    # vot_1_max < VOT for User Class 2 < vot_2_max

df.loc[df['vot'] <= vot_1_max, 'inc_class'] = 1
df.loc[(df['vot'] > vot_1_max) & (df['vot'] <= vot_2_max), 'inc_class'] = 2
df.loc[df['vot'] > vot_2_max, 'inc_class'] = 3


mode_dict = {3: 'sov',
             4: 'hov2',
             5: 'hov3',
             9: 'tnc'}


def fetch_skim_data(bank, matrix_name, col_name):

    _matrix = bank.matrix(matrix_name).get_numpy_data()
    _matrix = _matrix[0:3700, 0:3700]
    matrix_df = pd.DataFrame(_matrix)
    matrix_df['from'] = matrix_df.index
    matrix_df = pd.melt(matrix_df, id_vars='from', value_vars=list(matrix_df.columns[0:3700]), var_name='to', value_name=col_name)

    # Join with parcel data; add 1 to get zone ID because emme matrices are indexed starting with 0
    matrix_df['to'] = matrix_df['to'] + 1 
    matrix_df['from'] = matrix_df['from'] + 1
    matrix_df['od'] = matrix_df['from'].astype('str')+'-'+matrix_df['to'].astype('str')

    return matrix_df


def update_df(target_df, target_index, update_df, update_index, col_name):

    target_df[col_name] = 0
    target_df.set_index(target_index, inplace = True)
    update_df.set_index(update_index, inplace = True)
    target_df.update(update_df)
    #target_df.reset_index(inplace = True)
    #update_df.reset_index(inplace = True)

    return target_df


# Get skim value from bank
# Iterate through time, cost, and distance
# Output will be a long df with o, D, time, cost, dist

import h5py
myh5 = h5py.File(r'C:\Workspace\sc_2018_rtp\soundcast\inputs\model\roster\7to8.h5', 'r')

def load_skim_data(skim_root_dir, tod, skim_name, col_name):
    myh5 = h5py.File(os.path.join(skim_root_dir,tod+'.h5'), 'r')
    _matrix  = myh5['Skims'][skim_name]
    _matrix = _matrix[0:3700, 0:3700]
    matrix_df = pd.DataFrame(_matrix)
    matrix_df['from'] = matrix_df.index
    matrix_df = pd.melt(matrix_df, id_vars='from', value_vars=list(matrix_df.columns[0:3700]), var_name='to', value_name=col_name)

    # Join with parcel data; add 1 to get zone ID because emme matrices are indexed starting with 0
    matrix_df['to'] = matrix_df['to'] + 1 
    matrix_df['from'] = matrix_df['from'] + 1
    matrix_df['od'] = matrix_df['from'].astype('str')+'-'+matrix_df['to'].astype('str')

    return matrix_df

#load_skim_data(skim_root_dir, tod, 'sov_inc2t', 'travtime')
#matrix_df = fetch_skim_data(bank, 'sov_inc2t', 'travtime')
# Update the index of df only once
# update the index of the matrix_df once it's pulled?

tod_list = ['5to6']
#tod_list = ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20','20to5']
for mode_val, mode_name in mode_dict.items():
    print(mode_name)
    print("--- %s seconds --- " % (time.time() - start_time))
    for inc_class in [1,2,3]:
        print("--- %s seconds --- " % (time.time() - start_time))
        print(inc_class)
        for tod in tod_list:
            print("--- %s seconds --- " % (time.time() - start_time))
            test_df= pd.DataFrame()
            _df = df[(df['mode'] == mode_val) & 
                 (df['inc_class'] == inc_class) & 
                 (df['departure_hour'] == tod)]
            bank = _eb.Emmebank(os.path.join(model_path, 'Banks/'+tod+'/emmebank'))
            print(tod)
            for skim_name, skim_id in  {'travtime': 't', 
                                        'travcost': 'c'}.items():
                matrix_df = fetch_skim_data(bank, mode_name+'_inc'+str(inc_class)+skim_id, skim_name)
                update_df(df, df['od'], matrix_df, 
                          matrix_df['od'], 
                          skim_name)


        _df = df[(df['mode'] == mode_val) & 
                 (df['inc_class'] == inc_class)]
        # Get distance from 7to8 time period for all trips (?)
        bank = _eb.Emmebank(os.path.join(model_path, 'Banks/7to8/emmebank'))
        matrix_df = fetch_skim_data(bank, mode_name+'_inc'+str(inc_class)+'d', 'travdist')
        update_df(df, df['od'], matrix_df, 
                          matrix_df['od'], 
                          skim_name)

#submode_dict = {
#    3: 'b', # bus
#    4: 'r', # light rail
#    5: 'p', # passenger ferry
#    6: 'c', # commuter rail
#    7: 'f' # ferry
#    }

#print("--- %s seconds --- TRANSIT" % (time.time() - start_time))
## Loop through transit trips
#transit_df = df[df['mode'] == 6]
##for tod in ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20']:
#for tod in ['8to9']:
#    for pathtype, mode_val in submode_dict.items():
#        _df = transit_df[transit_df['pathtype'] == pathtype]
#        if len(_df) > 0:
#            # Travel time
#            bank = _eb.Emmebank(os.path.join(model_path, 'Banks/'+tod+'/emmebank'))
#            matrix_df = fetch_skim_data(bank, 'mfivtwa'+mode_val, 'travtime')

#            df = update_df(df, df['od'], matrix_df, 
#                          matrix_df['od'], 'travtime')

#            results_df = results_df.append(_df[['id','travtime']])

#            # Travel cost
#            if tod in ['6to7','7to8','8to9','15to16','16to17','17to18','18to20']:
#               # Use peak period fares
#                skim_name = 'mfafarbx'
#                use_tod = '6to7'
                
#            else:
#                skim_name = 'mfmfarbx'
#                use_tod = '9to10'

#            bank = _eb.Emmebank(os.path.join(model_path, 'Banks/'+use_tod+'/emmebank'))
#            matrix_df = fetch_skim_data(bank, skim_name, 'travcost')
#            update_df(df, df['od'], matrix_df, 
#                          matrix_df['od'], 'travcost')


#print("--- %s seconds --- WALK" % (time.time() - start_time))
## Walk 
#walk_speed = 3
#bike_speed = 10
#_df = df[df['mode'] == 1]   # bike_walk_skim_tod
#tod = '5to6'
#bank = _eb.Emmebank(os.path.join(model_path, 'Banks/'+tod+'/emmebank'))
#matrix_df = fetch_skim_data(bank, 'mfwalkt', 'travtime')
#update_df(df, df['od'], matrix_df, 
#                matrix_df['od'], 'travtime')
#_df['travdist'] = _df['travtime']/bike_speed
#_df['travcost'] = 0
#update_df(df, df['od'], matrix_df, 
#                matrix_df['od'], 'travdist')
#update_df(df, df['od'], matrix_df, 
#                matrix_df['od'], 'travcost')

## bike
#_df = df[df['mode'] == 2]
#matrix_df = fetch_skim_data(bank, 'mfbiket', 'travtime')
#update_df(df, df['od'], matrix_df, 
#                matrix_df['od'], 'travtime')
#_df['travdist'] = _df['travtime']/bike_speed
#_df['travcost'] = 0
#update_df(df, df['od'], matrix_df, 
#                matrix_df['od'], 'travdist')
#update_df(df, df['od'], matrix_df, 
#                matrix_df['od'], 'travcost')


# Walk and bike distances are calculated assuming constant speeds
# 



# Merge results_df back to original dataframe and export

df.to_csv('output_test.csv')

# returns a melted matrix (long format)
# left join on origin/destination TAZ for each trip/TOD/income class; need time, cost, and distance (distance is only on the 7to8)

# for transit trips, iterate over the pathtype


print("--- %s seconds ---" % (time.time() - start_time))

temp = pd.read_csv(r'C:\Workspace\sc_2018_rtp\soundcast\output_test.csv')