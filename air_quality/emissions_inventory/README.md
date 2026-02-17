# Emissions Inventory — PSRC Travel Modeling

## Overview

- This emissions inventory is derived from PSRC’s [travel demand model](https://github.com/psrc/soundcast) outputs (e.g., roadway vehicle miles traveled [VMT] and speed by vehicle type) and emissions factors from the EPA's MOVES model.  
- Base year (2023) and forecast year (2035) data are consistent with the latest [2026-2050 Regional Transportation Plan](https://www.psrc.org/planning-2050/regional-transportation-plan)

## Methodology & Assumptions

PSRC estimates vehicle emissions based on vehicle activity and MOVES-generated rates. Vehicle activity comes from PSRC's travel model results for base and forecast years (2023, 2035, 2050 for the 2026-2050 RTP). The procedure here is the [same used](https://github.com/psrc/soundcast/blob/master/scripts/summarize/standard/emissions.py) for regional GHG and conformity analysis. 
- Emissions estimates (grams or U.S. short tons per day of a pollutant) for a model year are calculated for a county by identifying only roadway links within a county. City-level emissions estimates are scaled based on the share of county VMT within the city boundaries. This calculation is performed in the [city_vmt.py script](https://github.com/psrc/travel-modeling/blob/master/air_quality/emissions_inventory/city_vmt.py)
- County emissions estimates for non-model years introduce complications in that both the vehicle activity (VMT) and emissions rates are changing due to new, cleaner vehicles being purchased and older vehicles being phased out.
    - For a forecasted year (e.g., 2024), VMT is scaled versus a base year (2023) by applying observed county-level change from WSDOT's HPMS data. This data provides a percent change in VMT versus 2023, which is applied to the model base year. For instance, if VMT increases 2%, volumes on all model network links are multiplied by 1.02.
    - Emissions rates must be taken as in interpolation between base year (2023) rates and the next available set of [forecasted rates](https://github.com/psrc/travel-modeling/tree/master/air_quality/moves/2026_2050_RTP), which is currently 2035. PSRC assumes WA State's [Clean Vehicles Law](https://app.leg.wa.gov/wac/default.aspx?cite=173-423&full=true) will require 100% EV sales beginning in 2035, which is incorporated into the emission rates assumptions. For an analysis year non-model years such as 2024 and beyond, emissions rates are interpolated between 2023 and 2035 to provide the best guess for fleet emissions changes between model years.

The PSRC travel model is updated every four years, so when new baseline and forecast data are available, the process will be applied to the latest data.   
 
## Outputs

Results are available for light (passenger) vehicles, medium trucks, heavy trucks, and transit buses in terms of tons/day of pollutants by county. City estimates of the same are calculated based on the VMT distributions from the base year multiplied by the county totals. Python notebooks in the **analysis** directory format the outputs of this tool into tables for final formatting in Excel. Results include VMT and both running and start emissions. 

## Running the Tool
There are two scripts that can be run with Python. They must be run by specifying a config.toml file:
- python city_vmt.py -c configs/config_2024.toml
- python create_county_emissions.py -c configs/config_2024.toml

The config file contains settings for which counties and years to run for an analysis, as well as the location of travel model output data and assumptions like annualization factors (**320** is the latest recommended factor). 
  
