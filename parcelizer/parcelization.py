import os
import pyodbc
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely import wkt
from pymssql import connect

path_bldgs_file = r'W:\gis\projects\parcelization\buildings_2018.csv' 
path_gq_file = r'W:\gis\projects\parcelization\gq_2018.csv' 

path_block_shp = 'block2020'
geoid_col = 'GEOID20'
publication_id = '8'

ofm_year = '2022'

out_dir = r'J:\Staff\Christy\OFM\parcelizer'
#out_dir = r'J:\OtherData\OFM\SAEP\SAEP Extract_2020-10-02\parcelized'
out_file = 'parcelized_ofm_' + ofm_year + '_vintage_2022.shp'

# functions ----

def sqlconn(dbname):
    # create Elmer connection
    con = pyodbc.connect('DRIVER={SQL Server};SERVER=AWS-PROD-SQL\SOCKEYE;DATABASE=' + dbname + ';trusted_connection=true')
    return(con)

def query_tblOfmSaep(year, publication_id):
    # retrieve ofm data from Elmer
    con = sqlconn('Elmer')
    table_name = 'ofm.estimate_facts'
    geog_table_name = 'census.geography_dim' 
    query = "SELECT a.geography_dim_id, b.block_geoid, a.estimate_year, a.housing_units, a.occupied_housing_units, a.group_quarters_population, a.household_population FROM " + table_name + " AS a LEFT JOIN " +  geog_table_name + " AS b ON a.geography_dim_id = b.geography_dim_id WHERE a.estimate_year = " +  year + " AND a.publication_dim_id = " + publication_id + ";"
    df = pd.read_sql(query, con)
    con.close()
    return(df)

def query_and_tidy_ofm_estimates(year, publication_id):
    # gather and filter for a single years worth of ofm block estimates data
    print("Gathering " + year + " OFM estimates")
    col_names = {'block_geoid':geoid_col, 'housing_units':'HU', 'occupied_housing_units':'OHU', 'group_quarters_population':'GQ', 'household_population':'HHP'}
    col_order = [geoid_col, 'POP', 'HHP', 'GQ', 'HU', 'OHU']
    elmer_ofm = query_tblOfmSaep(year, publication_id)
    elmer_ofm = elmer_ofm.drop(columns = ['geography_dim_id', 'estimate_year'])
    elmer_ofm = elmer_ofm.rename(columns = col_names)
    elmer_ofm['POP'] = elmer_ofm['HHP'] + elmer_ofm['GQ']
    elmer_ofm = elmer_ofm[col_order]
    return(elmer_ofm)

def read_shapefile(path, keep_columns):
    # read shapefile
    print("Reading shapefile")
    shp = gpd.read_file(path)
    return shp.filter(keep_columns)

def read_elmergeo_shapefile(elmergeo_layer, keep_columns):
    # read shapefile
    print("Reading shapefile")
    con = connect('AWS-Prod-SQL\Sockeye', database="ElmerGeo")
    feature_class_name = elmergeo_layer 
    geo_col_stmt = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=" + "\'" + feature_class_name + "\'" + " AND DATA_TYPE='geometry'"
    geo_col = str(pd.read_sql(geo_col_stmt, con).iloc[0,0])
    query_string = 'SELECT *,' + geo_col + '.STGeometryN(1).ToString()' + ' FROM ' + feature_class_name
    df = pd.read_sql(query_string, con)
    con.close()
    df.rename(columns={'':'geometry'}, inplace = True)
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf = gdf.filter(keep_columns)
    if 'block' in elmergeo_layer:
        gdf = gdf.rename(columns={geoid_col.lower(): geoid_col})
    return gdf

def blocks_without_parcels(prcls_to_blks_shp, ofm_df_single_year):
    # identifies blocks that do not have parcels (with and without estimates)
    # returns a dataframe
    print("Assembling dataframe of blocks without parcels")
    blks_with_prcls = prcls_to_blks_shp[geoid_col].unique()
    blks_without_prcls = ofm_df_single_year[~ofm_df_single_year[geoid_col].isin(blks_with_prcls)]
    return(blks_without_prcls)

