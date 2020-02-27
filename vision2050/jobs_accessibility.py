import os, sys
import collections
import re
import time
import pandas as pd
import numpy as np 
import inro.emme.database.emmebank as _eb
from pyproj import Proj, transform

############################################
# How to Run
############################################

# Set full run path to root of completed soundcast run
# Update path to the geo_file_name 
# Set time max to the boundary of jobs accessible (time_max = 30 sums all jobs accessible in 30 minuters or less)
# outputs will be stored in outputs\jobs_accessibility.csv of the soundcast run

run_path = r'L:\vision2050\soundcast\pugs_stc\pugs_stc_run_10.run_2019_04_04_11_39\2050'
geo_file_name = r'parcel_tract_county.csv'
time_max = 30

############################################

def assign_nodes_to_dataset(dataset, network, column_name, x_name, y_name):
    """Adds an attribute node_ids to the given dataset."""
    dataset[column_name] = network.get_node_ids(dataset[x_name].values, dataset[y_name].values)
 
def process_net_attribute(network, attr, fun, distances):
    # print "Processing %s" % attr
    newdf = None
    for dist_index, dist in distances.iteritems():        
        res_name = "%s_%s" % (re.sub("_?p$", "", attr), dist_index) # remove '_p' if present
        # print res_name
        res_name_list.append(res_name)
        aggr = network.aggregate(dist, type=fun, decay="flat", name=attr)
        if newdf is None:
            newdf = pd.DataFrame({res_name: aggr, "node_ids": aggr.index.values})
        else:
            newdf[res_name] = aggr
    return newdf

def get_weighted_jobs(household_data, new_column_name):
    for res_name in res_name_list:
          weighted_res_name = new_column_name + res_name
          household_data[weighted_res_name] = household_data[res_name]*household_data['HH_P']
          # print weighted_res_name
    return household_data

def get_average_jobs(household_data, geo_boundry, new_columns_name):
    data = household_data.groupby([geo_boundry]).sum()
    data.reset_index(inplace = True)
    for res_name in res_name_list: 
         weighted_res_name = 'HHweighted_' + res_name
         averaged_res_name = new_columns_name + res_name
         data[averaged_res_name] = data[weighted_res_name]/data['HH_P']
    return data

def get_average_jobs_transit(transit_data, geo_attr, parcel_attributes_list):
    """ Calculate the weighted average number of jobs available across a geography. """

    for attr in parcel_attributes_list: 
        # print 'process attribute: ', attr
        
        # Calculated weight values
        weighted_attr = 'HHweighted_' + attr
        transit_data[weighted_attr] = transit_data['HH_P']*transit_data[attr]
    
    # Group results by geographic defintion
    transit_data_groupby = transit_data.groupby([geo_attr]).sum()
    transit_data_groupby.reset_index(inplace = True)
    for attr in parcel_attributes_list: 
        weighted_attr = 'HHweighted_' + attr
        averaged_attr = 'HHaveraged_' + attr
        transit_data_groupby[averaged_attr] = transit_data_groupby[weighted_attr]/transit_data_groupby['HH_P']
    return transit_data_groupby

def get_average_jobs_auto(auto_data, geo_attr, parcel_attributes_list):
    """ Calculate the weighted average number of jobs available across a geography. """

    for attr in parcel_attributes_list: 
        # print 'process attribute: ', attr
        
        # Calculated weight values
        weighted_attr = 'HHweighted_' + attr
        auto_data[weighted_attr] = auto_data['HH_P']*auto_data[attr]
    
    # Group results by geographic defintion
    auto_data_groupby = auto_data.groupby([geo_attr]).sum()
    auto_data_groupby.reset_index(inplace = True)
    for attr in parcel_attributes_list: 
        weighted_attr = 'HHweighted_' + attr
        averaged_attr = 'HHaveraged_' + attr
        auto_data_groupby[averaged_attr] = auto_data_groupby[weighted_attr]/auto_data_groupby['HH_P']
    return auto_data_groupby


