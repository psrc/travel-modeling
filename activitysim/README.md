# Generate Survey Inputs
- Run the script activitysim_survey_conversion.py
- copy results to activitysim survey_data directory in a run directory ([e.g.](https://github.com/ActivitySim/activitysim/tree/master/activitysim/examples/example_estimation/data_full/survey_data))
- run infer.py
    - ensure `apply_controls = False`
    - note that this script may have been slightly modified from Jeff's found [here](https://github.com/ActivitySim/activitysim/blob/master/activitysim/examples/example_estimation/scripts/infer.py)
    - this script produces the files override_x for each survey file x (household, person, trip, etc.)

# Generate Synthetic Population Inputs and Landuse Files
- Run the script create_activitysim_inputs.py
- Check input and output paths at the top of the script
- Set the following to desired outcomes
    - run_hh
    - run_person
    - use_buffered_parcels: this will produce land use variables based on preprocessed buffered parcel variables instead of the raw parcels land use. 
- Copy outputs to the [data folder of a run](https://github.com/ActivitySim/activitysim/tree/master/activitysim/examples/example_psrc/data)
