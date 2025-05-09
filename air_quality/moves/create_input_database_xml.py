# MOVES input databases are created from the input CSV files
# A template file 

import os
import shutil
import pandas as pd
import xml.etree.ElementTree
import subprocess
import toml

def create_input_database_xml():
    config = toml.load('configuration.toml')

    for year in config["year_list"]:
        for county in config["county_id_dict"].keys():
            for veh_type in config['vehicle_type_list']:
                et = xml.etree.ElementTree.parse(os.path.join(config["working_dir"],
                                                              "moves_run_specifications_templates","batch_input_template_"+veh_type+".xml"))
                root = et.getroot()
                # Set the county name, description, database name (for MOVES inputs), and year
                for i in root.iter('geographicselection'):
                    i.set('key',config["county_id_dict"][county])
                    i.set('description',county + ' County - ' + config["county_id_dict"][county])
                for i in root.iter('databaseselection'):
                    i.set('databasename',county+'_in_'+veh_type+'_'+year+'_'+config["db_tag"])
                for order in root.iter('timespan'):
                    for child in order:
                        if child.tag == 'year':
                            child.set('key',year)


                # for all county-specific tags
                for tag in ['sourceTypeAgeDistribution','IMCoverage',
                            'roadTypeDistribution','sourceTypeYear','HPMSVtypeYear',
                            'monthVMTFraction','AVFT','zoneMonthHour','FuelUsageFraction']:
                    for i in root.iter(tag):
                        # i[0].text = 'Y:\\Air Quality\\Puget Sound Emissions Inventory (Port)\\forecast_year_input_data\\'+year+'\\'+county+'\\'+county+'_'+fname_dict[tag]+'_'+year+'.csv'
                        i[0].text = os.path.join(config["working_dir"], "forecast_year_input_data", year, county, county+"_"+config["fname_dict"][tag]+"_"+year+".csv")

                # for generic tags
                if "cnty_independent" in config['county_list']:
                    for tag in ['avgSpeedDistribution','FuelSupply','FuelFormulation',
                                'dayVMTFraction','hourVMTFraction',
                                ]:
                        for i in root.iter(tag):
                            # i[0].text = 'Y:\\Air Quality\\Puget Sound Emissions Inventory (Port)\\forecast_year_input_data\\'+year+'\\cnty_independent\\'+fname_dict[tag]+year+'.csv'
                            i[0].text = os.path.join(config["working_dir"], "forecast_year_input_data", year, "cnty_independent", config["fname_dict"][tag]+"_"+year+".csv")

                # et.write(r'Y:\Air Quality\Puget Sound Emissions Inventory (Port)\batch_input_database_creation\\'+county+'_'+year+'_'+veh_type+'.xml')
                et.write(os.path.join(config["working_dir"], "batch_input_database_creation", county+'_'+year+'_'+veh_type+".xml"))

    #if create_db:
    #    for year in year_list:
    #        for county in county_id_dict.keys():
    #            for veh_type in ['light','medium','heavy','all']:
    #                xml_file = "Y:\Air Quality\RTP_2022\MOVES3\batch_input_database_creation\\"+county+"_"+year+"_"+veh_type+".xml"
    #                command = 'ant dbimporter -Dimport="'+xml_file+'"'
    #                subprocess.run(command)
        