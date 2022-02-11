import os
import pyodbc
import sqlalchemy
import time
from pandas import read_sql
from shapely import wkt
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
import os
import numpy as np
import yaml
import time
import sys
import transit_service_analyst as tsa

def read_from_sde(connection_string, feature_class_name, version,
                  crs={'init': 'epsg:2285'}, is_table=False):
    """
    Returns the specified feature class as a geodataframe from ElmerGeo.

    Parameters
    ----------
    connection_string : SQL connection string that is read by geopandas
                        read_sql function

    feature_class_name: the name of the featureclass in PSRC's ElmerGeo
                        Geodatabase

    cs: cordinate system
    """

    engine = sqlalchemy.create_engine(connection_string)
    con = engine.connect()
    con.execute("sde.set_current_version {0}".format(version))

    if is_table:
        gdf = pd.read_sql('select * from %s' %
                          (feature_class_name), con=con)
        con.close()

    else:
        df = pd.read_sql('select *, Shape.STAsText() as geometry from %s' %
                         (feature_class_name), con=con)
        con.close()

        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.crs = crs
        cols = [col for col in gdf.columns if col not in
                ['Shape', 'GDB_GEOMATTR_DATA', 'SDE_STATE_ID']]
        gdf = gdf[cols]

    return gdf

def get_points_by_transit_type(tsa_instance, route_type):
    transit_lines = tsa_instance.get_lines_gdf()
    transit_lines = transit_lines[transit_lines['route_type']== route_type]
    route_stops = tsa_instance.get_line_stops_gdf()
    route_stops = route_stops[route_stops['rep_trip_id'].isin(transit_lines['rep_trip_id'])]
    stops = tsa_instance.stops
    stops = stops[stops['stop_id'].isin(route_stops['stop_id'])]
    return stops

def get_transit_stops_by_route_frequency(gsu_instance, route_type, min_tph, list_of_hrs, min_hrs):
    freq = gsu_instance.get_tph_by_line()
    # create binary column for each our
    cols = []
    for hour in list_of_hours:
        print (len(freq))
        new_col = hour + '_recode'
        cols.append(new_col)
        freq[new_col] = np.where(freq[hour]>=min_tph, 1 ,0)
    freq['total_hours'] = freq[cols].sum(axis=1)
    freq = freq[freq['total_hours']>=min_hrs]
    route_stops = gsu_instance.get_line_stops_gdf()
    route_stops = route_stops[route_stops['rep_trip_id'].isin(freq['rep_trip_id'])]
    stops = gsu_instance.stops
    stops = stops[stops['stop_id'].isin(route_stops['stop_id'])]
    return stops

def get_transit_stops_by_stop_frequency(gsu_instance, route_type, min_tph, list_of_hrs):
    freq = gsu_instance.get_tph_at_stops()
    for hour in list_of_hours:
        print (len(freq))
        freq = freq[freq[hour]>=min_tph]
    stops = gsu_instance.stops
    stops = stops[stops['stop_id'].isin(freq['stop_id'])]

    transit_lines = gsu_instance.get_routes_gdf()
    transit_lines = transit_lines[transit_lines['route_type']== route_type]
    route_stops = gsu_instance.get_route_stops_gdf()
    route_stops = route_stops[route_stops['rep_trip_id'].isin(transit_lines['rep_trip_id'])]
    stops = stops[stops['stop_id'].isin(route_stops['stop_id'])] 
    return stops
    # now only keep the stops that belong to routes with 
    # the route_type parameter



model_year = 2050
high_regular_junction = 199262
model_dir = '//modelstation1/c$/workspace/sc_rtp_2050_constrained_final/soundcast'
#model_dir = '//modelstation2/c$/Workspace/sc_2018_rtp_final/soundcast'

list_of_hours = ['hour_6', 'hour_7', 'hour_8', 'hour_15', 'hour_16', 'hour_17']

route_type_dict = {0: 'streetcar', 1: 'light_rail', 2: 'commuter_rail', 4:'ferry', 5: 'BRT'}

buffer_dict = {'streetcar' : 2640, 'light_rail' : 2640, 'commuter_rail' : 2640, 'ferry' : 2640, 'BRT' : 1320}

server= 'AWS-Prod-SQL\Sockeye'

elmer_geo_database= 'ElmerGeo'
osm_geo_database = 'OSMTest'

version= "'sde.DEFAULT'"

