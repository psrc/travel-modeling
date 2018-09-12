% BC2: User Benefit Calculator Overview

# Background

The user benefits calculator "2" (BC2) compares one transportation
scenario to a baseline in order to calculate the economic benefit to
system users. PSRC has used such a tool in conjunction with its
trip-based travel model since 2009, when the tool was first developed.

Since the time that the original tool was first developed by consultants at
ECONorthwest, the travel model has undergone substantial
redevelopment. In that time, two new travel models have been developed
in parallel. The first, called "4K" represents an incremental change
to the existing trip-based travel model, most notably the increase
from 1,200 zones to 4,000. The second, "SoundCast," represents a more
fundamental change to an activity-based approach.

The space-efficient / time-inefficient computation strategy of the
original tool, combined with the expansion to 4,000 analysis zones,
forced PSRC to redevelop the user benefits calculator starting
in 2013. Processing time with the 1,200 zone system had already been
identified as a problem, and the expansion to 4,000 zones was deemed
untenable.

The rewritten BC2 tool had attempted to reproduce the functionality of the
original BCA tool exactly. This, however, proved undesirable as it
would have been a significant undertaking to maintain backward
compatibility with a retired model system.

Finally, this tool becomes largely irrelevant once SoundCast, the
activity-based travel model, comes into use. Activity-based models
provide more detailed characteristics of each modeled trip, making the
user-benefits calculation more of an analyst's excercise in R, than a
detailed accounting of many travel model matrices.

# Operation

In both the old and new generation of the BC2 tool, there are
(broadly) three steps:

1. Extract, transform, and load -- converts travel model outputs from
   a vendor- or platform-specific format to a format usable by the BC2
   tool. This step is performed separately on both the baseline and
   the alternative.

2. Calculate marginal user benefits -- performs the consumer surplus
   calculations, comparing the baseline scenario to an alternative.

3. Visualization and summarization of results (not part of the tool as
   written, though it is facilitated) -- performs a set of "canned"
   summaries, plus provides access from analytical tools for
   additional ad-hoc analysis.

## Extract, transform, and load (ETL) "emme2h5.py"

Currently, the BC2 tool supports extraction of data from Emmebanks via
the Emme Python API. This is a change from the previous generation of
the tool, which used a custom binary reader to extract data. The
choice to use the Emme API creates a dependency on having an Emme
license.

In order to limit the Emme license dependency, the ETL step is
intended to be modular and self-contained. That is, once the requisite
Emmebanks have been extracted and bundled into a scenario, there is no
need for an Emme license in order to perform the remainder of the BC2
analysis.

In its first generation, the BC2 tool tranformed the data from its
Emme representation to tabular format. Tabular data was then loaded
the data into a SQL (Postgres) database for further processing. This
original approach had two main deficiencies. First, iterating over the
margins of many skim matrices was slow, resulting in a multi-hour ETL
proces. Second, the schema imposed by the database meant that changes
to the model format needed to be reflected in the BC2 code.

In the rewritten tool, data is minimally transformed before being
loaded into HDF5 for further processing. Further, few assumptions are
made about exact schema of the data in the benefit calculation phase,
meaning that various benefit components are defined in the ETL phase.
This should allow the BC2 tool to accommodate changes to the model
structure as well as to allow addition / subtraction of benefits
considered in the analysis.

The script `emme2h5.py` is designed to be run from the command prompt,
and takes two or more mandatory arguments including the path to the
output HDF5 file and the path to one or more Emmebank files. It is
invoked as follows:

    python emme2h5.py OUTPUT INPUTS [INPUTS...]

The script will not, by default, write to an existing HDF5 file. The
script can be called with `-a` flag if this is desired. `python
emme2h5.py --help` will give the program's commandline usage.

When run, the script extracts all "full" or zone-to-zone matrices from
the Emmebank(s). Zonal and link-level attributes are not currently
supported. Each Emmebank processed will be stored in its own HDF5
group whose name is derived from the long description stored in Emme.

