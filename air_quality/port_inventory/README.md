# Puget Sound Port Emissions Inventory 
This repository contains the inputs, methods, and results of the regional port inventory, updated in 2023. 
The methods used in this repository vary from those used in previous analyses, but should represent a more accurate estimate of emissions.

## Repository Directory
Input data are stored in the **data** folder. These include the following files:
- **port_model_data.csv**: data generated from [Soundcast](https://github.com/psrc/soundcast) that includes truck trips between ports and locations in region, average trip distances and speed. (See Kris Overby for more information.)
- **port_provided_truck_trips.csv**: data supplied by Starcrest that includes total truck trips generated annually from each port location.
- **emissions_rates**: MOVES-based emissions rates per mile for each analysis year. These were generated separately for the analysis year.
    - See the [PSRC's MOVES repository](https://github.com/psrc/travel-modeling/tree/master/air_quality/moves) for information on how these were generated.
    - MOVES3 was used for these rates, which varies from past versions that used MOVES2014 and earlier models.
    - Input data and intermediate data is available here: Y:\Air Quality\Puget Sound Emissions Inventory (Port).

The **Output** directory contains updated results in spreadsheet format, consistent with previous inventories. 
- **2021** contains the latest inventory, generated in 2023 within the file `2021_Port_Onroad_HeavyTrucks.xlsx`. This spreadsheet was updated by pasting in values from interactively running the `Calculate Port Emissions.ipynb` notebook.
- Additionally, the **python_generated** folder contains a file that was created programatically to double-check copying and pasting. The data here should match the main spreadsheet.
- **2016** contains the original inventory file submitted for a previous inventory `2016_Port_Onroad_HeavyTrucks_original.xlsx` as well as a version that was updated with the latest methods for comparison (`2016_Port_Onroad_HeavyTrucks_revised.xlsx`).
- This directory also contains a python-generated file for validation of the revised methods.

The **analysis** directory contains a spreadsheet comparison of results for each port and pollutant to demonstrate the differences between inventories and methods. 
These results compare both the initial 2016 and the revised 2016 estimate against the 2021 results. This helps draw the distinction between differences
in method and differences in input data and new emissions rates and emissions rates software updates (MOVES3). 

## Methods
Calculations are performed in the `Calculate Port Emissions.ipynb` notebook. This python-based notebook can be opened with Jupyter and run interactively in a browswer window. 
The notebook is designed to generate a set of input tables that can be copied into an existing spreadsheet. This will allow future updates to maintain the same spreadsheet format but add in new data. 
The data to be pasted into the spreadsheet includes estimates of average speed, trips, and VMT, as well as formatted emissions rates. The notebook provides instructions on where data should be pasted,
as well as more information on how the data was developed. 

Inventory calculations are based on observed trip data, model behaviors, and emissions rates. Starcrest has provided annual truck trips from each port, which is the main controlling 
value for an analysis year. These data are converted to an average daily total, which are multiplied against a distribution of trips between each port and surrounding areas, 
which is provided by Soundcast. The distribution of trips represents a modeled base year and measures the percent of total trips from a port origin to various desination geographies
throughout the region (as defined in previous analyses). For each of those origin-destination pairs, an average distance and an average speed is calculated. The average speed is used to 
select an emissions rate of grams per mile (which varies by speed and other factors such as facility type and hour, which are kept constant). Multiplying average distance by trips yields VMT, which
generates the daily grams for each origin-destination pair of each port and for all pollutants. Further details and assumptions are outlined within the notebook and in the spreadsheet results. 