def blocks_with_est_without_parcels(prcls_to_blks_shp, ofm_df_single_year):
    # identifies blocks (where HU > 0) without parcels ### of GQ > 0 and HU == 0
    # returns a dataframe
    print("Assembling dataframe of blocks without parcels that have OFM estimates")
    blks_without_prcls = blocks_without_parcels(prcls_to_blks_shp, ofm_df_single_year)
    blks_with_est_without_parcels = blks_without_prcls[(blks_without_prcls['HU'] > 0) | ((blks_without_prcls['GQ'] >0) & (blks_without_prcls['HU']==0))]
    return(blks_with_est_without_parcels)

def summarize_blocks_prcls_units(prcls_to_blks_shp, prcls_units):
    # create dataframe of blocks with parcels, count of parcels, and sum of baseyear units
    df_join = pd.merge(prcls_to_blks_shp, prcls_units, how = 'left')
    df_join['residential_units'].fillna(0.0, inplace = True)
    colnames = {'PSRC_ID' : 'parcels'}
    df_sum = df_join.groupby(geoid_col).agg({'PSRC_ID': 'count', 'residential_units': 'sum'}).reset_index().rename(columns = colnames)
    return(df_sum)

def blocks_with_parcels_and_est_without_byrunits(prcls_to_blks_shp, prcls_units, ofm_df_single_year):
    print("Assembling dataframe of blocks with parcels and OFM estimates that do not have base year units")
    df = summarize_blocks_prcls_units(prcls_to_blks_shp, prcls_units)
    df_sub = df[df['residential_units'] == 0]
    df_sub_join = pd.merge(df_sub, ofm_df_single_year, how = 'left') 
    df_sub_join_est = df_sub_join[df_sub_join['HU'] > 0]
    return(df_sub_join_est)

# process ----

# spatial join parcels & blocks NEW
prcls_elmergeo_sub = read_elmergeo_shapefile('parcels_urbansim_2018_pts', ['parcel_id', 'geometry'])
prcls_elmergeo_sub = prcls_elmergeo_sub.set_crs("EPSG:2285")
prcls_elmergeo_sub = prcls_elmergeo_sub.to_crs("EPSG:2285")
prcls_elmergeo_sub = prcls_elmergeo_sub.rename(columns = {'parcel_id' : 'PSRC_ID'})

blks_sub = read_elmergeo_shapefile(path_block_shp, [geoid_col.lower(), 'geometry'])
blks_sub = blks_sub.set_crs("EPSG:2285")
blks_sub = blks_sub.to_crs("EPSG:2285")

prcls_to_blks = gpd.sjoin(prcls_elmergeo_sub, blks_sub, op = 'within', how = 'left')

# assemble baseyear units 
raw_bldgs = pd.read_csv(path_bldgs_file)
keep_cols = ['parcel_id', 'residential_units']
prcls_units = raw_bldgs.filter(keep_cols).groupby('parcel_id').sum().reset_index()
prcls_units = prcls_units.rename(columns = {'parcel_id' : 'PSRC_ID'})

#### non residential sqft, sqft_per_unit
#raw_bldgs, bldg_sqft = sqft_per_unit * residential_units + non res sqft, agg by prclid, join with prcls_units 
keep_cols_sqft = ['parcel_id', 'non_residential_sqft', 'sqft_per_unit', 'residential_units']
prcls_sqft = raw_bldgs.filter(keep_cols_sqft)
prcls_sqft['bldg_sqft'] = prcls_sqft['sqft_per_unit']*prcls_sqft['residential_units'] + prcls_sqft['non_residential_sqft']
prcls_sqft = prcls_sqft.filter(['parcel_id', 'bldg_sqft']).groupby('parcel_id').sum().reset_index()
prcls_sqft = prcls_sqft.rename(columns = {'parcel_id' : 'PSRC_ID'})

