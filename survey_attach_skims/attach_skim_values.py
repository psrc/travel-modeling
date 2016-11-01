# This script attaches skim values to Daysim records

# Extract skim values based on Daysim attributes
import pandas as pd
import numpy as np
import h5py
import glob
import math
from EmmeProject import *

# Read the h5-formatted 2014 survey data
# Note that the trip-record tables needs a unique trip id field
# this will need to be added to the DAT files sent by Mark Bradley.
input_dir = r'R:\SoundCastDocuments\2014Estimation\Files_From_Mark_2014\new_weights_10_28_16'
output_dir = r'R:\SoundCastDocuments\2014Estimation\Files_From_Mark_2014\new_weights_10_28_16\skims_attached'

# save DAT file with MAM time format conversion
output_dats = r'R:\SoundCastDocuments\2014Estimation\Files_From_Mark_2014\new_weights_10_28_16\time_converted\\'
h5output = 'survey2014_nov16.h5'
version_tag = 'P14'


matrix_dict_loc = r'R:\SoundCast\releases\TransportationFutures2010\inputs\skim_params\demand_matrix_dictionary.json'
working_dir = r'R:\SoundCast\releases\TransportationFutures2010\inputs'
project_dir = r'R:\SoundCast\releases\TransportationFutures2010\projects\8to9\8to9.emp'

tollclass = 'nt'

tripcols = ['hhno','pno','tour','tseg', 'half','travtime','travcost','travdist','mode','opurp','dpurp',
			'deptm','otaz','dtaz','arrtm','trexpfac']

hhcols = ['hhno','hhsize','hhwkrs','hhincome','hhtaz','hhexpfac']

tourcols = ['hhno','pno','tour','tautotime','tautocost','tautodist','tmodetp','pdpurp',
			'tlvorig','tarorig','tlvdest','totaz','tardest','toexpfac']

personcols = ['hhno','pno','pwtaz','pwautime','pwaudist','puwmode','puwarrp','pstaz','psaudist','psautime']

bike_speed = 10 # miles per hour
walk_speed = 3 # miles per hour

# lookup for departure time to skim times
tod_dict = {
	0: '20to5',
	1: '20to5',
	2: '20to5',
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
    23: '20to5'
}

