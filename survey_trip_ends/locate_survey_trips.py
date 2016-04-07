import pandas as pd
#import geopandas as gpd
#from shapely.geometry import Polygon, Point, MultiPoint
import geocoder
from pyproj import Proj, transform
import pyproj
import h5py
import numpy as np
from operator import itemgetter

LOG_EVERY_N = 100

# Parcels
#parcels = pd.DataFrame.from_csv(r'R:\SoundCast\Inputs\2010\landuse\parcels_urbansim.txt', sep = " ", index_col = None )
parcels = pd.DataFrame.from_csv(r'D:\Stefan\geocode_survey_trips\parcels.txt', sep = " ", index_col = None )
for col in parcels.columns:
    parcels.rename(columns = {col:col.upper()}, inplace = True)

# Trips
trips = pd.DataFrame.from_csv(r'D:\Stefan\geocode_survey_trips\survey_trips_destination.csv', index_col = None )
trips['real_trip_id'] = trips.FID_2014_p + 1
trips['real_parcel_id'] = 0
trips['distance'] = 0
trips['test_passed'] = 0
purpose_recode = {1: 0, 2: 1, 3:1, 4:5, 5:5, 6:2, 7:9, 8:4, 9:3, 10:8, 11:6, 12:7, 13:8, 14:7, 15:10, 16:16}
trips['new_purpose'] = trips["d_purpose"].map(purpose_recode)

# Trip ends to Near Parcels:
near_parcels_660 = pd.DataFrame.from_csv(r'D:\Stefan\geocode_survey_trips\trips_d_660.csv', index_col = None )
#near_parcels_1320 = pd.DataFrame.from_csv(r'D:\Stefan\geocode_survey_trips\trips_d_1320.csv', index_col = None )

# Households
hh_persons = h5py.File(r'D:\Stefan\geocode_survey_trips\hh_and_persons.h5', 'r')
hh_set = hh_persons['Household']
col_dict = {}
for col in hh_set.keys():
    if col <> 'incomeconverted':
        my_array = np.asarray(hh_set[col])
        col_dict[col] = my_array
hh_df = pd.DataFrame(col_dict)

def reproject_to_wgs84(parcels_df):
    '''
    Converts the passed in coordinates from their native projection (default is state plane WA North-EPSG:2926)
    to wgs84. Returns a two item tuple containing the longitude (x) and latitude (y) in wgs84. Coordinates
    must be in meters hence the default conversion factor- PSRC's are in state plane feet.  
    '''
    ESPG = "+init=EPSG:2926" 
    conversion = 0.3048006096012192
    #print longitude, latitude
    # Remember long is x and lat is y!
    prj_wgs = Proj(init='epsg:4326')
    prj_sp = Proj(ESPG)
    
    # Need to convert feet to meters:
    longitude = parcels_df.XCOORD_P * conversion
    latitude = parcels_df.YCOORD_P * conversion
    x, y = transform(prj_sp, prj_wgs, longitude, latitude)
    #print parcels_df.PARCELID, x, y
    return parcels_df.PARCELID, x, y


def get_parcels_within_buffer(trip_lat_long, parcels_df, max_distance_in_feet):
    geod = pyproj.Geod(ellps='WGS84')
    buffer = max_distance_in_feet * 0.3048
    #taz_points = taz_df.as_matrix(columns=['lon', 'stop_lat', 'taz'])
    parcel_points = parcels_df.as_matrix(columns=['long', 'lat', 'parcelid'])
    parcel_list = []
    
    x = [[geod.inv(trip_lat_long[2], trip_lat_long[1], y[0], y[1])[2], trip_lat_long[0], y[2]] for y in parcel_points if geod.inv(trip_lat_long[2], trip_lat_long[1], y[0], y[1])[2] <= buffer]
    return x
       
