import os
import pandas as pd
from emissions import finalize_emissions, pollutant_map

# Process county-level totals
county_name = 'King'
base_year = 2018
annualization_factor = 290
output_dir = os.path.join('output', county_name)
if not os.path.exists(os.path.join('output', county_name, 'hpms_trend')):
    os.makedirs(os.path.join('output', county_name, 'hpms_trend'))

df_intrazonal = pd.read_csv(os.path.join(output_dir,'intrazonal_'+county_name+'.csv'))
df_interzonal = pd.read_csv(os.path.join(output_dir,'interzonal_'+county_name+'.csv'))
start_emissions_df = pd.read_csv(os.path.join(output_dir,'starts_'+county_name+'.csv'))

df_inter_group = df_interzonal.groupby(['pollutantID','detailed_veh_type']).sum()[['tons_tot','vmt']].reset_index()
df_inter_group.rename(columns={'tons_tot': 'interzonal_tons', 
                               'vmt': 'interzonal_vmt',
                               'detailed_veh_type': 'veh_type'}, inplace=True)
df_intra_group = df_intrazonal.groupby(['pollutantID','detailed_veh_type']).sum()[['tons_tot','vmt']].reset_index()
df_intra_group.rename(columns={'tons_tot': 'intrazonal_tons', 
                               'vmt': 'intrazonal_vmt',
                               'detailed_veh_type': 'veh_type'}, inplace=True)
df_start_group = start_emissions_df.groupby(['pollutantID','veh_type']).sum()[['start_tons']].reset_index()

# FIXME: add start emissions as separate output

running_df = pd.merge(df_inter_group, df_intra_group, how='left').fillna(0)
running_df = finalize_emissions(running_df, col_suffix="")
running_df.loc[~running_df['pollutantID'].isin(['PM','PM10','PM25']),'pollutantID'] = running_df[~running_df['pollutantID'].isin(['PM','PM10','PM25'])]['pollutantID'].astype('int')
running_df['pollutant_name'] = running_df['pollutantID'].astype('int', errors='ignore').astype('str').map(pollutant_map)
running_df['running_daily_tons'] = running_df['interzonal_tons']+running_df['intrazonal_tons']
running_df['daily_vmt_total'] = running_df['interzonal_vmt']+running_df['intrazonal_vmt']
running_df = running_df[['pollutantID','pollutant_name','veh_type','intrazonal_vmt','interzonal_vmt','daily_vmt_total','intrazonal_tons','interzonal_tons','running_daily_tons']]
running_df.to_csv(os.path.join(output_dir,'running_summary.csv'))

start_df = finalize_emissions(df_start_group, col_suffix="")
start_df = finalize_emissions(start_df, col_suffix="")
start_df.loc[~start_df['pollutantID'].isin(['PM','PM10','PM25']),'pollutantID'] = start_df[~start_df['pollutantID'].isin(['PM','PM10','PM25'])]['pollutantID'].astype('int')
start_df['pollutant_name'] = start_df['pollutantID'].astype('int', errors='ignore').astype('str').map(pollutant_map)
start_df.to_csv(os.path.join(output_dir,'start_summary.csv'))

# Calculate trends using HPMS data
hpms_df = pd.read_csv(r'inputs/hpms_observed.csv')

running_df.index = running_df['veh_type']
df_vmt = running_df[running_df['pollutant_name'] == 'CO2 Equivalent'][['daily_vmt_total']].T
df_vmt.index = [base_year]
df_vmt.index.name = 'year'
df_co2e = running_df[running_df['pollutant_name'] == 'CO2 Equivalent'][['running_daily_tons']].T
df_co2e.index = [base_year]
df_co2e.index.name = 'year'
start_df.index = start_df['veh_type']
df_start_co2e = start_df[start_df['pollutant_name'] == 'CO2 Equivalent'][['start_tons']].T
df_start_co2e.index = [base_year]
df_start_co2e.index.name = 'year'

# Scale for future years using HPMS data

hpms_df = hpms_df[hpms_df['year'] >= base_year]
hpms_df.index = hpms_df['year']

for year in hpms_df['year'].unique():
    if year > 2018:
        county_scale = (hpms_df.loc[year,'king']/hpms_df.loc[base_year,'king'])
        df_vmt.loc[year, :] = df_vmt.loc[base_year,:]
        df_co2e.loc[year, :] = df_co2e.loc[base_year,:]*county_scale
        df_start_co2e.loc[year, :] = df_start_co2e.loc[base_year,:]*county_scale


df_vmt[['sov','hov2','hov3','transit','medium','heavy']].to_csv(os.path.join(output_dir,
                                                                             'hpms_trend',
                                                                             'daily_vmt_hpms_estimate.csv'))
df_co2e[['sov','hov2','hov3','transit','medium','heavy']].to_csv(os.path.join(output_dir,
                                                                              'hpms_trend',
                                                                              'daily_running_co2e_hpms_estimate.csv'))
(df_co2e[['sov','hov2','hov3','transit','medium','heavy']]*annualization_factor).to_csv(os.path.join(output_dir,
                                                                                                   'hpms_trend',
                                                                                                   'annual_running_co2e_hpms_estimate.csv'))
(df_start_co2e[['light','transit','medium','heavy']]*annualization_factor).to_csv(os.path.join(output_dir,
                                                                                             'hpms_trend',
                                                                                             'annual_start_co2e_estimate.csv'))