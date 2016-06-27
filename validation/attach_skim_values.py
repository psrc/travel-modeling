# This script attaches skim values to Daysim records

# Extract skim values based on Daysim attributes
import pandas as pd
import numpy as np
import h5py
from EmmeProject import *

# Hardcoded paths, yippee!

# Read the h5-formatted 2014 survey data
# Note that the trip-record tables needs a unique trip ID field
# this will need to be added to the DAT files sent by Mark Bradley.
input_data = h5py.File(r'R:\SoundCastDocuments\2014Estimation\Files_From_Mark_2014\xxxxP14\survey2014.h5')
output_dir = r'R:\SoundCastDocuments\2014Estimation\Files_From_Mark_2014\xxxxP14\skims_attached'
version_tag = 'P14'
matrix_dict_loc = r'R:\SoundCast\releases\TransportationFutures2010\inputs\skim_params\demand_matrix_dictionary.json'
working_dir = r'R:\SoundCast\releases\TransportationFutures2010\inputs'
project_dir = r'R:\SoundCast\releases\TransportationFutures2010\projects\7to8\7to8.emp'

# Are we processing a daysim or survey file? Each have slightly different formats
daysim = False
tollclass = 'nt'

# List of fields to extract from trip records
tripdict={	'Household ID': 'hhno',
            'Person Number': 'pno',
            'Tour Number': 'tour',
            'Tour Segment': 'tseg',
            'Travel Time':'travtime',
            'Travel Cost': 'travcost',
            'Travel Distance': 'travdist',
            'Mode': 'mode',
            'Origin Purpose':'opurp',
            'Destination Purpose': 'dpurp',
            'Departure Time': 'deptm',
            'Origin TAZ': 'otaz',
            'Destination TAZ': 'dtaz',
            'Arrival Time': 'arrtm',
            'Expansion Factor': 'trexpfac'}

# List of fields to extract from household records
hhdict={'Household ID': 'hhno',
        'Household Size': 'hhsize',
        'Household Vehicles': 'hhvehs',
        'Household Workers': 'hhwkrs',
        'Household Income': 'hhincome',
        'Household TAZ': 'hhtaz',
        'Expansion Factor': 'hhexpfac'}

tourdict={
	'Household ID': 'hhno',
    'Person Number': 'pno',
    'Tour Number': 'tour',
    'Travel Time':'tautotime',
    'Travel Cost': 'tautocost',
    'Travel Distance': 'tautodist',
    'Mode': 'tmodetp',
    'Destination Purpose': 'pdpurp',
    'Origin Departure Time': 'tlvorig',
    'Origin Arrival Time': 'tarorig',
    'Destination Departure Time': 'tlvdest',
    'Destination Arrival Time': 'tardest',
    'Origin TAZ': 'totaz',
    'Destination TAZ': 'tdtaz',
    'Arrival Time': 'tardest',
    'Expansion Factor': 'toexpfac'
}

persondict={
	'Household ID': 'hhno',
	'Person Number': 'pno',
	'Work TAZ': 'pwtaz',
	'Work Auto Time': 'pwautime',
	'Work Auto Distance': 'pwaudist',
	'Work Mode': 'puwmode',
	'Work Arrival Time': 'puwarrp',
	'Work Departure Time': 'puwdepp',
	'School TAZ' : 'pstaz',
	'School Auto Time': 'pstaz',
	'School Auto Distance': 'psaudist'
}

# lookup for departure time to skim times
tod_dict = {
    3: '20to5',
    4: '20to5',
    5: '5to6',
    6: '6to7',
    7: '7to8',
    8: '8to9',
    9: '9to10',
    10: '10to14',
    11: '10to14',
    12: '10to14',
    13: '10to14',
    14: '14to15',
    15: '15to16',
    16: '16to17',
    17: '17to18',
    18: '18to20',
    19: '18to20',
    20: '20to5',
    21: '20to5',
    22: '20to5',
    23: '20to5',
    24: '20to5',
    25: '20to5',
    26: '20to5'
}

# Create an ID to match skim naming method
mode_dict = {
    1: 'walk',
    2: 'bike',
    3: 'sv',
    4: 'h2',
    5: 'h3',
    6: 'tr',
    7: 'ot',
    8: 'ot',
    9: 'ot'
}



def build_df(h5file, h5table, var_dict, survey_file=False):
    ''' Convert H5 into dataframe '''
    data = {}
    if survey_file:
        # survey h5 have nested data structure, different than daysim_outputs
        for col_name, var in var_dict.iteritems():
            data[col_name] = [i[0] for i in h5file[h5table][var][:]]
    else:
        for col_name, var in var_dict.iteritems():
            data[col_name] = [i for i in h5file[h5table][var][:]]

    return pd.DataFrame(data)


