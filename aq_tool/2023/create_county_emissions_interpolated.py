# These data are used to support local emissions inventories.
# PSRC provides county-level emissions and VMT estimates and local jurisdictions
# further scale results by local VMT.

import os
import toml
from sqlalchemy import create_engine
import pandas as pd
from functions import load_network_summary
from emissions import *

###############################################################
# Settings
###############################################################

# Set root of model run to analyze AND the model year

run_dir = r'N:\rtp_2026_2050\scenarios_for_sept\sc_base_year_2023\soundcast'
run_dir_future = r'N:\rtp_2026_2050\skims_2035\sc_2035_test'

model_year = '2023'    # Make sure to update this since rates used are based on this value
county_list = ['King']
annualization_factor = 320

analysis_year_list = ['2023','2024']
lower_bound_year = '2023'
upper_bound_year = '2035'
produce_emissions = True
summarize_results = True

# Bus Operators (excluding Sound Transit for now because they span multiple counties)
county_transit_operators = {
    'King': ['King County Metro'],
    'Pierce': ['Pierce Transit'],
    'Snohomish': ['Community Transit','Everett Transit'],
    'Kitsap': ['Kitsap Transit']
}

# Load run config toml files
input_settings = toml.load(os.path.join(run_dir, 'configuration', 'input_configuration.toml'))
summary_settings = toml.load(os.path.join(run_dir, 'configuration', 'summary_configuration.toml'))

def evaluate_emissions(df_network, hpms_scale, model_year, df_running_rates, df_start_rates, hh_veh_year, county_name):

    df_interzonal_vmt = calculate_interzonal_vmt(df_network, input_settings, summary_settings)
    df_interzonal = calculate_interzonal_emissions(df_interzonal_vmt, df_running_rates)

    # Load intrazonal trips for zones in the area
    df_iz = pd.read_csv(os.path.join(run_dir,r'outputs\network\iz_vol.csv'))

    # Get TAZ/county overlay
    # select only county desired
    df_intrazonal_vmt = calculate_intrazonal_vmt(df_iz, conn)

    df_intrazonal_vmt = df_intrazonal_vmt[df_intrazonal_vmt['geog_name'] == county_name]

    df_intrazonal = calculate_intrazonal_emissions(df_intrazonal_vmt, df_running_rates)

    start_emissions_df = calculate_start_emissions_county(conn, hh_veh_year, df_start_rates, df_bus_veh)
    start_emissions_df = start_emissions_df[start_emissions_df['county'] == county_name.lower()]

    # Write all results to file
    return df_intrazonal, df_interzonal, start_emissions_df

    # df_intrazonal.to_csv(os.path.join(output_dir,'intrazonal_'+county_name+'.csv'))
    # df_interzonal.to_csv(os.path.join(output_dir,'interzonal_'+county_name+'.csv'))
    # start_emissions_df.to_csv(os.path.join(output_dir,'starts_'+county_name+'.csv'))

def process_results(df_interzonal, df_intrazonal, start_emissions_df):

    df_inter_group = df_interzonal.groupby(['pollutantID','detailed_veh_type']).sum()[['tons_tot','vmt']].reset_index()
    df_inter_group.rename(columns={'tons_tot': 'interzonal_tons', 
                                'vmt': 'interzonal_vmt',
                                'detailed_veh_type': 'veh_type'}, inplace=True)
    df_intra_group = df_intrazonal.groupby(['pollutantID','detailed_veh_type']).sum()[['tons_tot','vmt']].reset_index()
    df_intra_group.rename(columns={'tons_tot': 'intrazonal_tons', 
                                'vmt': 'intrazonal_vmt',
                                'detailed_veh_type': 'veh_type'}, inplace=True)
    df_start_group = start_emissions_df.groupby(['pollutantID','veh_type']).sum()[['start_tons']].reset_index()

    running_df = pd.merge(df_inter_group, df_intra_group, how='left').fillna(0)
    running_df = finalize_emissions(running_df, col_suffix="")
    running_df.loc[~running_df['pollutantID'].isin(['PM','PM10','PM25']),'pollutantID'] = running_df[~running_df['pollutantID'].isin(['PM','PM10','PM25'])]['pollutantID'].astype('int')
    running_df['pollutant_name'] = running_df['pollutantID'].astype('int', errors='ignore').astype('str').map(pollutant_map)
    running_df['running_daily_tons'] = running_df['interzonal_tons']+running_df['intrazonal_tons']
    running_df['daily_vmt_total'] = running_df['interzonal_vmt']+running_df['intrazonal_vmt']
    running_df = running_df[['pollutantID','pollutant_name','veh_type','intrazonal_vmt','interzonal_vmt','daily_vmt_total','intrazonal_tons','interzonal_tons','running_daily_tons']]

    start_df = finalize_emissions(df_start_group, col_suffix="")
    start_df = finalize_emissions(start_df, col_suffix="")
    start_df.loc[~start_df['pollutantID'].isin(['PM','PM10','PM25']),'pollutantID'] = start_df[~start_df['pollutantID'].isin(['PM','PM10','PM25'])]['pollutantID'].astype('int')
    start_df['pollutant_name'] = start_df['pollutantID'].astype('int', errors='ignore').astype('str').map(pollutant_map)

    return running_df, start_df