def get_transit_information(bank):
    """Extract transit travel times from skim matrices, between all zones"""

    # Bus and rail travel times are the sum of access, wait time, and in-vehicle times; Bus and rail have separate paths
    bus_time = bank.matrix('auxwa').get_numpy_data() + bank.matrix('twtwa').get_numpy_data() + bank.matrix('ivtwa').get_numpy_data() 
    rail_time = bank.matrix('auxwr').get_numpy_data() + bank.matrix('twtwr').get_numpy_data() + bank.matrix('ivtwr').get_numpy_data() 
    
    # Take the shortest transit time between bus or rail
    transit_time = np.minimum(bus_time, rail_time)
    transit_time = transit_time[0:3700, 0:3700]
    transit_time_df = pd.DataFrame(transit_time)
    transit_time_df['from'] = transit_time_df.index
    transit_time_df = pd.melt(transit_time_df, id_vars= 'from', value_vars=list(transit_time_df.columns[0:3700]), var_name = 'to', value_name='travel_time')

    # Join with parcel data; add 1 to get zone ID because emme matrices are indexed starting with 0
    transit_time_df['to'] = transit_time_df['to'] + 1 
    transit_time_df['from'] = transit_time_df['from'] + 1

    return transit_time_df

def get_auto_information(bank):
    """Extract auto skims between all zones"""

    # Auto time is SOV toll class 2
    auto_time = bank.matrix('h3tl1t').get_numpy_data()
    auto_time_df = pd.DataFrame(auto_time)
    auto_time_df['from'] = auto_time_df.index
    auto_time_df = pd.melt(auto_time_df, id_vars= 'from', value_vars=list(auto_time_df.columns[0:3700]), var_name = 'to', value_name='travel_time')
    auto_time_df['to'] = auto_time_df['to'] + 1 
    auto_time_df['from'] = auto_time_df['from'] + 1

    return auto_time_df


def process_transit_attribute(transit_time_data, time_max,  attr_list, origin_df, dest_df, tract_dict, county_dict, taz_dict):
    # get transit information
    transit = transit_time_data[transit_time_data.travel_time <= time_max]
    # delete transit opportunities for internal zone travel, we assume all people won't take transit if it is internal zone
    transit = transit[transit['from'] != transit['to']]
    #prepare orgin and destination information
    dest_transit = transit.merge(dest_df, left_on = 'to', right_on = 'TAZ_P', how = 'left')
    dest_transit = pd.DataFrame(dest_transit.groupby(dest_transit['from'])['EMPTOT_P'].sum())
    dest_transit.reset_index(inplace=True)
    origin_dest = origin_df.merge(dest_transit, left_on = 'taz_id', right_on = 'from', how = 'left') 
    # groupby destination information by origin geo id 
    origin_dest_emp = pd.DataFrame(origin_dest.groupby('parcel_id')[attr_list].sum())
    origin_dest_emp.reset_index(inplace=True)
    # get the origin geo level household info
    transit_hh = pd.DataFrame(origin_df.groupby('parcel_id')['HH_P'].sum())
    transit_hh.reset_index(inplace=True)
    # print '2', 'total household: ', transit_hh['HH_P'].sum()
    transit_hh_emp = transit_hh.merge(origin_dest_emp, on = 'parcel_id', how='left')
    transit_hh_emp['census_tract'] = transit_hh_emp['parcel_id'].map(tract_dict)
    transit_hh_emp['county_id'] = transit_hh_emp['parcel_id'].map(county_dict)
    transit_hh_emp['region_id'] = 1
    # Add a column for region minus kitsap
    transit_hh_emp['msa'] = 1
    transit_hh_emp.loc[transit_hh_emp['county_id'] == 35,'msa'] = 0

    return transit_hh_emp

