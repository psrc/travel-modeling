# Convert all expanded csv files to h5

import os
import glob
import sys
import pandas as pd
import h5py

# Lookup for group name based on file name
group_dict={
	'hday': 'HouseholdDay',
	'hrec': 'Household',
	'pday': 'PersonDay',
	'prec': 'Person',
	'tour': 'Tour',
	'trip': 'Trip'
}

def main():

	# Create H5 container (overwrite if exists)
	h5name = 'survey-expanded.h5'
	if os.path.isfile(h5name):
		os.remove(h5name)
	f = h5py.File(h5name, 'w')

	# Process all csv files in this directory
	for fname in glob.glob('*.dat'):
		print fname
		# Read csv data
		df = pd.read_csv(fname,sep=' ')

		# # Create new group name based on CSV file name
		group_name = [group_dict[i] for i in group_dict.keys() if i in fname][0]
		# grp = f.create_group(group_name)

		# for column in df.columns:
		# 	if column in ['travdist','travcost','travtime', 'trexpfac',
		# 	'tautotime','tautocost','tautodist','toexpfac', 'hdexpfac'
		# 	'pwautime','pwaudist', 'psautime','psaudist,''psexpfac',
		# 	'pdexpfac', 'hhexpfac'
		# 	]:
		# 		grp.create_dataset(column, data=list(df[column].astype('float64')))
		# 	else:
		# 		grp.create_dataset(column, data=list(df[column].astype('int32')))

		# print "Added to h5 container: " + str(group_name)
	
	f.close()

if __name__=="__main__":
	main()