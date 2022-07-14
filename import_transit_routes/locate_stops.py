import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString
import itertools
from operator import itemgetter
from scipy.spatial import cKDTree
from shapely.geometry import Point, LineString

# open gtfs files:
stop_times = pd.read_csv(r"")
routes = gpd.read_file(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\import_routes.gdb",
    layer="emme_routes_sp",
)
edges = gpd.read_file(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\import_routes.gdb",
    layer="edges_2050",
)
stop_times = gpd.read_file(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\import_routes.gdb",
    layer="rep_trip_stop_times_fc_sp",
)

junctions = gpd.read_file(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\import_routes.gdb",
    layer="junctions_2050",
)
junctions["PSRCjunctI"] = junctions["PSRCjunctI"].astype(int)
junctions = junctions[junctions["PSRCjunctI"] == junctions["i"]]
junctions_coord_dict = {
    x.geometry.coords[0]: x.PSRCjunctI for x in junctions.itertuples()
}


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


# c = ckdnearest(gpd1, gpd2)

# def near(point, pts=pts3):
#     # find the nearest point and return the corresponding Place value
#     nearest = gpd2.geometry == nearest_points(point, pts)[1]
#     return gpd2[nearest].Place.get_values()[0]

# for index, row in routes.iterrows():
located_stops = gpd.GeoDataFrame()
for line_id in routes["LineID"]:
    route = routes[routes["LineID"] == line_id]
    route_stops = stop_times[stop_times["trip_id"].isin(route["RepTripID"])]
    if len(route["geometry"]) > 1:
        print("multipart")
    else:
        # route_buff = route.copy()
        # route_buff['geometry'] = route.geometry.buffer(100)
        # line_edges = gpd.sjoin(edges, route_buff, how='inner',op='within')
        # line_junctions_i = list(line_edges.i.values.astype(int))
        # line_junctions_j = list(line_edges.j.values.astype(int))
        # line_junctions = list(set(line_junctions_i + line_junctions_j))

        # + line_edges.j.values.astype(int)))

        coords = [(coords) for coords in list(route.iloc[0]["geometry"][0].coords)]
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
            junctions_coord_dict[x] for x in coords if x in junctions_coord_dict.keys()
        ]
        route_junctions = junctions[junctions["PSRCjunctI"].isin(route_junctions)]
        if len(route_junctions) > 0:
            stop_junctions = ckdnearest(route_stops, route_junctions, ["PSRCjunctI"])
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
                    stop_junctions.index = stop_junctions.index + 1  # shifting index
                # stop_junctions = stop_junctions.sort_index()  # sorting by index
                if not stop_junctions.iloc[-1]["PSRCjunctI"] == last_junction:
                    # stop_junctions['rep_trip_stop_times_stop_sequence'] = stop_junctions['rep_trip_stop_times_stop_sequence'] + 1

                    stop_junctions.loc[-1] = [
                        stop_junctions.loc[0]["trip_id"],
                        len(stop_junctions) + 1,
                        last_junction,
                        0,
                    ]
                    stop_junctions.index = stop_junctions.index + 1  # shifting index
                # stop_junctions = stop_junctions.sort_index()  # sortin
                stop_junctions.sort_values("stop_sequence", inplace=True)
                stop_junctions = stop_junctions.groupby(
                    (
                        stop_junctions["PSRCjunctI"]
                        != stop_junctions["PSRCjunctI"].shift()
                    )
                    .cumsum()
                    .values
                ).first()
                located_stops = located_stops.append(stop_junctions)
                located_stops.groupby(
                    (located_stops["PSRCjunctI"] != located_stops["PSRCjunctI"].shift())
                    .cumsum()
                    .values
                ).first()
    # gdf.at[index,'first'] = Point(first_coord)
    # gdf.at[index,'last'] = Point(last_coord)
    # gdf
located_stops.sort_values(["trip_id", "stop_sequence"], inplace=True)

located_stops["PointOrder"] = located_stops.groupby(["trip_id"]).cumcount()
located_stops["PointOrder"] = located_stops["PointOrder"] + 1
located_stops.to_file(
    r"W:\gis\projects\OSM\Transit\Transit_2022\outputs\final_outputs.gdb",
    layer="located_stops",
    driver="FileGDB",
)
print("done")
