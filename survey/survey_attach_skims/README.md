Update survey skim values with model results

Designed to read directly from Daysim-formatted survey records in h5 format.

The script "attach_skim_values" processes .dat files, adding skim values to 
person, tour, and trip records and outputting results as an h5. 
The resulting h5 file format matches Soundcast outputs from "daysim_outputs.h5"
and past survey results from 2006. 

Time from input dat files are expected in HHMM format, but are converted
to minutes after midnight for use in the model.