def test1(parcel_id, trip_record):
    parcel_row = parcels.loc[(parcels.PARCELID == parcel_id)]
    #home
    if int(trip_record.new_purpose) == 0 and len(hh_df.loc[(hh_df.hhparcel==parcel_id)]) > 0:
        return True
    #work
    elif int(trip_record.new_purpose) == 1 and int(parcel_row.EMPTOT_P) > 0:
        return True
    #school
    elif int(trip_record.new_purpose) == 2 and (int(parcel_row.STUGRD_P) + int(parcel_row.STUHGH_P) + int(parcel_row.STUUNI_P)) > 0:
        return True
    #escort
    elif int(trip_record.new_purpose) == 3 and (int(parcel_row.EMPTOT_P) + int(parcel_row.STUGRD_P) + int(parcel_row.STUHGH_P)) > 0:
        return True
    #personal bus
    elif int(trip_record.new_purpose) == 4 and (int(parcel_row.EMPRET_P) + int(parcel_row.EMPSVC_P)) > 0:
        return True
    #shop
    elif int(trip_record.new_purpose) == 5 and int(parcel_row.EMPRET_P) > 0:
        return True
    #meal
    elif int(trip_record.new_purpose) == 6 and int(parcel_row.EMPFOO_P) > 0:
        return True
    #social
    elif int(trip_record.new_purpose) == 7 and len(hh_df.loc[(hh_df.hhparcel ==parcel_id)]) > 0:
        return True
    #recreational
    elif int(trip_record.new_purpose) == 8 and len(hh_df.loc[(hh_df.hhparcel ==parcel_id)]) > 0:
        return True
    #medical
    elif int(trip_record.new_purpose) == 9 and int(parcel_row.EMPMED_P) > 0:
        return True
    #change mode inserted purpose
    elif int(trip_record.new_purpose) == 10:
        return True
    #other
    elif int(trip_record.new_purpose)== 16 and (int(parcel_row.EMPTOT_P) + int(parcel_row.STUGRD_P) + int(parcel_row.STUHGH_P)) > 0:
        return True
    else:
        return False

def test2(parcel_id, trip_record):
    parcel_row = parcels.loc[(parcels.PARCELID == parcel_id)]
    #home
    if int(trip_record.new_purpose) == 0 and len(hh_df.loc[(hh_df.hhparcel ==parcel_id)]) + (int(parcel_row.STUGRD_P) + int(parcel_row.STUHGH_P)) > 0:
        return True
    #work
    elif int(trip_record.new_purpose) == 1 and int(parcel_row.EMPTOT_P) + len(hh_df.loc[(hh_df.hhparcel ==parcel_id)]) > 0:
        return True
    #school
    elif int(trip_record.new_purpose) == 2 and (int(parcel_row.STUGRD_P) + int(parcel_row.STUHGH_P) + int(parcel_row.STUUNI_P) + int(parcel_row.EMPEDU_P)) > 0:
        return True
    #escort, pers bus, social, recreational
    elif (int(trip_record.new_purpose) == 3 or int(trip_record.new_purpose) == 4 or int(trip_record.new_purpose) == 7 or int(trip_record.new_purpose) == 8 + int(trip_record.new_purpose) == 16) and (int(parcel_row.EMPTOT_P) > 0 + int(parcel_row.STUGRD_P) + int(parcel_row.STUHGH_P) + int(parcel_row.STUUNI_P) + len(hh_df.loc[(hh_df.hhparcel ==parcel_id)])) > 0:
        return True
    #shop
    elif int(trip_record.new_purpose) == 5 and int(parcel_row.EMPTOT_P) > 0:
        return True
    #meal
    elif int(trip_record.new_purpose) == 6 and int(parcel_row.EMPTOT_P) > 0:
        return True
    #medical
    elif int(trip_record.new_purpose) == 9 and int(parcel_row.EMPTOT_P) > 0:
        return True
    #meal
    elif int(trip_record.new_purpose) == 5 and int(parcel_row.EMPTOT_P) > 0:
        return True
    #shop
    elif int(trip_record.new_purpose) == 6 and int(parcel_row.EMPTOT_P) > 0:
        return True
    #personal bus, social, recreation, serve passenger, escort, other
    elif int(trip_record.new_purpose) > 6 and (int(parcel_row.EMPTOT_P) > 0 + int(parcel_row.STUGRD_P) + int(parcel_row.STUHGH_P) + int(parcel_row.STUUNI_P) + len(hh_df.loc[(hh_df.hhparcel ==parcel_id)])) > 0:
        return True
    else:
        return False


