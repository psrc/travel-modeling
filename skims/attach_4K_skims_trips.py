# This script attaches skim values to trip records for 4K

# Extract skim values 
import pandas as pd
import numpy as np
import h5py
import glob
import math
from shutil import copyfile
import array as _array
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import inro.emme.database.emmebank as _eb
import json



input_trips_file = r'R:\4K\2014\Mode Choice\raw_inputs\trip_2014_survey_gps_lu_vars.csv'
# this needs to be updated when get the skims
input_skims_dir = r'N:\2014_banks\Banks\Daily'
output_file = r'R:\4K\2014\Mode Choice\estimation_inputs\trips_2014_mode_choice.csv'


# this needs to be filled in later with the actual names if needed,and code down there updated
# currently the code is set up to pick up all matrices in the bank
skims_names =  ['mfaa1tm1','mfaa1tm2']

def get_skim_value(trip, skim):
    return skim[trip.otaz_np][trip.dtaz_np]


def read_in_skims(input_skims_dir):
    print 'reading in skims'

    skims_dict = {}
    emmebank = _eb.Emmebank(input_skims_dir+'\\' +'emmebank')

    for matrix in emmebank.matrices():
          if matrix.type == 'FULL':
              matrix_name = matrix.name
              print 'reading matrix ' + matrix_name
              skims_dict[matrix_name] = matrix.get_numpy_data()

    return  skims_dict

def attach_skims(input_trips, all_skims):
    print 'attaching all skims to the trip records by origin-destination pair'

    input_trips['otaz_np'] = input_trips['otaz']-1
    input_trips['dtaz_np'] = input_trips['dtaz']-1
    
    for matrix_name in all_skims.keys():
        print 'filling trips with ' + matrix_name
        input_trips[matrix_name] = input_trips.apply(get_skim_value, args = (all_skims[matrix_name],) , axis=1)
    
    return input_trips

def main():

    input_trips = pd.read_csv(input_trips_file)
    all_skims = read_in_skims(input_skims_dir)
    trips_w_skims = attach_skims(input_trips, all_skims)
    trips_w_skims.to_csv(output_file)

if __name__ == "__main__":
    main()