def process_auto_attribute(auto_time_data, time_max,  attr_list, origin_df, dest_df, tract_dict, county_dict, taz_dict):
    # get auto information
    auto = auto_time_data[auto_time_data.travel_time <= time_max]
    # delete auto opportunities for internal zone travel, we assume all people won't take auto if it is internal zone
    auto = auto[auto['from'] != auto['to']]
    #prepare orgin and destination information
    dest_auto = auto.merge(dest_df, left_on = 'to', right_on = 'TAZ_P', how = 'left')
    dest_auto = pd.DataFrame(dest_auto.groupby(dest_auto['from'])['EMPTOT_P'].sum())
    dest_auto.reset_index(inplace=True)
    origin_dest = origin_df.merge(dest_auto, left_on = 'taz_id', right_on = 'from', how = 'left') 
    # groupby destination information by origin geo id 
    origin_dest_emp = pd.DataFrame(origin_dest.groupby('parcel_id')[attr_list].sum())
    origin_dest_emp.reset_index(inplace=True)
    # get the origin geo level household info
    auto_hh = pd.DataFrame(origin_df.groupby('parcel_id')['HH_P'].sum())
    auto_hh.reset_index(inplace=True)

    auto_hh_emp = auto_hh.merge(origin_dest_emp, on = 'parcel_id', how='left')
    auto_hh_emp['census_tract'] = auto_hh_emp['parcel_id'].map(tract_dict)
    auto_hh_emp['county_id'] = auto_hh_emp['parcel_id'].map(county_dict)
    auto_hh_emp['region_id'] = 1
    # Add a column for region minus kitsap
    auto_hh_emp['msa'] = 1
    auto_hh_emp.loc[auto_hh_emp['county_id'] == 35,'msa'] = 0
    
    return auto_hh_emp

def label_df(df):

    df.loc[(df['Geography'] == 1) & (df['geography_group'] == 'region'), 'Geography'] = 'Region'
    df.loc[df['Geography']==33, 'Geography'] = 'King County'
    df.loc[df['Geography']==35, 'Geography'] = 'Kitsap County'
    df.loc[df['Geography']==53, 'Geography'] = 'Pierce County'
    df.loc[df['Geography']==61, 'Geography'] = 'Snohomish County'

    df = df.drop('geography_group', axis=1)

    return df

def transit_jobs_access(geo_df, parcel_attributes_list, minority_df, time_max, geo_list, model_path, geo_boundry):
    """ Calculate weighted average numbers of jobs available to a parcel by mode, within a max distance."""
    tract_dict = geo_df.set_index(['parcel_id']).to_dict()['census_tract']
    taz_dict = geo_df.set_index(['parcel_id']).to_dict()['TAZ_P']
    county_dict = geo_df.set_index(['parcel_id']).to_dict()['county_id']

    # organize origin information
    origin_df = pd.DataFrame(geo_df.groupby(['parcel_id'])['HH_P'].sum())
    origin_df.reset_index(inplace=True)
    origin_df['taz_id'] = origin_df['parcel_id'].map(taz_dict) #need TAZ to join with transit time table 

    # organize destination information
    dest_df = pd.DataFrame(geo_df.groupby(['TAZ_P'])[parcel_attributes_list].sum())
    dest_df.reset_index(inplace=True)
    dest_df['TAZ_P'] = dest_df['TAZ_P'].astype('object')

    # extract transit travel time from emme matrices from AM time period
    bank = _eb.Emmebank(os.path.join(model_path, 'Banks/7to8/emmebank'))
    transit_time_df = get_transit_information(bank)
    transit_hh_emp = process_transit_attribute(transit_time_df, time_max, parcel_attributes_list, origin_df, dest_df, tract_dict, county_dict, taz_dict)
    print(transit_hh_emp.columns)
    # flag the minority tracts
    transit_hh_emp = transit_hh_emp.merge(minority_df, left_on = 'census_tract', right_on = 'GEOID10', how = 'left')
    print(transit_hh_emp.columns)
    # Append results to initally empty df
    df = pd.DataFrame()

    for geo in geo_list:

        average_jobs_df = get_average_jobs_transit(transit_hh_emp, geo_boundry[geo], parcel_attributes_list) 

        _df = average_jobs_df[[geo_boundry[geo]] + ['HHaveraged_EMPTOT_P']]
        _df['geography_group'] = geo
        _df.columns = ['Geography', 'Value','geography_group']
        df = df.append(_df)

    df['Grouping'] = 'Total'
    df = label_df(df)
    df['Data Item'] = 'Jobs within '+str(time_max) +'-min Transit Trip'

    return df

