# MOVES input data is provided for an existing, observed year
# As of 2021, the latest available data from WA Dept. of Ecology was for year 2017
# To create input data for future years, the existing input data must be modified in key fields
# The future year files can be created by copying the existing year data and changing the year field
# This tells MOVES to use existing distributions for inputs, but will use any year-specific data internal to MOVES.
# This script will generate a number of inputs by county, year, and vehicle types, pivoting off base year data

import shutil
import os
import pandas as pd
import toml

def create_moves_input_data(config):

    if not os.path.exists(os.path.join(config['working_dir'],'forecast_year_input_data')):
        os.makedirs(os.path.join(config['working_dir'],'forecast_year_input_data'))

    # Work through each year and county
    for year in config['year_list']:
        for county in config["county_list"]+['cnty_independent']:
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

            if year != config['base_year'] and 'age_distribution_inputs' in config.keys():
                # Copy manually-generated age distribution files if available
                fname = os.path.join(config['age_distribution_inputs'],f'{county}_sourcetypeagedistribution_{year}.csv')
                if os.path.exists(fname):
                    # copy file to forecast year directory
                    shutil.copy(fname, os.path.join(config['working_dir'],'forecast_year_input_data',year,county,f'{county}_sourcetypeagedistribution_{year}.csv'))

            # Copy modified AVFT file if available
            if 'avft_file_dir' in config.keys():
                fname = os.path.join(config['avft_file_dir'],county+"_avft.csv")
                if os.path.exists(fname):
                    # copy file to forecast year directory
                    shutil.copy(fname, os.path.join(config['working_dir'],'forecast_year_input_data',year,county,f"{county}_avft_{year}.csv"))