import inro.emme.database.emmebank as _eb
import pandas as pd
import numpy as np
import os

#year = 2014
#model_path = r'L:\T2040\soundcast_2014'
year_path_dict = {2014 : r'L:\T2040\soundcast_2014', 2025 : r'L:\T2040\soundcast_2025', 2040 : r'L:\T2040\soundcast_2040_constrained'}
bank_tod = '7to8'
output_dir = r'R:\SoundCast\util\STOPS'

def get_skim(matrix_name, o_zone, d_zone, skim_name):
    skim = bank.matrix(matrix_name).get_numpy_data()
    skim = skim[0:o_zone, 0:d_zone]
    skim_df = pd.DataFrame(skim)
    skim_df['from'] = skim_df.index
    skim_df = pd.melt(skim_df, id_vars= 'from', value_vars=list(skim_df.columns[0:3700]), var_name = 'to', value_name=skim_name)
    skim_df['from'] = skim_df['from'] + 1
    skim_df['to'] = skim_df['to'] + 1
    return skim_df

skim_df_dict = {}
for year in year_path_dict:
    print year
    model_path = year_path_dict[year]
    print model_path
    bank = _eb.Emmebank(os.path.join(model_path, 'Banks', bank_tod, 'emmebank'))
    # drive distance
    drive_dist_df = get_skim('svtl2d', 3700, 3700, str(year)+'drive_distance')
    #drive time
    drive_time_df = get_skim('svtl2t', 3700, 3700, str(year)+'drive_time')
    #merge distance and time
    skim_df = pd.merge(drive_dist_df, drive_time_df, left_on = ['from', 'to'], right_on = ['from', 'to'], how = 'inner')
    skim_df_dict[year] = skim_df
    skim_df.to_csv(os.path.join(output_dir, 'skims_' + str(year) + '.csv'))

#merge years
skim_df_total = skim_df_dict[2014].merge(skim_df_dict[2014], on=['from', 'to']).merge(skim_df_dict[2025], on=['from', 'to']).merge(skim_df_dict[2040], on=['from', 'to'])

'''
# rename the columns if needed
list_columns = ['from', 'to', 
                'current_year_drive_distance', 'current_year_drive_time', 
                'opening_year_drive_distance', 'opening_year_drive_time', 
                '10_years_forecast_drive_distance', '10_years_forecast_drive_time', 
                '20_years_forecast_drive_distance', '20_years_forecast_drive_time']
skim_df_total.columns = list_columns
skim_df_total.to_csv(os.path.join(output_dir, 'STOPS_PATH_Auto_Skim_w_Header.csv'))
'''
skim_df_total.to_csv(os.path.join(output_dir, 'STOPS_PATH_Auto_Skim.csv'), index = False, header=False)