# Create an ID to match skim naming method
mode_dict = {
    1: 'walk',
    2: 'bike',
    3: 'sv',
    4: 'h2',
    5: 'h3',
    6: 'ivtwa',    # transit in-vehicle time
    7: 'sv',
    8: 'sv',   # assign school bus as sov
    9: 'sv'    # assign other as sov
}

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

   	print 'in write_skims'

	for i in xrange(len(df)):

		print i
		rowdata = df.iloc[i]
		rowresults = {}

		if rowdata['dephr'] == -1:
			print 'skip'
			next

		rowresults['id'] = rowdata['id']
		rowresults['skimid'] = rowdata['skim_id']
		rowresults['tod_orig'] = rowdata['dephr']

		# write transit in vehicle times
		if rowdata['mode code'] == 'ivtwa':
			tod = '7to8'
			rowresults['tod_pulled'] = tod

			try:
				my_matrix = skim_dict[tod]['Skims']['ivtwa']

				otaz = rowdata[otaz_field]
				dtaz = rowdata[dtaz_field]

				skim_value = my_matrix[dictZoneLookup[otaz]][dictZoneLookup[dtaz]]
				rowresults['t'] = skim_value

				my_matrix = skim_dict[tod]['Skims']['svnt2d']
				skim_value = my_matrix[dictZoneLookup[otaz]][dictZoneLookup[dtaz]]
				rowresults['d'] = skim_value

				# fare data is only available for 6to7 time period for AM peak, or 9to10 for mid-dat (off-peak)
				# assuming all trips are peak for now
				my_matrix = skim_dict['6to7']['Skims']['mfafarbx']
				skim_value = my_matrix[dictZoneLookup[otaz]][dictZoneLookup[dtaz]]
				rowresults['c'] = skim_value

			# if value unavailable, keep going and assign -1 to the field
			except:
				rowresults['t'] = -1
				rowresults['d'] = skim_value
				rowresults['c'] = -1
		else:
			for skim_type in ['d','t','c']:

				tod = rowdata['dephr']
				
				# assign atlernate tod value for special cases
				if skim_type == 'd':
					tod = distance_skim_tod
				
				if rowdata['mode code'] in ['bike','walk']:
					tod = '5to6'

				rowresults['tod_pulled'] = tod

				# write results out 
				try:
					my_matrix = skim_dict[tod]['Skims'][rowdata['skim_id']+skim_type]

					otaz = rowdata[otaz_field]
					dtaz = rowdata[dtaz_field]

					skim_value = my_matrix[dictZoneLookup[otaz]][dictZoneLookup[dtaz]]
					rowresults[skim_type] = skim_value
				# if value unavailable, keep going and assign -1 to the field
				except:
					rowresults[skim_type] = -1

		output_array.append(rowresults)
	 
	df = pd.DataFrame(output_array)
	df.to_csv('before_bike_edits.csv')

	# For bike and walk skims, calculate distance from time skims using average speeds
	for mode, speed in {'bike': bike_speed, 'walk': walk_speed}.iteritems():
		row_index = df['skimid'] == mode
		df.loc[row_index, 'd'] =  (df['t']*speed/60).astype('int')

	# Replace all bike and walk cost skims with 0
	df.ix[df['skimid'].isin(['bike','walk']),'c'] = 0
	df.to_csv('after_bike_edits.csv')

	# write results to a csv
	try:
		df.to_csv(skim_output_file, index=False)
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

	df['VOT Bin'] = pd.cut(df['hhincome'], bins=[-1,84500,108000,9999999999], right=True, 
		labels=[1,2,3], retbins=False, precision=3, include_lowest=True)

	df['VOT Bin'] = df['VOT Bin'].astype('int')

	# Divide by 60 and round down to get hours (from minutes after midnight)
	hours = np.asarray(df[time_field].apply(lambda row: int(math.floor(row/60))))
	# hours = np.asarray(df[time_field].astype('str').str[:-2].astype('int'))
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
	# mfivtwa

	final_df = pd.DataFrame()
	for mode in np.unique(df['mode code']):
	    print "processing skim lookup ID: " + mode
	    mylen = len(df[df['mode code'] == mode])
	    tempdf = df[df['mode code'] == mode]
	    if mode not in ['walk','bike','ivtwa']:
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
	tour_per = pd.merge(tour,person, on=['hhno','pno'], how='left')
	# tour_per = pd.merge(tour_per,hh[['hhno','hhincome', 'Household TAZ']],
	# 	on='Household ID',how='left')
	tour_per['unique_id'] = tour_per.hhno.astype('str') + '_' + tour_per.pno.astype('str') 
	tour_per['unique_tour_id'] = tour_per['unique_id'] + '_' + tour_per['tour'].astype('str')
	
	# Use tour file to get work departure/arrival time and mode
	# Get work tours 
	work_tours = tour_per[tour_per['pdpurp'] == 1]

	# Fill fields for usual wor mode and times
	work_tours['puwmode'] = work_tours['tmodetp']
	work_tours['puwarrp'] = work_tours['tardest']
	work_tours['puwdepp'] = work_tours['tlvdest']

	# some people make multiple work tours; select only the tours with greatest distance
	primary_work_tour = work_tours.groupby('unique_id')['tlvdest','unique_tour_id'].max()
	work_tours = work_tours[work_tours.unique_tour_id.isin(primary_work_tour['unique_tour_id'].values)]
	# Merge these results back into the original person file

	# drop the original Work Mode field
	person.drop(['puwmode','puwarrp', 'puwdepp'],axis=1, inplace=True)

	person = pd.merge(person,work_tours[['hhno', 'pno', 'puwmode', 'puwarrp','puwdepp']],
	                    on=['hhno','pno'], how='left')
	
	# person.to_csv('out.csv')

	# Fill NA for this field with -1

	for field in ['puwmode','puwarrp', 'puwdepp']:
	    person[field].fillna(-1,inplace=True)

	# Get school tour info
	# pusarrp and pusdepp are non-daysim variables, meaning usual arrival and departure time from school
	school_tours = tour_per[tour_per['pdpurp'] == 2]
	school_tours['pusarrp'] = school_tours['tardest']
	school_tours['pusdepp'] = school_tours['tlvdest']

	# Select a primary school trip, based on longest distance
	primary_school_tour = school_tours.groupby('unique_id')['tlvdest','unique_tour_id'].max()
	school_tours = school_tours[school_tours.unique_tour_id.isin(primary_school_tour['unique_tour_id'].values)]

	person = pd.merge(person,school_tours[['hhno', 'pno','pusarrp', 'pusdepp']], 
		on=['hhno','pno'], how='left')

	for field in ['pusarrp','pusdepp']:
	    person[field].fillna(-1,inplace=True)

	# Attach hhincome and TAZ info 
	person = pd.merge(person,hh[['hhno','hhincome','hhtaz']],
		on='hhno',how='left')    

	# Fill -1 income (college students) with lowest income category
	min_income = person[person['hhincome'] > 0]['hhincome'].min()
	person.ix[person['hhincome']>0,'hhincome'] = min_income
	
	# Convert fields to int
	for field in ['pusarrp', 'pusdepp','puwarrp','puwdepp']:
		person[field] = person[field].astype('int')

	# Write results to CSV for new derived fields
	person.to_csv('person_skims.csv', index=False)
	# person[['hhno','pno','puwdepp',
	# 'puwarrp','Work Mode', 'Work TAZ', 'School Arrival Time', 
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

	for df in [trip_skim,tour_skim,person_skim,work_skim,school_skim]:
		df['id'] = df['id'].astype('str')

	for df in [trip,tour,person]:
		df['id'] = df['id'].astype('str')

	trip_cols = {'travtime': 't','travcost':'c','travdist':'d'}
	tour_cols = {'tautotime': 't','tautocost':'c','tautodist':'d'}
	person_cols = {'puwmode':'puwmode','puwarrp':'puwarrp','puwdepp':'puwdepp'}
	work_cols = {'pwautime':'t','pwaudist':'d'}
	school_cols = {'psautime':'t','psaudist':'d'}

	# drop skim columns from the old file
	trip.drop(trip_cols.keys(),axis=1,inplace=True)
	tour.drop(tour_cols.keys(),axis=1,inplace=True)
	person.drop(person_cols.keys(),axis=1,inplace=True)
	person.drop(work_cols.keys(),axis=1,inplace=True)
	person.drop(school_cols.keys(),axis=1,inplace=True)

	# Join skim file to original
	df = pd.merge(trip,trip_skim[['id','c','d','t']],on='id',how='left')
	for colname, skimname in trip_cols.iteritems():
	    df.to_csv('testout.csv')
	    df[colname] = df[skimname]
	    df.drop(skimname,axis=1,inplace=True)
	    
	    # divide skims by 100
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide all existing skim values by 100 
	    df[colname].fillna(-1.0,inplace=True)
	    
	    # export results
	    df.to_csv(output_dir + r'\trip' + version_tag + '.dat', sep=' ',index=False) 
	    
	# For tour
	df = pd.merge(tour,tour_skim[['id','c','d','t']],on='id',how='left')

	for colname, skimname in tour_cols.iteritems():
	    df[colname] = df[skimname]
	    # df.drop(skimname,axis=1.0,inplace=True)
	    
	    
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide all existing skim values by 100 
	    df[colname].fillna(-1.0,inplace=True)
	    
	    # export results
	    df.to_csv(output_dir + r'\tour' + version_tag + '.dat', sep=' ',index=False)

	# Person records
	df = pd.merge(person,person_skim[['id','puwmode','puwarrp','puwdepp']],on='id',how='left')
	for colname, skimname in person_cols.iteritems():
	    print skimname
	    df[colname] = df[skimname]
	    # df.drop(skimname,axis=1.0,inplace=True)
	    
	df = pd.merge(df,work_skim[['id','d','t']],on='id',how='left')
	for colname, skimname in work_cols.iteritems():
	    df[colname] = df[skimname]
	
	    
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide skim values by 100 
	    df[colname].fillna(-1.0,inplace=True)

	df.to_csv('testy.csv')
	df = df.drop(['d','t'],axis=1)
	# df

	df = pd.merge(df,school_skim[['id','d','t']],on='id',how='left')
	for colname, skimname in school_cols.iteritems():
	    df[colname] = df[skimname]
	    # df.drop(skimname,axis=1.0,inplace=True)
	    
	    df[colname] = df[df[colname]>=0][colname].ix[:]/100    # divide skim values by 100 
	    df[colname].fillna(-1.0,inplace=True)

	df = df.drop(['d','t'],axis=1)
	# export results
	df.to_csv(output_dir + r'\prec' + version_tag + '.dat', sep=' ',index=False) 

