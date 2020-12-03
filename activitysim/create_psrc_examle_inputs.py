import pandas as pd
import numpy as np
import h5py
import os

# Household 
df_mtc = pd.read_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\original_mtc\households.csv')

hh_persons = h5py.File(r'R:\e2projects_two\SoundCast\Inputs\dev\landuse\2018\base_year\hh_and_persons.h5')
df_psrc = pd.DataFrame()
for col in hh_persons['Household'].keys():
    df_psrc[col] = hh_persons['Household'][col][:len(df_mtc)]
    
df_psrc_person = pd.DataFrame()
for col in hh_persons['Person'].keys():
    df_psrc_person[col] = hh_persons['Person'][col][:]

df_psrc = df_psrc.iloc[0:len(df_mtc)]
df_psrc_person = df_psrc_person[df_psrc_person['hhno'].isin(df_psrc['hhno'])]

# Join missing data to household file from seed HH file (PUMS)
# load_cols = ['hhnum','HHT', 'NOC', 'SERIALNO','TYPE','VEH',
#             'PUMA5','TEN','WIF']
seed_hh = pd.read_csv(r'R:\e2projects_two\SyntheticPopulation_2018\populationsim_inputs\data\seed_households.csv')


# get col list required from PUMS


# df_psrc = df_psrc.merge(syn_hh[['household_id']], left_on='hhno', right_on='household_id')
df_psrc = df_psrc.merge(seed_hh, left_on='hhno', right_on='hhnum')

df_psrc.rename(columns={'hhno': 'HHID',
                           'hhtaz': 'TAZ',
                           'hhincome': 'income',
                            'hhsize': 'PERSONS',
                           'VEH': 'VEHCIL',
                           'TYPE': 'UNITTYPE',
                        'BLD': 'BLDGSZ',
                       'PUMA': 'PUMA5',
                        'TEN':'TENURE',
                        'WIF': 'hwrkrcat'}, inplace=True)



# Houeshold income categorization number 
# Integer, 1 - 0 to 20k(-); 
# 2 - 20 to 50k;
# 3 - 50 to 100k; 
# 4 - more than 100k
df_psrc['hinccat1'] = pd.cut(df_psrc['income'], 
                                 [0,20000,50000,100000,99999999999999],
                                labels=[1,2,3,4])

df_psrc['hinccat2'] = pd.cut(df_psrc['income'], 
                                 [0,10000,20000,30000,40000,
                                  50000, 60000,75000, 100000, 99999999999999],
                                labels=[1,2,3,4,5,6,7,8,9])

# Create other categories 
# hsizecat (houeshold size category, 1, 2, 3, 4+)
df_psrc['hsizecat'] = df_psrc['PERSONS'].copy()
df_psrc.loc[df_psrc['hsizecat']  >= 4, 'hsizecat'] = 4

# From person PUMS files
# hhagecat (head of hoeshold age category)

# hfamily

# hunittype
df_psrc['hunittype'] = df_psrc['UNITTYPE'].copy()

# hNOCcat (number of children category)
df_psrc['hNOCcat'] = 0
df_psrc.loc[df_psrc['NOC'] >= 1, 'hhNOCcat'] = 1

# h0004 (int for members 0 to 4)
# h0511
# h1215
# h1617
# h1824
# h2534
# h3549
# h5064
# h6579
# h80+

age_cols = ['h004','h0511','h1215','h1617',
            'h1824','h2534','h3549','h5064',
            'h6579','h80up']
df_psrc_person['age_category'] = pd.cut(df_psrc_person['pagey'], 
                                 [-1,4,11,15,17,24,34,49,64,79,999],
                                 labels=age_cols)

df = df_psrc_person.groupby(['hhno','age_category']).size().reset_index()
# dfnew = df_psrc.copy()
for age_category in age_cols:
    _df = df.loc[df['age_category'] == age_category]
    df_psrc = df_psrc.merge(_df[['hhno',0]],how='left', left_on='HHID', right_on='hhno')
    df_psrc.drop('hhno', axis=1, inplace=True)
    df_psrc[0] = df_psrc[0].fillna(0).astype('int')
    df_psrc.rename(columns={0: age_category}, inplace=True)

