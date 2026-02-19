import os
import pyodbc
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely import wkt
from pymssql import connect
import numpy

pd.options.display.float_format = '{:.5f}'.format

vintage_year = 2024
years = list(range(2023, 2024))
# years = [2011, 2015]
geoid_col = 'GEOID20'
publication_id = '10'

# open shapefiles in output dir
out_dir = r'J:\OtherData\OFM\SAEP\SAEP Extract_2025-11-07\parcelized'

def sqlconn(dbname):
    # create Elmer connection
    conn_string = "DRIVER={ODBC Driver 17 for SQL Server}; SERVER=SQLserver; DATABASE=Elmer; trusted_connection=yes"
    con = pyodbc.connect(conn_string)
    return(con)

def query_tblOfmSaep(years, publication_id):
    # retrieve ofm data from Elmer
    con = sqlconn('Elmer')
    table_name = 'ofm.estimate_facts'
    min_y = str(min(years))
    max_y = str(max(years))
    # get min and max years
    query = ("SELECT a.publication_dim_id, a.estimate_year, HU = SUM(a.housing_units), OHU = SUM(a.occupied_housing_units), GQPOP = SUM(a.group_quarters_population), HHPOP = SUM(a.household_population) "
            "FROM ") + table_name + (" AS a "
            "WHERE a.publication_dim_id = ") + publication_id + (" AND a.estimate_year BETWEEN ") + min_y + (" AND ") + max_y + (" GROUP BY a.estimate_year, a.publication_dim_id;")
    df = pd.read_sql(query, con)
    con.close()
    return(df)

# QC parcelizer output
df = pd.DataFrame()

for year in years:
    out_file = 'parcelized_ofm_' + str(year) + '_vintage_' + str(vintage_year) + '.shp'
    print('Reading shapefile')
    shp = gpd.read_file(os.path.join(out_dir, out_file))

    # summarise where headers start with parcel_
    sum_cols = [col for col in shp if col.startswith('parcel_')]
    sum_df = pd.DataFrame(shp[sum_cols].sum())
    sum_df = sum_df.rename(columns={0:"est"})
    sum_df['est_year'] = str(year)
    sum_df = sum_df.reset_index(names=['est_type'])
    sum_df = sum_df.pivot(index='est_year', values='est', columns='est_type')
    sum_df = sum_df.reset_index()
    sum_df = sum_df.rename_axis(None, axis=1)

    if df.empty:
        df = sum_df
    else:
        df = pd.concat([df, sum_df])

print(df)

# compare with Elmer results
x = query_tblOfmSaep(years, publication_id)
x = x[['publication_dim_id', "estimate_year", "GQPOP", "HHPOP", "HU", "OHU"]]
print(x)

# compare df and x
df1 = df.copy()
df1['est_year'] = numpy.int64(df1['est_year'])
df2 = x.copy()
dfs = df1.merge(df2, left_on='est_year', right_on='estimate_year')

dfs['diff_gq'] = dfs['parcel_gq'] - dfs['GQPOP']
dfs['diff_hhpop'] = dfs['parcel_hhp'] - dfs['HHPOP']
dfs['diff_hu'] = dfs['parcel_hu'] - dfs['HU']
dfs['diff_ohu'] = dfs['parcel_ohu'] - dfs['OHU']

# parcelized subtract elmerdb (original)
dfs_diff = dfs[['est_year', 'diff_gq', 'diff_hhpop', 'diff_hu', 'diff_ohu']]

# compare df and x
# df1 = df.drop(labels=['est_year', 'parcel_tot'], axis=1)
# df1 = df1.rename(columns={"parcel_gq": "GQPOP", "parcel_hhp":"HHPOP", "parcel_hu":"HU", "parcel_ohu":"OHU"})
# df1 = df1.reset_index()

# df2 = x.drop(labels=['estimate_year',"publication_dim_id"], axis=1)
# df2 = df2.reset_index()

# df1.compare(df2)
