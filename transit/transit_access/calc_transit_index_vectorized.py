import numpy as np
import partridge as ptg
import pandas as pd
import pandana as pdna
import geopandas as gpd
from shapely.geometry import Point
import sqlalchemy
from shapely import wkt
import multiprocessing as mp
import calc_score_parallel

import time
t0 = time.time()

def read_from_sde(connection_string, feature_class_name, crs = {'init' :'epsg:2285'}):
    engine = sqlalchemy.create_engine(connection_string)
    con=engine.connect()
    feature_class_name = feature_class_name + '_evw'
    df=pd.read_sql('select *, Shape.STAsText() as geometry from %s' % (feature_class_name), con=con)
    con.close()
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf=gpd.GeoDataFrame(df, geometry='geometry')
    gdf.crs = crs
    cols = [col for col in gdf.columns if col not in ['Shape', 'GDB_GEOMATTR_DATA', 'SDE_STATE_ID']]

    return gdf[cols]

def get_route_stop_times(feed):
    df = feed.trips.merge(feed.routes, how = 'left', on = 'route_id')
    df = df[['route_id', 'trip_id', 'route_type']]
    return feed.stop_times.merge(df, how = 'left', on = 'trip_id')

def rescale(values, new_min = 0, new_max = 100):
    output = []
    values = np.log1p(values)
    #old_min, old_max = values.min(), values.max()
    old_min, old_max = 2, 9
    return (new_max - new_min) / (old_max - old_min) * (values - old_min) + new_min

def create_pandana_network(nodes_path, links_path, nodes_index_id, impedance_field):
    nodes = pd.read_csv(nodes_path, index_col = nodes_index_id)
    links = pd.read_csv(links_path, index_col = None )

    # get rid of circular links
    links = links.loc[(links.from_node_id != links.to_node_id)]

    # assign impedance
    imp = pd.DataFrame(links.Shape_Length).astype('int')
    imp = imp.rename(columns = {impedance_field : 'distance'})

    return pdna.network.Network(nodes['x'], nodes['y'], links['from_node_id'], links['to_node_id'], imp)

if __name__ == '__main__':

    nodes_path = r'R:\e2projects_two\SoundCast\Inputs\dev\base_year\2018\all_streets_nodes.csv'
    links_path = r'R:\e2projects_two\SoundCast\Inputs\dev\base_year\2018\all_streets_links.csv'
    node_id = 'node_id'

    # how far to search for stops in feet
    buffer_size = 7920

    #mp stuff
    num_strides = 1 # this is the number of partitions.Set to 1 if RAM is not an issue. 
    num_procs = 8 # this is the number of procs run for each partition. 

    # max number of stops to include
    max_search_amount = 500

    # coordinate system
    crs = "EPSG:2285"

    # other inputs:
    gdb_connection_string = 'mssql+pyodbc://AWS-PROD-SQL\Sockeye/ElmerGeo?driver=SQL Server?Trusted_Connection=yes'
    gtfs_dir = r'R:\e2projects_two\Angela\transit_routes_2018\emme_gtfs_sum\gtfs'
    #gtfs_dir = r'W:\gis\projects\OSM\Transit\Transit_2040_OSM\GTFS\2040_GTFS\revised_final\gtfs'

    # the feature class to run the analysis on 
    use_gdb = False
    #fc = r'T:\2020September\Stefan\transit_index\movers.shp'
    fc = 'ElmerGeo.DBO.parcels_urbansim_2018_pts'
    feature_id = 'PSRC_ID'
    output_file = r'T:\2020October\Stefan\transit_score.csv'
    # initialize pandana network
    net = create_pandana_network(nodes_path, links_path, node_id, 'Shape_Length')
    net.precompute(buffer_size)

    # load gtfs using partridge 
    _date, service_ids = ptg.read_busiest_date(gtfs_dir)

    view = {'trips.txt': {'service_id': service_ids}}
    feed = ptg.load_geo_feed(gtfs_dir, view)

    # use partridge feed to get GTFS tables in pandas/geopandas 
    transit_stops = feed.stops.to_crs(crs)
    transit_stops['x'] = transit_stops.geometry.x 
    transit_stops['y'] = transit_stops.geometry.y 

    route_stop_times = get_route_stop_times(feed)
    # keep needed columns for memoery convervation
    route_stop_times = route_stop_times[['trip_id', 'stop_id', 'route_type']]

    if use_gdb:
        gdf = read_from_sde(gdb_connection_string, fc)
    else:
        gdf = gpd.read_file(fc)
    #gdf = gdf.head(500000)
    gdf['geometry'] = gdf['geometry'].centroid
    gdf['x'] = gdf.geometry.x 
    gdf['y'] = gdf.geometry.y 
    # get the nearest node_id from the newtork 
    gdf['node_id'] = net.get_node_ids(gdf['x'].values, gdf['y'].values)

    transit_stops.set_index('stop_id', inplace = True)
    # set stop locations as points of interests on the network. poi id is based on the index set above.
    net.set_pois('stops', buffer_size, max_search_amount, transit_stops['x'], transit_stops['y'])
    res = net.nearest_pois(buffer_size, 'stops', num_pois=max_search_amount, max_distance=99999, include_poi_ids = True)
    res = res[res.index.isin(gdf['node_id'])]
    res.reset_index(inplace = True)

    
    df = gdf[[feature_id, node_id]]
    # This is where things can get large, start MP:
    print ('start parallel processing')
    result_list = []
    x = 1
    df_strides = np.array_split(df, num_strides)
    for df_stride in df_strides:
        print ('stride ' + str(x))
        df_chunks = np.array_split(df_stride, num_procs)

        pool = mp.Pool(num_procs, calc_score_parallel.init_pool, [route_stop_times, res, feature_id])
        results = pool.map(calc_score_parallel.calc_score, df_chunks)

        #merge results back together
        df = pd.concat(results)
        df['scaled_score'] = rescale(df['score'])
        df['scaled_score'] = np.where(df['scaled_score'] < 0, 0, df['scaled_score'])
        result_list.append(df)
        x = x + 1
        pool.close()

    if num_strides == 1:
        df = result_list[0]
    else:
        df = pd.concat(result_list)

    df.to_csv(output_file)
     
    t1 = time.time()
    print (str(t1-t0))