# First test if geocoded parcel is right:
a = 0
for i, row in trips.iterrows():
#TEST 1
    if (a % LOG_EVERY_N) == 0:
        print a
    trip = pd.DataFrame(row).transpose()
    if int(trip.parcel_id) <> 0:
        if test1(int(trip.parcel_id), trip):
            trips.loc[i, "real_parcel_id"] = int(trip.parcel_id)
            trips.loc[i, "test_passed"] = 1
    a = a + 1
#parcel 0 did not pass the 1st test, see if there is on within 1/8 mile that does
#TEST 1
a = 0
for i, row in trips.iterrows():
    if (a % LOG_EVERY_N) == 0:
        print a
    
    trip = pd.DataFrame(row).transpose()
    if int(trip.real_parcel_id) == 0:
        trip_parcels = near_parcels_660.loc[(near_parcels_660.trip_id == int(trip.real_trip_id))]
        trip_parcels = trip_parcels.sort(['DISTANCE'])
        for x, parcel in trip_parcels.iterrows():
            print a
            parcel = pd.DataFrame(parcel).transpose()
            if test1(int(parcel.parcel_id), trip):
                print 'true2'
                trips.loc[i, "real_parcel_id"] = int(parcel.parcel_id)
                trips.loc[i, "distance"] = int(parcel.DISTANCE)
                trips.loc[i, "test_passed"] = 2
                break
    a = a + 1
#Parcel 0 and 1 did not pass 1st test, let's see if parcel 0 passes second test:
#TEST 2
for i, row in trips.iterrows():
    trip = pd.DataFrame(row).transpose()
    if int(trip.real_parcel_id) == 0:   
        if int(trip.parcel_id) <> 0:
            if test2(int(trip.parcel_id), trip):
                print 'true3'
                trips.loc[i, "real_parcel_id"] = int(trip.parcel_id)
                trips.loc[i, "test_passed"] = 3
      
##parcel 0 did not pass the 2nd test, see if there is one within 1/8 mile that does
##TEST 2
for i, row in trips.iterrows():
    trip = pd.DataFrame(row).transpose()
    if int(trip.real_parcel_id) == 0:
        trip_parcels = near_parcels_660.loc[(near_parcels_660.trip_id == int(trip.real_trip_id))]
        trip_parcels = trip_parcels.sort(['DISTANCE'])
        for x, parcel in trip_parcels.iterrows():
            parcel = pd.DataFrame(parcel).transpose()
            if test2(int(parcel.parcel_id), trip):
                print 'true2'
                trips.loc[i, "real_parcel_id"] = int(parcel.parcel_id)
                trips.loc[i, "distance"] = int(parcel.DISTANCE)
                trips.loc[i, "test_passed"] = 4
                

#########Increase Buffer##########
#TEST 1, large buffer
#for i, row in trips.iterrows():
#    trip = pd.DataFrame(row).transpose()
#    if trip.real_parcel_id == 0:
#        trip_parcels = near_parcels_1320.loc[(near_parcels_1320.real_trip_id == trip.real_trip_id)]
#        trip_parcels = trip_parcels.sort(['DISTANCE'])
#        for x, parcel in trip_parcels.iterrows():
#            parcel = parcel[1]
#            if test1(parcel.parcel_id, trip):
#                print 'true2'
#                trips.loc[i, "real_parcel_id"] = parcel.parcel_id
#                trips.loc[i, "distance"] = parcel.distance

## TEST 2, large buffer
#for i, row in trips.iterrows():
#    trip = pd.DataFrame(row).transpose()
#    if trip.real_parcel_id == 0:
#        trip_parcels = near_parcels_1320.loc[(near_parcels_1320.real_trip_id == trip.real_trip_id)]
#        trip_parcels = trip_parcels.sort(['DISTANCE'])
#        for x, parcel in trip_parcels.iterrows():
#            parcel = parcel[1]
#            if test2(parcel.parcel_id, trip):
#                print 'true2'
#                trips.loc[i, "real_parcel_id"] = int(parcels.parcel_id)
#                trips.loc[i, "distance"] = int(parcel.distance)


#x = trips.apply(test2, axis = 1)

#test = pd.DataFrame(x.tolist(), columns=['trip_id','parcel_id', 'distance'])