def dat_to_h5(file_list):
	group_dict={
			'hday': 'HouseholdDay',
			'hrec': 'Household',
			'pday': 'PersonDay',
			'prec': 'Person',
			'tour': 'Tour',
			'trip': 'Trip'
		}

	# Create H5 container (overwrite if exists)
	print output_dir + r'\\' + h5output
	if os.path.isfile(output_dir + r'\\' + h5output):
		os.remove(output_dir + r'\\' + h5output)
	f = h5py.File(output_dir + r'\\' + h5output, 'w')

	# Process all csv files in this directory
	for fname in file_list:
		print fname
		# Read csv data
		df = pd.read_csv(fname,sep=' ')

		df = df.fillna(-1)
		# # Create new group name based on CSV file name
		group_name = [group_dict[i] for i in group_dict.keys() if i in fname][0]
		grp = f.create_group(group_name)

		for column in df.columns:
			if column in ['travdist','travcost','travtime','trexpfac',
			'tautotime','tautocost','tautodist','toexpfac','hdexpfac'
			'pwautime','pwaudist', 'psautime','psaudist','psexpfac',
			'pdexpfac', 'hhexpfac'
			]:
				grp.create_dataset(column, data=list(df[column].astype('float64')))
			else:
				grp.create_dataset(column, data=list(df[column].astype('int32')))

		print "Added to h5 container: " + str(group_name)
	
	f.close()

