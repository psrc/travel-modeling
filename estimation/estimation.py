import pandas as pd

def load_f12(working_dir, fname, suffix=None):
    """
    Convert F12 output to dataframe, calcualte t-stat
    """
    df = pd.read_csv(working_dir + r'\\' + fname, delim_whitespace=True, skiprows=1)
    
    # Assume a fixed format for conversion
    df = df.ix[1:,0:5]
    cols = ['coefficient','constrained','value','standard error']
    if suffix != None:
        cols = [col + suffix for col in cols]
    cols.insert(0,'id')
    df.columns = cols

    # drop the covariance matrix bit, marked with -1 
    df = df.ix[:df[df['id'] == "-1"].index.tolist()[0]-1,:]
    
    # Calculate a t-statistic
    df['standard error'] = df['standard error'].astype('float')
    df['value'] = df['value'].astype('float')
    df['t-stat'] = abs(df['value']/df['standard error'])
    
    return df

def compare_df(df1,df2,suffixes):
    """
    Compare two F12 based dataframes
    """
        
    df = pd.merge(df1, df2, on='coefficient', suffixes=suffixes, how='left')
    df.index = df['coefficient']
    
    # set resolution
    figsize=(10,len(df)*.5)
    
    field = 'value'
    df[[field+suffix for suffix in suffixes]].plot(kind='barh',figsize=figsize, title='coefficient value',
                                                         alpha=0.6)
    
    field = 't-stat'
    df[[field+suffix for suffix in suffixes]].astype('float').plot(kind='barh', figsize=figsize, title='t-stat', 
                                                                        alpha=0.6)
    return df