import pandas as pd
import numpy as np
import h5py
PATH = r'T:\2017March\angela\district_trips' 
DAYSIM_OUTPUTS = r'U:\stefan\Soundcast_2014_university_transit\outputs\daysim_outputs.h5'

# DAYSIM_OUTPUTS = r'U:\stefan\soundcast_2014\outputs\daysim_outputs.h5'
#TRIPLIST_OUTFILE= os.path.join(OUTPUT_PATH, 'trip_list.txt')

# Daysim outputs:
my_store = h5py.File(DAYSIM_OUTPUTS, "r+")
# Build the dataframe
def build_df(set_name, set_fields_dict):
     daysim_set = my_store[set_name]
     #Populate trip_array_dict, key is new field name, value are numpy arrays:
     arrays_dict = {}
     for FTs_field_name, field_name in set_fields_dict.iteritems():
         print field_name
         arrays_dict[FTs_field_name] = np.asarray(daysim_set[field_name], dtype = "int")
     print arrays_dict 
     #Create a DataFrame from the individual arrays 
     set_table = pd.DataFrame(arrays_dict)
     return set_table

# Get the fields we need from the trip table
trip_fields_dict = {'o_taz': 'otaz', 
                    'd_taz' : 'dtaz', 
                    'Mode' : 'mode',
                    'purpose' : 'dpurp', 
                    'deptm': 'deptm', 
                    'arrtm' : 'arrtm'}


trip_table = build_df('Trip', trip_fields_dict)
print trip_table.head()
trip_table = trip_table[trip_table['Mode'] == 6]
#validation_area = pd.read_csv(PATH + '\district_area.csv')

# Create district lookup dictionary
zone_lookup = pd.read_csv(PATH + '\zone_st_dist_lookup.csv')
zone_lookup_dict = dict(zip(zone_lookup.Scen_Node, zone_lookup.LLE_19))
# Sign District ID to TAZ
trip_table['o_dist'] = trip_table["o_taz"].map(zone_lookup_dict)
trip_table['d_dist'] = trip_table["d_taz"].map(zone_lookup_dict)
# Create matrix
district_trip_table = pd.get_dummies(trip_table.d_dist).groupby(trip_table.o_dist).apply(sum)

district_trip_table.to_csv(PATH + '\district_trip_table327.csv')

# Survey inputs:
SURVEY = r'U:\stefan\Soundcast_2014_university_transit\scripts\summarize\inputs\calibration\survey.h5'
my_store = h5py.File(SURVEY, "r+")
# update columns we need
survey_trip_fields_dict = {'o_taz': 'otaz', 
                    'd_taz' : 'dtaz', 
                    'Mode' : 'mode',
                    'purpose' : 'dpurp', 
                    'deptm': 'deptm', 
                    'arrtm' : 'arrtm',
                    'factor' : 'trexpfac'}

survey_trip_table = build_df('Trip', survey_trip_fields_dict)
survey_trip_table = survey_trip_table[survey_trip_table['Mode'] == 6]

survey_trip_table['o_dist'] = survey_trip_table["o_taz"].map(zone_lookup_dict)
survey_trip_table['d_dist'] = survey_trip_table["d_taz"].map(zone_lookup_dict)

s_sorted = survey_trip_table.groupby(['o_dist', 'd_dist'], as_index=False).sum()
district_survey_table = s_sorted.pivot(index='o_dist', columns='d_dist', values='factor').fillna(0)
district_survey_table.to_csv(PATH + '\district_survey_table327.csv')