import pandana as pdna
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

# Specify survey years to be included
year_list = [2017,2019,2021]

def find_nearest(gdA, gdB):
    """ Find nearest value between two geodataframes.
        Returns "dist" for distance between nearest points.
    """

    nA = np.array(list(gdA.geometry.apply(lambda x: (x.x, x.y))))
    nB = np.array(list(gdB.geometry.apply(lambda x: (x.x, x.y))))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdB_nearest = gdB.iloc[idx].drop(columns="geometry").reset_index(drop=True)
    gdf = pd.concat(
        [
            gdA.reset_index(drop=True),
            gdB_nearest,
            pd.Series(dist, name='dist')
        ], 
        axis=1)

    return gdf

############################################################
# Load All-Streets Network as Pandana Network Object
############################################################

# This is base-year Soundcast network data, created from OSM-based all-streets data
# Nodes must be indexed by node_id column, which is the first column
nodes = pd.read_csv(r'R:\e2projects_two\SoundCast\Inputs\dev\base_year\2018\all_streets_nodes.csv', index_col='node_id')
links = pd.read_csv(r'R:\e2projects_two\SoundCast\Inputs\dev\base_year\2018\all_streets_links.csv', index_col=None)

# Remove circular links
links = links.loc[(links.from_node_id != links.to_node_id)]

# Assign distance as impedance
imp = pd.DataFrame(links.Shape_Length)
imp = imp.rename(columns = {'Shape_Length':'distance'})
links[['from_node_id','to_node_id']] = links[['from_node_id','to_node_id']].astype('int') 

# Create pandana network
net = pdna.network.Network(nodes.x, nodes.y, links.from_node_id, links.to_node_id, imp)

############################################################
# Load survey data
############################################################
import pyodbc
import pandas as pd

conn_string = "DRIVER={ODBC Driver 17 for SQL Server}; SERVER=AWS-PROD-SQL\Sockeye; DATABASE=Elmer; trusted_connection=yes"
sql_conn = pyodbc.connect(conn_string)
df = pd.read_sql(sql='select * from HHSurvey.v_persons', con=sql_conn)
# Select persons with work locations and filter for associated households
df = df[df['survey_year'].isin(year_list)]
df = df[~df['work_lat'].isnull()]
# Only include work locations within the region
df = df[df['work_county'].isin(['KING','KITSAP','PIERCE','SNOHOMISH'])]

# Load household lat/lng data
#df_hh = pd.read_sql(sql='select household_id, final_home_lng, final_home_lat from HHSurvey.households_2021', con=sql_conn)
df_hh = pd.read_sql(sql='select * from HHSurvey.v_households', con=sql_conn)
df_hh = df_hh[df_hh['survey_year'].isin(year_list)]
df_hh = df_hh[df_hh['household_id'].isin(df['household_id'])]

# Load work lat and lng as geoDataFrame, convert from WSG84 to WA State Plane projection
gdf_work = gpd.GeoDataFrame(
    df, geometry=gpd.points_from_xy(df.work_lng, df.work_lat))
gdf_work.crs = ('EPSG:4326')
gdf_work = gdf_work.to_crs('EPSG:2285')

# Load home lat/lng as geoDataFrame, convert from VSG84 to WA State Plane projection
gdf_home = gpd.GeoDataFrame(
    df_hh, geometry=gpd.points_from_xy(df_hh.final_home_lng, df_hh.final_home_lat))
gdf_home.crs = ('EPSG:4326')
gdf_home = gdf_home.to_crs('EPSG:2285')

# Load nodes as geoDataFrame
gdf_nodes = gpd.GeoDataFrame(
    nodes, geometry=gpd.points_from_xy(nodes.x, nodes.y))
gdf_nodes.crs = 'EPSG:2285'
gdf_nodes['node'] = gdf_nodes.index

# Snap work lat/lng to find nearest network node
df = find_nearest(gdf_work, gdf_nodes)
df_home = find_nearest(gdf_home, gdf_nodes)

# Merge home and work nodes to single dataframe
df_result = df[['person_id','node','household_id']].merge(df_home[['node','household_id']], suffixes=['_work','_home'], 
                                    how='left', on='household_id')

# Calculate shortest distance between nodes 
def shortest_dist(a, b, net):
    return net.shortest_path_length(a, b, imp_name=None)

# Remove any null values
print(str(len(df_result[df_result['node_home'].isnull()])) + " records skipped for null home values")
df_result = df_result[~df_result['node_home'].isnull()]
print(str(len(df_result[df_result['node_work'].isnull()])) + " records skipped for null work values")
df_result = df_result[~df_result['node_work'].isnull()]
df_result['home_to_work_distance'] = df_result.apply(lambda x: shortest_dist(x.node_home, x.node_work, net), axis=1)

# Convert to miles
df_result['home_to_work_distance'] = df_result['home_to_work_distance']/5280.0

df_result.to_csv(r'T:\2022October\Brice\survey_17_19_21_home_work_distance.csv')