# hwork_f
# hwork_p
# huniv
# hnwork
# hretire
# hpresch
# hschpred
# hschdriv
# Create a recode for employment type
df_psrc_person['mtc_worker_type'] = df_psrc_person['pptyp'].copy()
df_psrc_person['mtc_worker_type'] = df_psrc_person['mtc_worker_type'].map(
                            {1:'hwork_f',
                              2:'hwork_p',
                              5:'huniv',
                               4:'hnwork',
                               3:'hretire',
                               8:'hpresch',
                               7:'hschpred',
                               6:'hschdriv',
                              })

df = df_psrc_person.groupby(['hhno','mtc_worker_type']).size().reset_index()
mtc_worker_cats = ['hwork_f','hwork_p','huniv','hnwork','hretire','hrpresch',
                  'hschpred','hschdriv']

for worker_cat in mtc_worker_cats:
#     print(worker_cat)
    _df = df.loc[df['mtc_worker_type'] == worker_cat]
    df_psrc = df_psrc.merge(_df[['hhno',0]],how='left', left_on='HHID', right_on='hhno')
    df_psrc.drop('hhno', axis=1, inplace=True)
    df_psrc[0] = df_psrc[0].fillna(0).astype('int')
    df_psrc.rename(columns={0: age_category}, inplace=True)


# htypdwel (1 SFH detached, 2 duplex or apt, 3 mobile home etc)
# df_psrc['htypdwel'] = df_psrc['BLDGSZ'].copy()
df_psrc.loc[df_psrc['BLDGSZ'].isin([2,3]), 'htypdwel'] = 1
df_psrc.loc[df_psrc['BLDGSZ'].isin([4,5,6,7,8,9]), 'htypdwel'] = 2
df_psrc.loc[df_psrc['BLDGSZ'].isin([1,10]), 'htypdwel'] = 3

# hownrent (same as in soundcast)

# hadnwst (nonworking students in household)
# hadwpst

# student nonworker
df_psrc_person['hadnwst'] = 0
df_psrc_person.loc[(df_psrc_person['pstyp'] > 0) 
                    & (df_psrc_person['pwtyp'] == 0),'hadnwst'] = 1
# student worker
# df_psrc_person[(df_psrc_person['student'] > 0) & df_psrc_person['pwtyp'] > 0]
df_psrc_person['hadwpst'] = 0
df_psrc_person.loc[(df_psrc_person['pstyp'] > 0) 
                    & (df_psrc_person['pwtyp'] > 0),'hadwpst'] = 1

df = df_psrc_person.groupby('hhno').sum()[['hadwpst']].reset_index()
df.loc[df['hadwpst'] > 0, 'hadwpst'] = 1
df_psrc = df_psrc.merge(df[['hhno','hadwpst']],how='left', left_on='HHID', right_on='hhno')
df_psrc.drop('hhno', axis=1, inplace=True)

df = df_psrc_person.groupby('hhno').sum()[['hadnwst']].reset_index()
df.loc[df['hadnwst'] > 0, 'hadnwst'] = 1
df_psrc = df_psrc.merge(df[['hhno','hadnwst']],how='left', left_on='HHID', right_on='hhno')
df_psrc.drop('hhno', axis=1, inplace=True)


# hadkids
###### FIXME###########
# Set to 0 for now
df_psrc['hadkids'] = 0

# bucketBin
df_psrc['bucketBin'] = 1

# originalPUMA
df_psrc['orginalPUMA'] = df_psrc['PUMA5'].copy()

# hmultiunit
df_psrc['hmultiunit'] = 1
df_psrc.loc[df_psrc['htypdwel'] == 1, 'hmultiunit'] = 0

seed_persons = pd.read_csv(r'R:\e2projects_two\SyntheticPopulation_2018\populationsim_inputs\data\seed_persons.csv')

len(df_psrc)

df_psrc = df_psrc.loc[:,~df_psrc.columns.duplicated()]
output_cols = np.intersect1d(df_mtc.columns, df_psrc.columns)

df_psrc.to_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\households.csv',index=False)

############################
# Person
############################

df_mtc_persons = pd.read_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\original_mtc\persons.csv')

df_psrc_person['HHID'] = df_psrc_person['hhno'].copy()
df_psrc_person['household_id'] = df_psrc_person['hhno'].copy()
df_psrc_person['PERID'] = range(len(df_psrc_person))
df_psrc_person['age'] = df_psrc_person['pagey'].copy()
df_psrc_person['sex'] = df_psrc_person['pgend'].copy()

