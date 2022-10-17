# MOVES input databases are created from the input CSV files
# A template file 

import os
import shutil
import pandas as pd
import xml.etree.ElementTree
import subprocess

#create_xml = False
#create_db = True

db_tag = '10_17_2022'
year_list = ['2018','2030','2040','2050']

county_id_dict = {
    'King': '53033',
    'Kitsap': '53035',
    'Pierce': '53053',
    'Snohomish': '53061'}



for year in year_list:
    for county in county_id_dict.keys():
        for veh_type in ['light','medium','heavy','transit','all']:
            et = xml.etree.ElementTree.parse(r'Y:\Air Quality\RTP_2022\MOVES3\batch_input_database_creation\templates\batch_input_template_'+veh_type+'.xml')
            root = et.getroot()
            # Set the county name, description, database name (for MOVES inputs), and year
            for i in root.iter('geographicselection'):
                i.set('key',county_id_dict[county])
                i.set('description',county + ' County - ' + county_id_dict[county])
            for i in root.iter('databaseselection'):
                i.set('databasename',county+'_in_'+veh_type+'_'+year+'_'+db_tag)
            for order in root.iter('timespan'):
                for child in order:
                    if child.tag == 'year':
                        child.set('key',year)

            fname_dict = {'sourceTypeAgeDistribution': 'sourcetypeagedistribution',
                            'FuelUsageFraction': 'Default_fuelusagefraction',
                            'zoneMonthHour': 'Default_zonemonthhour',
                        'roadTypeDistribution': 'roadtypedistribution',
                        'sourceTypeYear': 'sourcetypeyear',
                        'HPMSVtypeYear': 'hpmsvtypeyear',
                        'monthVMTFraction': 'monthvmtfraction',
                        'IMCoverage': 'imcoverage',
                        'avgSpeedDistribution': 'Default_avgspeeddistribution_',
                        'FuelSupply': 'Region500000000_Default_fuelsupply_',
                        'FuelFormulation':'Default_fuelformulation_',
                            'AVFT': 'Default_avft_',
                            'dayVMTFraction': 'WA_dayvmtfraction_2008.csv',
                            'hourVMTFraction': 'WA_hourvmtfraction_2008.csv'}

            # for all county-specific tages
            for tag in ['sourceTypeAgeDistribution','FuelUsageFraction','zoneMonthHour',
                        'roadTypeDistribution','sourceTypeYear','HPMSVtypeYear',
                        'monthVMTFraction','IMCoverage']:
                for i in root.iter(tag):
                    i[0].text = 'Y:\\Air Quality\\RTP_2022\\forecast_year_input_data\\files\\'+year+'\\'+county+'\\'+county+'_'+fname_dict[tag]+'_'+year+'.csv'

            # for generic tags
            for tag in ['avgSpeedDistribution','FuelSupply','FuelFormulation',
                        'AVFT','dayVMTFraction','hourVMTFraction']:
                for i in root.iter(tag):
                    i[0].text = 'Y:\\Air Quality\\RTP_2022\\forecast_year_input_data\\'+year+'\\cnty_independent\\'+fname_dict[tag]+year+'.csv'

            et.write(r'Y:\Air Quality\RTP_2022\MOVES3\batch_input_database_creation\\'+county+'_'+year+'_'+veh_type+'.xml')

#if create_db:
#    for year in year_list:
#        for county in county_id_dict.keys():
#            for veh_type in ['light','medium','heavy','all']:
#                xml_file = "Y:\Air Quality\RTP_2022\MOVES3\batch_input_database_creation\\"+county+"_"+year+"_"+veh_type+".xml"
#                command = 'ant dbimporter -Dimport="'+xml_file+'"'
#                subprocess.run(command)
    