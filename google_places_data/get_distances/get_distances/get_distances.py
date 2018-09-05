from googleplaces import GooglePlaces
import pandas as pd
import os
import numpy as np

#where to find googleplaces: https://github.com/slimkrazy/python-google-places

working_dir = r'C:\Users\SChildress\Documents\google_places_data'
zone_file = 'zone_lat_long_test.csv'

amenity_types = ['supermarket','library','hospital','pharmacy','post_office','school','cafe','store']
amenity_type = 'supermarket'
API_KEY = open(working_dir+'/google_api_key.txt').read()
google_places = GooglePlaces(API_KEY)
# 10K is the farther away to look
max_search =10000

def distance(s_lat, s_lng, e_lat, e_lng):
        # approximate radius of earth in km
    R = 3959.0
    
    s_lat = s_lat*np.pi/180.0                      
    s_lng = np.deg2rad(s_lng)     
    e_lat = np.deg2rad(e_lat)                       
    e_lng = np.deg2rad(e_lng)  
    
    d = np.sin((e_lat - s_lat)/2)**2 + np.cos(s_lat)*np.cos(e_lat) * np.sin((e_lng - s_lng)/2)**2
    
    return 2 * R * np.arcsin(np.sqrt(d))

def find_distance(zone_id, zone_lat, zone_long, amenity_type):
    query_result = google_places.nearby_search(keyword=amenity_type,
    lat_lng={'lat': zone_lat, 'lng': zone_long}, rankby = 'distance', 
    radius=max_search)

    try:
        nearest_lat = float(query_result.places[0].geo_location['lat'])
        nearest_long = float(query_result.places[0].geo_location['lng'])
        dist_between = distance(zone_lat, zone_long, nearest_lat, nearest_long)
    except:
        dist_between = -1
    
    return pd.Series({'ZoneID': zone_id, 'Dist_'+amenity_type:dist_between})



def get_distances(zones):
    amenity_count = 0
    for amenity in amenity_types:
        print amenity
        if amenity_count == 0:
            zones_out = zones.apply(lambda row: find_distance(row['ZoneID'], row['LAT'], row['LONG'], amenity), axis=1)
            
        else:
            zones_next = zones.apply(lambda row: find_distance(row['ZoneID'], row['LAT'], row['LONG'], amenity), axis=1)
            zones_out = pd.merge(zones_next, zones_out, on ='ZoneID')
        
        amenity_count = amenity_count + 1

        return zones_out


def main():
    
    zones = pd.read_csv(working_dir +'\\' +zone_file)
    zones_distances = get_distances(zones)

    # read in the list of zone centroids lat longs
    # define list of amenities to search for
    # for each zone for each amenity find the lat long of the nearest amenity by type
    #write it out




if __name__ == "__main__":
    main()

