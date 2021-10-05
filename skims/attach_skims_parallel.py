import os, sys
import collections
import h5py
import re
import time
import pandas as pd
pd.options.mode.chained_assignment = None
import numpy as np 
import pandana as pdna
import inro.emme.database.emmebank as _eb
from pyproj import Proj, transform
import multiprocessing as mp
from multiprocessing import Pool
#from input_configuration import base_year

start_time = time.time()
model_path = r'C:\Workspace\sc_2018_rtp\soundcast'

#### FIXME: remove nrows for full runs!

# Get trip list
df = pd.read_csv(r'C:\Workspace\sc_2018_rtp\soundcast\outputs\daysim\_trip.tsv', delim_whitespace=True)
                 #usecols=['deptm','otaz','dtaz','mode','vot','pathtype'], nrows=10000)
df['id'] = range(1,len(df)+1)
usecols=['id','deptm','otaz','dtaz','mode','vot','pathtype']
df_orig = df.copy()
df = df[usecols]
#df[df['id'] == 109]

# Drop the existing skim columns
#df.drop(['travcost','travdist','travtime'], axis=1, inplace=True)
for col in ['cost','dist','time']:
    df['trav'+col] = -1

df['od'] = df['otaz'].astype('str')+'-'+df['dtaz'].astype('str')
df.index = df['od']

df['departure_hour'] = (df['deptm']).floordiv(60)

submode_dict = {
    3: 'b', # bus
    4: 'r', # light rail
    5: 'p', # passenger ferry
    6: 'c', # commuter rail
    7: 'f' # ferry
    }

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



# Import from emme_config
vot_1_max = 14.32    # VOT for User Class 1 < vot_1_max
vot_2_max = 26.64    # vot_1_max < VOT for User Class 2 < vot_2_max

df.loc[df['vot'] <= vot_1_max, 'inc_class'] = 1
df.loc[(df['vot'] > vot_1_max) & (df['vot'] <= vot_2_max), 'inc_class'] = 2
df.loc[df['vot'] > vot_2_max, 'inc_class'] = 3


mode_dict = {'sov': 3,
             'hov2': 4,
             'hov3': 5,
             'tnc': 9}

dict_mode ={''}


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

    target_df.loc[:,col_name] = 0
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
    matrix_df.loc[:,'from'] = matrix_df.index
    matrix_df = pd.melt(matrix_df, id_vars='from', value_vars=list(matrix_df.columns[0:3700]), var_name='to', value_name=col_name)
    matrix_df[col_name] = matrix_df[col_name]/100.0

    # Join with parcel data; add 1 to get zone ID because emme matrices are indexed starting with 0
    matrix_df.loc[:,'to'] = matrix_df['to'] + 1 
    matrix_df.loc[:,'from'] = matrix_df['from'] + 1
    matrix_df.loc[:,'od'] = matrix_df['from'].astype('str')+'-'+matrix_df['to'].astype('str')

    return matrix_df

# function that can be run in parallel
def run_auto_skims(tod):

    local_results_df = pd.DataFrame()

    for mode_name, mode_val in mode_dict.items():
        print(tod + ': ' + mode_name)
        for inc_class in [1,2,3]:
            print(tod + ': ' + str(inc_class))
            _df = df[(df['mode'] == mode_val) & 
                         (df['inc_class'] == inc_class) & 
                         (df['departure_hour'] == tod)]
            bank = _eb.Emmebank(os.path.join(model_path, 'Banks/'+tod+'/emmebank'))
            #print(tod)
            for skim_name, skim_id in  {'travtime': 't', 
                                        'travcost': 'c'}.items():
                matrix_df = fetch_skim_data(bank, mode_name+'_inc'+str(inc_class)+skim_id, skim_name)
                update_df(_df, _df['od'], matrix_df, 
                          matrix_df['od'], 
                          skim_name)
            local_results_df = local_results_df.append(_df[['id','travtime','travcost','travdist']])

    return local_results_df

def get_travdist(mode_inc):
    mode = mode_dict[mode_inc.split('_')[0]]
    inc = int(mode_inc.split('inc')[1])

    matrix_df = load_skim_data(os.path.join(model_path,r'inputs/model/roster'), '7to8', mode_inc+'d', 'travdist')

    _df = df[(df['mode'] == mode) & 
                         (df['inc_class'] == inc)]
    update_df(_df, _df['od'], matrix_df, 
                        matrix_df['od'], 
                        'travdist')
    return _df[['id','travtime','travcost','travdist']]

walk_bike_dict = {'bike': 2,
                 'walk': 1}
walk_bike_speed = {'walk': 3,
                    'bike': 10}

