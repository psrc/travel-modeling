import pandana as pdna
import pandas as pd
import numpy as np
import os
import re
import sys
from pyproj import Proj, transform
from flask import Flask, jsonify
from flask import abort
import json
import geojson
import sqlite3
import shapely
from shapely.geometry import Point, MultiPoint
from geopandas import GeoDataFrame, GeoSeries

#os.chdir(r'D:\Stefan\Isochrone')
#app = Flask(__name__)

parcels_file_name = r'D:\Stefan\Isochrone\parcels_urbansim.txt'
nodes_file_name = r'D:\Stefan\Isochrone\all_streets_nodes_2014.csv'
links_file_name = r'D:\Stefan\Isochrone\all_streets_links_2014.csv'

max_dist = 5280 # 3 miles 
parcels = pd.DataFrame.from_csv(parcels_file_name, sep = " ", index_col = None )
#parcels = parcels.columns.map(lambda x: x.upper())

# nodes must be indexed by node_id column, which is the first column
nodes = pd.DataFrame.from_csv(nodes_file_name)
links = pd.DataFrame.from_csv(links_file_name, index_col = None )

# get rid of circular links
links = links.loc[(links.from_node_id <> links.to_node_id)]

# assign impedance
imp = pd.DataFrame(links.Shape_Length)
imp = imp.rename(columns = {'Shape_Length':'distance'})

# create pandana network
network = pdna.network.Network(nodes.x, nodes.y, links.from_node_id, links.to_node_id, imp)

def assign_nodes_to_dataset(dataset, network, column_name, x_name, y_name):
    """Adds an attribute node_ids to the given dataset."""
    dataset[column_name] = network.get_node_ids(dataset[x_name].values, dataset[y_name].values)

assign_nodes_to_dataset(parcels, network, 'node_ids', 'xcoord_p', 'ycoord_p')
network.init_pois(1, max_dist, 1)

#class MyEncoder(json.JSONEncoder):
#    def default(self, obj):
#        if isinstance(obj, numpy.integer):
#            return int(obj)
#        elif isinstance(obj, numpy.floating):
#            return float(obj)
#        elif isinstance(obj, numpy.ndarray):
#            return obj.tolist()
#        else:
#            return super(MyEncoder, self).default(obj)



def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d



#@app.route('/todo/get_parcels/<int:x>/<int:y>', methods=['GET'])
#def get_parcels(x,y):
x = pd.Series([1265627])
y = pd.Series([255656])
network.set_pois('tstop', x, y)
res = network.nearest_pois(max_dist, 'tstop', num_pois=1, max_distance=99999)
res[res <> 999] = (res[res <> 99999]/5280.).astype(res.dtypes) # convert to miles
res_name = "dist_tstop"
test = parcels
test[res_name] = res.loc[test.node_ids].values
test = test.loc[(test.dist_tstop<99999)]



geometry = [(xy) for xy in zip (test.xcoord_p, test.ycoord_p)]
geo_series = GeoSeries(MultiPoint(geometry))
geo_series.crs = {'init' :'epsg:2285'}
poly = geo_series.geometry.convex_hull
poly.crs = {'init' :'epsg:2285'}
poly = poly.to_crs({'init' :'epsg:4326'})
g2 = geojson.Feature(geometry=poly.geometry[0], properites={})
f = open('d:/poly4.geojson', 'w')
geojson.dump(g2, f)
f.close()




geometry = MultiPoint(geometry)
poly = geometry.convex_hull
g2 = geojson.Feature(geometry=poly, properites={})

geo_df = GeoDataFrame(df_parcels, crs=credits, geometry = geometry)
geo_series = GeoSeries(MultiPoint(geometry))




test = ''
test = ",".join(map(str,x))
test = '(' + test + ')'
    #x = test.parcelid.to_json
    #return json.dumps({'parcels': x})
    #return json.dumps(x)
    #return {'key': test.parcelid.to_dict(orient='record')}
psqlite='D:/Stefan/Isochrone/sqlite'
os.environ["PATH"] = psqlite + os.pathsep + os.environ["PATH"]
    #no import sqlite3
    
    #connect to a sqlite database
dbpath=os.path.abspath(r'D:\Stefan\Isochrone\parcels.sqlite')
conn=sqlite3.connect(dbpath)
    #load the spatialite extension - if everything is fine, you should not get any errors
conn.enable_load_extension(True) 
conn.execute("SELECT load_extension('mod_spatialite.dll')")
    # apply the function to the sqlite3 enginemy
conn.row_factory = dict_factory

getResultsQuery = """SELECT AsGeoJSON(geometry), psrc_id FROM parcels WHERE psrc_id in %s""" % test
#print getResultsQuery
    

    # fetch the results in form of a list of dictionaries
results = conn.execute(getResultsQuery).fetchall()
#print results 
    # create a new list which will store the single GeoJSON features
featureCollection = []

# iterate through the list of result dictionaries
for row in results:

        # create a single GeoJSON geometry from the geometry column which already contains a GeoJSON string
    geom = geojson.loads(row['AsGeoJSON(geometry)'])

        # remove the geometry field from the current's row's dictionary
    row.pop('AsGeoJSON(geometry)')

        # create a new GeoJSON feature and pass the geometry columns as well as all remaining attributes which are stored in the row dictionary
    feature = geojson.Feature(geometry=geom, properties=row)

        # append the current feature to the list of all features
    print feature
    featureCollection.append(feature)

        # when single features for each row from the database table are created, pass the list to the FeatureCollection constructor which will merge them together into one object
featureCollection = geojson.FeatureCollection(featureCollection)
        # print the FeatureCollection as string
    
GeoJSONFeatureCollectionAsString = geojson.dumps(featureCollection)
#return GeoJSONFeatureCollectionAsString
f = open('d:/parcels2.geojson', 'w')
geojson.dump(featureCollection, f)
f.close()
