import os
import pyodbc
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely import wkt
from pymssql import connect

pd.options.display.float_format = '{:.5f}'.format

vintage_year = 2022
years = list(range(2020, 2023))
geoid_col = 'GEOID20'
publication_id = '8'

# open shapefiles in output dir
out_dir = r'J:\Staff\Christy\OFM\parcelizer'

def sqlconn(dbname):
    # create Elmer connection
    con = pyodbc.connect('DRIVER={SQL Server};SERVER=AWS-PROD-SQL\SOCKEYE;DATABASE=' + dbname + ';trusted_connection=true')
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
print(x)