The current structure of the 4k model includes many Emmebank files
nested throughout the directory hive. It can be cumbersome to specify
each of the Emmebank files as input to the script. From the bash
prompt in the Windows git shell, you can automatically pass all the
emmebank files into the script:

    python emme2h5.py /path/to/output.h5 `find /path/to/4k/ -name
    emmebank -type f`
    

## User benefits calculation "bc2.py"

The user benefits tool atomistically calculates user benefits, currently from
zone-to-zone matrices only.

`bc2.py` is similarly designed to run from the command line. At a
minimum, the script requires two HDF5 files---one alternative, and
one baseline scenario---and a (JSON) configuration file. All aspects
of the tool's operation are controlled via the configuration file,
though the output path and input paths of the alternative and baseline
scenarios can be overridden via optional command line arguments.

By default, the tool writes user benefits in matrix format, or in
tabular (pytables) format with an optional command line flag. Writing
to tabular format may be more convenient for subsequent analysis using
Pandas, however it is much slower to write in part because Pandas
builds and writes indices for the tabular dataframe objects. In
practice, these indices greatly improve the speed of summarization and
aggregation if using Pandas.

## Structure of user benefits configuration file

The BC2 configuration file is organized in a hierarchical structure.
At the top level are data describing elements relating to the overall
analysis. Beneath that are:

1. data describing elements relating to the alternative and baseline scenarios. 
2. list of individual benefit components
3. definition of values of time for each user class

The structure of this file is as follows:

    +-description (unused currently)
    +-year (unused currently)
    +-outputpath (optional if specified on command line)
    +-constantdollars (unused currently)
    +-baseline{}
    | +-description
    | +-filepath (optional if specified on command line)
    +-alternative{}
    | +-description
    | +-filepath (optional if specified on command line)
    +-zzbenefits[]
    | +-{}
    | | +-description (optional, otherwise inferred from user/time)
    | | +-costpath
    | | +-volumepath
    | | +-costunits (optional, otherwise "minutes" assumed)
    | | +-userclass
    | | +-timeperiod
    | +-{} ...
    +-vot{}
      +-description (unused currently)
      +-<userclassname>{}
      | +-<timeperiodname>
      +-<userclassname>{} ...
        +-<timeperiodname> ...

The heart and soul of this structure is the concept of "benefit
components." Each user benefit included in the analysis must be
explictly defined in the configuration file. Each user benefit
component is represented as a series of key:value pairs.

User benefit components are atomic and represent the minimum set of
data needed for the consumer surplus calculation. Nevertheless,
specifying each benefit component in necessarily verbose.

A few attempts were made to infer the benefit components from matrix
names, however nuances of the naming structure made this unsuccessful.
Someone with a good understanding of the 4k model structure could
potentially generate these components automatically. This is left as
an excercise to the reader. As a consolation, having a JSON
dictionary of each benefit component makes for a nice, programatically
useful data dictionary.

The detailed structure of the benefits component is as follows:

| key name    | value type                      | value if unspecified   |
|-------------+---------------------------------+------------------------|
| description | freeform string                 | timeperiod + userclass |
| costpath    | h5 path string                  | none, mandatory        |
| volumepath  | h5 path string                  | none, mandatory        |
| costunits   | string: minutes, dollars, cents | minutes                |
| userclass   | freeform string                 | none, mandatory        |
| timeperiod  | freeform string                 | none, mandatory        |

IMPORTANT: Please note that the "costpath" and "volumepath" keys
assume an identical structure in the alternative and baseline HDF5
files. There is currently no way to define a different file structure
for these two scenarios.

The remaining non-trivial portion of the configuration file is the
value of time dictionary, "vot." The example configuration file
includes values of time seeded from an Excel file from Chris Johnson.
Please note that there were not values of time for each user class
represented in the spreadsheet. In addition there were no values of
time included for all the user classes represented in the model. To
run successfully, each user benefit must have a corresponding value of
time defined in this dictionary.

