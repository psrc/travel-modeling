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
dataset = 'acs/acs1/cprofile'
comparision_year = '2012'
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
tables = {'CP02_*_001E':'Total Households',
          'CP02_*_013E': 'Households People Under 18',
          'CP02_*_014E': 'Households People Over 65',
          'CP02_*_015E' : 'Average HH Size',
          'CP05_*_032E' : 'Race - One White',
          'CP05_*_033E' : 'Race -One Black'
         }

years_to_compare = ['2012','2016']



# Functions to Download and Format Census API datatables
def create_census_url(dataset, data_tables, geography_type, geography_id, year, year_to_compare, api_key, ):
    data_tables = data_tables.replace('*', year_to_compare)
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
            first_year = 1
            for year_compare in years_to_compare:
                url_call = create_census_url(dataset, census_data, geography_ids[geography_id][0], geography_id,data_year,year_compare, my_key)
                print url_call
                if first_year:
                    last_df =pd.read_json(download_census_data(url_call))
                    print last_df
                    last_df.drop(last_df.columns[[2,3]], axis=1, inplace=True)
                    last_df.columns = ['Geography', tables[key]+'_'+ str(year_compare)]
                    last_df = last_df.iloc[1:]
                    last_df[tables[key]+'_'+ str(year_compare)]=pd.to_numeric(last_df[tables[key]+'_'+ str(year_compare)])
                    first_year = False
                else:
                    current_df= pd.read_json(download_census_data(url_call))
                    current_df.drop(current_df.columns[[2,3]], axis=1, inplace=True)
                    current_df.columns = ['Geography', tables[key]+'_'+ str(year_compare)]
                    current_df = current_df.iloc[1:]
                    current_df = pd.merge(current_df, last_df, on = 'Geography')
                    current_df[tables[key]+'_'+ str(year_compare)]=pd.to_numeric(current_df[tables[key]+'_'+ str(year_compare)])
                    last_df = current_df

            #current_df = current_df.iloc[1:]
            new_df = new_df.append(current_df)



  

   
    new_df.to_excel(writer, sheet_name = tables[key], index = False)
    writer.save()