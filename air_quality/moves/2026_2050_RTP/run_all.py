import create_moves_input_data
import create_input_database_xml
import create_mrs_files
import sys
import toml

# Get configuration dir from args
if len(sys.argv) > 1:
    config_path = sys.argv[1]
    print(f"Configuration file path: {config_path}")
    config = toml.load(config_path)
else:
    print("No config file path provided.")
    sys.exit(1)

if config["run_create_moves_input_data"]:
    create_moves_input_data.create_moves_input_data()

if config["run_create_input_database_xml"]:
    create_input_database_xml.create_input_database_xml()

if config["run_create_mrs_files"]:
    create_mrs_files.create_mrs_files()

print("done")