def auto_jobs_access(geo_df, parcel_attributes_list, minority_df, time_max, geo_list, model_path, geo_boundry):
    """ Calculate weighted average numbers of jobs available to a parcel by mode, within a max distance."""
    tract_dict = geo_df.set_index(['parcel_id']).to_dict()['census_tract']
    taz_dict = geo_df.set_index(['parcel_id']).to_dict()['TAZ_P']
    county_dict = geo_df.set_index(['parcel_id']).to_dict()['county_id']

    # organize origin information
    origin_df = pd.DataFrame(geo_df.groupby(['parcel_id'])['HH_P'].sum())
    origin_df.reset_index(inplace=True)
    origin_df['taz_id'] = origin_df['parcel_id'].map(taz_dict) #need TAZ to join with auto time table 

    # organize destination information
    dest_df = pd.DataFrame(geo_df.groupby(['TAZ_P'])[parcel_attributes_list].sum())
    dest_df.reset_index(inplace=True)
    dest_df['TAZ_P'] = dest_df['TAZ_P'].astype('object')

    # extract auto travel time from emme matrices from AM time period
    bank = _eb.Emmebank(os.path.join(model_path, 'Banks/7to8/emmebank'))
    auto_time_df = get_auto_information(bank)
    auto_hh_emp = process_auto_attribute(auto_time_df, time_max, parcel_attributes_list, origin_df, dest_df, tract_dict, county_dict, taz_dict)

    # flag the minority tracts
    auto_hh_emp = auto_hh_emp.merge(minority_df, left_on = 'census_tract', right_on = 'GEOID10', how = 'left')

    # Append results to initally empty df
    df = pd.DataFrame()

    for geo in geo_list:

        average_jobs_df = get_average_jobs_auto(auto_hh_emp, geo_boundry[geo], parcel_attributes_list) 

        _df = average_jobs_df[[geo_boundry[geo]] + ['HHaveraged_EMPTOT_P']]
        _df['geography_group'] = geo
        _df.columns = ['Geography', 'Value','geography_group']
        df = df.append(_df)

    df['Grouping'] = 'Total'
    df = label_df(df)
    df['Data Item'] = 'Jobs within '+str(time_max)+'-min Auto Trip'

    return df

def main():

    taz_geog = pd.read_csv(geo_file_name)
    county_taz = pd.read_csv(os.path.join(run_path,'scripts/summarize/inputs/county_taz.csv'))
    equity_geog = pd.read_csv(os.path.join(run_path,'scripts/summarize/inputs/equity_geog.csv'))

    ##################################
    # Calculate access to jobs
    ##################################

    # Define time buffer for transit - caclulate available jobs at this travel time or less

    geo_list = ['region', 'minority', 'poverty', 'county','msa']
    parcel_attributes_list = ['EMPTOT_P']
    
    global res_name_list
    res_name_list = []

    distances = { # miles to feet; 
                 #1: 2640, # 0.5 mile
                 1: 5280, # 1 mile
                 3: 15840 # 3 miles
                 }

    geo_boundry = {'county': 'county_id',
                   'city': 'city_id', 
                   'taz': 'TAZ_P',
                   'parcel': 'PARCELID',
                   'region': 'region_id',
                   'tract': 'census_tract',
                   'minority': 'People Of Color',
                   'poverty': 'Low Income',
                   'msa': 'msa'}

    parcel_df = pd.read_csv(os.path.join(run_path, 'inputs/scenario/landuse/parcels_urbansim.txt'), sep=' ')

    nodes = pd.DataFrame.from_csv(os.path.join(run_path,r'inputs/base_year/all_streets_nodes_2014.csv'), sep=',')
    links = pd.DataFrame.from_csv(os.path.join(run_path,r'inputs/base_year/all_streets_links_2014.csv'), sep=',', index_col=None )
    geo_df = pd.DataFrame.from_csv(geo_file_name, sep=',', index_col=None )
    minority_df = pd.read_excel(os.path.join(run_path,r'scripts/summarize/inputs/equity_populations_acs5yr.xlsx'), sheetname='acs5yr_2016')
    parcel_df = pd.merge(parcel_df, geo_df, left_on='PARCELID', right_on='parcel_id', how='left')
    geo_df = parcel_df.copy()
    parcel_df['region_id'] = 1

    df_transit = transit_jobs_access(geo_df, parcel_attributes_list, minority_df, time_max, geo_list, run_path, geo_boundry)
    df_auto = auto_jobs_access(geo_df, parcel_attributes_list, minority_df, time_max, geo_list, run_path, geo_boundry)

    # df = df_bike_walk.append(df_transit)
    df = df_transit.append(df_auto)

    # Write results to local CSV
    df.to_csv(os.path.join(run_path,'outputs/jobs_accessibility.csv'), index=False)

if __name__ == "__main__":
    main()
