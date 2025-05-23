#!/usr/bin/python
import os
import pandas as pd
import sqlalchemy


output_dir = r'Y:\Air Quality\2026_2050_RTP\fuel_economy\moves_runs\outputs'

hostname = 'localhost'
username = 'moves'
password = 'moves'

#e = sqlalchemy.create_engine('mariadb+pymysql://moves:moves@localhost:3307/king_out_medium_2050_07_19_2021')
#df = pd.read_sql('SELECT * FROM rateperdistance', e)



# Different suffixes were used for each year group's output db name
#2050: 
#db_suffix = '_01_16_21'
#2040 and 2018: 
db_suffix = '_05_19_25_NO_EVS'
# 2030 (no suffix used)
#db_suffix = ''

for year in ['2050']:
    for county in ['king']:
        _dir = os.path.join(output_dir,county.capitalize())
        if not os.path.exists(_dir):
            os.makedirs(_dir)
    #for county in ['king']:
        #for veh_type in ['light','medium','heavy']:
        # for veh_type in ['light','heavy','medium','transit']:
        for veh_type in ['light']:
            database = county + '_out_' + veh_type + '_' + year + db_suffix
            # Running emissions
            _query = "SELECT pollutantID, sourceTypeID, roadTypeID, avgSpeedBinID, hourID, dayID, monthID, linkID, ratePerDistance FROM rateperdistance GROUP BY pollutantID, sourceTypeID, roadTypeID, avgSpeedBinID, hourID, dayID, monthID, linkID"

            e = sqlalchemy.create_engine('mariadb+pymysql://moves:moves@localhost:3306/'+database)
            df = pd.read_sql(_query, con=e)

            #df = pd.read_sql(_query, con=conn)
            df.to_csv(os.path.join(output_dir,county.capitalize(),county+'_'+year+'_'+veh_type+'.csv'), index=False)

            # Start emissions
            _query = 'SELECT * FROM ratepervehicle'
            df = pd.read_sql(_query, con=e)
            df.to_csv(os.path.join(output_dir,county.capitalize(),county+'_'+year+'_'+veh_type+'_starts.csv'), index=False)