def text_to_dictionary(input_filename):
	''' Convert text input to Python dictionary'''
	my_file=open(input_filename)
	my_dictionary = {}

	for line in my_file:
		k, v = line.split(':')
    	my_dictionary[eval(k)] = v.strip()

	return(my_dictionary)

def write_skims(df, skim_dict, otaz_field, dtaz_field, my_project, skim_output_file):
	'''Look up skim values from trip records and export as csv'''

	zones = my_project.current_scenario.zone_numbers
	dictZoneLookup = dict((value,index) for index,value in enumerate(zones))
	
	bikewalk_tod = '5to6'   # bike and walk are only assigned in 5to6
	distance_skim_tod = '7to8'    # distance skims don't change over time, only saved for a single time period

	output_array = []

	for i in xrange(len(df)):
		print i
		rowdata = df.iloc[i]
		rowresults = {}

		if rowdata['dephr'] == '-1':
			print 'skip'
			next

		rowresults['ID'] = rowdata['ID']
		rowresults['skimid'] = rowdata['skim_id']

		for skim_type in ['d','t','c']:

			tod = rowdata['dephr']
			
			# assign atlernate tod value for special cases
			if skim_type == 'd':
				tod = distance_skim_tod
			
			if rowdata['mode code'] in ['bike','walk']:
				tod = '5to6'
			
			rowresults['tod_orig'] = rowdata['dephr']
			rowresults['tod_pulled'] = tod

			# write results out 
			try:
				my_matrix = skim_dict[tod]['Skims'][rowdata['skim_id']+skim_type]
				# otaz=rowdata['Origin TAZ']
				# dtaz=rowdata['Destination TAZ']
				otaz = rowdata[otaz_field]
				dtaz = rowdata[dtaz_field]

				skim_value = my_matrix[dictZoneLookup[otaz]][dictZoneLookup[dtaz]]
				rowresults[skim_type] = skim_value
			# if value unavailable, keep going and assign -1 to the field
			except:
				rowresults[skim_type] = '-1'

		output_array.append(rowresults)
       
	
	# write results to a csv
	try:
		pd.DataFrame(output_array).to_csv(skim_output_file)
	except:
		print 'failed on export of output'

def fetch_skim(df_name, df, time_field, mode_field, otaz_field, dtaz_field, my_project, use_mode=False):
	"""
	Look up skim values form survey records.
	Survey fields required: 
	Household income in dollars, 
	time field (departure/arrival) in hhmm,
	optional: use standard mode for all skims (for auto distance/time skims only)

	"""

	# Filter our records with missing data for required skim fields
	df = df[df[time_field] >= 0]
	df = df[df[otaz_field] >= 0]
	df = df[df[dtaz_field] >= 0]

	# Build a lookup variable to find skim value
	matrix_dict  = text_to_dictionary(matrix_dict_loc)
	uniqueMatrices = set(matrix_dict.values())

	skim_output_file = df_name + '_skim_output.csv'

	############ Get a subsample for testing
	# df = df.iloc[0:10]

	# Use the same toll preference for all skims
	df['Toll Class'] = np.ones(len(df))

	# Convert continuous VOT to bins (0-15,15-25,25+) based on average household income

	# Note that all households with -1 (missing income) represent university students
	# These households are lumped into the lowest VOT bin 1,

	df['VOT Bin'] = pd.cut(df['Household Income'], bins=[-1,84500,108000,9999999999], right=True, 
		labels=[1,2,3], retbins=False, precision=3, include_lowest=True)

	df['VOT Bin'] = df['VOT Bin'].astype('int')

	# Remove last two digits from time field (in hhmm) to retrieve departure hour
	
	hours = np.asarray(df[time_field].astype('str').str[:-2].astype('int'))
	# pd.DataFrame(hours).to_csv('hours.csv')

	df['dephr'] = [tod_dict[hours[i]] for i in xrange(len(hours))]

	# Look up mode keyword unless using standard mode value (e.g.)
	modes = np.asarray(df[mode_field].astype('int'))
	if use_mode:
		df['mode code'] = [mode_dict[use_mode] for i in xrange(len(df))]
	else:	
		df['mode code'] = [mode_dict[modes[i]] for i in xrange(len(df))]

	# Concatenate to produce ID to use with skim tables
	# but not for walk or bike modes
	final_df = pd.DataFrame()
	for mode in np.unique(df['mode code']):
	    print "processing skim lookup ID: " + mode
	    mylen = len(df[df['mode code'] == mode])
	    tempdf = df[df['mode code'] == mode]
	    if mode not in ['walk','bike']:
	        tempdf['skim_id'] = tempdf['mode code'] + tollclass + tempdf['VOT Bin'].astype('str')
	    else:
	        tempdf['skim_id'] = tempdf['mode code']
	    final_df = final_df.append(tempdf)
	    print 'number of ' + mode + 'trips: ' + str(len(final_df))
	df = final_df; del final_df

	# Load skim data from h5 into a dictionary
	tods = set(tod_dict.values())
	skim_dict = {}
	for tod in tods:
	    contents = h5py.File(working_dir + r'/'+ tod + '.h5')
	    skim_dict[tod] = contents


	# If the skim output file doesn't already exist, create it
	# if not os.path.isfile(skim_output_file):
	write_skims(df, skim_dict, otaz_field, dtaz_field, my_project, skim_output_file)


	# join skim data to original .dat files
	# Attach trip-level skim data to person records

