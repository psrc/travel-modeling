import pickle
import shutil
from shutil import copy2 as shcopy
import os
from GTFS_Utilities2 import *
import configuration
import yaml
from shapely.geometry import Point, LineString
import numpy as np
import itertools
from operator import itemgetter
from scipy.spatial import cKDTree


import_routes = False
locate_stops = True


def read_from_sde(
    connection_string,
    feature_class_name,
    version,
    crs={"init": "epsg:2285"},
    is_table=False,
):
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
        gdf = pd.read_sql("select * from %s" % (feature_class_name), con=con)
        con.close()

    else:
        df = pd.read_sql(
            "select *, Shape.STAsText() as geometry from %s" % (feature_class_name),
            con=con,
        )
        con.close()

        df["geometry"] = df["geometry"].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry="geometry")
        gdf.crs = crs
        cols = [
            col
            for col in gdf.columns
            if col not in ["Shape", "GDB_GEOMATTR_DATA", "SDE_STATE_ID"]
        ]
        gdf = gdf[cols]

    return gdf


def ckdnearest(gdfA, gdfB, gdfB_cols=["Place"]):
    # resetting the index of gdfA and gdfB here.
    gdfA = gdfA.reset_index(drop=True)
    gdfB = gdfB.reset_index(drop=True)
    A = np.concatenate([np.array(geom.coords) for geom in gdfA.geometry.to_list()])
    B = [np.array(geom.coords) for geom in gdfB.geometry.to_list()]
    B_ix = tuple(
        itertools.chain.from_iterable(
            [itertools.repeat(i, x) for i, x in enumerate(list(map(len, B)))]
        )
    )
    B = np.concatenate(B)
    ckd_tree = cKDTree(B)
    dist, idx = ckd_tree.query(A, k=1)
    idx = itemgetter(*idx)(B_ix)
    gdf = pd.concat(
        [
            gdfA,
            gdfB.loc[idx, gdfB_cols].reset_index(drop=True),
            pd.Series(dist, name="dist"),
        ],
        axis=1,
    )
    return gdf


def emme_tlines_to_gdf(emme_network, config):
    rows = []
    for line in network.transit_lines():
        geom = []
        for segment in line.segments():
            for cords in segment.link.shape:
                geom.append(cords)
        rows.append(
            {
                "LineID": line.id,
                "geometry": LineString(geom),
                "mode": str(line.mode),
                "Description": line.description,
                "route_name": line["#route_name"],
                "rep_trip_id": line["#trip_id"],
            }
        )
    return rows


config = yaml.safe_load(open(configuration.args.config_file))
if import_routes:
    from EmmeProject import *

    # import geopandas as gpd
    my_project = EmmeProject(config["emme_project_path"])
    network = my_project.current_scenario.get_network()

    # create network fields required by emme import_from_gtfs tool
    my_project.create_network_field("#route_name", "TRANSIT_LINE", "STRING")
    my_project.create_network_field("#stop_id", "TRANSIT_SEGMENT", "STRING")
    my_project.create_network_field("#trip_id", "TRANSIT_LINE", "STRING")

    if os.path.exists(config["output_dir"]):
        shutil.rmtree(config["output_dir"])
        os.makedirs(config["output_dir"])

    shapefile_dir = os.path.join(config["output_dir"], "shapefiles")
    os.makedirs(shapefile_dir)
    my_project.change_curremt_scenario(config["time_of_day"])

    my_project.delete_transit_lines()
    output = my_project.import_from_gtfs(config, shapefile_dir)

    # transit_lines = emme_tlines_to_gdf(my_project.current_scenario.get_network())
    # for line in network.transit_lines():
    #    geom = []
    #    for segment in line_segments:
    #        geom.append(segment.link.shape)

    pickle.dump(output, open(f"{config['output_dir']}/import_results_log.p", "wb"))

    gtfs_utils = GTFS_Utilities2(config["gtfs_dir"], 0, 1439, config["service_ids"])

    headways = gtfs_utils.get_tph_emme_rep_trip_id(output)
    headways.to_csv(os.path.join(config["output_dir"], "headways.csv"))
    import_summary = pd.DataFrame(output[1])
    import_summary.to_csv(os.path.join(config["output_dir"], "emme_import_summary.csv"))

    # export lines
    my_project.export_network_as_shapefile(shapefile_dir, my_project.current_scenario)