###############################################################
# Script Start
###############################################################


if produce_emissions:
    hpms_df = pd.read_csv(os.path.join(os.getcwd(),'inputs/hpms_observed.csv'))
    db_dir = 'sqlite:///R:/e2projects_two/SoundCast/Inputs/dev/db/soundcast_inputs.db'

    df_taz_geog = pd.read_csv(r'R:\e2projects_two\SoundCast\Inputs\db_inputs\taz_geography.csv')

    running_emissions_fname = r'R:\e2projects_two\SoundCast\Inputs\db_inputs\running_emission_rates_by_veh_type.csv'
    start_emissions_fname = r'R:\e2projects_two\SoundCast\Inputs\db_inputs\start_emission_rates_by_veh_type.csv'
    # Calculate interzonal emissions using same approach as for regional/county emissions

    # Scale all vehicles by difference between base year and modeled total vehicles owned from auto ownership model
    df_hh_base = pd.read_csv(os.path.join(run_dir,r'outputs/daysim/_household.tsv'), delim_whitespace=True, usecols=['hhvehs','hhparcel'])
    df_hh_future = pd.read_csv(os.path.join(run_dir_future,r'outputs/daysim/_household.tsv'), delim_whitespace=True, usecols=['hhvehs','hhparcel'])

    conn = create_engine(db_dir)

    # Load running emission rates by vehicle type, for the model year
    # Get base year and future rates to be able to interpolate for an analysis year

    df_running_rates_0 = load_rates(lower_bound_year, running_emissions_fname)
    df_running_rates_1 = load_rates(upper_bound_year, running_emissions_fname)

    df_running_rates_merged = df_running_rates_0.merge(df_running_rates_1, on=['pollutantID', 'roadTypeID', 'avgSpeedBinID', 
                                                        'monthID','hourID','county','veh_type'],
                                                        suffixes=[lower_bound_year, upper_bound_year])

    df_start_rates_0 = load_start_rates(lower_bound_year, start_emissions_fname)
    df_start_rates_1 = load_start_rates(upper_bound_year, start_emissions_fname)
    df_start_rates_merged = df_start_rates_0.merge(df_start_rates_1, on=['pollutantID','county','veh_type'],
                                                        suffixes=[lower_bound_year, upper_bound_year])

    df_network_results = load_network_summary(os.path.join(run_dir, r'outputs\network\network_results.csv'))

    for county_name in county_list:
        print(county_name)
        # Select only links in the analysis county
        df_network = df_network_results[df_network_results['county'] == county_name]

        for analysis_year in analysis_year_list:

            print(analysis_year)

            output_dir = os.path.join(os.getcwd(),'output', 'interpolated', county_name, analysis_year)
            # Create outputs directory if needed
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Interpolate emissions rates if not a base year
            if analysis_year == lower_bound_year:
                df_running_rates = df_running_rates_0
                df_start_rates = df_start_rates_0
            elif analysis_year == upper_bound_year:
                df_running_rates = df_running_rates_1
                df_start_rates = df_start_rates_1
            else:
                df_running_rates = interpolate_rates(df_running_rates_merged, 'grams_per_mile', lower_bound_year, upper_bound_year, analysis_year)
                df_start_rates = interpolate_rates(df_start_rates_merged, 'ratePerVehicle', lower_bound_year, upper_bound_year, analysis_year)

            df_running_rates.to_csv(os.path.join(output_dir,'running_rates.csv'))
            df_start_rates.to_csv(os.path.join(output_dir,'start_rates.csv'))

            # Scale VMT to match HPMS variations
            base_year_vmt = hpms_df[hpms_df['year'] == int(base_year)][county_name.lower()]
            analysis_year_vmt = hpms_df[hpms_df['year'] == int(analysis_year)][county_name.lower()]
            hpms_scale = (analysis_year_vmt.values[0]/base_year_vmt.values[0])
            print(hpms_scale)

            # Interpolate vehicle ownership between base and forecast model years and scale vehicles for starts
            lower_bound_veh = df_hh_base['hhvehs'].sum()
            upper_bound_veh = df_hh_future['hhvehs'].sum()
            annual_veh_change = (upper_bound_veh-lower_bound_veh)/(int(upper_bound_year)-int(lower_bound_year))
            hh_veh_year =  lower_bound_veh + (int(analysis_year)-int(lower_bound_year))*annual_veh_change
            
            # Load number of bus vehicles in service
            # FIXME: no interpolation available for this yet, add to improvements, assume base year
            df_bus_veh = pd.read_sql('SELECT * FROM bus_vehicles WHERE year=='+base_year, con=conn)
            # Select only buses within county
            # Note that we aren't including Sound Transit because they operate thorughout the region
            # FIXME: future improvements could distribute Sound Transit vehicles by county
            df_bus_veh = df_bus_veh[df_bus_veh['agency'].isin(county_transit_operators[county_name])]

            df_intrazonal, df_interzonal, start_emissions_df = evaluate_emissions(df_network, hpms_scale, model_year, df_running_rates, df_start_rates, hh_veh_year, county_name)
            running_df, start_df = process_results(df_interzonal, df_intrazonal, start_emissions_df)

            running_df.to_csv(os.path.join(output_dir,'running_summary.csv'))
            start_df.to_csv(os.path.join(output_dir,'start_summary.csv'))

