import pandas as pd
import numpy as np
import h5py

# Bike and walk skims
mtc_skims = h5py.File(r'R:\e2projects_two\activitysim\psrc_example\skims.omx')

# Bike and walk skims
myh5 = h5py.File(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster\5to6.h5')

results_dict = {}
matrix_size = len(myh5['Skims']['sov_inc2t'])

# Assuminig DIST is centroid-centroid distance...using walk distance
results_dict['DIST'] = myh5['Skims']['walkt'][:matrix_size,:matrix_size]*(3.0/60.0) # Assuming 3 mph walk speed
results_dict['DISTBIKE'] = myh5['Skims']['biket'][:matrix_size,:matrix_size]*(10.0/60.0) # Assuming 10 mph bike speed
results_dict['DISTWALK'] = myh5['Skims']['walkt'][:matrix_size,:matrix_size]*(3.0/60.0) # Assuming 10 mph bike speed

myh5 = h5py.File(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster\6to7.h5')

for tod in ['AM','MD','PM','EV','EA']:
    for mtc_mode in ['COM', 'EXP','HVY','LOC','LRF','TRN']:
    # Fare
        # Using AM fares for all time periods for now
        results_dict['WLK_'+mtc_mode+'_WLK_FAR__'+tod] = myh5['Skims']['mfafarbx'][:matrix_size,:matrix_size]
        results_dict['WLK_'+mtc_mode+'_DRV_FAR__'+tod] = myh5['Skims']['mfafarbx'][:matrix_size,:matrix_size]
        results_dict['DRV_'+mtc_mode+'_WLK_FAR__'+tod] = myh5['Skims']['mfafarbx'][:matrix_size,:matrix_size]

myh5 = h5py.File(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster\7to8.h5')

# np.zeros(len())

zero_array = np.zeros((matrix_size,matrix_size))
# Vehicle matrices
#### DISTANCE ####
# Distance is only skimmed for once (7to8); apply to all TOD periods
for tod in ['AM','MD','PM','EV','EA']: # EA=early AM
    results_dict['SOV_DIST__'+tod] = myh5['Skims']['sov_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV2_DIST__'+tod] = myh5['Skims']['hov2_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV3_DIST__'+tod] = myh5['Skims']['hov3_inc2d'][:matrix_size,:matrix_size]
    results_dict['SOVTOLL_DIST__'+tod] = myh5['Skims']['sov_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV2TOLL_DIST__'+tod] = myh5['Skims']['hov2_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV3TOLL_DIST__'+tod] = myh5['Skims']['hov3_inc2d'][:matrix_size,:matrix_size]

# Time
    results_dict['SOV_TIME__'+tod] = myh5['Skims']['sov_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV2_TIME__'+tod] = myh5['Skims']['hov2_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV3_TIME__'+tod] = myh5['Skims']['hov3_inc2t'][:matrix_size,:matrix_size]
    results_dict['SOVTOLL_TIME__'+tod] = myh5['Skims']['sov_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV2TOLL_TIME__'+tod] = myh5['Skims']['hov2_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV3TOLL_TIME__'+tod] = myh5['Skims']['hov3_inc2t'][:matrix_size,:matrix_size]

# Cost 
# BTOLL is bridge toll
# Set this to 0 and only use the value toll (?)
    results_dict['SOV_BTOLL__'+tod] = zero_array
    results_dict['HOV2_BTOLL__'+tod] = zero_array
    results_dict['HOV3_BTOLL__'+tod] = zero_array
    results_dict['SOVTOLL_BTOLL__'+tod] = zero_array
    results_dict['HOV2TOLL_BTOLL__'+tod] = zero_array
    results_dict['HOV3TOLL_BTOLL__'+tod] = zero_array

# VTOLL is value toll, assuming a per-mile price?
#     results_dict['SOV_VTOLL__'+tod] = myh5['Skims']['sov_inc2c'][:matrix_size,:matrix_size]
#     results_dict['HOV2_VTOLL__'+tod] = myh5['Skims']['hov2_inc2c'][:matrix_size,:matrix_size]
#     results_dict['HOV3_VTOLL__'+tod] = myh5['Skims']['hov3_inc2c'][:matrix_size,:matrix_size]
    results_dict['SOVTOLL_VTOLL__'+tod] = myh5['Skims']['sov_inc2c'][:matrix_size,:matrix_size]
    results_dict['HOV2TOLL_VTOLL__'+tod] = myh5['Skims']['hov2_inc2c'][:matrix_size,:matrix_size]
    results_dict['HOV3TOLL_VTOLL__'+tod] = myh5['Skims']['hov3_inc2c'][:matrix_size,:matrix_size]


import os
import numpy as np
time_dict = {'AM': '7to8','MD': '10to14', 'PM': '17to18', 'EV': '18to20', 'EA': '5to6'}



# Averages taken from daysim outputs (see below)
# need to actually model this
access_dist = {'COM': 6.561, 'EXP': 6.948, 'HVY': 9.31, 'LOC':7.69 , 'LRF': 7.6803, 'TRN': 9.31}
access_time = {'COM': 16.195, 'EXP': 16.71, 'HVY': 20.66, 'LOC': 17.759, 'LRF': 15.892, 'TRN': 20.66}

egress_dist = {'COM': 6.338, 'EXP': 6.71, 'HVY': 9.04, 'LOC':7.41 , 'LRF': 7.321, 'TRN': 9.04}
egress_time = {'COM': 15.93, 'EXP': 15.936, 'HVY': 20.08, 'LOC': 17.479, 'LRF': 15.325, 'TRN': 20.08}

for tod, hour in time_dict.items():
    print(tod)
    print(hour)
    myh5 = h5py.File(os.path.join(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster',hour+'.h5'))

    submode_dict = {'COM':'c', 'EXP':'p', 'HVY':'r', 'LOC':'b','LRF':'f', 'TRN': 'r'}

    for mtc_mode, psrc_mode in submode_dict.items():
        print(mtc_mode)
        if mtc_mode == 'LOC':
            # Walk Access Time
            results_dict['WLK_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
            
            # Initial Wait Time
            results_dict['WLK_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_IWAIT__'+tod] = myh5['Skims']['iwtwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtwa'][:matrix_size,:matrix_size]
            
            # Total Wait Time
            results_dict['WLK_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAIT__'+tod] = myh5['Skims']['twtwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtwa'][:matrix_size,:matrix_size]
            
            # In vehicle time for Walk access/egress
            results_dict['WLK_'+mtc_mode+'_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwa'][:matrix_size,:matrix_size]
        
            # Transfer Time 
            results_dict['WLK_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_XWAIT__'+tod] = myh5['Skims']['xfrwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrwa'][:matrix_size,:matrix_size]
            
            # Boardings
            results_dict['WLK_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_BOARDS__'+tod] = myh5['Skims']['ndbwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbwa'][:matrix_size,:matrix_size]

            
        else:
            results_dict['WLK_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAUX__'+tod] = myh5['Skims']['auxw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_IWAIT__'+tod] = myh5['Skims']['iwtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAIT__'+tod] = myh5['Skims']['twtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_XWAIT__'+tod] = myh5['Skims']['xfrw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_BOARDS__'+tod] = myh5['Skims']['ndbw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbw'+psrc_mode][:matrix_size,:matrix_size]

        # In Vehicle Time
        
        results_dict['WLK_'+mtc_mode+'_DRV_TOTIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
        results_dict['DRV_'+mtc_mode+'_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
        
        # Modified In Vehicle Time
        # FIXME: look up how this is defined in TM1
        results_dict['DRV_'+mtc_mode+'_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
        results_dict['WLK_'+mtc_mode+'_DRV_KEYIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
                
        ####################
        # Drive to Transit #
        ####################
        
        # Drive access time
        results_dict['DRV_'+mtc_mode+'_WLK_DTIM__'+tod] = np.full([matrix_size,matrix_size], access_time[mtc_mode]*100) 
        results_dict['WLK_'+mtc_mode+'_DRV_DTIM__'+tod] = np.full([matrix_size,matrix_size], access_time[mtc_mode]*100) 
        
        # Drive access distance
        results_dict['DRV_'+mtc_mode+'_WLK_DDIST__'+tod] = np.full([matrix_size,matrix_size], egress_time[mtc_mode]*100) 
        results_dict['WLK_'+mtc_mode+'_DRV_DDIST__'+tod] = np.full([matrix_size,matrix_size], egress_time[mtc_mode]*100)
        
    ##### Some other random stuff
    results_dict['DRV_LRF_WLK_FERRYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_WLK_FERRYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_DRV_FERRYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_COM_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwac'][:matrix_size,:matrix_size]
    results_dict['WLK_COM_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwac'][:matrix_size,:matrix_size]
    results_dict['WLK_EXP_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwap'][:matrix_size,:matrix_size]
    results_dict['WLK_EXP_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwap'][:matrix_size,:matrix_size]
    results_dict['WLK_HVY_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwar'][:matrix_size,:matrix_size]
    results_dict['WLK_HVY_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwar'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    
    results_dict['WLK_TRN_WLK_IVT__'+tod] = myh5['Skims']['ivtwar'][:matrix_size,:matrix_size]
    results_dict['WLK_TRN_WLK_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
    results_dict['WLK_TRN_WLK_WEGR__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
    results_dict['WLK_TRN_WLK_WACC__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]

# If skim name in mtc_skims, write to h5

f = h5py.File('new.h5', 'w')
f.create_group("data")

for skim_matrix in results_dict.keys():
    if skim_matrix in mtc_skims['data'].keys():
        print(skim_matrix)
        f.create_dataset("data/"+skim_matrix, data=results_dict[skim_matrix])
f.close()