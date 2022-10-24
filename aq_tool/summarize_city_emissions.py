# Once results are available for a base year, apply observed HPMS data to 
# scale the data between a base year and a current/future year

import os, shutil
import pandas as pd
from input_configuration import base_year

rootdir = r'output\2018'
output_dir = r'output\2018\interpolations'

df_hpms = pd.read_csv('inputs/hpms_observed.csv')

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
else:
    shutil.rmtree(output_dir)
    os.makedirs(output_dir)

# Load df output
vmt_result_df = pd.DataFrame()
tons_results_df = pd.DataFrame()

for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        df = pd.read_csv(os.path.join(rootdir,file))
        city = file.split('.')[0]
        print(city)

        # All cities are from King County except for Bainbridge Island
        # FIXME: make this more generalizable
        if city != 'Bainbridge Island':
            county = 'king'
        else:
            county = 'kitsap'
        
        df['vmt'] = df['interzonal_vmt'] + df['intrazonal_vmt']
        df = df.groupby(['pollutant_name','veh_type']).sum()[['total_daily_tons','vmt']].reset_index()

        # Get list of all years beyond model base year
        future_years = df_hpms[df_hpms.year > int(base_year)].year.to_list()
        for year in future_years:
        #     
            # Get VMT scale for each year
            base_vmt = df_hpms.loc[df_hpms['year'] == int(base_year), county].values[0]
            future_vmt = df_hpms.loc[df_hpms['year'] == year, county].values[0]
            vmt_diff = (future_vmt-base_vmt)/base_vmt

            # Apply the County VMT difference between the future year and the model year to calculate local VMT impacts
            df['total_daily_tons_'+str(year)] = df['total_daily_tons'] + df['total_daily_tons']*vmt_diff
            df['vmt_'+str(year)] = df['vmt'] + df['vmt']*vmt_diff

        # Requests often ask for data beyond HPMS availability; 
        # Create extrapolation based on 2 most recent HPMS years, relative to second most recent year VMT
        vmt_hpms_latest_year = df_hpms.loc[df_hpms['year'] == future_years[-1], county].values[0]
        vmt_hpms_second_latest_year = df_hpms.loc[df_hpms['year'] == future_years[-2], county].values[0]
        extrapolation_rate = 1+((vmt_hpms_latest_year-vmt_hpms_second_latest_year)/vmt_hpms_second_latest_year)
        extrapolated_year = future_years[-1]+1

        last_hpms_year  = df_hpms['year'].max()

        df['total_daily_tons_'+str(extrapolated_year)+'*'] = df['total_daily_tons_'+str(last_hpms_year)]*extrapolation_rate 
        df['vmt_'+str(extrapolated_year)+'*'] = df['vmt_'+str(last_hpms_year)]*extrapolation_rate 

        df.rename(columns={'vmt': 'vmt_'+str(base_year), 
                           'total_daily_tons': 'total_daily_tons_'+str(base_year)}, inplace=True)
    

        # export VMT summary
        year_list = [str(base_year)]+[str(i) for i in future_years]+[str(extrapolated_year)+'*']
        df_vmt = df[['veh_type']+['vmt_' + i for i in year_list]].groupby('veh_type').first()
        df_vmt = df_vmt.reset_index()

        index_map = {'light': 1,
                    'medium': 2,
                    'heavy': 3,
                    'transit': 4}

        df_vmt['index_sort'] = df_vmt['veh_type'].map(index_map)
        df_vmt.index = df_vmt['index_sort']
        df_vmt = df_vmt.sort_index()
        df_vmt.drop('index_sort', axis=1, inplace=True)
        df_vmt.reset_index().drop('index_sort', axis=1, inplace=True)
        df_vmt['city'] = city
        vmt_result_df = vmt_result_df.append(df_vmt)
            
        # Export emissions summary
        df_tons = df[['veh_type']+['total_daily_tons_' + i for i in year_list]].groupby('veh_type').first()
        df_tons = df_tons.reset_index()

        index_map = {'light': 1,
                    'medium': 2,
                    'heavy': 3,
                    'transit': 4}

        df_tons['index_sort'] = df_tons['veh_type'].map(index_map)
        df_tons.index = df_tons['index_sort']
        df_tons = df_tons.sort_index()
        df_tons.drop('index_sort', axis=1, inplace=True)
        df_tons.reset_index().drop('index_sort', axis=1, inplace=True)
        df_tons['city'] = city
        tons_results_df = tons_results_df.append(df_tons)

vmt_result_df.to_csv(os.path.join(output_dir,'annual_city_vmt.csv'), index=False)
tons_results_df.to_csv(os.path.join(output_dir,'annual_city_tons_co2e.csv'), index=False)