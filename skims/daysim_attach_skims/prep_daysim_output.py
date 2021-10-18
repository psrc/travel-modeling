import pandas as pd
import os
import h5py

#copydir = r'C:\Workspace\sc_2018_rtp_TEST\soundcast\outputs\daysim'
#copydir = r'C:\Workspace\sc_new_emp_SCEN4_optimistic2018\soundcast\outputs_original\daysim'
#outdir = r'C:\Workspace\sc_new_emp_SCEN4_optimistic2018\soundcast\outputs\daysim'
copydir = r'\\modelstation3\c$\Workspace\sc_new_emp_SCEN3_2018\soundcast\outputs_original\daysim'
outdir = r'\\modelstation3\c$\Workspace\sc_new_emp_SCEN3_2018\soundcast\outputs\daysim'
survey_root = r'R:\e2projects_two\2018_base_year\survey\daysim_format'

##########
# Reformat daysim outputs so columns are in an expceted order (Same as survey data for estimation)
##########

survey_dict = {'person': 'prec', 'person_day' : 'pday', 'household': 'hrec','household_day': 'hday', 'trip': 'trip', 'tour': 'tour'}
for fname in ['tour','person','person_day','household','household_day','trip']:
#for fname in ['trip']:
    print(fname)
    df = pd.read_csv(os.path.join(copydir,'_'+fname+'.tsv'), sep='\t')
    #for col in df.columns:
    #    print(col)
    #    df[col] = df[col].astype('str')
    # Load survey file
    df_survey = pd.read_csv(os.path.join(survey_root, survey_dict[fname]+'P17.csv'),sep=',')
    if 'Unnamed: 0' in df.columns:
        print('dropping')
        df = df.drop('Unnamed: 0', axis=1)
    #if len(df[''])
    # Reorder columns to match survey file
    df = df[df_survey.columns]
    df.to_csv(os.path.join(outdir,'_'+fname+'.tsv'),sep='\t', index=False)

##########
# Write the results out to h5 file
##########

# Update h5 file with new results
h5_template = h5py.File(os.path.join(copydir, 'daysim_outputs.h5'),'r')
myh5 = h5py.File(os.path.join(outdir,'daysim_outputs.h5'), 'w')

for csv_file, tablename in {'person': 'Person', 'person_day' : 'PersonDay', 'household': 'Household',
                            'household_day': 'HouseholdDay', 'trip': 'Trip', 'tour': 'Tour'}.items():
    print(csv_file)
    df = pd.read_csv(os.path.join(outdir,'_'+csv_file+'_final.tsv'), sep='\t')
    myh5.create_group(tablename)
    for col in h5_template[tablename]:
        print(col)
        if col in df.columns:
            myh5[tablename][col] = df[col]
        else:
            print('missing ' + col)

myh5.close()

##########
# Update the outputs so they include sov_ff_time req'd for summaries
# Run this with network_summary.py
##########

# Create sov_ff_time field
#daysim =  h5py.File(os.path.join(outdir,'daysim_outputs.h5'), 'r+')
#df = pd.DataFrame()
#for field in ['travtime','otaz','dtaz']:
#    df[field] = myh5['Trip'][field][:]
#df['od']=df['otaz'].astype('str')+'-'+df['dtaz'].astype('str')

#skim_vals = h5py.File(os.path.join(outdir,r'../../inputs/model/roster/20to5.h5'), 'r')['Skims']['sov_inc3t'][:]

#skim_df = pd.DataFrame(skim_vals)
## Reset index and column headers to match zone ID
#skim_df.columns = [dictZoneLookup[i] for i in skim_df.columns]
#skim_df.index = [dictZoneLookup[i] for i in skim_df.index.values]

#skim_df = skim_df.stack().reset_index()
#skim_df.columns = ['otaz','dtaz','ff_travtime']
#skim_df['od'] = skim_df['otaz'].astype('str')+'-'+skim_df['dtaz'].astype('str')
#skim_df.index = skim_df['od']

#df = df.join(skim_df,on='od', lsuffix='_cong',rsuffix='_ff')

## Write to h5, create dataset if 
#if 'sov_ff_time' in myh5['Trip'].keys():
#    del myh5['Trip']['sov_ff_time']
#try:
#    myh5['Trip'].create_dataset("sov_ff_time", data=df['ff_travtime'].values, compression='gzip')
#except:
#    print('could not write freeflow skim to h5')
#myh5.close()

## Write to TSV files
#trip_df = pd.read_csv(os.path.join(outdir,'_trip.tsv'), delim_whitespace=True)
#trip_df['od'] = trip_df['otaz'].astype('str')+'-'+trip_df['dtaz'].astype('str')
#skim_df['sov_ff_time'] = skim_df['ff_travtime']
## Delete sov_ff_time if it already exists
#if 'sov_ff_time' in trip_df.columns:
#    trip_df.drop('sov_ff_time', axis=1, inplace=True)
#skim_df = skim_df.reset_index(drop=True)
#trip_df = pd.merge(trip_df, skim_df[['od','sov_ff_time']], on='od', how='left')
#trip_df.to_csv(r'outputs/daysim/_trip.tsv', sep='\t', index=False)