df_psrc_person.loc[df_psrc_person['pwtyp'] == 1,'pemploy'] = 1
df_psrc_person.loc[df_psrc_person['pwtyp'] == 2,'pemploy'] = 2
df_psrc_person.loc[df_psrc_person['pwtyp'] == 0,'pemploy'] = 3
df_psrc_person.loc[df_psrc_person['age'] < 16,'pemploy'] = 4
df_psrc_person['pemploy'] = df_psrc_person['pemploy'].astype('int')

df_psrc_person['pstudent'] = 3
df_psrc_person.loc[df_psrc_person['pptyp'].isin([7,6]),'pstudent'] = 1
df_psrc_person.loc[df_psrc_person['pptyp']==5 ,'pstudent'] = 2

df_psrc_person['ptype'] = df_psrc_person['pptyp']
df_psrc_person.loc[df_psrc_person['pptyp'] == 3, 'ptype'] = 5
df_psrc_person.loc[df_psrc_person['pptyp'] == 5, 'ptype'] = 3

# Join seed person data for required columns
seed_person_cols = ['hhnum']
for col in seed_persons.columns:
    if col.lower() in [i.lower() for i in df_mtc_persons.columns]:
        seed_person_cols.append(col)
#     if col.lower() in df_mtc

df_psrc_person = df_psrc_person.merge(seed_persons[seed_person_cols], left_on='HHID', right_on='hhnum', how='left')

# Drop columns not in the original MTC data
for col in df_mtc_persons.columns:
    if col not in df_psrc_person.columns:
        df_psrc_person[col] = -1

output_cols = np.intersect1d(df_mtc_persons.columns, df_psrc_person.columns)

df_psrc_person[output_cols].to_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\persons.csv',index=False)

###########################
# Land Use
###########################

# Read household and person files
df_psrc_person = pd.read_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\persons.csv')
df_psrc = pd.read_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\households.csv')
df_mtc_lu = pd.read_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\original_mtc\land_use.csv')
df_parcel = pd.read_csv(r'R:\e2projects_two\SoundCast\Inputs\dev\landuse\2018\base_year\parcels_urbansim.txt',
                       delim_whitespace=True)
df_lu = df_parcel.groupby('taz_p').sum()[['hh_p','emptot_p','empret_p','stuhgh_p',
                                 'stuuni_p']]
df_lu.rename(columns={'hh_p': 'HHPOP','emptot_p': 'TOTEMP','empret_p': 'RETEMPN',
                     'stuhgh_p': 'HSENROLL', 'stuuni_p': 'COLLFTE'}, inplace=True)
df_lu = df_lu.reset_index()
df_lu['ZONE'] = df_lu['taz_p']

# Total population by TAZ
df = df_psrc.groupby('TAZ').sum()['PERSONS'].reset_index()
df.rename(columns={'PERSONS': 'TOTPOP'}, inplace=True)
df_lu = df_lu.merge(df, left_on='ZONE', right_on='TAZ')
df_lu.drop('TAZ',axis=1,inplace=True)

# MPRES
# employed residents
df_psrc_person['EMPRES'] = 0
df_psrc_person.loc[df_psrc_person['pemploy'].isin([1,2]),'EMPRES'] = 1

df = df_psrc_person.groupby('HHID').sum()[['EMPRES']].reset_index()
df_psrc = df_psrc.merge(df, on='HHID')
df_lu = df_lu.merge(df_psrc.groupby('TAZ').sum()[['EMPRES']].reset_index(), left_on='ZONE', right_on='TAZ', how='left')
df_lu.drop('TAZ', axis=1, inplace=True)

# SFDU (single family dwelling units, not used)
df_lu['SFDU'] = -1
df_lu['MFDU'] = -1

# Households in the lowest income quartile (less than $30,000 annually in $2000)
for colname in ['HHINCQ1','HHINCQ2','HHINCQ3','HHINCQ4']:
    df_psrc[colname] = 0

df_psrc.loc[df_psrc['income'] < 30000, 'HHINCQ1'] = 1
df_psrc.loc[(df_psrc['income'] >= 30000) & (df_psrc['income'] < 60000), 'HHINCQ2'] = 1
df_psrc.loc[(df_psrc['income'] >= 60000) & (df_psrc['income'] < 100000), 'HHINCQ3'] = 1
df_psrc.loc[df_psrc['income'] >= 100000, 'HHINCQ4'] = 1

