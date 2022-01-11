This folder contains 6 CSV files in response to King County's data request from December 2021. 
Emissions and VMT data are provided for 3 geography types:
    - All cities in King County (provided individually)
    - Unincorporated King County (calcualted as county total minus sum of all city totals) 
    - County-level totals for King, Kitsap, Pierce, and Snohomish counties

The files report total daily emissions in tons and VMT for 3 vehicle classes
    - Light (all passenger vehicles)
    - Medium (commercial trucks e.g., Fedex delivery vehicles)
    - Heavy (large commercial freight vehicles, e.g., semi-trucks with trailers)

A column of data is provided for the following years:
    - 2018 (base year model data for RTP 2050)
    - 2019 (interpolated between 2018 and 2030 model outputs)
    - 2020 (interpolated between same)
    - 2030 (model forecast year for RTP 2050)
    - 2040 (same as above)
    - 2050 (same as above)

The following CSV files are included in this directory:
    - king_county_cities_emissions.csv (daily emissions in tons by vehicle type and city for each year)
    - king_county_cities_vmt.csv (average daily weekday vmt for each city by vehicle type and year)
    - king_county_unincorporated_emissions.csv (daily emissions in tons by vehicle type and year for King County area not included in any city totals)
    - king_county_unincoporated_vmt.csv (average daily weekday vmt for same are as above)
    - regional_emissions_by_county.csv (county-wide daily emissions in tons by vehicle type and year, for each county)
    - regional_vmt_by_county.csv (average daily weekday vmt total for each county by vehicle type and year)



Additionally, 2 HTML documents are provided as reference for the methods used to produce the results. 

Emissions are included for CO2eq and Atmoshperic CO2 below the county level. Insufficient precision was available to provide 
methane and N20 at the fine levels of aggregation required for this analysis. Atmospheric CO2 comprises the vast majority
of CO2eq emissions. The remainder can be attributed to a combination of methane and N20. Methane and N20 are provided for county totals.  