if summarize_results:

    vmt_results_df = pd.DataFrame()
    co2e_results_df = pd.DataFrame()
    start_co2e_results_df = pd.DataFrame()

    for analysis_year in analysis_year_list:

        output_dir = os.path.join(os.getcwd(),'output', 'interpolated', county_name, analysis_year)
        running_df = pd.read_csv(os.path.join(output_dir,'running_summary.csv'))
        start_df = pd.read_csv(os.path.join(output_dir,'start_summary.csv'))

        running_df.index = running_df['veh_type']

        df_vmt = running_df[running_df['pollutant_name'] == 'CO2 Equivalent'][['daily_vmt_total']].T
        df_vmt.index = [analysis_year]
        df_vmt.index.name = 'year'
        vmt_results_df = pd.concat([vmt_results_df,df_vmt])

        df_co2e = running_df[running_df['pollutant_name'] == 'CO2 Equivalent'][['running_daily_tons']].T
        df_co2e.index = [analysis_year]
        df_co2e.index.name = 'year'
        co2e_results_df = pd.concat([co2e_results_df,df_co2e])

        start_df.index = start_df['veh_type']
        df_start_co2e = start_df[start_df['pollutant_name'] == 'CO2 Equivalent'][['start_tons']].T
        df_start_co2e.index = [analysis_year]
        df_start_co2e.index.name = 'year'
        start_co2e_results_df = pd.concat([start_co2e_results_df,df_start_co2e])

final_output_dir = os.path.join(os.getcwd(),'output', 'interpolated', county_name)  
vmt_results_df.to_csv(os.path.join(final_output_dir,'running_vmt.csv'))
co2e_results_df.to_csv(os.path.join(final_output_dir,'running_co2e.csv'))
start_co2e_results_df.to_csv(os.path.join(final_output_dir,'start_co2e.csv'))
annual_start_co2e_results_df = start_co2e_results_df*annualization_factor
annual_start_co2e_results_df.to_csv(os.path.join(final_output_dir,'start_co2e_annual.csv'))