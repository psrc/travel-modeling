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
import toml

def create_mrs_files():
    # Inputs are 3 template files, created in MOVES for 3 vehicle type classes (light, medium, heavy)
    config = toml.load('configuration.toml')

    # Iterate through each year, county, and vehicle type and update XML
    for year in config["year_list"]:
        if not os.path.exists(os.path.join(config["working_dir"],"moves_run_specifications",year)):
            os.makedirs(os.path.join(config["working_dir"],"moves_run_specifications",year))
        for county in config["county_list"]:
            if county != 'cnty_independent':
                for veh_type in config['vehicle_type_list']:
                    et = xml.etree.ElementTree.parse(os.path.join(config["working_dir"],
                                                                "moves_run_specifications_templates",'template_'+veh_type+'.mrs'))
                    root = et.getroot()
                    for i in root.iter('geographicselection'):
                        i.set('key',config["county_id_dict"][county])
                        i.set('description',county + ' County - ' + config["county_id_dict"][county])
                    for i in root.iter('outputdatabase'):
                        i.set('databasename',county+'_out_'+veh_type+'_'+year+'_'+config["db_tag"])
                    for i in root.iter('scaleinputdatabase'):
                        i.set('databasename',county+'_in_'+veh_type+'_'+year+'_'+config["db_tag"])
                    for i in root.iter('description'):
                        i.text = config['description']
                    for order in root.iter('timespan'):
                        for child in order:
                            if child.tag == 'year':
                                child.set('key',year)

                    et.write(os.path.join(config["working_dir"],"moves_run_specifications",year,county+'_'+year+'_'+veh_type+'.mrs'))

