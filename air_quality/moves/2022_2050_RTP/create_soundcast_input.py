# Compile emission rate files for use in the Soundcast databasee

import os
import pandas as pd

input_dir = r'Y:\Air Quality\2026_2050_RTP\scenarios\2040_full_light_duty_EV\moves_outputs'
output_dir = r'Y:\Air Quality\2026_2050_RTP\fuel_economy\moves_runs\outputs\soundcast'

# We can process scenario outputs for targeted years only with outputs from different MOVES runs
# To only run for a full set of inputs, set scenario_def_file = None
# scenario_def_file = None
scenario_def_file = r'Y:\Air Quality\2026_2050_RTP\fuel_economy\moves_runs\inputs\scenario_definition.csv'

# Work through each County
county_list = ['King','Kitsap','Pierce','Snohomish']
year_list = ['2050']

if scenario_def_file is not None:

    df_running = pd.DataFrame()
    df_start = pd.DataFrame()

    # Allow a combination of outputs for year and county
    scen_df = pd.read_csv(scenario_def_file)
    county_list = scen_df['county'].unique().tolist()
    year_list = scen_df['year'].unique().tolist()

    # Load each line
    for index, row in scen_df.iterrows():
        # Get the year and county
        year = row['year']
        county = row['county']
        veh_type = row['veh_type']
        input_dir = row['source']

        # Check if the file exists
        fname = f"{county.lower()}_{year}_{veh_type}.csv"
        fname = os.path.join(input_dir,county,fname)
        if not os.path.exists(fname):
            print(f"File {fname} does not exist.")
            break

        # Read the file
        df = pd.read_csv(fname)
        df['year'] = year
        df['county'] = county.lower()
        df['veh_type'] = veh_type
        df_running = pd.concat([df_running,df])

        # Check if the file exists
        fname = f"{county.lower()}_{year}_{veh_type}_starts.csv"
        fname = os.path.join(input_dir,county,fname)
        if not os.path.exists(fname):
            print(f"File {fname} does not exist.")
            break    

        df = pd.read_csv(fname)
        df['year'] = year
        df['county'] = county.lower()
        df['veh_type'] = veh_type
        df_start = pd.concat([df_start,df])


else:
    df_running = pd.DataFrame()
    df_start = pd.DataFrame()

    for year in year_list:
        print(year)
        for county in county_list:
            for veh_type in ['light','medium','heavy','transit']:
            # for veh_type in ['light','medium','heavy']:
                fname = county.lower() + '_' + year + '_' + veh_type + '.csv'
                df = pd.read_csv(os.path.join(input_dir,county,fname))
                df['year'] = year
                df['county'] = county.lower()
                df['veh_type'] = veh_type
                df_running = pd.concat([df_running,df])

                fname = county.lower() + '_' + year + '_' + veh_type + '_starts.csv'
                df = pd.read_csv(os.path.join(input_dir,county,fname))            
                df['year'] = year
                df['county'] = county.lower()
                df['veh_type'] = veh_type
                #df.rename(columns={'sum(ratePerDistance)':'ratePerVehicle'}, inplace=True)
                df_start = pd.concat([df_start,df])

# Aggregate and finalize data
df_running.rename(columns={'avgSpeed': 'avgSpeedBinID'}, inplace=True)
df_running['year'] = df_running['year'].astype('int')

running_cols = ['pollutantID','roadTypeID','avgSpeedBinID','monthID','hourID','ratePerDistance','county','veh_type','year']
start_cols = ['pollutantID','processID','monthID','dayID','hourID','ratePerVehicle','county','veh_type','year']

df_running[running_cols].to_csv(os.path.join(output_dir,'running_emission_rates_by_veh_type.csv'))
df_start[start_cols].to_csv(os.path.join(output_dir,'start_emission_rates_by_veh_type.csv'))