def process_person_skims(tour, person, hh):
	"""

	"""
	# Add person and HH level data to trip records
	tour_per = pd.merge(tour,person, on=['Household ID','Person Number'], how='left')
	# tour_per = pd.merge(tour_per,hh[['Household ID','Household Income', 'Household TAZ']],
	# 	on='Household ID',how='left')

	tour_per.to_csv('out.csv')

	# Use tour to get work 
	# Get work tours 
	work_tours = tour_per[tour_per['Destination Purpose'] == 1]

	# Fill fields for usual wor mode and times
	work_tours['Work Mode'] = work_tours['Mode']
	work_tours['Work Arrival Time'] = work_tours['Destination Arrival Time']
	work_tours['Work Departure Time'] = work_tours['Destination Departure Time']

	# Merge these results back into the original person file

	# drop the original Work Mode field
	person.drop(['Work Mode','Work Arrival Time', 'Work Departure Time'],axis=1, inplace=True)

	person = pd.merge(person,work_tours[['Household ID', 'Person Number', 'Work Mode', 'Work Arrival Time','Work Departure Time']],
	                    on=['Household ID','Person Number'], how='left')
	

	# Fill NA for this field with -1
	for field in ['Work Mode','Work Arrival Time', 'Work Departure Time']:
	    person[field].fillna(-1,inplace=True)

	# Get school tour info
	school_tours = tour_per[tour_per['Destination Purpose'] == 2]

	school_tours['School Arrival Time'] = school_tours['Destination Arrival Time']
	school_tours['School Departure Time'] = school_tours['Destination Departure Time']

	person = pd.merge(person,school_tours[['Household ID', 'Person Number',
		'School Arrival Time', 'School Departure Time']], 
		on=['Household ID','Person Number'], how='left')

	for field in ['School Departure Time','School Arrival Time']:
	    person[field].fillna(-1,inplace=True)

	# Attach household income and TAZ info 
	person = pd.merge(person,hh[['Household ID','Household Income','Household TAZ']],
		on='Household ID',how='left')    

	# Fill -1 income (college students) with lowest income category
	min_income = person[person['Household Income'] > 0]['Household Income'].min()
	person.ix[person['Household Income']>0,'Household Income'] = min_income
	
	# Convert fields to int
	for field in ['School Arrival Time', 'School Departure Time',
	'Work Arrival Time','Work Departure Time']:
		person[field] = person[field].astype('int')

	# Write results to CSV for new derived fields
	person.to_csv('person_skims.csv', index=False)
	# person[['Household ID','Person Number','Work Departure Time',
	# 'Work Arrival Time','Work Mode', 'Work TAZ', 'School Arrival Time', 
	# 'School Departure Time', 'School TAZ']].to_csv('person_skims.csv')

	return person

