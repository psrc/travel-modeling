import os
from os.path import basename
import pandas as pd
from pandas import *
import time
import urllib
import gzip

# Configuration Data to be moved to a config file

# Year for the BAse YEar Inputs that will be downloaded
base_year = 2013

# List Inputs for LEHD Column titles for the consolidated sectors in the Travel Model
construction = ['CNS01', 'CNS02', 'CNS04']
fires = ['CNS09', 'CNS10', 'CNS11', 'CNS12', 'CNS13', 'CNS16', 'CNS17', 'CNS19']
manu = ['CNS05']
wtu = ['CNS03', 'CNS06', 'CNS08']
retail = ['CNS07', 'CNS18']
govt = ['CNS14', 'CNS20']
edu = ['CNS15']

# Directory to put the files
working_directory = 'D:/LEHD/LODES'

def download_LODES():

    # Path to LEHD LODES Files
    LODESfile = urllib.URLopener()
    LODESfile.retrieve('http://lehd.ces.census.gov/data/lodes/LODES7/wa/wac/wa_wac_S000_JT00_'+str(base_year)+'.csv.gz',working_directory+'/'+str(base_year)+'_LODES_Employment.gz')
    
    inF = gzip.open(working_directory+'/'+str(base_year)+'_LODES_Employment.gz','rb')
    s = inF.read()
    inF.close()

    outF = file(working_directory+'/wa_wac_S000_JT00_'+str(base_year)+'.csv','wb')
    outF.write(s)
    outF.close()
    
def model_sectors(my_lehd, working_directory):

    # Create a Dataframe from the Full Statewide LEHD data (by Census Block) and create a starter dataframe with only BLock ID's
    df=pd.read_csv(my_lehd)
    df_blocks = pd.DataFrame(df['w_geocode'])

    # Create a Dataframe by combined sectors of Construction, FIRES, Manu, WTU, Retail, Govt and Education
    # Create Single Column Dataframes by Travel Model Sector for All Jobs and title the column
    df_construction=pd.DataFrame(df[construction].sum(axis=1))
    df_construction.columns = ['Construction']

    df_fires=pd.DataFrame(df[fires].sum(axis=1))
    df_fires.columns = ['FIRES + Services']

    df_manu=pd.DataFrame(df[manu].sum(axis=1))
    df_manu.columns = ['Manufacturing']

    df_wtu=pd.DataFrame(df[wtu].sum(axis=1))
    df_wtu.columns = ['WTU']

    df_retail=pd.DataFrame(df[retail].sum(axis=1))
    df_retail.columns = ['Retail + Food Service']

    df_govt=pd.DataFrame(df[govt].sum(axis=1))
    df_govt.columns = ['Government + Higher Ed']

    df_edu=pd.DataFrame(df[edu].sum(axis=1))
    df_edu.columns = ['K-12 Education']

    my_list = [0] * len(df_edu)
    df_college=pd.DataFrame(my_list)
    df_college.columns = ['College FTE']

    # Use a list of dataframes to join datasets based on the index
    df_all = [df_construction,df_fires,df_manu,df_wtu,df_retail,df_govt,df_edu,df_college]
    df_total = df_blocks.join(df_all)

    # Now Consolidate Statewide data to the PSRC Blocks and replace NaN with 0 (for Blocks with no data).
    psrc_blocks = working_directory + '/adjustments/psrc_blocks.csv'
    df_psrc_blocks = pd.read_csv(psrc_blocks)
    df_psrc = pd.merge(df_psrc_blocks,df_total,on='w_geocode',suffixes=('_x','_y'),how='left')
    df_psrc=df_psrc.fillna(0)

    return df_psrc

def adj_higher_ed(my_lehd,df_psrc, working_directory,input_file):

    # Move Education Jobs to Government Jobs for Colleges since Higher Education is combined with Government in the Model
    df_higher_ed = pd.read_csv(working_directory + '/adjustments/' + input_file)
    
    df=pd.read_csv(my_lehd)
    df_blocks = pd.DataFrame(df['w_geocode'])
    df_edu=pd.DataFrame(df[edu].sum(axis=1))
    df_edu.columns = ['K-12 Education']
    df_adjust = df_blocks.join(df_edu)
    df_adjust = df_adjust.rename(columns = {'K-12 Education': 'Adjustment'})

    # Copy Govt and Education employment into the Block Dataframe for Higher Ed
    df_higher_ed = pd.merge(df_higher_ed,df_adjust,on='w_geocode',suffixes=('_x','_y'),how='left')
    df_higher_ed = df_higher_ed.fillna(0)
    df_higher_ed = df_higher_ed.drop('College',axis=1)

    # Read the Adjustment Column back to the Full Employment DataFrame and replace the NaN with 0
    df_psrc = pd.merge(df_psrc,df_higher_ed,on='w_geocode',suffixes=('_x','_y'),how='left')
    df_psrc=df_psrc.fillna(0)

    # Add the adjustment to Government and Subtract from Education and then delete the adjustment column
    df_psrc['Government + Higher Ed'] = df_psrc['Government + Higher Ed'] + df_psrc['Adjustment']
    df_psrc['K-12 Education'] = df_psrc['K-12 Education'] - df_psrc['Adjustment']
    df_psrc = df_psrc.drop('Adjustment',axis=1)

    return df_psrc

def add_inputs(df_psrc,input_file,adjustment_column):

    # Add in Enlisted Personnel by Blocks
    df_add = pd.read_csv(working_directory + '/adjustments/' + input_file)
    
    # Select out the Column of Base Year Data and add w_geocode to it
    df_by_yr = df_add[str(base_year)]
    df_blocks = pd.DataFrame(df_add['w_geocode'])
    df_total = df_blocks.join(df_by_yr)

    # Now Merge the Adjustment Column in to the main PSRC database and replace NaN with 0
    df_psrc = pd.merge(df_psrc,df_total,on='w_geocode',suffixes=('_x','_y'),how='left')
    df_psrc=df_psrc.fillna(0)

    # Now add the personnel to Government then delete the adjustment column
    df_psrc[adjustment_column] = df_psrc[adjustment_column] + df_psrc[str(base_year)]
    df_psrc = df_psrc.drop(str(base_year),axis=1)

    return df_psrc

def main ():
    
    start_of_production = time.time()

    # Download the appropiate LODES file from the Census Website
    download_LODES()
    my_lehd = working_directory+'/wa_wac_S000_JT00_'+str(base_year)+'.csv'

    # Create Employment Inputs by Block and Adjust inputs as necessary
    df_psrc = model_sectors(my_lehd, working_directory)
    df_psrc = adj_higher_ed(my_lehd,df_psrc, working_directory,'higher_ed.csv')
    df_psrc = add_inputs(df_psrc, 'enlisted_personnel.csv','Government + Higher Ed')
    df_psrc = add_inputs(df_psrc, 'college_fte.csv','College FTE')
    
    # Output CSV file for model use
    df_psrc.to_csv(working_directory + '/psrc_block_employment_' + str(base_year) + '.csv')

    end_of_production = time.time()
    print 'The Total Time for all processes took', (end_of_production-start_of_production), 'seconds to execute.'

if __name__ == "__main__":
    main()

exit()
