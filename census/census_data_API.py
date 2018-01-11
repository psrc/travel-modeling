# This script creates data summaries in the PSRC region
# Created by Puget Sound Regional Council Staff
# December 2017

# Load the libraries we need
import pandas as pd
import urllib
import time
import datetime as dt     

#from census_variables import *


working_directory = r'C:\Users\SChildress\Documents\Scripted-Data-Profiles'
my_key = 'd35ff72cb418d90e16e0a6e221a69c00e1209c5c'
data_years =['2016']
dataset = 'acs/acs1/subject'

geography_ids = {'033': ('county','King','co'),
                       '035': ('county','Kitsap','co'),
                       '053': ('county','Pierce','co'),
                       '061': ('county','Snohomish','co'),
                       '03180':('place','Auburn' ,'place'),
                       '05210':('place','Bellevue' ,'place'),
                       '22640':('place','Everett' ,'place'),
                       '23515':('place','Federal Way' ,'place'),
                       '35415':('place','Kent', 'place'),
                       '35940':('place','Kirkland' ,'place'),
                       '57745':('place','Renton' ,'place'),
                       '63000':('place','Seattle' ,'place'),
                       '70000':('place','Tacoma' ,'place'),
                       '80010':('place','Yakima' ,'place')
                      }

## Dictionaries for Census Data Tables with labels
tables = {'B01001_001E':'Total People',
          'B01001_003E':'Total Females Under 5',
          'B01001_027E':'Percent People Over 18 years',
          'S0101_C01_028E':'Percent People Over 65 years',
          'S1701_C01_001E':'Population with Pov Status',
          'S1701_C01_042E':'Income Below 200% Poverty'
          }




# Functions to Download and Format Census API datatables
def create_census_url(dataset, data_tables, geography_type, geography_id, year, api_key, ):
    census_api_call = 'https://api.census.gov/data/' + str(year) + '/'+ dataset + '?get=' + data_tables + '&' + 'for='+geography_type+':'+ geography_id+ '&in=state:53'+ '&key=' + api_key
    return census_api_call

def download_census_data(data_url):

    response = urllib.urlopen(data_url)
    census_data = response.read()
    
    return census_data

for key in tables:
    writer = pd.ExcelWriter(working_directory + '/output/acs'+'-'+ tables[key]+'.xlsx')
    new_df = pd.DataFrame()

    census_data = 'NAME,'+key

    print 'working on '+ key
    for data_year in data_years:
        print data_year
        for geography_id in geography_ids:
             # Create the query and do the census api call to collect the data in json format
            url_call = create_census_url(dataset, census_data, geography_ids[geography_id][0], geography_id,data_year, my_key)
            print url_call
            current_df= pd.read_json(download_census_data(url_call))
            current_df = current_df.iloc[1:]
            new_df = new_df.append(current_df)


    new_df.drop(new_df.columns[[2,3]], axis=1, inplace=True)
    new_df.columns = ['Geography', tables[key]]

    new_df[tables[key]] = pd.to_numeric(new_df[tables[key]])

    new_df.to_excel(writer, sheet_name = tables[key], index = False)
    writer.save()