def update_records(trip,tour,person):
	"""
	Add skim value results to original survey files.
	"""

	# Load skim data
	trip_skim = pd.read_csv('trip_skim_output.csv')
	tour_skim = pd.read_csv('tour_skim_output.csv')
	person_skim = pd.read_csv('person_skims.csv')
	work_skim = pd.read_csv('work_travel_skim_output.csv')
	school_skim = pd.read_csv('school_travel_skim_output.csv')

	trip_tour_cols = {'Travel Time': 't','Travel Cost':'c','Travel Distance':'d'}
	person_cols = {'Work Mode':'Work Mode','Work Arrival Time':'Work Arrival Time','Work Departure Time':'Work Departure Time'}
	work_cols = {'Work Auto Time':'t','Work Auto Distance':'d'}
	school_cols = {'School Auto Time':'t','School Auto Distance':'d'}

	# drop skim columns from the old file
	trip.drop(trip_tour_cols.keys(),axis=1,inplace=True)
	tour.drop(trip_tour_cols.keys(),axis=1,inplace=True)
	person.drop(person_cols.keys(),axis=1,inplace=True)
	person.drop(work_cols.keys(),axis=1,inplace=True)
	person.drop(school_cols.keys(),axis=1,inplace=True)

	# Join skim file to original
	df = pd.merge(trip,trip_skim[['ID','c','d','t']],on='ID',how='left')
	for colname, skimname in trip_tour_cols.iteritems():
	    df[colname] = df[skimname]
	    df.drop(skimname,axis=1,inplace=True)
	    
	    # divide skims by 100
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide all existing skim values by 100 
	    df[colname].fillna(-1,inplace=True)
	    
	    # export results
	    df.to_csv(output_dir + r'\trip.dat', sep=' ',index=False) 
	    
	# For tour
	df = pd.merge(tour,tour_skim[['ID','c','d','t']],on='ID',how='left')

	for colname, skimname in trip_tour_cols.iteritems():
	    df[colname] = df[skimname]
	    df.drop(skimname,axis=1,inplace=True)
	    
	    
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide all existing skim values by 100 
	    df[colname].fillna(-1,inplace=True)
	    
	    # export results
	    df.to_csv(output_dir + r'\tour.dat', sep=' ',index=False)

	# Person records
	df = pd.merge(person,person_skim[['ID','Work Mode','Work Arrival Time','Work Departure Time']],on='ID',how='left')
	for colname, skimname in person_cols.iteritems():
	    df[colname] = df[skimname]
	    df.drop(skimname,axis=1,inplace=True)
	    
	df = pd.merge(df,work_skim[['ID','d','t']],on='ID',how='left')
	for colname, skimname in work_cols.iteritems():
	    df[colname] = df[skimname]
	    df.drop(skimname,axis=1,inplace=True)
	    
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide skim values by 100 
	    df[colname].fillna(-1,inplace=True)

	df = pd.merge(df,school_skim[['ID','d','t']],on='ID',how='left')
	for colname, skimname in school_cols.iteritems():
	    df[colname] = df[skimname]
	    df.drop(skimname,axis=1,inplace=True)
	    
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide skim values by 100 
	    df[colname].fillna(-1,inplace=True)
	    	    
	    # export results
	    df.to_csv(output_dir + r'\prec' + version_tag + '.dat', sep=' ',index=False) 

def main():

	# Open Emme project to acquire zone numbers for lookup to skim indeces
	my_project = EmmeProject(project_dir)

	# Extract daysim data from h5 files, for specified files
	trip = build_df(h5file=input_data, h5table='Trip', var_dict=tripdict, survey_file=False)
	hh = build_df(h5file=input_data, h5table='Household', var_dict=hhdict, survey_file=False)
	tour = build_df(h5file=input_data, h5table='Tour', var_dict=tourdict, survey_file=False)
	person = build_df(h5file=input_data, h5table='Person', var_dict=persondict, survey_file=False)

	# Add unique ID fields
	person['ID'] = person['Household ID'].astype('str') + person['Person Number'].astype('str')
	trip['ID'] = trip['Household ID'].astype('str') + trip['Person Number'].astype('str') + \
	    trip['Tour Number'].astype('str') + trip['Tour Segment'].astype('str')
	tour['ID'] = tour['Household ID'].astype('str') + tour['Person Number'].astype('str') + tour['Tour Number'].astype('str')

	# Join household to trip data to get income
	trip_hh = pd.merge(trip,hh, on='Household ID')
	tour_hh = pd.merge(tour,hh, on='Household ID')

	# # Extract person-level results from trip file
	person_modified = process_person_skims(tour,person,hh)

	# Fetch trip skims based on trip departure time
	fetch_skim('trip',trip_hh, time_field='Departure Time', mode_field='Mode',
		otaz_field='Origin TAZ', dtaz_field='Destination TAZ', my_project=my_project)

	# Fetch tour skims based on tour departure time from origin
	fetch_skim('tour', tour_hh, time_field='Origin Departure Time', mode_field='Mode',
		otaz_field='Origin TAZ', dtaz_field='Destination TAZ', my_project=my_project)

	# Attach person-level skims based on home to work auto trips
	fetch_skim('work_travel', person_modified, time_field='Work Arrival Time', mode_field='Work Mode',
		otaz_field='Household TAZ', dtaz_field='Work TAZ', my_project=my_project, use_mode=3)

	# Attach person-level skims based on home to work auto trips
	fetch_skim('school_travel', person_modified, time_field='School Arrival Time', mode_field='Work Mode',
		otaz_field='Household TAZ', dtaz_field='School TAZ', my_project=my_project, use_mode=3)

	# # Attach skim results to original survey files
	update_records(trip,tour,person)

if __name__ == "__main__":
	main()