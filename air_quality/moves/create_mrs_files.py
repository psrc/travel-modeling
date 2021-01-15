# This script creates MOVES Run Specficiation (MRS) files for a set of years and counties.
# It modifies a template MRS and updates the county, vehicle type, year, and database names for use in MOVES.
# Note that before runningthese spec files in MOVES, the input and output databases must be generated.
#
# An input database must be available for each county and year; these can be used across vehicle types without making changes.
# Create the input database in MOVES by loading all the year- and county-specific CSV data through the County Data Manager in the MOVES GUI. 
# These data can be generated from the associated script 
#       - create_moves_input_data.py
# 
# When generating the input database, be sure to follow the following convention for a given county and year
#       - county_in_year (e.g., kitsap_in_2030)
# 
# Empty output databases must also be generated before running these MRS files in MOVES.
# To generate these databases, open any existing MOVES MRS file and navigate to the the Output tab.
# In the list of databases, create the required databases at any time (no need to load new MRS files for each run)
# Use the following format:
#       -  county_year_out_vehicletype (e.g. kitsap_2030_out_light)

import os
import shutil
import pandas as pd
import xml.etree.ElementTree

# Open original file
root_dir = r'Y:\Air Quality\RTP_2022'

for year in ['2030','2040','2050']:
    for county in ['king','kitsap','pierce','snohomish']:
        et = xml.etree.ElementTree.parse(os.path.join(root_dir,county.capitalize(),county+'_2018_light.mrs'))
        root = et.getroot()
        for veh_type in ['light','medium','heavy']:
            for i in root.iter('outputdatabase'):
                i.set('databasename',county+'_'+year+'_out_'+veh_type)
            for i in root.iter('scaleinputdatabase'):
                i.set('databasename',county+'_in_'+year)
            root[0].set('description','Puget Sound Regional \nRTP 2022 \nRegional Emissions Analysis \nAnalysis year '+year)

            for order in root.iter('timespan'):
                for child in order:
                    if child.tag == 'year':
                        child.set('key',year)

            et.write(os.path.join(root_dir,'test\\'+county+'_'+year+'_'+veh_type+'.mrs'))