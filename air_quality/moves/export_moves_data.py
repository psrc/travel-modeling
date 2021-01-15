#!/usr/bin/python
import pandas as pd
from __future__ import print_function

hostname = 'localhost'
username = 'root'
password = 'IndiaPaleAle!'

# Simple routine to run a query on a database and print the results:
def doQuery( conn ) :
    cur = conn.cursor()

    cur.execute( "SELECT pollutantID, sourceTypeID FROM rateperdistance" )

    for firstname, lastname in cur.fetchall() :
        print( firstname, lastname )

# Fetch 
#print( "Using mysqlclient (MySQLdb):" )
#import MySQLdb
#myConnection = MySQLdb.connect( host=hostname, user=username, passwd=password, db=database )
#doQuery( myConnection )
#myConnection.close()

database  = 'king_out_2050_medium_07_01_2'
_query = "SELECT pollutantID, sourceTypeID, roadTypeID, avgSpeedBinID, hourID, dayID, monthID, linkID, sum(ratePerDistance) FROM rateperdistance GROUP BY pollutantID, sourceTypeID, roadTypeID, avgSpeedBinID, hourID, dayID, monthID, linkID;"
conn = MySQLdb.connect( host=hostname, user=username, passwd=password, db=database )
cur = conn.cursor()
cur.execute(_query)

df = pd.read_sql(_query, con=conn)