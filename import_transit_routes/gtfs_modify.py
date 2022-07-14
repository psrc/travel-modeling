import pandas as pd

delete_route_ids = ["2b10424c"]
merge_route_ids = ["202ea615"]
merge_service_id = 3
base_service_id = 1

base_stops = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\revised_routes_new_stop_ids\stops.txt"
)
base_routes = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\revised_routes_new_stop_ids\routes.txt"
)
base_routes = base_routes[~base_routes["route_id"].isin(delete_route_ids)]

base_trips = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\revised_routes_new_stop_ids\trips.txt"
)
delete_trips = base_trips[base_trips["route_id"].isin(delete_route_ids)]["trip_id"]
# delete_trips = delete_trips[delete_trips['service_id']== service_id]
base_trips = base_trips[~base_trips["route_id"].isin(delete_route_ids)]

base_stop_times = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\revised_routes_new_stop_ids\stop_times.txt"
)
base_stop_times = base_stop_times[~base_stop_times["trip_id"].isin(delete_trips)]

base_shapes = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\model_import\revised_routes_new_stop_ids\shapes.txt"
)
base_shapes = base_shapes[base_shapes["shape_id"].isin(base_trips["shape_id"])]


merge_routes = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\PT_constrained\PT_2050_Constrained\PT_2050_Constrained_GTFS\routes.txt"
)
merge_routes = merge_routes[merge_routes["route_id"].isin(merge_route_ids)]

merge_trips = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\PT_constrained\PT_2050_Constrained\PT_2050_Constrained_GTFS\trips.txt"
)
merge_trips = merge_trips[merge_trips["route_id"].isin(merge_route_ids)]

# deal with new stop ids
merge_stops_lookup = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\PT_constrained\PT_2050_Constrained\PT_2050_Constrained_GTFS\brt2\new_stop_lookup.csv"
)

merge_stop_times = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\PT_constrained\PT_2050_Constrained\PT_2050_Constrained_GTFS\stop_times.txt"
)
merge_stop_times = merge_stop_times[
    merge_stop_times["trip_id"].isin(merge_trips["trip_id"])
]
merge_stop_times_cols = merge_stop_times.columns


merge_stop_times = merge_stop_times.merge(
    merge_stops_lookup, how="left", left_on="stop_id", right_on="old_stop_id"
)
merge_stop_times["stop_id"] = merge_stop_times["new_stop_id"]
merge_stop_times = merge_stop_times[merge_stop_times_cols]

merge_shapes = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2050\PT_constrained\PT_2050_Constrained\PT_2050_Constrained_GTFS\shapes.txt"
)
merge_shapes = merge_shapes[merge_shapes["shape_id"].isin(merge_trips["shape_id"])]


ct_routes = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2021\ct\702\routes.txt"
)

ct_trips = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2021\ct\702\trips.txt"
)


ct_stop_times = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2021\ct\702\stop_times.txt"
)
ct_stop_times = ct_stop_times[merge_stop_times_cols]

ct_shapes = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2021\ct\702\shapes.txt"
)

ct_stops = pd.read_csv(
    r"Y:\2022 RTP\Future Transit Network\newest\2021\ct\702\stops.txt"
)

routes = pd.concat([base_routes, merge_routes, ct_routes], axis=0)
routes["agency_id"] = 1
routes.to_csv(r"C:\Workspace\stefan\routes.txt", index=False)


trips = pd.concat([base_trips, merge_trips, ct_trips], axis=0)
trips.to_csv(r"C:\Workspace\stefan\trips.txt", index=False)

stop_times = pd.concat([base_stop_times, merge_stop_times, ct_stop_times], axis=0)
stop_times.to_csv(r"C:\Workspace\stefan\stop_times.txt", index=False)

shapes = pd.concat([base_shapes, merge_shapes, ct_shapes], axis=0)
shapes.to_csv(r"C:\Workspace\stefan\shapes.txt", index=False)

stops = pd.concat([base_stops, ct_stops], axis=0)
stops = stops[base_stops.columns]
stops.to_csv(r"C:\Workspace\stefan\stops.txt", index=False)