df = df_psrc.groupby('TAZ').sum()[['HHINCQ1','HHINCQ2','HHINCQ3','HHINCQ4']].reset_index()
df_lu = df_lu.merge(df, left_on='ZONE', right_on='TAZ', how='left')
df_lu.drop('TAZ', axis=1, inplace=True)

# Total acres
df = (df_parcel.groupby('taz_p').sum()[['sqft_p']]/43560).reset_index()
df.rename(columns={'sqft_p': 'TOTACRE'}, inplace=True)
df_lu = df_lu.merge(df, on='taz_p')

# Acreage occupied by residential development - don't know if we have that
# set to 0.5 total
df_lu['RESACRE'] = df['TOTACRE']*0.5

# commercial acreage, set to 0.5 for now
df_lu['CIACRE'] = df['TOTACRE']*0.5

# Share of population 62 or older
df_psrc_person.loc[df_psrc_person['pagey'] >= 62, 'SHPOP62P'] = 1
df = df_psrc_person.groupby('hhno').sum()['SHPOP62P'].fillna(0).reset_index()
df_psrc = df_psrc.merge(df, left_on='HHID', right_on='hhno')
df = df_psrc.groupby('TAZ').sum()['SHPOP62P'].reset_index()
df_lu = df_lu.merge(df, left_on='ZONE', right_on='TAZ')
df_lu['SHPOP62P'] = df_lu['SHPOP62P']/df_lu['TOTPOP']

df_psrc_person.loc[df_psrc_person['pagey'] < 5, 'AGE0004'] = 1
df_psrc_person.loc[(df_psrc_person['pagey'] >= 5) & (df_psrc_person['pagey'] < 20), 'AGE0519'] = 1
df_psrc_person.loc[(df_psrc_person['pagey'] >= 20) & (df_psrc_person['pagey'] < 45), 'AGE2044'] = 1
df_psrc_person.loc[(df_psrc_person['pagey'] >= 45) & (df_psrc_person['pagey'] < 65), 'AGE4564'] = 1
df_psrc_person.loc[df_psrc_person['pagey'] >= 65, 'AGE65P'] = 1

for colname in ['AGE0004','AGE0519','AGE2044','AGE4564','AGE65P']:
    df = df_psrc_person.groupby('hhno').sum()[colname].fillna(0).reset_index()
    df_psrc = df_psrc.merge(df, left_on='HHID', right_on='hhno')
    df = df_psrc.groupby('TAZ').sum()[colname].reset_index()
    df_lu = df_lu.merge(df, left_on='ZONE', right_on='TAZ')
    if 'TAZ' in df_lu.columns:
        df_lu.drop('TAZ', axis=1, inplace=True)

# PRKCST Hourly parking rate paid by long-term hours (8 hours)

# Take the average for all parcels (weighted by number of spaces)
df_parcel['weighted_daily_price'] = df_parcel['parkdy_p']*df_parcel['ppricdyp']
df = df_parcel.groupby('taz_p').sum()['weighted_daily_price']/df_parcel.groupby('taz_p').sum()['parkdy_p']

# Convert the daily total rate to hourly assuming 8 hours
df = df/8
df = pd.DataFrame(df,columns=['PRKCST']).reset_index().fillna(0)

df_lu = df_lu.merge(df, on='taz_p')

# OPRKCST Hourly parking rate paid by short-term parkers
df_parcel['weighted_hourly_price'] = df_parcel['parkhr_p']*df_parcel['pprichrp']
df = df_parcel.groupby('taz_p').sum()['weighted_hourly_price']/df_parcel.groupby('taz_p').sum()['parkhr_p']

# Convert the daily total rate to hourly assuming 8 hours
df = df/8
df = pd.DataFrame(df,columns=['OPRKCST']).reset_index().fillna(0)

df_lu = df_lu.merge(df, on='taz_p')

# FIXME!!!!!!!!!!!!!
# AREATYPE area type designation
df_lu['AREATYPE'] = 3

# HSENROLL high school enrollment
# df_psrc_person.loc[(df_psrc_person['pstyp'] == 6), 'HSENROLL'] = 1
# df = df_psrc_person.groupby('hhno').sum()['HSENROLL'].fillna(0).reset_index()
# df_psrc = df_psrc.merge(df, left_on='HHID', right_on='hhno')
# df = df_psrc.groupby('TAZ').sum()['HSENROLL'].reset_index()
# df_lu = df_lu.merge(df, left_on='ZONE', right_on='TAZ')

