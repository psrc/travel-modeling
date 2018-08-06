import pandas as pd
import numpy as np 
import os as os

dir = 'R:/Angela/transit_routes_2018/'
trips = pd.read_csv(dir + 'emme_gtfs_sum/' + 'trips.txt')
agency = pd.read_csv(dir + 'emme_gtfs_sum/' + 'agency.txt')

service_date = 20180417
start_date = 20180416
end_date = 20180418
day_of_week= 'tuesday'
#feed_list = ['KC', 'PT', 'ET', 'CT', 'KT', 'FERRY']
feed_list = ['KC']
feed_dict = {}

def get_service_ids(calendar, calendar_dates, day_of_week, service_date):
    regular_service_dates = calendar[(calendar['start_date']<= service_date) & (calendar['end_date'] >= service_date) & (calendar[day_of_week] == 1)]['service_id'].tolist()
    exceptions_df = calendar_dates[calendar_dates['date'] == service_date]
    add_service = exceptions_df.loc[exceptions_df['exception_type'] == 1]['service_id'].tolist() 
    remove_service = exceptions_df[exceptions_df['exception_type'] == 2]['service_id'].tolist()
    service_id_list = [x for x in (add_service + regular_service_dates) if x not in remove_service]
    return service_id_list

def create_id(df, feed, id_name, psrc_id_name):
    df[psrc_id_name] = feed + '_' + df[id_name].astype(str)
    return df   

for feed in feed_list: 
    print feed
    feed_dict[feed] = {}
    # read data
    calendar = pd.read_csv(dir + feed + '_gtfs/' + 'calendar.txt')
    if os.path.exists(dir + feed + '_gtfs/'+ 'calendar_dates.txt') is False:
        calendar_dates = pd.DataFrame(columns=['service_id', 'date', 'exception_type']) 
    else:
        calendar_dates = pd.read_csv(dir + feed + '_gtfs/'+ 'calendar_dates.txt')
    trips = pd.read_csv(dir + feed + '_gtfs/' + 'trips.txt')
    stops = pd.read_csv(dir + feed + '_gtfs/' + 'stops.txt')
    stop_times = pd.read_csv(dir + feed + '_gtfs/' + 'stop_times.txt')
    routes = pd.read_csv(dir + feed + '_gtfs/' + 'routes.txt')
    shapes = pd.read_csv(dir + feed + '_gtfs/' + 'shapes.txt')
    fare_rules = pd.read_csv(dir + feed + '_gtfs/' + 'fare_rules.txt')
    fare_attributes = pd.read_csv(dir + feed + '_gtfs/' + 'fare_attributes.txt')
    agency = pd.read_csv(dir + feed + '_gtfs/' + 'agency.txt')

    # create new IDs 
    trips = create_id(trips, feed, 'trip_id', 'trip_id')
    trips = create_id(trips, feed, 'route_id', 'route_id')
    trips = create_id(trips, feed, 'shape_id', 'shape_id')

    # get service_id
    service_id_list = get_service_ids(calendar, calendar_dates, day_of_week, service_date)


    # trips
    trips_df = trips.loc[trips['service_id'].isin(service_id_list)]


# verify GTFS trips with KC Metro's trip
trips_df['TRIP_ID'] = trips_df['trip_id'].str[3:]
list_trip1 = trips_df['TRIP_ID'].astype(int).tolist()

trip_verify = trips = pd.read_csv(dir + 'KC_TripIDs_for_verfication/' + 'Spring2018_WeekdayTripIDs.csv')
list_trip2 = trip_verify['TRIP_ID'].tolist()

i = [] 
j = []
for trip in list_trip1: 
    if trip in list_trip2: 
        i.append(trip)
    else: 
        j.append(trip)

