# AQ Tool

This tool was created in response to multiple data requests from jurisidctions for city and county emissions. In the past we factored county-level emissions using VMT from the HPMS.
Data requests often required GHG emissions for non-modeled years, so forecasts were grown based on interpolations from previous models. This tool was provided due to a large data request from King County for emissions and VMT in every city in the county for multiple model and intermediate years. 
This tool uses Soundcast network outputs and emissions calculations scripts built from those used to calculate regional emissions totals. This allows a better consistency across emissions forecast products and more detailed results. 
Emissions can now be provided by vehicle type for any location, using spatial intersection of city (or other geographical) boundaries and network outputs. 
Rather than scaling on VMT, the emissions results are based directly on model network outputs, which are sensitive to local speeds, facility types, time of day, and other factors. 

The main tool can be run from the aq_tool.ipynb notebook. This notebook imports functions from local python scripts (functions.py, emissions.py) that perform spatial procedures and detailed emissions calculations.
The current aq_tool.ipynb notebook is set up to create emissions totals for all cities in King County for years 2018, 2030, 2040, and 2050, based on the RTP 2050 forecasts. 

In the "Request...ipnyb" notebook, this data is tabulated for summaries provided in response to a December 2021 data request from King County. Addtional summaries are also provided 
for the entire county, and unincorporated King County, which are assumed as total county minus the sum of all city emissions and VMT. 

Pollutants included are CO2eq and atomospheric CO2. It was found that when applying this technique to pollutants with very small rates (N20), that city totals could be greater than
county total by vehicle type. This is likely due to the coarse assumptions around vehicle ownership and starts applied for small cities. This was not a problem for pollutants with 
greater magnitude such as CO2 and CO2eq, or other commonly reported pollutants like PM. This finding suggests that either a more refined method be used to estimate start emissions or 
that certain pollutants be aggregated to sufficient level (e.g., do not break down by vehicle type at the city level). In general, reporting results at the city level, especially for smaller cities
should be used with caution and caveat that these are regional models and data is not guaranteed as such fine levels. 
