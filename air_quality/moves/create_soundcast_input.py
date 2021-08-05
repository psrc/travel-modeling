# Compile emission rate files for use in the Soundcast databasee

import os
import pandas as pd

input_dir = r'Y:\Air Quality\RTP_2022\MOVES3\rates'
output_dir = r'T:\2021July\brice'

# Work through each County
county_list = ['King','Kitsap','Pierce','Snohomish']
year_list = ['2018','2030','2040','2050']
year_list = ['2018','2050']


df_running = pd.DataFrame()
df_start = pd.DataFrame()

for year in year_list:
    print(year)
    for county in county_list:
        #for veh_type in ['light','medium','heavy']:
         for veh_type in ['all']:
            fname = county.lower() + '_' + year + '_' + veh_type + '.csv'
            df = pd.read_csv(os.path.join(input_dir,county,fname))
            df['year'] = year
            df['county'] = county.lower()
            df['veh_type'] = veh_type
            df_running = df_running.append(df)

            fname = county.lower() + '_' + year + '_' + veh_type + '_starts.csv'
            df = pd.read_csv(os.path.join(input_dir,county,fname))            
            df['year'] = year
            df['county'] = county.lower()
            df['veh_type'] = veh_type
            #df.rename(columns={'sum(ratePerDistance)':'ratePerVehicle'}, inplace=True)
            df_start = df_start.append(df)

df_running.rename(columns={'avgSpeed': 'avgSpeedBinID'}, inplace=True)
df_running['year'] = df_running['year'].astype('int')
running_cols = ['pollutantID','roadTypeID','avgSpeedBinID','monthID','hourID','ratePerDistance','county','veh_type','year']
start_cols = ['pollutantID','processID','monthID','dayID','hourID','ratePerVehicle','county','veh_type','year']
df_running[running_cols].to_csv(os.path.join(output_dir,'running_emission_rates_by_veh_type.csv'))
df_start[start_cols].to_csv(os.path.join(output_dir,'start_emission_rates_by_veh_type.csv'))

# Compare to existing data
##df_running_new = pd.read_csv(os.path.join(output_dir,'start_emission_rates_by_veh_type.csv'))
#df_running_old = pd.read_csv(r'R:\e2projects_two\SoundCast\Inputs\db_inputs\running_emission_rates_by_veh_type.csv')

#df_running['source'] = 'new'
#df_running_old['source'] = 'old'
#df = df_running.append(df_running_old)

# Generate report that calculates the average rates within each category, before and after