# assess which blocks need dummy parcels or need to evenly distribute
ofm_df = query_and_tidy_ofm_estimates(ofm_year, publication_id)
blks_with_est_without_parcels = blocks_with_est_without_parcels(prcls_to_blks, ofm_df) ### CHECK
blks_with_parcels_est_without_byrunits = blocks_with_parcels_and_est_without_byrunits(prcls_to_blks, prcls_units, ofm_df)

# create dummy parcels for block groups that have estimates but no parcels
dummy_prcls = blks_sub[blks_sub[geoid_col].isin(blks_with_est_without_parcels[geoid_col])] 
dummy_prcls['geometry'] = dummy_prcls['geometry'].centroid
start_id = prcls_to_blks['PSRC_ID'].max() + 1
rows = len(dummy_prcls)
dummy_prcls_id = [1.0 * n for n in range(int(start_id), int((start_id + rows)))]
dummy_prcls['PSRC_ID'] = dummy_prcls_id

# add dummy parcels
new_prcls_to_blks = gpd.GeoDataFrame(pd.concat([prcls_to_blks, dummy_prcls], sort = False)) 

# add OFM estimates to shapefile
new_prcls_to_blks = new_prcls_to_blks.merge(ofm_df, how = 'left')

# add units and bldg sqft to parcels_blocks
new_prcls_to_blks = new_prcls_to_blks.merge(prcls_sqft, how = 'left')
new_prcls_to_blks = new_prcls_to_blks.merge(prcls_units, how = 'left')
new_prcls_to_blks['residential_units'].fillna(0.0, inplace = True)
new_prcls_to_blks['bldg_sqft'].fillna(0.0, inplace = True)

# set number of units to 1 for dummy parcels
new_prcls_to_blks.loc[new_prcls_to_blks['PSRC_ID'].isin(dummy_prcls_id), 'residential_units'] = 1.0

# set number of units to 1 for blocks with estimates and parcels but no base year units
new_prcls_to_blks.loc[new_prcls_to_blks[geoid_col].isin(blks_with_parcels_est_without_byrunits[geoid_col]), 'residential_units'] = 1.0

# allocate block estimates to parcels
new_prcls_to_blks['total_units'] = new_prcls_to_blks.groupby(geoid_col)['residential_units'].transform('sum')
new_prcls_to_blks['proportion'] = new_prcls_to_blks.residential_units / new_prcls_to_blks.total_units

# evaluate GQ 
raw_gqlu = pd.read_csv(path_gq_file)
blks_with_gq = ofm_df[ofm_df['GQ'] > 0]

# blocks and parcels with GQ land use with GQ estimates
prcls_with_gq_est_gqlu = new_prcls_to_blks[(new_prcls_to_blks['PSRC_ID'].isin(raw_gqlu['parcel_id'])) & (new_prcls_to_blks[geoid_col].isin(blks_with_gq[geoid_col]))]
blks_prcls_with_gq_est_gqlu = prcls_with_gq_est_gqlu[geoid_col].unique()

prcls_with_gq_est_gqlu_sqft = prcls_with_gq_est_gqlu[prcls_with_gq_est_gqlu['bldg_sqft'] > 0]
new_prcls_to_blks.loc[new_prcls_to_blks['PSRC_ID'].isin(prcls_with_gq_est_gqlu_sqft['PSRC_ID']), 'gq_numerator'] = new_prcls_to_blks['bldg_sqft']

blks_acctd = prcls_with_gq_est_gqlu_sqft[geoid_col].unique()

# blocks and parcels without GQ land use with GQ estimates
blks_not_acctd = [x for x in blks_prcls_with_gq_est_gqlu if x not in blks_acctd]