# # COLLFTE full time college student
# df_psrc_person.loc[(df_psrc_person['pstyp'] == 1) & (df_psrc_person['pptyp'] == 5), 'COLLFTE'] = 1
# df = df_psrc_person.groupby('hhno').sum()['COLLFTE'].fillna(0).reset_index()
# df_psrc = df_psrc.merge(df, left_on='HHID', right_on='hhno')
# df = df_psrc.groupby('TAZ').sum()['COLLFTE'].reset_index()
# df_lu = df_lu.merge(df, left_on='ZONE', right_on='TAZ')

# # COLLPTE
# df_psrc_person.loc[(df_psrc_person['pstyp'] == 2) & (df_psrc_person['pptyp'] == 5), 'COLLPTE'] = 1
# df = df_psrc_person.groupby('hhno').sum()['COLLPTE'].fillna(0).reset_index()
# df_psrc = df_psrc.merge(df, left_on='HHID', right_on='hhno')
# df = df_psrc.groupby('TAZ').sum()['COLLPTE'].reset_index()
# df_lu = df_lu.merge(df, left_on='ZONE', right_on='TAZ')

# TERMINAL
# get terminal times from file
df_tt = pd.read_csv(r'https://raw.githubusercontent.com/psrc/soundcast/dev/inputs/model/intrazonals/destination_tt.in',
                   delim_whitespace=True, skiprows=4)

df_tt.columns = ['taz_p','TERMINAL']
df_tt['taz_p'] = df_tt['taz_p'].apply(lambda i: i.split(':')[0]).astype('int')
df_lu = df_lu.merge(df_tt, on='taz_p')

# TOPOLOGY
df_lu['TOPOLOGY'] = 1

# ZERO placeholder
df_lu['ZERO'] = 0

df_lu['SFTAZ'] = df_lu['taz_p']

# Group quarters population
df_lu['GQPOP'] = 0

for col in df_mtc_lu.columns:
    if col not in df_lu.columns:
        df_lu[col] = -1
        
output_cols = output_cols = np.intersect1d(df_mtc_lu.columns, df_lu.columns)

df_lu[output_cols].to_csv(r'C:\Users\bnichols\activitysim\psrc_example\data\land_use.csv',index=False)

###################################
# Skims
###################################

# Bike and walk skims
mtc_skims = h5py.File(r'C:\Users\bnichols\activitysim\psrc_example\data\original_mtc\skims.omx')

