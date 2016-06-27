Update survey skim values with model results

Designed to read directly from Daysim-formatted survey records in h5 format.

Use "dat_to_h5" to convert Dayism-formatted dat files into h5 format. 
Format matches Soundcast inputs for results comparison. 

The script "attach_skim_values" processes .dat files, adding skim values to 
person, tour, and trip records and outputting results as dat text files. 
Use "dat_to_h5" to convert results back into h5 format for use as validation tool
in Soundcast. 