def compute_walk_bike(mode):
    
    _df = df[df['mode'] == walk_bike_dict[mode]]
    matrix_df = load_skim_data(os.path.join(model_path,r'inputs/model/roster'), '5to6', mode+'t', 'travtime')
    update_df(df, df['od'], matrix_df, 
                    matrix_df['od'], 'travtime')
    ###### FIXME - is this calc correct??
    _df['travdist'] = _df['travtime']/walk_bike_speed[mode]
    _df['travcost'] = 0
    update_df(_df, _df['od'], matrix_df, 
                    matrix_df['od'], 'travdist')
    update_df(_df, _df['od'], matrix_df, 
                    matrix_df['od'], 'travcost')

    return _df[['id','travtime','travcost','travdist']]



def compute_transit(tod):
    transit_df = df[(df['mode'] == 6) & (df['departure_hour'] == tod)]    # Select only transit trips within a given time period

    for pathtype, mode_val in submode_dict.items():
        _df = transit_df[transit_df['pathtype'] == pathtype]
        if len(_df) > 0:
            # Travel time
            #bank = _eb.Emmebank(os.path.join(model_path, 'Banks/'+tod+'/emmebank'))
            #matrix_df = fetch_skim_data(bank, 'mfivtwa'+mode_val, 'travtime')
            matrix_df= load_skim_data(os.path.join(model_path,r'inputs/model/roster'), tod, 'ivtwa'+mode_val, 'travtime')

            update_df(_df, _df['od'], matrix_df, 
                            matrix_df['od'], 'travtime')

            # Travel cost
            if tod in ['6to7','7to8','8to9','15to16','16to17','17to18','18to20']:
                # Use peak period fares
                skim_name = 'mfafarbx'
                use_tod = '6to7'
                
            else:
                skim_name = 'mfmfarbx'
                use_tod = '9to10'

            #bank = _eb.Emmebank(os.path.join(model_path, 'Banks/'+use_tod+'/emmebank'))
            #matrix_df = fetch_skim_data(bank, skim_name, 'travcost')
            matrix_df = load_skim_data(os.path.join(model_path,r'inputs/model/roster'), use_tod, skim_name, 'travcost')
            update_df(_df, _df['od'], matrix_df, 
                            matrix_df['od'], 'travcost')

            # FIXME: what should we use for travdist? Keep as -1 and use last iteration? not sure where daysim creates this from

            return _df[['id','travcost','travtime','travdist']]

if __name__ == '__main__':

    ########################################
    # Trip
    ########################################

    results_df = pd.DataFrame()

    # Get travcost and travtime for all auto modes
    tod_pool_list = ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20','20to5']
    p = Pool(len(tod_pool_list))
    results_df = pd.concat(p.map(run_auto_skims, tod_pool_list))
    p.close()

    print('auto_modes')
    print("--- %s seconds ---" % (time.time() - start_time))

    # We can't use a pooled process for multiple matrices inside the 7to8 period
    # but if the bank is alre
    # For these modes, get travdist which is only available in 7to8 perio
    # Create a pooled process by modes and income classes
    mode_pool_list = ['sov_inc1','sov_inc2','sov_inc3',
                      'hov2_inc1','hov2_inc2','hov2_inc3',
                      'hov3_inc1','hov3_inc2','hov3_inc3']
                      #'tnc_inc1','tnc_inc2','tnc_inc3'] FIXME: not sure what is going on with TNC skims, only have intrazonals...
    p = Pool(len(mode_pool_list))
    results_df = results_df.append(pd.concat(p.map(get_travdist, mode_pool_list)))
    p.close()

    print('auto_modes_distance')
    print("--- %s seconds ---" % (time.time() - start_time))

    # Since we appended this result onto rows that had no travdist
    results_df = results_df.groupby('id').max()
    print('auto_modes groupby')
    results_df = results_df.reset_index()    # reset index to retain the id column
    print("--- %s seconds ---" % (time.time() - start_time))

    # Compute walk and bike
    mode_pool_list = ['walk','bike']
    p = Pool(len(mode_pool_list))
    results_df = results_df.append(pd.concat(p.map(compute_walk_bike, mode_pool_list)))
    p.close()
    print('walk bike')
    print("--- %s seconds ---" % (time.time() - start_time))

    # Compute transit
    tod_pool_list = ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20']
    p = Pool(len(tod_pool_list))
    results_df = results_df.append(pd.concat(p.map(compute_transit, tod_pool_list)))
    p.close()
    print('everything')
    print("--- %s seconds ---" % (time.time() - start_time))

    # Process the results
    print(results_df)

    # join the results back to the original df and write out to file
    df_merged = df_orig.merge(results_df, how='left', on='id')
    df_merged

    ########################################
    # Tour
    ########################################



    ########################################
    # Person
    ########################################