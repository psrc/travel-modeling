import create_moves_input_data
import create_input_database_xml
import create_mrs_files
import os
import toml

config = toml.load('configuration.toml')

if config["run_create_moves_input_data"]:
    create_moves_input_data.create_moves_input_data()

if config["run_create_input_database_xml"]:
    create_input_database_xml.create_input_database_xml()

if config["run_create_mrs_files"]:
    create_mrs_files.create_mrs_files()

print("done")