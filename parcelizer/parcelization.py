import os
import pyodbc
import geopandas as gpd
import pandas as pd
import numpy as np

path_bldgs_file = r'W:\gis\projects\parcelization\buildings_2014.csv'
path_block_shp = r'W:\geodata\census\Block\block2010.shp'
path_prcl_shp = r'J:\Projects\UrbanSim\NEW_DIRECTORY\GIS\Shapefiles\Parcels\Region\2014\gapwork\prcl15_4kpt.shp'

ofm_year = '2014'

out_dir = r'C:\Users\clam\Desktop\parcelization\data'
out_file = 'parcelized_ofm_' + ofm_year + '.shp'

def sqlconn(dbname):
    # create Elmer connection
    con = pyodbc.connect('DRIVER={SQL Server};SERVER=AWS-PROD-SQL\COHO;DATABASE=' + dbname + ';trusted_connection=true')
    return(con)

def query_tblOfmSaep(year):
    # retrieve ofm data from Elmer
    con = sqlconn('Sandbox')
    table_name = 'Christy.tblOfmSaep'
    query = "SELECT * FROM " + table_name + " WHERE Year = " + year
    df = pd.read_sql(query, con)
    con.close()
    return(df)

def query_and_tidy_ofm_estimates(year):
    # gather and filter for a single years worth of ofm block estimates data, wide format
    print("Gathering " + year + " OFM estimates")
    elmer_ofm = query_tblOfmSaep(year)
    keep_cols = ['GEOID', 'Attribute', 'Estimate']
    df = elmer_ofm.filter(keep_cols)
    df_pivot = pd.pivot_table(df, values = 'Estimate', index = 'GEOID', columns = 'Attribute', aggfunc = np.sum).reset_index()
    df_pivot['GEOID'] = df_pivot['GEOID'].astype('str')
    df_pivot.columns.name = None
    df_pivot = df_pivot.rename(columns = {'GEOID':'GEOID10'})
    df_pivot = df_pivot[['GEOID10', 'POP', 'HHP', 'GQ', 'HU', 'OHU']]
    return(df_pivot)

def read_shapefile(path, keep_columns):
    # read shapefile
    print("Reading shapefile")
    shp = gpd.read_file(path)
    return shp.filter(keep_columns)

def blocks_without_parcels(prcls_to_blks_shp, ofm_df_single_year):
    # identifies blocks that do not have parcels (with and without estimates)
    # returns a dataframe
    print("Assembling dataframe of blocks without parcels")
    blks_with_prcls = prcls_to_blks_shp['GEOID10'].unique()
    blks_without_prcls = ofm_df_single_year[~ofm_df_single_year['GEOID10'].isin(blks_with_prcls)]
    return(blks_without_prcls)

def blocks_with_est_without_parcels(prcls_to_blks_shp, ofm_df_single_year):
    # identifies blocks (where HU > 0) without parcels
    # returns a dataframe
    print("Assembling dataframe of blocks without parcels that have OFM estimates")
    blks_without_prcls = blocks_without_parcels(prcls_to_blks_shp, ofm_df_single_year)
    hu_col = ofm_df_single_year.columns[ofm_df_single_year.columns.str.contains('^HU')][0] 
    blks_with_est_without_parcels = blks_without_prcls[blks_without_prcls[hu_col] > 0]
    return(blks_with_est_without_parcels)

def summarize_blocks_prcls_units(prcls_to_blks_shp, prcls_units):
    # create dataframe of blocks with parcels, count of parcels, and sum of baseyear units
    df_join = pd.merge(prcls_to_blks_shp, prcls_units, how = 'left')
    df_join['residential_units'].fillna(0.0, inplace = True)
    colnames = {'PSRC_ID' : 'parcels'} #, 'residential_units' : 'baseyear_res_units'
    df_sum = df_join.groupby('GEOID10').agg({'PSRC_ID': 'count', 'residential_units': 'sum'}).reset_index().rename(columns = colnames)
    return(df_sum)

