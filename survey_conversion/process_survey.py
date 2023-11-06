import locate_parcels
import process_survey
import attach_skims
import yaml
import configuration
import os
from pathlib import Path
from EmmeProject import *

file = Path().joinpath(configuration.args.configs_dir, "config.yaml")
config = yaml.safe_load(open(file))

project_path = os.path.join(
    config["project_path"], "projects/LoadTripTables/LoadTripTables.emp"
)
my_project = EmmeProject(project_path)
if config["build_supplemental_skims"]:
    supplemental_skims.create_supplemental_skims(
        my_project,
        Path(config["supplemental_skim_file_path"]),
        Path(config["assigmment_spec_file_path"]),
        config["time_period_lookup"],
    )
if config["run_park_and_ride"]:
    park_and_ride.run_park_and_ride(
        my_project,
        Path(config["supplemental_skim_file_path"]),
        Path(config["assigmment_spec_file_path"]),
        config["time_period_lookup"],
        Path(config["project_path"]),
    )
if config["build_skims"]:
    skims = skims.create_skims(
        my_project, config["skim_file_path"], config["time_period_lookup"]
    )


print("done")