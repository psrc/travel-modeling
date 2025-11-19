# Emissions Inventory — PSRC Travel Modeling

## Overview

- This emissions inventory is derived from PSRC’s [travel demand model](https://github.com/psrc/soundcast) outputs (e.g., roadway VMT and speed by vehicle type) and emissions factors from the EPA's MOVES model.  
- Base year (2023) and forecast year (2035) data are consistent with the latest [2026-2050 Regional Transportation Plan](https://www.psrc.org/planning-2050/regional-transportation-plan)

## Methodology & Assumptions

- PSRC estimates vehicle emissions based on vehicle activity and MOVES-generated rates. Vehicle activity comes from PSRC travel model results for base and forecast years (2023, 2035, 2050 for the 2026-2050 RTP). The procedure here is the [same used](https://github.com/psrc/soundcast/blob/master/scripts/summarize/standard/emissions.py) for regional GHG and conformity analysis. 
- Emissions estimates (grams or tons per day of a pollutant) for a model year are calculated for a county by identifying only roadway links within a county. City level emissions estimates are scaled based on the share of county VMT within the city boundaries. This calculation is performed in the [city_vmt.py script](https://github.com/psrc/travel-modeling/blob/master/air_quality/emissions_inventory/city_vmt.py)
- County emissions estimates for non-model years introduce complications in that both the vehicle activity and emissions rates from an evolving fleet are changing.
    - Vehicle activity can be scaled versus a base year (2023) by applying observed county-level change from WSDOT's HPMS data. This data provides a percent change in VMT versus 2023, which is applied to the model base year. For instance, if VMT increases 2%, volumes on all model network links are multiplied by 1.02.
    - Emissions rates must be taken as in interpolation between base year (2023) rates and the next available set of forecasting rates, which is currently 2035. PSRC assumes WA state law for 100% EV sales beginning in 2035, which is incorporated into the emission rates assumptions. For an analysis year of 2024, emissions rates are interpolated between 2023 and 2035 to provide the best guess for fleet emissions changes between model years.
    - For non-model years, the HPMS-scaled vehicle activity (VMT) is multiplied by the interpolated rates in the same manner as for a standard model year.
 
## Outputs

Results are available for light (passenger) vehicles, medium trucks, heavy trucks, and transit buses in terms of tons/day of pollutants by county. City estimates of the same are calculated based on the VMT distributions from the base year mulitplied by the county totals. Python notebooks in the **analysis** directory format the outputs of this tool into tables for final formatting in Excel.
Results include both running as well as start emissions. 

## Running the Tool
There are two scripts that can be run with Python. They must be run by specifying a config.toml file:
- python city_vmt.py -c config.toml
- create_county_emissions.py -c config.toml

The config file contains settings for which counties and years to run for an analysis, as well as the location of travel model output data and assumptions like annualization factors. 
  