if locate_stops:
    import geopandas as gpd
    import pyodbc
    import sqlalchemy
    from shapely import wkt
    import fiona

    fiona.drvsupport.supported_drivers["kml"] = "rw"
    sp_crs = {"init": "epsg:2285"}
    geog_crs = 4326
    shapefile_dir = os.path.join(config["output_dir"], "shapefiles")
    # server= 'AWS-Prod-SQL\Sockeye'
    # osm_geo_database = 'OSMTest'
    # version= "'sde.DEFAULT'"

    # osm_geo_conn_string = '''mssql+pyodbc://%s/%s?driver=SQL Server?Trusted_Connection=yes''' % (server, osm_geo_database)

    # edges = read_from_sde(osm_geo_conn_string,
    #                                  'TransRefEdges_evw',
    #                                  version, crs=sp_crs, is_table=False)

    stop_times = pd.read_csv(os.path.join(config["gtfs_dir"], "stop_times.txt"))
    stops = pd.read_csv(os.path.join(config["gtfs_dir"], "stops.txt"))
    routes = gpd.read_file(os.path.join(shapefile_dir, "emme_tlines.shp"))
    stop_times = stop_times[stop_times["trip_id"].isin(routes["#trip_id"])]
    stop_times = stop_times.merge(stops, how="left", on="stop_id")
    stop_times = gpd.GeoDataFrame(
        stop_times,
        geometry=gpd.points_from_xy(stop_times["stop_lon"], stop_times["stop_lat"]),
        crs=geog_crs,
    )
    stop_times = stop_times.to_crs(routes.crs)

    edges = gpd.read_file(
        os.path.join(config["output_dir"], "shapefiles/emme_links.shp")
    )
    # stop_times = gpd.read_file(r'Y:\2022 RTP\Future Transit Network\newest\2050\model_import\import_routes.gdb', layer = 'rep_trip_stop_times_fc_sp')
    junctions = gpd.read_file(
        os.path.join(config["output_dir"], "shapefiles/emme_nodes.shp")
    )

    junctions["PSRCjunctI"] = junctions["ID"].astype(int)
    # junctions = junctions[junctions['PSRCjunctI'] == junctions['i']]
    junctions_coord_dict = {
        x.geometry.coords[0]: x.PSRCjunctI for x in junctions.itertuples()
    }

    located_stops = gpd.GeoDataFrame()
    routes["LineID"] = 122000 + routes.index + 1
    routes["RepTripID"] = routes["#trip_id"]

    for line_id in routes["LineID"]:
        route = routes[routes["LineID"] == line_id]
        route_stops = stop_times[stop_times["trip_id"].isin(route["RepTripID"])]
        if len(route["geometry"]) > 1:
            print("multipart")

        else:
            coords = [(coords) for coords in list(route.iloc[0]["geometry"].coords)]
            first_coord, last_coord = [coords[i] for i in (0, -1)]
            try:
                first_junction = junctions_coord_dict[first_coord]
            except:
                first_junction = -1
            try:
                last_junction = junctions_coord_dict[last_coord]
            except:
                last_junction = -1
            route_junctions = [
                junctions_coord_dict[x]
                for x in coords
                if x in junctions_coord_dict.keys()
            ]
            route_junctions = junctions[junctions["PSRCjunctI"].isin(route_junctions)]
            if len(route_junctions) > 0:
                stop_junctions = ckdnearest(
                    route_stops, route_junctions, ["PSRCjunctI"]
                )
                if len(stop_junctions) > 1:
                    stop_junctions = stop_junctions[
                        ["trip_id", "stop_sequence", "PSRCjunctI", "dist"]
                    ]
                    if not stop_junctions.iloc[0]["PSRCjunctI"] == first_junction:
                        stop_junctions["stop_sequence"] = (
                            stop_junctions["stop_sequence"] + 1
                        )

                        stop_junctions.loc[-1] = [
                            stop_junctions.loc[0]["trip_id"],
                            1,
                            first_junction,
                            0,
                        ]
                        stop_junctions.index = (
                            stop_junctions.index + 1
                        )  # shifting index

                    if not stop_junctions.iloc[-1]["PSRCjunctI"] == last_junction:
                        stop_junctions.loc[-1] = [
                            stop_junctions.loc[0]["trip_id"],
                            len(stop_junctions) + 1,
                            last_junction,
                            0,
                        ]
                        stop_junctions.index = (
                            stop_junctions.index + 1
                        )  # shifting index

                    stop_junctions.sort_values("stop_sequence", inplace=True)
                    stop_junctions = stop_junctions.groupby(
                        (
                            stop_junctions["PSRCjunctI"]
                            != stop_junctions["PSRCjunctI"].shift()
                        )
                        .cumsum()
                        .values
                    ).first()
                    stop_junctions["LineID"] = route.LineID.values[0]
                    located_stops = located_stops.append(stop_junctions)
                    located_stops.groupby(
                        (
                            located_stops["PSRCjunctI"]
                            != located_stops["PSRCjunctI"].shift()
                        )
                        .cumsum()
                        .values
                    ).first()

    located_stops.sort_values(["trip_id", "stop_sequence"], inplace=True)

    located_stops["PointOrder"] = located_stops.groupby(["trip_id"]).cumcount()
    located_stops["PointOrder"] = located_stops["PointOrder"] + 1
    located_stops = located_stops.merge(junctions, how="left", on="PSRCjunctI")
    located_stops = gpd.GeoDataFrame(located_stops)
    located_stops["PSRCJuntID"] = located_stops["PSRCjunctI"]
    located_stops.to_file(os.path.join(shapefile_dir, "located_stops.shp"))
    routes.to_file(os.path.join(shapefile_dir, "routes_final.shp"))

    print("done")
