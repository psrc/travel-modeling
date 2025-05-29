#!/usr/bin/python
import os
import pandas as pd
import sqlalchemy

def export_moves_data(config):
    """
    Export MOVES data to CSV files for specified years and counties.
    """


    # Assume default database connection parameters
    hostname = 'localhost'
    username = 'moves'
    password = 'moves'

    for year in config["year_list"]:
        for county in config["county_list"]:
            _dir = os.path.join(config["working_dir"],county)
            if not os.path.exists(_dir):
                os.makedirs(_dir)
            for veh_type in config["vehicle_type_list"]:
                database = county.lower() + '_out_' + veh_type + '_' + year + "_" + config["db_tag"]
                # Running emissions
                _query = "SELECT pollutantID, sourceTypeID, roadTypeID, avgSpeedBinID, hourID, dayID, monthID, linkID, ratePerDistance FROM rateperdistance GROUP BY pollutantID, sourceTypeID, roadTypeID, avgSpeedBinID, hourID, dayID, monthID, linkID"

                e = sqlalchemy.create_engine('mariadb+pymysql://moves:moves@localhost:3306/'+database)
                df = pd.read_sql(_query, con=e)

                #df = pd.read_sql(_query, con=conn)
                df.to_csv(os.path.join(config["working_dir"],county,county+'_'+year+'_'+veh_type+'.csv'), index=False)

                # Start emissions
                _query = 'SELECT * FROM ratepervehicle'
                df = pd.read_sql(_query, con=e)
                df.to_csv(os.path.join(config["working_dir"],county,county+'_'+year+'_'+veh_type+'_starts.csv'), index=False)