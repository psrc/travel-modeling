# MOVES input data is provided for an existing, observed year
# As of 2021, the latest available data from WA Dept. of Ecology was for year 2017
# To create input data for future years, the existing input data must be modified in key fields
# The future year files can be created by copying the existing year data and changing the year field
# This tells MOVES to use existing distributions for inputs, but will use any year-specific data internal to MOVES.
# This script will generate a number of inputs by county, year, and vehicle types, pivoting off base year data

import os
import pandas as pd
import toml

def create_moves_input_data():
    config = toml.load('configuration.toml')

    if not os.path.exists(os.path.join(config['working_dir'],'forecast_year_input_data')):
        os.makedirs(os.path.join(config['working_dir'],'forecast_year_input_data'))

    # Work through each year and county
    for year in config['year_list']:
        for county in config["county_list"]:
            if not os.path.exists(os.path.join(config['working_dir'],'forecast_year_input_data',year,county)):
                os.makedirs(os.path.join(config['working_dir'],'forecast_year_input_data',year,county))
            for fname in os.listdir(os.path.join(config['input_dir'],county)):
                df = pd.read_csv(os.path.join(config['input_dir'],county,fname))
            
                # Update year in file name
                output_fname = fname.split(config['base_year'])[0]+year+'.csv'

                for col in ['yearID', 'fuelYearID']:
                    if col in df.columns:
                        print(fname)
                        df[col] = year

                df.to_csv(os.path.join(config['working_dir'],'forecast_year_input_data',year,county,output_fname),index=False)