def hhmm_to_mam(df,field):
    '''
    Convert time in HHMM format to minutes after midnight
    '''

    # Strip minutes and seconds fields HHMM format
    hr = df[field].astype('str').apply(lambda row: row[:len(row)-2]).astype('int')
    minute = df[field].astype('str').apply(lambda row: row[len(row)-2:]).astype('int')
    
    # Hours range from 3-27; if any are greater than 24, subtract 24 so the range goes from 0-24
    hr = pd.DataFrame(hr)
    hr.ix[hr[field] >= 24, field] = hr.ix[hr[field] >= 24, field] -24
    
    df[field] = (hr[field]*60)+minute

    return df

def main():

	# Open Emme project to acquire zone numbers for lookup to skim indeces
	my_project = EmmeProject(project_dir)

	# Load data
	trip = pd.read_csv(input_dir + r'/trip' + version_tag + '.dat', sep=' ')
	tour = pd.read_csv(input_dir + r'/tour' + version_tag + '.dat', sep=' ')
	hh = pd.read_csv(input_dir + r'/hrec' + version_tag + '.dat', sep=' ')
	person = pd.read_csv(input_dir + r'/prec' + version_tag + '.dat', sep=' ')

	# Correct time fields (from HHMM to minutes after midnight)
	# Save updated dat files
	for field in ['tlvorig','tardest','tlvdest','tarorig']:
	    tour = hhmm_to_mam(tour,field)
	tour.to_csv(output_dats + 'tour' + 'P14.dat', index=False)

	for field in ['deptm','arrtm','endacttm']:
	    trip = hhmm_to_mam(trip,field)
	trip.to_csv(output_dats + 'trip' + 'P14.dat', index=False)

	# drop any rows with -1 expansion factor
	person = person[person['psexpfac']>=0]

	# Add unique id fields 
	person['id'] = person['hhno'].astype('str') + person['pno'].astype('str')
	trip['id'] = trip['hhno'].astype('str') + trip['pno'].astype('str') + trip['tour'].astype('str') + trip['half'].astype('str') + trip['tseg'].astype('str')
	tour['id'] = tour['hhno'].astype('str') + tour['pno'].astype('str') + tour['tour'].astype('str')

	# # Join household to trip data to get income
	trip_hh = pd.merge(trip,hh, on='hhno')
	tour_hh = pd.merge(tour,hh, on='hhno')

	# # # # Extract person-level results from trip file
	person_modified = process_person_skims(tour,person,hh)

	# Fetch trip skims based on trip departure time
	fetch_skim('trip',trip_hh, time_field='deptm', mode_field='mode',
		otaz_field='otaz', dtaz_field='dtaz', my_project=my_project)

	# Fetch tour skims based on tour departure time from origin
	fetch_skim('tour', tour_hh, time_field='tlvorig', mode_field='tmodetp',
		otaz_field='totaz', dtaz_field='tdtaz', my_project=my_project)

	# Attach person-level work skims based on home to work auto trips
	fetch_skim('work_travel', person_modified, time_field='puwarrp', mode_field='puwmode',
		otaz_field='hhtaz', dtaz_field='pwtaz', my_project=my_project, use_mode=3)
	
	# Attach person-level school skims based on home to school auto trips
	# NOTE: mode is irrelevant in this case
	fetch_skim('school_travel', person_modified, time_field='pusarrp', mode_field='puwmode',
		otaz_field='hhtaz', dtaz_field='pstaz', my_project=my_project, use_mode=3)

	# Reload original person file and attach skim results	# 
	person = pd.read_csv(input_dir + r'/prec' + version_tag + '.dat', sep=' ')
	person['id'] = person['hhno'].astype('str') + person['pno'].astype('str')
	
	# Update records
	update_records(trip,tour,person)

	# Write results to h5
	write_list = ['tour','trip','prec','hrec','hday','pday']
	dat_to_h5([output_dir + r'\\' +file+version_tag+'.dat' for file in ['tour','trip','prec','hrec','hday','pday']])


if __name__ == "__main__":
	main()