# Bike and walk skims
myh5 = h5py.File(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster\5to6.h5')

results_dict = {}
matrix_size = len(myh5['Skims']['sov_inc2t'])

# Assuminig DIST is centroid-centroid distance...using walk distance
results_dict['DIST'] = myh5['Skims']['walkt'][:matrix_size,:matrix_size]*(3.0/60.0) # Assuming 3 mph walk speed
results_dict['DISTBIKE'] = myh5['Skims']['biket'][:matrix_size,:matrix_size]*(10.0/60.0) # Assuming 10 mph bike speed
results_dict['DISTWALK'] = myh5['Skims']['walkt'][:matrix_size,:matrix_size]*(3.0/60.0) # Assuming 10 mph bike speed

myh5 = h5py.File(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster\6to7.h5')

for tod in ['AM','MD','PM','EV','EA']:
    for mtc_mode in ['COM', 'EXP','HVY','LOC','LRF','TRN']:
    # Fare
        # Using AM fares for all time periods for now
        results_dict['WLK_'+mtc_mode+'_WLK_FAR__'+tod] = myh5['Skims']['mfafarbx'][:matrix_size,:matrix_size]
        results_dict['WLK_'+mtc_mode+'_DRV_FAR__'+tod] = myh5['Skims']['mfafarbx'][:matrix_size,:matrix_size]
        results_dict['DRV_'+mtc_mode+'_WLK_FAR__'+tod] = myh5['Skims']['mfafarbx'][:matrix_size,:matrix_size]

        myh5 = h5py.File(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster\7to8.h5')

# np.zeros(len())

zero_array = np.zeros((matrix_size,matrix_size))
# Vehicle matrices
#### DISTANCE ####
# Distance is only skimmed for once (7to8); apply to all TOD periods
for tod in ['AM','MD','PM','EV','EA']: # EA=early AM
    results_dict['SOV_DIST__'+tod] = myh5['Skims']['sov_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV2_DIST__'+tod] = myh5['Skims']['hov2_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV3_DIST__'+tod] = myh5['Skims']['hov3_inc2d'][:matrix_size,:matrix_size]
    results_dict['SOVTOLL_DIST__'+tod] = myh5['Skims']['sov_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV2TOLL_DIST__'+tod] = myh5['Skims']['hov2_inc2d'][:matrix_size,:matrix_size]
    results_dict['HOV3TOLL_DIST__'+tod] = myh5['Skims']['hov3_inc2d'][:matrix_size,:matrix_size]

# Time
    results_dict['SOV_TIME__'+tod] = myh5['Skims']['sov_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV2_TIME__'+tod] = myh5['Skims']['hov2_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV3_TIME__'+tod] = myh5['Skims']['hov3_inc2t'][:matrix_size,:matrix_size]
    results_dict['SOVTOLL_TIME__'+tod] = myh5['Skims']['sov_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV2TOLL_TIME__'+tod] = myh5['Skims']['hov2_inc2t'][:matrix_size,:matrix_size]
    results_dict['HOV3TOLL_TIME__'+tod] = myh5['Skims']['hov3_inc2t'][:matrix_size,:matrix_size]

# Cost 
# BTOLL is bridge toll
# Set this to 0 and only use the value toll (?)
    results_dict['SOV_BTOLL__'+tod] = zero_array
    results_dict['HOV2_BTOLL__'+tod] = zero_array
    results_dict['HOV3_BTOLL__'+tod] = zero_array
    results_dict['SOVTOLL_BTOLL__'+tod] = zero_array
    results_dict['HOV2TOLL_BTOLL__'+tod] = zero_array
    results_dict['HOV3TOLL_BTOLL__'+tod] = zero_array

# VTOLL is value toll, assuming a per-mile price?
#     results_dict['SOV_VTOLL__'+tod] = myh5['Skims']['sov_inc2c'][:matrix_size,:matrix_size]
#     results_dict['HOV2_VTOLL__'+tod] = myh5['Skims']['hov2_inc2c'][:matrix_size,:matrix_size]
#     results_dict['HOV3_VTOLL__'+tod] = myh5['Skims']['hov3_inc2c'][:matrix_size,:matrix_size]
    results_dict['SOVTOLL_VTOLL__'+tod] = myh5['Skims']['sov_inc2c'][:matrix_size,:matrix_size]
    results_dict['HOV2TOLL_VTOLL__'+tod] = myh5['Skims']['hov2_inc2c'][:matrix_size,:matrix_size]
    results_dict['HOV3TOLL_VTOLL__'+tod] = myh5['Skims']['hov3_inc2c'][:matrix_size,:matrix_size]

time_dict = {'AM': '7to8','MD': '10to14', 'PM': '17to18', 'EV': '18to20', 'EA': '5to6'}



# Averages taken from daysim outputs (see below)
# need to actually model this
access_dist = {'COM': 6.561, 'EXP': 6.948, 'HVY': 9.31, 'LOC':7.69 , 'LRF': 7.6803, 'TRN': 9.31}
access_time = {'COM': 16.195, 'EXP': 16.71, 'HVY': 20.66, 'LOC': 17.759, 'LRF': 15.892, 'TRN': 20.66}

egress_dist = {'COM': 6.338, 'EXP': 6.71, 'HVY': 9.04, 'LOC':7.41 , 'LRF': 7.321, 'TRN': 9.04}
egress_time = {'COM': 15.93, 'EXP': 15.936, 'HVY': 20.08, 'LOC': 17.479, 'LRF': 15.325, 'TRN': 20.08}

for tod, hour in time_dict.items():
    print(tod)
    print(hour)
    myh5 = h5py.File(os.path.join(r'L:\RTP_2022\sc_2018_BASE\inputs\model\roster',hour+'.h5'))

    submode_dict = {'COM':'c', 'EXP':'p', 'HVY':'r', 'LOC':'b','LRF':'f', 'TRN': 'r'}

    for mtc_mode, psrc_mode in submode_dict.items():
        print(mtc_mode)
        if mtc_mode == 'LOC':
            # Walk Access Time
            results_dict['WLK_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
            
            # Initial Wait Time
            results_dict['WLK_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_IWAIT__'+tod] = myh5['Skims']['iwtwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtwa'][:matrix_size,:matrix_size]
            
            # Total Wait Time
            results_dict['WLK_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAIT__'+tod] = myh5['Skims']['twtwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtwa'][:matrix_size,:matrix_size]
            
            # In vehicle time for Walk access/egress
            results_dict['WLK_'+mtc_mode+'_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwa'][:matrix_size,:matrix_size]
        
            # Transfer Time 
            results_dict['WLK_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_XWAIT__'+tod] = myh5['Skims']['xfrwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrwa'][:matrix_size,:matrix_size]
            
            # Boardings
            results_dict['WLK_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbwa'][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_BOARDS__'+tod] = myh5['Skims']['ndbwa'][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbwa'][:matrix_size,:matrix_size]

            
        else:
            results_dict['WLK_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAUX__'+tod] = myh5['Skims']['auxw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_IWAIT__'+tod] = myh5['Skims']['iwtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_WAIT__'+tod] = myh5['Skims']['twtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_XWAIT__'+tod] = myh5['Skims']['xfrw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['WLK_'+mtc_mode+'_DRV_BOARDS__'+tod] = myh5['Skims']['ndbw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAUX__'+tod] = myh5['Skims']['auxw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_IWAIT__'+tod] = myh5['Skims']['iwtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_WAIT__'+tod] = myh5['Skims']['twtw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_XWAIT__'+tod] = myh5['Skims']['xfrw'+psrc_mode][:matrix_size,:matrix_size]
            results_dict['DRV_'+mtc_mode+'_WLK_BOARDS__'+tod] = myh5['Skims']['ndbw'+psrc_mode][:matrix_size,:matrix_size]

        # In Vehicle Time
        
        results_dict['WLK_'+mtc_mode+'_DRV_TOTIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
        results_dict['DRV_'+mtc_mode+'_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
        
        # Modified In Vehicle Time
        # FIXME: look up how this is defined in TM1
        results_dict['DRV_'+mtc_mode+'_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
        results_dict['WLK_'+mtc_mode+'_DRV_KEYIVT__'+tod] = myh5['Skims']['ivtwa'+psrc_mode][:matrix_size,:matrix_size]
                
        ####################
        # Drive to Transit #
        ####################
        
        # Drive access time
        results_dict['DRV_'+mtc_mode+'_WLK_DTIM__'+tod] = np.full([matrix_size,matrix_size], access_time[mtc_mode]*100) 
        results_dict['WLK_'+mtc_mode+'_DRV_DTIM__'+tod] = np.full([matrix_size,matrix_size], access_time[mtc_mode]*100) 
        
        # Drive access distance
        results_dict['DRV_'+mtc_mode+'_WLK_DDIST__'+tod] = np.full([matrix_size,matrix_size], egress_time[mtc_mode]*100) 
        results_dict['WLK_'+mtc_mode+'_DRV_DDIST__'+tod] = np.full([matrix_size,matrix_size], egress_time[mtc_mode]*100)
        
    ##### Some other random stuff
    results_dict['DRV_LRF_WLK_FERRYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_WLK_FERRYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_DRV_FERRYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_COM_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwac'][:matrix_size,:matrix_size]
    results_dict['WLK_COM_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwac'][:matrix_size,:matrix_size]
    results_dict['WLK_EXP_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwap'][:matrix_size,:matrix_size]
    results_dict['WLK_EXP_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwap'][:matrix_size,:matrix_size]
    results_dict['WLK_HVY_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwar'][:matrix_size,:matrix_size]
    results_dict['WLK_HVY_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwar'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_WLK_KEYIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    results_dict['WLK_LRF_WLK_TOTIVT__'+tod] = myh5['Skims']['ivtwaf'][:matrix_size,:matrix_size]
    
    results_dict['WLK_TRN_WLK_IVT__'+tod] = myh5['Skims']['ivtwar'][:matrix_size,:matrix_size]
    results_dict['WLK_TRN_WLK_WAUX__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
    results_dict['WLK_TRN_WLK_WEGR__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]
    results_dict['WLK_TRN_WLK_WACC__'+tod] = myh5['Skims']['auxwa'][:matrix_size,:matrix_size]