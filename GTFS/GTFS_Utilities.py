__copyright__ = "Copyright 2015 Contributing Entities"
__license__   = """
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
        http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import os
import pandas as pd
from numpy import NaN
import pickle
from pandas.util.testing import rands

#from .Logger import FastTripsLogger

class GTFS_Utilities2(object):
    """
    Documentation forthcoming.
    """

    #: File with routes.
    #: TODO document format
    
    def __init__(self, gtfs_dir, start_time, end_time, service_id = 'WEEKDAY'):
        """
        Constructor from dictionary mapping attribute to value.
        """
        #: Trips_stop_times DataFrame
        self.dir = gtfs_dir
        self.start_time = start_time
        self.end_time = end_time
        self.service_id = service_id
        #self.trips = self._get_trips(start_time, end_time, service_id)
        #self.all_trips_df = pd.DataFrame.from_csv(self.dir + '/trips.txt', index_col=False)
        self.df_all_stops_by_trips = self._get_trips_stop_times()
        self.df_stops_by_window = self._get_stops_by_window()
        self.trip_list = self._get_trip_list()
        self.departure_times = self._get_departure_times()
        self.schedule_pattern_dict = self.get_schedule_pattern()
        self.schedule_pattern_df = self.get_schedule_pattern_df()   
        self.unique_stop_sequences_df = self.df_all_stops_by_trips.groupby(['shape_id', 'stop_sequence']).first()
    def  _get_trips_stop_times(self):
        """
        Creates a merged dataframe consisting of trips & stop_ids for the start time, end time and service_id (from GTFS Calender.txt).
        This can include partial itineraries as only stops within the start and end time are included.  
        """
        trips_df = pd.read_csv(self.dir + '/trips.txt', index_col=None)
        # Get the trips for this service_id
        trips_df = trips_df.loc[(trips_df.service_id == self.service_id)]

        stop_times_df = pd.DataFrame.from_csv(self.dir + '/stop_times.txt', index_col=None)
        stop_times_df = self._make_sequence_col(stop_times_df, ['trip_id', 'stop_sequence'], 'trip_id', 'stop_sequence')
        # Add columns for arrival/departure in decimal minutes and hours:
        #stop_times_df['arrival_time_mins'] = stop_times_df.apply(self._convert_to_decimal_minutes, axis=1, args=('arrival_time',))
        # Some schedules only have arrival/departure times for time points, not all stops:
        if stop_times_df['departure_time'].isnull().any():
            stop_times_df['departure_time'].fillna('00:00:00', inplace=True)
            stop_times_df['departure_time_mins'] = stop_times_df.apply(self._convert_to_decimal_minutes, axis=1,args=('departure_time',))
            stop_times_df['departure_time_mins'].replace(0, NaN, inplace = True)
            stop_times_df['departure_time_mins'].interpolate(inplace = True)
        else:
            stop_times_df['departure_time_mins'] = stop_times_df.apply(self._convert_to_decimal_minutes, axis=1,args=('departure_time',))
        stop_times_df['departure_time_hrs'] = stop_times_df['departure_time_mins']/60
        stop_times_df['departure_time_hrs'] = stop_times_df['departure_time_hrs'].astype(int)
        # Get all trips for this time window
        trips_tw_df = stop_times_df.loc[(stop_times_df.departure_time_mins >= self.start_time) & (stop_times_df.departure_time_mins < self.end_time)]
        # Only need the trip_id column
        trips_tw_df = pd.DataFrame(trips_tw_df.trip_id)
        #print len(trips_tw_df)
        trips_tw_df = trips_tw_df.drop_duplicates('trip_id')
        # Merge trips on trip_id, so we can have shape_id. Use inner so we get trips for time window and service_id
        trips_tw_df = trips_tw_df.merge(trips_df, 'inner', left_on = ["trip_id"], right_on = ["trip_id"])
        # Get all the stops for the trips that operate in this window, even if some of the stops occur outside the window
        trips_stop_times_df = stop_times_df.merge(trips_tw_df, 'right', left_on = ["trip_id"], right_on = ["trip_id"])
        trips_stop_times_df = trips_stop_times_df.sort_values(['trip_id', 'stop_sequence'])
        return trips_stop_times_df
        

    def _get_trip_list(self):
        trips = self.df_all_stops_by_trips.trip_id.tolist()
        trips = list(set(trips))   
        return trips

    def _tph_from_frequencies(self):
        
        freq_df = pd.DataFrame.from_csv(self.dir + '/frequencies.txt', index_col=False)
        trips_df = pd.DataFrame.from_csv(self.dir + '/trips.txt', index_col=False)
        # Get the trips for this service_id
        trips_df = trips_df.loc[(trips_df.service_id == self.service_id)]
        trips_df = trips_df[['trip_id', 'shape_id']]

        freq_df['start_time_secs'] = freq_df.apply(self._convert_to_seconds, axis=1,args=('start_time',))
        freq_df['end_time_secs'] = freq_df.apply(self._convert_to_seconds, axis=1,args=('end_time',))
        freq_df = freq_df.merge(trips_df, 'left', left_on = ["trip_id"], right_on = ["trip_id"])
        freq_df.shape_id.fillna(0, inplace = True)
        freq_df = freq_df[freq_df.shape_id != 0]

        my_list = []
        for row in freq_df.iterrows():
            for i in range(row[1].start_time_secs, row[1].end_time_secs, row[1].headway_secs):
                my_list.append({'trip_id' : row[1].trip_id, 'shape_id' : row[1].shape_id, 'departure_time_hrs' : i/3600})
                
        first_departure = pd.DataFrame(my_list)
        first_departure = first_departure.groupby(['shape_id', 'departure_time_hrs'])['departure_time_hrs'].count()
        first_departure_df = pd.DataFrame(first_departure)
        first_departure_df.reset_index(level=0, inplace=True)
        first_departure_df = first_departure_df.rename(columns = {'departure_time_hrs' : 'frequency'})
        first_departure_df.reset_index(level=0, inplace=True)
        t = pd.pivot_table(first_departure_df, values='frequency', index=['shape_id'], columns=['departure_time_hrs'])
        t = t.fillna(0)

        for col in t.columns:
            if not col == 'shape_id':
                t = t.rename(columns = {col : 'hour_' + str(col)})
        return t
    
    def _get_stops_by_window(self):
         stops_by_window_df = self.df_all_stops_by_trips.loc[(self.df_all_stops_by_trips.departure_time_mins >= self.start_time) & (self.df_all_stops_by_trips.departure_time_mins < self.end_time)]
         return stops_by_window_df
    
        
    def _get_departure_times(self):
        """
        Returns a dictionary where the key is shape_id and the value is a list of departure times at the first stop for the time window 
        specified in the constructor. 
        """
        
        first_departure = self.df_stops_by_window.sort_values('stop_sequence', ascending=True).groupby('trip_id', as_index=False).first()
        first_departure = first_departure.loc[(first_departure.stop_sequence == 1)]
        departure_times = {k: g["departure_time_mins"].tolist() for k,g in first_departure.groupby("shape_id")}
        
        return departure_times

    
       
    def get_departure_times_by_ids(self, list_of_shape_ids):
        """
        Using the list_of_shape_ids parameter, returns a list of combined departure times at the first stop for the time window 
        specified in the constructor. This can be used to get departure times for indivudal TDM routes that represents more than 
        one shape_id. 
        """
        
        departure_time_dict = dict((k, self.departure_times[k]) for k in (list_of_shape_ids))
        departure_times = []
        # We are getting the departure times for one or more shape_ids so put them all 
        # in one list:oh
        for departure_time in departure_time_dict.values():    
            departure_times.extend(departure_time)
        
        return departure_times
        
    def get_trips_per_hour(self):
        """
        Returns a dictionary where key is shape_id and value is the number of departures from the first stop. Does this only for
        the time window specified in the constructor.  
        """
        # get unique trips:
        first_departure = self.df_stops_by_window.sort_values('stop_sequence', ascending=True).groupby('trip_id', as_index=False).first()
        first_departure = first_departure.loc[(first_departure.stop_sequence == 1)]
        first_departure = first_departure.groupby(['shape_id', 'departure_time_hrs'])['departure_time_hrs'].count()
        first_departure_df = pd.DataFrame(first_departure)
        first_departure_df.reset_index(level=0, inplace=True)
        first_departure_df = first_departure_df.rename(columns = {'departure_time_hrs' : 'frequency'})
        first_departure_df.reset_index(level=0, inplace=True)
        t = pd.pivot_table(first_departure_df, values='frequency', index=['shape_id'], columns=['departure_time_hrs'])
        t = t.fillna(0)
        for col in t.columns:
            if not col == 'shape_id':
                t = t.rename(columns = {col : 'hour_' + str(col)})
        
        return t

    def get_tph_rep_trip_id(self):
       
         #trips_tw_df = trips_tw_df.merge(trips_df, 'inner', left_on = ["trip_id"], right_on = ["trip_id"])
        a = self.df_all_stops_by_trips.merge(self.get_schedule_pattern_df(), 'inner', left_on=['trip_id'], right_on=['orig_trip_id'])
        #get the first stop for every trip
        first_departure = a.sort_values('stop_sequence', ascending=True).groupby('trip_id', as_index=False).first()
        #this may not be necessary
        first_departure = first_departure.loc[(first_departure.stop_sequence == 1)]
        first_departure = first_departure.groupby(['rep_trip_id', 'departure_time_hrs'])['departure_time_hrs'].count()
        first_departure_df = pd.DataFrame(first_departure)
        first_departure_df.reset_index(level=0, inplace=True)
        first_departure_df = first_departure_df.rename(columns = {'departure_time_hrs' : 'frequency'})
        first_departure_df.reset_index(level=0, inplace=True)
        t = pd.pivot_table(first_departure_df, values='frequency', index=['rep_trip_id'], columns=['departure_time_hrs'])
        t = t.fillna(0)
        for col in t.columns:
            if not col == 'rep_trip_id':
                t = t.rename(columns = {col : 'hour_' + str(col)})
        
        return t
             
    def get_tph_emme_rep_trip_id(self, pickle_file):
        f = open(pickle_file, 'r')
        my_file = pickle.load(f)
        f.close()
        trip_ids_df = pd.DataFrame(None, columns = ['rep_trip', 'trip_id'], dtype = int)

        for dict in my_file[1]:
            trip_ids = dict['trip_ids']
            #rep_trip_id = int(dict['rep_trip'])
            rep_trip_id = dict['rep_trip']
            values = [x for x in trip_ids.split(',') if x]
            values = [x.strip(' ') for x in values]
            data = [(rep_trip_id, x) for x in values]
            df = pd.DataFrame(data, columns = ['rep_trip', 'trip_id'])
            trip_ids_df = trip_ids_df.append(df)

        trip_ids_df[['rep_trip', 'trip_id']] = trip_ids_df[['rep_trip', 'trip_id']]  
       
        #1. open pickle file:
        #2. extract dictionary of rep trip and list of trips
        #3. Loop through each rep trip id, get the trips per hour

         #trips_tw_df = trips_tw_df.merge(trips_df, 'inner', left_on = ["trip_id"], right_on = ["trip_id"])
        df = self.df_all_stops_by_trips.loc[self.df_all_stops_by_trips.groupby("trip_id")["stop_sequence"].idxmin()]
        df = df[['trip_id', 'departure_time_hrs']]
        df['trip_id'] = df['trip_id'].map(lambda x: x.strip())
        trip_ids_df['trip_id'] = trip_ids_df['trip_id'].map(lambda x: x.strip())
        first_departure = trip_ids_df.merge(df, 'left', left_on=['trip_id'], right_on=['trip_id'])
        #get the first stop for every trip
        #first_departure = a.sort_values('stop_sequence', ascending=True).groupby('trip_id', as_index=False).first()
        #this may not be necessary
        #first_departure = first_departure.loc[(first_departure.stop_sequence == 1)]
        first_departure = first_departure.groupby(['rep_trip', 'departure_time_hrs'])['departure_time_hrs'].count()
        first_departure_df = pd.DataFrame(first_departure)
        first_departure_df.reset_index(level=0, inplace=True)
        first_departure_df = first_departure_df.rename(columns = {'departure_time_hrs' : 'frequency'})
        first_departure_df.reset_index(level=0, inplace=True)
        t = pd.pivot_table(first_departure_df, values='frequency', index=['rep_trip'], columns=['departure_time_hrs'])
        t = t.fillna(0)
        for col in t.columns:
            if not col == 'rep_trip_id':
                t = t.rename(columns = {col : 'hour_' + str(col)})
        
        return t    
    def get_weighted_trips_per_hour(self):
        #get the rounded mean departure time for each trip:
        a = self.df_all_stops_by_trips.groupby(['trip_id', 'shape_id'])['departure_time_hrs'].mean()
        b = pd.DataFrame(a)
        b.reset_index(level=0, inplace=True)
        b.reset_index(level=0, inplace=True)
        b['departure_time_hrs'] = b['departure_time_hrs'].round().astype(int)
        first_departure = b.groupby(['shape_id', 'departure_time_hrs'])['departure_time_hrs'].count()
        first_departure_df = pd.DataFrame(first_departure)
        first_departure_df.reset_index(level=0, inplace=True)
        first_departure_df = first_departure_df.rename(columns = {'departure_time_hrs' : 'frequency'})
        first_departure_df.reset_index(level=0, inplace=True)
        t = pd.pivot_table(first_departure_df, values='frequency', index=['shape_id'], columns=['departure_time_hrs'])
        t = t.fillna(0)
        for col in t.columns:
            if not col == 'shape_id':
                t = t.rename(columns = {col : 'hour_' + str(col)})
        
        return t

    def get_weighted_tph_rep_trip_id(self):
        #get the rounded mean departure time for each trip:
        a = self.df_all_stops_by_trips.merge(self.get_schedule_pattern_df(), 'inner', left_on=['trip_id'], right_on=['orig_trip_id'])
        #print a.head()
        a = a.groupby(['trip_id', 'rep_trip_id'])['departure_time_hrs'].mean()
        b = pd.DataFrame(a)
        b.reset_index(level=0, inplace=True)
        b.reset_index(level=0, inplace=True)
        b['departure_time_hrs'] = b['departure_time_hrs'].round().astype(int)
        first_departure = b.groupby(['rep_trip_id', 'departure_time_hrs'])['departure_time_hrs'].count()
        first_departure_df = pd.DataFrame(first_departure)
        first_departure_df.reset_index(level=0, inplace=True)
        first_departure_df = first_departure_df.rename(columns = {'departure_time_hrs' : 'frequency'})
        first_departure_df.reset_index(level=0, inplace=True)
        t = pd.pivot_table(first_departure_df, values='frequency', index=['rep_trip_id'], columns=['departure_time_hrs'])
        t = t.fillna(0)
        for col in t.columns:
            if not col == 'rep_trip_id':
                t = t.rename(columns = {col : 'hour_' + str(col)})
        
        return t

    

    def _make_sequence_col(self, data_frame, sort_list, group_by_col, seq_col):

        """
        Sorts a pandas dataframe using sort_list, then creates a column of sequential integers (1,2,3, etc.) for
        groups, using the group_by_col. Then drops the existing sequence column and re-names the new sequence column.
        """
        #sort on tripId, sequence
        data_frame = data_frame.sort_values(sort_list, ascending=[1,1])
        #create a new field, set = to the position of each record in a group, grouped by tripId
        data_frame['temp'] = data_frame.groupby(group_by_col).cumcount() + 1
        #drop the old sequence column
        data_frame = data_frame.drop(seq_col, axis=1)
        #rename new column:
        data_frame = data_frame.rename(columns = {'temp':seq_col})

        return data_frame

    def _convert_to_decimal_minutes(self, row, field):
        '''Convert HH:MM:SS to seconds since midnight, for comparison purposes.'''
        H, M, S = row[field].split(':')
        seconds = float(((float(H) * 3600) + (float(M) * 60) + float(S))/60)
        
        return seconds

    def _convert_to_seconds(self, row, field):
        h, m, s = row[field].split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
    
    def get_schedule_pattern(self):
        """
        Returns a nested diciontary where the first level key is route_id and values are respresentative trip_ids that have unique stop sequences.
        These are are used as keys for the second level where each value is a dictinary that includes a list of trips_id's that share this
        stop pattern and a list of ordered stops.
        {route_id : trip_id {trips_ids : [list of trip ids], stops : [list of stops]}}
        """

        # Create a dictionary where the key is a tuple of trip_id, route_id and the value is a list of stop sequences for the trip
        # Need to use all the stops for the trips within the time window, even if those stops fall outside the time winwdow because we 
        # are interested in unique stop sequences 
        stop_sequence_dict = {k: list(v) for k,v in self.df_all_stops_by_trips.groupby(['trip_id', 'route_id'])['stop_id']}
        
        # Empty dictionary to store unique stop sequences
        my_dict = {}
        for key, value in stop_sequence_dict.iteritems():
            trip_id = key[0]
            route_id = key[1]
            # Handle some branching later on
            found = False
            # If this is the first trip for this route, just add it
            if not route_id in my_dict.keys():
                my_dict[route_id] = {trip_id : {'stops': value, 'trip_ids' : [trip_id]}}
            # Otherwise check to see if this stop sequence has already been added for this route
            else: 
                for k, v in my_dict[route_id].iteritems():
                    if value == v['stops']:
                        # This stop sequence has already been added for this route, add the trip_id to the list of trip_ids that have this sequence in common.
                        my_dict[route_id][k]['trip_ids'].append(trip_id)
                        found = True
                        break
                if not found:
                    # Add the stop sequence and route, trip info
                    my_dict[route_id][trip_id] = {'stops': value, 'trip_ids' : [trip_id]}
            # Set back to False for next iteration
            found = False
        return my_dict
    
    def get_schedule_pattern_df(self):
        rows = []
        for route_id, trips in self.schedule_pattern_dict.iteritems():
            for trip_id, data in trips.iteritems():
                for trip in data['trip_ids']:
                    #print trip
                    rows.append({'route_id' : route_id, 'trip_id1' : trip_id, 'trip_id2': trip})  
        df2 = pd.DataFrame(rows)
        df = self.df_all_stops_by_trips.drop_duplicates(['trip_id'])
        df2 = df2.merge(df[['trip_id','shape_id']], how ='right', left_on = ["trip_id2"], right_on = ["trip_id"])
        df2 = df2.rename(columns = {'trip_id1' : 'rep_trip_id', 'trip_id' : 'orig_trip_id'})
        df2 = df2.drop('trip_id2', 1)
        #b = df2.groupby('trip_id1').shape_id.nunique()
        #c = df2.shape_id.nunique()
        return df2
           
test = GTFS_Utilities2(r"D:\stefan\Transit_2040_OSM\GTFS\2040_GTFS\revised_final", 0, 1439, 1)

#am =test.get_tph_emme_rep_trip_id(r'D:\stefan\Transit_2018\reversible_routes\AM\AM_detail.p')
print 'done'
#am =test.get_tph_emme_rep_trip_id(r'D:\stefan\Transit_2018\reversible_routes\AM\AM_detail.p')
bus =test.get_tph_emme_rep_trip_id(r'D:\stefan\Transit_2040_OSM\Outputs\All\Bus\MD_detail.p')
ferry =test.get_tph_emme_rep_trip_id(r'D:\stefan\Transit_2040_OSM\Outputs\All\Ferry\MD_detail.p')
cr =test.get_tph_emme_rep_trip_id(r'D:\stefan\Transit_2040_OSM\Outputs\All\CR\MD_detail.p')
lr =test.get_tph_emme_rep_trip_id(r'D:\stefan\Transit_2040_OSM\Outputs\All\LR\MD_detail.p')





#pm =test.get_tph_emme_rep_trip_id(r'D:\stefan\Transit_2018\reversible_routes\PM\PM_detail.p')


#md_cols = [col for col in md.columns if col not in am.columns]
#pm_cols = [col for col in pm.columns if col not in md.columns]

#md = md[md_cols]


#final = pd.concat([am,md,pm], axis = 1)


                
                                                                                   
     



        


                
                                                                                   
     



        