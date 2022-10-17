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

# Inputs are 3 template files, created in MOVES for 3 vehicle type classes (light, medium, heavy)
template_dir = r'Y:\Air Quality\RTP_2022\moves_run_spec_templates'
output_dir = r'Y:\Air Quality\RTP_2022\moves_run_specs'
db_tag = '10_17_2022'    # set database tag to match input databases created
year_list = ['2018','2030','2040','2050']

county_id_dict = {
    'King': '53033',
    'Kitsap': '53035',
    'Pierce': '53053',
    'Snohomish': '53061'}

# Iterate through each year, county, and vehicle type and update XML
for year in year_list:
    for county in ['King','Kitsap','Pierce','Snohomish']:
        for veh_type in ['light','medium','heavy','transit','all']:
            et = xml.etree.ElementTree.parse(os.path.join(template_dir,'template_'+veh_type+'.mrs'))
            root = et.getroot()
            for i in root.iter('geographicselection'):
                i.set('key',county_id_dict[county])
                i.set('description',county + ' County - ' + county_id_dict[county])
            for i in root.iter('outputdatabase'):
                i.set('databasename',county+'_out_'+veh_type+'_'+year+'_'+db_tag)
            for i in root.iter('scaleinputdatabase'):
                i.set('databasename',county+'_in_'+veh_type+'_'+year+'_'+db_tag)
            for i in root.iter('description'):
                i.text = 'Puget Sound Regional \nRTP 2022 \nRegional Emissions Analysis \nAnalysis year '+year
            for order in root.iter('timespan'):
                for child in order:
                    if child.tag == 'year':
                        child.set('key',year)

            et.write(os.path.join(output_dir,county+'_'+year+'_'+veh_type+'.mrs'))

