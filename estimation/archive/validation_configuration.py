################################################################
# Validation input files and output directory names
################################################################

model_dir = "C:/Workspace/sc_2018_new_daysim"
survey_dir = "R:/e2projects_two/2018_base_year/survey/daysim_format/revised/skims_attached"

# survey data
# p_survey_households = "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/survey_outputs/final_households.csv"
# p_survey_persons =    "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/survey_outputs/final_persons.csv"
# p_survey_landuse =    "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/survey_outputs/final_land_use.csv"
# p_survey_tours =      "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/survey_outputs/override_tours.csv"
# p_survey_trips =      "R:/e2projects_two/activitysim/survey/formatted_data/tues_wed_thur/override_trips.csv"

# model results
p_model_households = "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/model_outputs/pipeline.parquetpipeline/households/mp_households.parquet"
p_model_persons =    "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/model_outputs/pipeline.parquetpipeline/persons/mp_households.parquet"
p_model_tours =      "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/model_outputs/pipeline.parquetpipeline/tours/mp_households.parquet"

# other validation dataset
p_acs_auto_ownership = "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/auto_ownership/bg_auto_ownership.csv"
p_maz_bg_lookup =      "R:/e2projects_two/activitysim/estimation/2017_2019_data/validation_data/auto_ownership/maz_bg_lookup.csv"

# validation output directory
p_output_dir = "outputs/validation"

################################################################
# run validation notebooks
################################################################
run_validation_nb = ['auto_ownership']

psrc_color = ["#F05A28", "#00A7A0", "#8CC63E", "#91268F","#4C4C4C"]