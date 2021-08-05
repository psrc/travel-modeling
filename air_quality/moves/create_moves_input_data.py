# MOVES input data is provided for an existing, observed year
# As of 2021, the latest available data from WA Dept. of Ecology was for year 2017
# To create input data for future years, the existing input data must be modified in key fields
# The future year files can be created by copying the existing year data and changing the year field
# This tells MOVES to use existing distributions for inputs, but will use any year-specific data internal to MOVES.
# This script will generate a number of inputs by county, year, and vehicle types, pivoting off base year data

import os
import pandas as pd

input_dir = r'Y:\Air Quality\RTP_2022\2017_data'
base_year = '2017'
year_list = ['2018','2030','2040','2050']
output_dir = r'Y:\Air Quality\RTP_2022\forecast_year_input_data'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Work through each County
county_list = ['King','Kitsap','Pierce','Snohomish','cnty_independent']

for year in year_list:
    for county in county_list:
        if not os.path.exists(os.path.join(output_dir,year,county)):
            os.makedirs(os.path.join(output_dir,year,county))
        for fname in os.listdir(os.path.join(input_dir,county)):
            df = pd.read_csv(os.path.join(input_dir,county,fname))
        
            # Update year in file name
            output_fname = fname.split(base_year)[0]+year+'.csv'

            for col in ['yearID', 'fuelYearID']:
                if col in df.columns:
                    print(fname)
                    df[col] = year

            df.to_csv(os.path.join(output_dir,year,county,output_fname),index=False)