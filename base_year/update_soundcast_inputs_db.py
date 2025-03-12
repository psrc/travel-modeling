# Create soundcast_inputs_db files from CSV records
# These input files are generated from different scripts/notebooks in this directory or updated manually
# Run this to generate

import pandas as pd
import sqlite3
import os
import time

# Location of CSV input files to become database tables
db_input_dir = r'R:\e2projects_two\SoundCast\Inputs\db_inputs'
db_output_name = r'C:\workspace\soundcast_inputs_2023.db'

start_time = time.time()

conn = sqlite3.connect(db_output_name) # Creates or connects to the database file

# iterate through all CSV files in this directory and load them into the database via pandas dataframes
for file_name in os.listdir(db_input_dir):
    if file_name.endswith('.csv'):
        print(file_name)
        # Use file name as table name
        table_name = os.path.splitext(file_name)[0]
        file_path = os.path.join(db_input_dir, file_name)
        df = pd.read_csv(file_path)
        df.to_sql(table_name, conn, if_exists='replace', index=False)

# Commit changes and close the connection
conn.commit()
conn.close()

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Process completed in {elapsed_time:.2f} seconds")