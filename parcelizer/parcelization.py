import os
import pyodbc
import geopandas as gpd
import pandas as pd
import numpy as np
import re

#path_bldgs_file = r'C:\Users\clam\Desktop\parcelization\data\buildings_2014.csv'
path_bldgs_file = r'W:\gis\projects\parcelization\buildings_2014.csv'
path_block_shp = r'W:\geodata\census\Block\block2010.shp'
path_prcl_shp = r'J:\Projects\UrbanSim\NEW_DIRECTORY\GIS\Shapefiles\Parcels\Region\2014\gapwork\prcl15_4kpt.shp'

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
    return(df_pivot)

def read_shape_file(path, keep_columns):
    # import parcel shapefile
    print("Reading parcel shapefile")
    keep_cols = ['OBJECTID_1', 'PSRC_ID', 'COUNTY', 'POINT_X', 'POINT_Y', 'geometry']
    prcls = gpd.read_file(path_prcl_shp)
    return prcls.filter(keep_cols)

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

def join_prcls_with_baseyear_units(prcls_to_blks_shp, prcl_units):
    # join baseyear units data to parcels
    df = pd.merge(prcls_to_blks_shp, prcl_units, how = 'left')
    df['residential_units'].fillna(0.0, inplace = True)
    return(df)

def summarize_blocks_prcls_units(prcls_to_blks_shp, prcls_units):
    # create dataframe of blocks with parcels, count of parcels, and sum of baseyear units
    df_join = join_prcls_with_baseyear_units(prcls_to_blks_shp, prcls_units)
    colnames = {'PSRC_ID' : 'parcels', 'residential_units' : 'baseyear_res_units'}
    df_sum = df_join.groupby('GEOID10').agg({'PSRC_ID': 'count', 'residential_units': 'sum'}).reset_index().rename(columns = colnames)
    return(df_sum)

def blocks_with_parcels_without_byrunits(prcls_to_blks_shp, prcls_units):
    print("Assembling dataframe of blocks with parcels that do not have base year units")
    df = summarize_blocks_prcls_units(prcls_to_blks_shp, prcls_units)
    df_sub = df[df['baseyear_res_units'] == 0]
    return(df_sub)

# spatial join parcels & blocks
prcls_sub = read_shape_file(path_prcl_shp, ['OBJECTID_1', 'PSRC_ID', 'COUNTY', 'POINT_X', 'POINT_Y', 'geometry'])
blks_sub = read_shape_file(path_block_shp, ['OBJECTID_1', 'PSRC_ID', 'COUNTY', 'POINT_X', 'POINT_Y', 'geometry'])
prcls_to_blks = gpd.sjoin(prcls_sub, blks_sub, op = 'within', how = 'left')

# assemble baseyear units:
raw_bldgs = pd.read_csv(path_bldgs_file)
keep_cols = ['parcel_id', 'residential_units']
prcls_units = raw_bldgs.filter(keep_cols).groupby('parcel_id').sum().reset_index()
prcls_units = prcls_units.rename(columns = {'parcel_id' : 'PSRC_ID'})


ofm_df = query_and_tidy_ofm_estimates('2014') # ofm data

blks_without_parcels = blocks_without_parcels(prcls_to_blks, ofm_df)
blks_with_est_without_parcels = blocks_with_est_without_parcels(prcls_to_blks, ofm_df)
blks_with_parcels_without_byr_units = blocks_with_parcels_without_byrunits(prcls_to_blks, prcls_units)