elmer_geo_conn_string = '''mssql+pyodbc://%s/%s?driver=SQL Server?
    Trusted_Connection=yes''' % (server, elmer_geo_database)

osm_geo_conn_string = '''mssql+pyodbc://%s/%s?driver=SQL Server?
    Trusted_Connection=yes''' % (server, osm_geo_database)

crs = {'init' : 'EPSG:2285'}


# 2050:
path = r'Y:\2022 RTP\Future Transit Network\newest\2050\model_import\revised_routes_new_stop_ids\merged\test'
#path = r'R:\e2projects_two\Angela\transit_routes_2018\latest_combined'

gtfs_util = tsa.load_gtfs(path, '20210707', 0, 1680)
#gtfs_util = gsu.load_gtfs(path, '20180417', 0, 1680)


gdf_parcels = read_from_sde(elmer_geo_conn_string,
                                      'parcels_urbansim_2018_pts',
                                      version, crs=crs, is_table=False)

gdf_transit_lines = read_from_sde(osm_geo_conn_string,
                                      'TransitLines_evw',
                                      version, crs=crs, is_table=False)

gdf_transit_lines = gdf_transit_lines[gdf_transit_lines['InServiceDate']==model_year]

transit_segments = pd.read_csv(os.path.join(model_dir, 'outputs/transit/transit_segment_results.csv'))
transit_segments = transit_segments[(transit_segments['i_node'] > high_regular_junction) | (transit_segments['j_node'] > high_regular_junction)]
hov_routes = gdf_transit_lines[gdf_transit_lines['LineID'].isin(transit_segments['line_id'])]['RouteID']
hov_gtfs_routes = gtfs_util.get_lines_gdf()
#hov_gtfs_routes = hov_gtfs_routes[hov_gtfs_routes['route_id'].isin(hov_routes)]
#hov_gtfs_routes = hov_gtfs_routes[~hov_gtfs_routes.geometry==None]
hov_route_stops = gtfs_util.get_line_stops_gdf()
hov_route_stops = hov_route_stops[hov_route_stops['route_id'].isin(hov_routes)]
stops = gtfs_util.stops
hov_stops = stops[stops['stop_id'].isin(hov_route_stops['stop_id'])] 
hov_stops.to_crs(crs, inplace = True)
hov_stops.geometry = hov_stops.geometry.buffer(2640)
join_left_df = gpd.sjoin(hov_stops, gdf_parcels, how="left")
gdf_parcels['hov_bus'] = np.where(gdf_parcels['parcel_id'].isin(join_left_df['parcel_id']), 1, 0)




for route_type_id, route_type_name in route_type_dict.items():
    if 5 not in gtfs_util.routes.route_type.values:
        brt_routes = gdf_transit_lines[gdf_transit_lines['TransitType']==3]['RouteID']
        gtfs_util.routes['route_type'] = np.where(gtfs_util.routes['route_id'].isin(brt_routes), 5, gtfs_util.routes['route_type'])
    stops = get_points_by_transit_type(gtfs_util, route_type_id)
    stops.to_crs(crs, inplace = True)
    stops.geometry = stops.geometry.buffer(buffer_dict[route_type_name])
    #stops.to_file('T:/2021December/Stefan/parcel_transit_proximity/shapefiles/' + route_type_name + str(buffer_dict[route_type_name]) + '.shp')
    join_left_df = gpd.sjoin(stops, gdf_parcels, how="left")
    gdf_parcels[route_type_name] = np.where(gdf_parcels['parcel_id'].isin(join_left_df['parcel_id']), 1, 0)

# now do frequent bus
stops = get_transit_stops_by_route_frequency(gtfs_util, 3, 4, list_of_hours, 5)
stops.to_crs(crs, inplace = True)
stops.geometry = stops.geometry.buffer(2640)
join_left_df = gpd.sjoin(stops, gdf_parcels, how="left")
gdf_parcels['frequent_bus'] = np.where(gdf_parcels['parcel_id'].isin(join_left_df['parcel_id']), 1, 0)

cols = ['parcel_id', 'hov_bus', 'frequent_bus']
cols.extend(list(route_type_dict.values()))
gdf_parcels = gdf_parcels[cols]


gdf_parcels.to_csv(r'T:\2022January\Stefan\parcel_transit_proximity\parcels_transit_centroids_brt_qmile_2018.csv', index = False)

#gdf_parcels.to_csv(r'T:\2021December\Stefan\parcel_transit_proximity\parcels_transit_polys.csv', index = False)





