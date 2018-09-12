'''
To create a table to see whether TAZs has accessibily to Westlake lightrail station
definition of "accessibility": if the station could be accissible by bus, ferry, or commuter rail
'''
import pandas as pd
import numpy as np
import h5py
output_path = 'D:/Stefan' 
SOUNDCAST_input = r'D:\Stefan\7to8.h5'
#2016_SOUNDCAST_input = r'Q:\Stefan\soundcast2016\inputs\7to8.h5'

# Pick one scenario 
my_store = h5py.File(SOUNDCAST_input, "r+")
#my_store = h5py.File(2016_SOUNDCAST_input, "r+")
# Read skim 
skim_set = my_store['Skims']
trip_fields_dict = {'bus_skim' : 'ivtwrb', 
                    'light_rail_skim' : 'ivtwrr', 
                    'ferry_skim' : 'ivtwrf', 
                    'commute_rail_skim' : 'ivtwrc'}
# Populate trip_array_dict, key is new field name, value are numpy arrays:
arrays_dict = {}
for skim_field_name, field_name in trip_fields_dict.iteritems():
         print field_name
         #array_test = np.asarray(daysim_set[field_name], dtype = "int")
         arrays_dict[skim_field_name] = np.asarray(skim_set[field_name], dtype = "int")
# Create a DataFrame from the individual arrays 
def westlake(skim_name, westlake_ID):
    df_skim = pd.DataFrame(arrays_dict[skim_name])
    my_skim = pd.DataFrame(df_skim[:][westlake_ID])
    my_skim['origin'] = my_skim.index + 1
    my_skim['destination'] = westlake_ID
    my_skim.columns = [[skim_name, 'origin', 'destination']]
    return my_skim

# Westlake lightrail station TAZ is 502
# bus time from all other TAZ to Westlake 
bus_skim = westlake('bus_skim', 502)
# lightrail time from all other TAZ to Westlake
lightrail_skim = westlake('light_rail_skim', 502)
# ferry time from all other TAZ to Westlake
ferry_skim = westlake('ferry_skim', 502)
# commute rail time from all other TAZ to Westlake
commute_rail_skim = westlake('commute_rail_skim', 502)

# create binary columns to flag whether each TAZ has positive travel time for each mode
bus_skim['bus_or_not'] = 0 
bus_skim.loc[bus_skim['bus_skim'] > 0, 'bus_or_not'] = 1
ferry_skim['ferry_or_not'] = 0 
ferry_skim.loc[ferry_skim['ferry_skim'] > 0, 'ferry_or_not'] = 1
commute_rail_skim['commute_rail_or_not'] = 0 
commute_rail_skim.loc[commute_rail_skim['commute_rail_skim'] > 0, 'commute_rail_or_not'] = 1

# create another extra binary column: 0 means only light rail, 1 means also include other transit mode (bus, ferry, commute rail)
merged_transit_skim = pd.merge(bus_skim, lightrail_skim, on=['origin'])
merged_transit_skim = pd.merge(merged_transit_skim, ferry_skim, on=['origin'])
merged_transit_skim = pd.merge(merged_transit_skim, commute_rail_skim, on=['origin'])
merged_transit_skim = merged_transit_skim[['bus_skim', 'bus_or_not', 'light_rail_skim', 'ferry_skim', 'commute_rail_skim', 'origin', 'ferry_or_not']]

merged_transit_skim['other_transit_or_not'] = 0 
merged_transit_skim['other_transit_or_not'][(merged_transit_skim['bus_skim'] > 0) | (merged_transit_skim['ferry_skim'] > 0) | (merged_transit_skim['commute_rail_skim'] > 0)] = 1

# Save
merged_transit_skim.to_csv(output_path + '/test.txt')




