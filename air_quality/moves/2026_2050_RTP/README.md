# MOVES Data For 2026-2050 RTP

## Base Year Inputs
Washington Department of Ecology provided MOVES inputs consistent with MOVES4 in early 2025. MOVES5 data was requested but not available at the time. The primary difference between MOVES4 and 5 input files seems to be fleet age distributions extending to 40 years instead of 30 years. 
Ecology provided county-specific and default data (in the “cnty_independent” folder).  For this RTP, we decided to only use King County data to produce the representative rates that will be used throughout the region. Most of the input data vary little by county and the resulting rates are often very similar. The exception to this is the current variation in fleet age and EV adoption rates. However, given that future forecasts will be relying on state ZEV mandates that apply to all counties, the impacts of these changes by counties may have less of an impact. Using only King County reduces the amount of MOVES model runs required and simplifies the process.

## AVFT (EVs)
Input assumptions on annual registrations by fuel type (e.g., gasoline, diesel, EV) from Ecology did not match presumed WA state law, so PSRC developed adoption trends to match these. See the [input notebook](https://github.com/psrc/travel-modeling/blob/master/air_quality/moves/2026_2050_RTP/2026_2050_RTP_Scenario_Inputs.ipynb) for the detailed process and assumptions used. The output of that notebook is a MOVES input file for King County `Y:\Air Quality\2026_2050_RTP\moves_inputs_2023\avft\wa_state_policy\King_avft.csv`, which is used in place of Ecology's inputs. This input is specified in the [configuration file](https://github.com/psrc/travel-modeling/blob/master/air_quality/moves/2026_2050_RTP/configuration.toml) in the `avft_file_dir` parameter.

## Age Distribution
EPA provides a tool to generate an age distribution reflecting observed trends, but in a smoothed trend following algorithms used for its default data. Age distributions were generated for 2035 and 2050 and made available here: Y:\Air Quality\2026_2050_RTP\moves_inputs_2023\age_distribution. These smoothed age distributions are used because they reduce the impacts of past abnormalities that should not necessarily be repeated in the future (e.g., large dip in vehicle sales in the 2008-2010 recession shouldn't mean that we expect a dip in 15-year old vehicles in 2050). To use these modified age distribution files, set their location in the [configuration file](https://github.com/psrc/travel-modeling/blob/master/air_quality/moves/2026_2050_RTP/configuration.toml) via the `age_distribution_inputs` parameter.

## Fleet Mix
AVFT and age distribution data are used to determine the share of EVs in the fleet over time. AVFT represents annual registration shares of vehicles by fuel type, which is used to determine the share of EVs in the full fleet (by light, medium, and heavy types) for a given year. This calculation is done alongside the generation of AVFT inputs in the [2026_2050_RTP_Scenario_Inputs notebook](https://github.com/psrc/travel-modeling/blob/master/air_quality/moves/2026_2050_RTP/2026_2050_RTP_Scenario_Inputs.ipynb). The result of this fleet mix is an input into the RTP's financial analysis, since it impacts the number of vehicles paying EV registration fees and non-EVs paying taxes on fuel consumed. The fleet mix results are available here: `Y:\Air Quality\2026_2050_RTP\moves_inputs_2023\avft\wa_state_policy\ev_fleet_shares_by_vehicle_type.csv`


### PSRC Revisions to Ecology Data
Ecology's county-independent fuel-related files did not work, so these were copied into each individual county’s folders and made available in the “revised” inputs (`Y:\Air Quality\2026_2050_RTP\wa_dept_of_ecology_data\2023_MOVES_inputs_revised`).
Additionally, the following inputs were updates were included in the revised version:
- copied 2017 speed distribution data for 61 and 62 vehicle types because these were missing from Dept of Ecology's dataset.
- copied 2017 default fuel supply; attempted to export from MOVES but some fuel types were missing.

## Future Year Inputs
In many cases, PSRC has carried forward base year inputs to the future when no other information is available. This involves copying the base year input files and replacing the yearID field with the model year (e.g., replacing 2023 with 2035 or 2050). This simple process is done in the "create_mrs_files.py" script. 