prcls_with_gq_est_gqlu_no_sqft = prcls_with_gq_est_gqlu[prcls_with_gq_est_gqlu[geoid_col].isin(blks_not_acctd)] # from this list need to know if each block contains resunits
blks_not_acctd_units_cnt = prcls_with_gq_est_gqlu_no_sqft.groupby(geoid_col)['residential_units'].sum().reset_index() # create summary table to see where to impute resunits
blks_not_acctd_zero_units = blks_not_acctd_units_cnt[blks_not_acctd_units_cnt['residential_units'] == 0]
blks_not_acctd_with_units = blks_not_acctd_units_cnt[blks_not_acctd_units_cnt['residential_units'] > 0]

new_prcls_to_blks.loc[(new_prcls_to_blks['PSRC_ID'].isin(prcls_with_gq_est_gqlu_no_sqft['PSRC_ID'])) & (new_prcls_to_blks[geoid_col].isin(blks_not_acctd_zero_units[geoid_col])), 'gq_numerator'] = 1.0
new_prcls_to_blks.loc[(new_prcls_to_blks['PSRC_ID'].isin(prcls_with_gq_est_gqlu_no_sqft['PSRC_ID'])) & (new_prcls_to_blks[geoid_col].isin(blks_not_acctd_with_units[geoid_col])),'gq_numerator'] = new_prcls_to_blks['residential_units']

# remainder of blocks with GQ estimates 
blks_rmning = blks_with_gq[~blks_with_gq[geoid_col].isin(blks_prcls_with_gq_est_gqlu)]
prcls_rmning_check = new_prcls_to_blks[new_prcls_to_blks[geoid_col].isin(blks_rmning[geoid_col])]
blks_rmning_check_summary = prcls_rmning_check.groupby(geoid_col)['bldg_sqft','residential_units'].sum().reset_index()

blks_rmning_with_gq_est_bldgsqft = blks_rmning_check_summary[blks_rmning_check_summary['bldg_sqft'] > 0] 
new_prcls_to_blks.loc[new_prcls_to_blks[geoid_col].isin(blks_rmning_with_gq_est_bldgsqft[geoid_col]), 'gq_numerator'] = new_prcls_to_blks['bldg_sqft'] 

blks_rmning_with_gq_est_no_bldgsqft_resunits = blks_rmning_check_summary[(blks_rmning_check_summary['bldg_sqft'] == 0) & (blks_rmning_check_summary['residential_units'] > 0)]
new_prcls_to_blks.loc[new_prcls_to_blks[geoid_col].isin(blks_rmning_with_gq_est_no_bldgsqft_resunits[geoid_col]), 'gq_numerator'] = new_prcls_to_blks['residential_units']

blks_rmning_with_gq_est_no_bldgsqft_no_resunits = blks_rmning_check_summary[(blks_rmning_check_summary['bldg_sqft'] == 0) & (blks_rmning_check_summary['residential_units'] == 0)]
new_prcls_to_blks.loc[new_prcls_to_blks[geoid_col].isin(blks_rmning_with_gq_est_no_bldgsqft_no_resunits[geoid_col]), 'gq_numerator'] = 1.0

new_prcls_to_blks['gq_denominator'] = new_prcls_to_blks.groupby(geoid_col)['gq_numerator'].transform('sum')
new_prcls_to_blks['gq_proportion'] = new_prcls_to_blks['gq_numerator'] / new_prcls_to_blks['gq_denominator'] 
new_prcls_to_blks['parcel_gq'] = new_prcls_to_blks['gq_proportion'] * new_prcls_to_blks['GQ']
new_prcls_to_blks['parcel_gq'].fillna(0.0, inplace = True)

# other estimates
estimate_types = ['HHP', 'HU', 'OHU']
for type in estimate_types:
    new_colname = 'parcel_' + type.lower()
    new_prcls_to_blks[new_colname] = new_prcls_to_blks['proportion'] * new_prcls_to_blks[type]
    new_prcls_to_blks[new_colname].fillna(0.0, inplace = True)

# create Total Population estimate
new_prcls_to_blks['parcel_totpop'] = new_prcls_to_blks['parcel_hhp'] + new_prcls_to_blks['parcel_gq']

# create shapefile
new_prcls_to_blks.to_file(os.path.join(out_dir, out_file)) # takes approx. 11 mins to write to file