def blocks_with_parcels_and_est_without_byrunits(prcls_to_blks_shp, prcls_units, ofm_df_single_year):
    print("Assembling dataframe of blocks with parcels and OFM estimates that do not have base year units")
    df = summarize_blocks_prcls_units(prcls_to_blks_shp, prcls_units)
    df_sub = df[df['residential_units'] == 0]#'baseyear_res_units'
    df_sub_join = pd.merge(df_sub, ofm_df_single_year, how = 'left') 
    df_sub_join_est = df_sub_join[df_sub_join['HU'] > 0]
    return(df_sub_join_est)


# spatial join parcels & blocks
prcls_sub = read_shapefile(path_prcl_shp, ['PSRC_ID', 'geometry']) #'OBJECTID_1','COUNTY', 'POINT_X', 'POINT_Y', 
blks_sub = read_shapefile(path_block_shp, ['GEOID10', 'geometry'])
prcls_to_blks = gpd.sjoin(prcls_sub, blks_sub, op = 'within', how = 'left')

# assemble baseyear units
raw_bldgs = pd.read_csv(path_bldgs_file)
keep_cols = ['parcel_id', 'residential_units']
prcls_units = raw_bldgs.filter(keep_cols).groupby('parcel_id').sum().reset_index()
prcls_units = prcls_units.rename(columns = {'parcel_id' : 'PSRC_ID'})

# assess which blocks need dummy parcels or need to evenly distribute
ofm_df = query_and_tidy_ofm_estimates(ofm_year)
#blks_without_parcels = blocks_without_parcels(prcls_to_blks, ofm_df)
blks_with_est_without_parcels = blocks_with_est_without_parcels(prcls_to_blks, ofm_df)
blks_with_parcels_est_without_byrunits = blocks_with_parcels_and_est_without_byrunits(prcls_to_blks, prcls_units, ofm_df)

# create dummy parcels for block groups that have estimates but no parcels
dummy_prcls = blks_sub[blks_sub['GEOID10'].isin(blks_with_est_without_parcels['GEOID10'])] 
dummy_prcls['geometry'] = dummy_prcls['geometry'].centroid
start_id = prcls_to_blks['PSRC_ID'].max() + 1
rows = len(dummy_prcls)
dummy_prcls_id = [1.0 * n for n in range(int(start_id), int((start_id + rows)))]
dummy_prcls['PSRC_ID'] = dummy_prcls_id

# add dummy parcels
new_prcls_to_blks = gpd.GeoDataFrame(pd.concat([prcls_to_blks, dummy_prcls], sort = False)) 

# add OFM estimates to shapefile
new_prcls_to_blks = new_prcls_to_blks.merge(ofm_df, how = 'left')

# add units to parcels_blocks
new_prcls_to_blks = new_prcls_to_blks.merge(prcls_units, how = 'left')
new_prcls_to_blks['residential_units'].fillna(0.0, inplace = True)

# set number of units to 1 for dummy parcels
new_prcls_to_blks.loc[new_prcls_to_blks['PSRC_ID'].isin(dummy_prcls_id), 'residential_units'] = 1.0

# set number of units to 1 for blocks with estimates and parcels but no base year units
new_prcls_to_blks.loc[new_prcls_to_blks['GEOID10'].isin(blks_with_parcels_est_without_byrunits['GEOID10']), 'residential_units'] = 1.0

# allocate block estimates to parcels
new_prcls_to_blks['total_units'] = new_prcls_to_blks.groupby('GEOID10')['residential_units'].transform('sum')
new_prcls_to_blks['proportion'] = new_prcls_to_blks.residential_units / new_prcls_to_blks.total_units

estimate_types = ['POP', 'HHP', 'GQ', 'HU', 'OHU']
for type in estimate_types:
    new_colname = 'parcel_' + type.lower()
    new_prcls_to_blks[new_colname] = new_prcls_to_blks['proportion'] * new_prcls_to_blks[type]
    new_prcls_to_blks[new_colname].fillna(0.0, inplace = True)

#new_prcls_to_blks.to_file(os.path.join(out_dir, out_file)) # takes approx. 11 mins to write to file