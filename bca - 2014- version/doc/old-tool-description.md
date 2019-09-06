% Detailed description of old BCA tool

# Background

This document describes the old, 2010 version of the BCA tool that is
discussed in the PSRC report "Benefit-Cost Analysis, General Methods
and Approach." This is a technical document that aims to describe the
tool in sufficient detail as to facilitate the development of a new
version of the tool.

As described elsewhere, the impetus for the redevelopment of the BCA
tool is several fold, including that the existing tool:

* The existing tool is slow (was designed for memory-efficiency)
* The existing tool is designed to work with a fixed schema
* The existing tool was not designed with the requirements of a 4k
  zone system in mind.

The remainder of this document describes the operation and design of
the tool, with an eye toward describing these limitations.

# Program operation: 30,000 ft. view

There are four distinct phases of execution:

Preparation (Emme -> Emme)

 :    Two completed model runs (one per scenario) are reformatted using the BCA Prep Tool. The tool consists of a series of Emme macros. Started from `BCA.bat`; run twice, once per scenario.

Data ETL (Emme -> SQL)

 :    Two prepared model runs are loaded into a Postgres database. Each scenario / model run is loaded into a separate schema within the database. Started from `databank.py`; run twice, once per scenario.

Calculate Benefits (SQL -> SQL)

 :    Component benefits are calculated for each origin / destination zone. Started from `benefits.py`; run once

Aggregation and Summarization

 :    Atomistic benefits (atomic by zone, user class, and time of day) are aggregated according to the desires of the analyst. This is done interactively in the Django-based front end (`/web` folder), with additional summarization typically done in Excel.

# Data

Data originates from Emme, and can be one of three basic types:

* Zone-to-zone
* Link
* Zone (origin or destination characteristics)

At the end of the BCA Preparation process, the relevant Emmebanks are
in the following directory structure (a full description of matrices
can be found in the [appendix](#appendix)):

    +-scenarios/
      +-base/
      | +-Bank1/
      | | +-Emmebank
      | +-Bank2/
      | | +-Emmebank
      | +-Bank3/
      | | +-Emmebank
      | +-CostBenTool/
      |   +-Emmebank
      +-alt/
        +-Bank1/
        | +-Emmebank
        +-Bank2/
        | +-Emmebank
        +-Bank3/
        | +-Emmebank
        +-CostBenTool/
          +-Emmebank



# Data preparation

The BCA prep tool is a collection of Emme macros and specially formatted
emmebanks, started from a batch script (`bca.bat`). In talking to
Chris Johnson, my understanding is that this tool was created solely
because of a change in the structure of the old model system. Because
the BCA tool was difficult to re-define benefit components, building
this adapter was seen as easier than refactoring the BCA tool itself.

As such, I believe this tool can be abandoned in favor of a new BCA
tool that supports a malleable data schema. Nevertheless, the tool is
described here as best as an Emme macro neophyte can manage.

Before it can be run, the tool requires each modeled scenario to be
copied together with the BCA prep tool in a particular way:

1. Copy `//file2/e2projects_two/CHRIS/Emme\ Setups/CostBenTool/` *into*
   the modeled scenario's folder.
2. Copy the model's `PATHS*` files to the newly copied `CostBenTool/`
   folder, into the corresponding Bank folder (e.g. `Bank1`, `Bank2`,
   `Bank3`)

In the `scripts-aux` folder of this repository, there is a shell
script, `bca_prep_orig.sh`, that may be useful to understanding how
these files are copied. Please note that this copying has historically
been a manual process.

The file structure expected by the BCA prep tool, with the relevant
executable macros and batch file, and order of execution (as
controlled by `bca.bat`) is as follows:

     +-scenarios/
       +-base/
       | +-Bank1/
    3. | | +-legimped.mac
       | +-CostBenTool/
       |   +-Bank1/
    6. |   | +-Bank1Prep.mac
       |   +-Bank2/
    7. |   | +-Bank2Prep.mac
       |   +-Bank3/
    8. |   | +-Bank3Prep.mac
    1. |   +-bca.bat
    2. |   +-pnrtim.mac
    4. |   +-Bank1BCPrep.mac
    5. |   +-Bank2BCPrep.mac
    9. |   +-CostBenData.mac
       +-alt/
         +-Bank1/
         | +-legimped.mac
         +-CostBenTool/
           +-Bank1/
           | +-Bank1Prep.mac
           +-Bank2/
           | +-Bank2Prep.mac
           +-Bank3/
           | +-Bank3Prep.mac
           +-bca.bat
           +-pnrtim.mac
           +-Bank1BCPrep.mac
           +-Bank2BCPrep.mac
           +-CostBenData.mac


# Extract, Transform, and Load

The `databank.py` script is used to load data from the Emmebanks into
a relational database. The functions in this script depend on
`emme2lib`, which is a third-party Emme3 emmebank reader written by
Ben Stabler. This section describes, in detail, what each of the
functions in the script does.

There are a few curiosities at the high level that should be noted.
The first thing to note, is that named functions are nested inside
named functions. Though legal python, it is not readily apparent to me
why this was done. I will describe these nested functions on their
own, as they require very little from the scope of the parent
functions.

Table: List of functions

| Function name          | Description                                        |
|------------------------+----------------------------------------------------|
| `links_and_segments()` | calls `make_link_data` and `make_segment_data`     |
| `make_link_data()`     | loads non-transit link data into DB                |
| `make_segment_data()`  | loads transit link data into DB                    |
|                        |                                                    |
| `bank1_full()`         | loads zone-to-zone data from Bank1                 |
| `bank2_full()`         | loads zone-to-zone data from Bank2                 |
| `bank3_full()`         | loads zone-to-zone data from Bank3                 |
| `bank4_full()`         | loads zone-to-zone data from CostBenTool bank      |
|                        |                                                    |
| `parking()`            | loads destination parking costs from Bank1         |
| `park_and_ride()`      | Creates PNR trip tables from 24hr P-A mat in Bank1 |
| `hbw_trips()`          | Not used. Long function; commented out.            |


## Global vars and `__main__()`

Global variables consist solely of command line arguments, and setup
of the database / database cursor. The `main()` function simply calls
in order: 1.) functions to extract and load links and segments data
2.) functions to extract and load matrix data

## Links and Segments: `make_link_data()` and `make_segment_data()`

These two functions extract segment and link data. In the nomenclature
of the app, segment data are transit lines and link data are for
non-transit modes. The specific variables to be read are hard-coded in
the source code.

The data are loaded into a single table (one each for transit and
segment data) inside the corresponding alternative's scenario in
Postgres.

The transit link data are loaded into a table with the
following fields:
`(scenario, i_node, j_node, line, transit_time, transit_volume,
headway, seated_capacity, total_capacity)`

The non-transit segment data are loaded into a table with the
following fields:

`(scenario, i_node, j_node, length, link_type, volume_delay_function,
					lanes, aux_transit_volume, auto_time,
					additional_volume, ul1, ul2, ul3, toll_da,
					toll_2p, toll_3plus, toll_lt_truck,
					toll_med_truck, toll_hvy_truck, ferry_link,
					bridge_link, transit_persons, sov_volume,
					hbw1_sov_volume, hbw2_sov_volume, hbw3_sov_volume,
					hbw4_sov_volume, hov2_volume, hov3plus_volume,
					vanpool_volume, lt_truck_volume, med_truck_volume,
					hvy_truck_volume, extra_time_medium_truck,
					extra_time_heavy_truck, uncertainty)`

## Zone to zone data: `bank[N]_full()`

The functions `bank[N]_full()` read the zone-to-zone matrix data,
reshape it into 'long' format, and load it into the database. Again,
the Emme reader functions are provided by the 3rd-party emme2lib
python package written by Ben Stabler. Once again, the specific
matrices are hard-coded.

The full list of variables is in the appendix.

## Zonal data: 'parking()':


## Park and ride data: `park_and_ride()`

This function uses zone-to-zone full matrix data. Only one variable,
`hbwtdp`, is read.

The value inserted into the database is transformed according to the
following formula:

    Origin-Destination * 0.741 + Destination-Origin * 0.259

In addition, if the number of park-and-ride trips exceeds 1,000, the
number is treated as invalid and reset to zero.


# Appendix -- Data Dictionary {#appendix}

Table: Zone-to-zone matrices

| Emmebank      | Matrix Name | Description                              |
|---------------+-------------+------------------------------------------|
| Bank1         | aa1cs1      | AM HBW GCost skim - Inc 1                |
|               | aa1cs2      | AM HBW GCost skim - Inc 2                |
|               | aa1cs3      | AM HBW GCost skim - Inc 3                |
|               | aa1cs4      | AM HBW GCost skim - Inc 4                |
|               | aauxau      | AM aux transit time - auto               |
|               | aauxwa      | AM aux transit time - walk               |
|               | abrdau      | AM boarding time - auto                  |
|               | abrdwa      | AM boarding time - walk                  |
|               | ahbw1v      | AM HBW auto trips - Inc 1                |
|               | ahbw2v      | AM HBW auto trips - Inc 2                |
|               | ahbw3v      | AM HBW auto trips - Inc 3                |
|               | ahbw4v      | AM HBW auto trips - Inc 4                |
|               | ahvtrk      | AM heavy trucks                          |
|               | aivtau      | AM in-vehicle time - auto                |
|               | aivtwa      | AM in-vehicle time - walk                |
|               | alttrk      | AM light trucks                          |
|               | ambike      | AM biking person trips                   |
|               | amdtrk      | AM medium trucks                         |
|               | amwalk      | AM walking person trips                  |
|               | anbdau      | AM number of boardings - auto            |
|               | anbdwa      | AM number of boardings - walk            |
|               | atrnst      | AM transit person trip table             |
|               | atrtau      | AM total transit time - auto             |
|               | atrtwa      | AM total transit time - walk             |
|               | atwkau      | AM Walk Time: PnR Lot > Transit Stop     |
|               | atwtau      | AM total wait time - auto                |
|               | atwtwa      | AM total wait time - walk                |
|               | au1cos      | Single vehicle to work travel cost       |
|               | au1dis      | Single vehicle to work travel distance   |
|               | au1tim      | Single vehicle to work travel time       |
|               | au2cos      | Share-Ride 2p to work travel cost        |
|               | au2tim      | Share-Ride 2p to work travel time        |
|               | au3cos      | Share-Ride 3+p to work travel cost       |
|               | au3tim      | Share-Ride 3+p to work travel time       |
|               | au4cos      | Vanpool to work travel costs             |
|               | au4tim      | Vanpool to work travel times             |
|               | avehda      | AM PK period drive-alone vehicle trips   |
|               | avehs2      | AM PK period share-ride 2 vehicle trips  |
|               | avehs3      | AM PK period share-ride 3+ vehicle trips |
|               | avpool      | vanpool Demand Matrix 2008               |
|               | awt1au      | AM transit transfer time - auto          |
|               | awt1wa      | AM transit transfer time - walk          |
|               | biketm      | Bike to work travel time                 |
|               | hvygcs      | Heavy trucks generalized cost            |
|               | hvytim      | Heavy trucks travel times                |
|               | lgtgcs      | Light trucks generalized cost            |
|               | lgttim      | Light trucks travel times                |
|               | medgcs      | Medium trucks generalized cost           |
|               | medtim      | Medium trucks travel times               |
|               | pkfara      | AM PK transit fare - auto access         |
|               | pkfarw      | AM PK transit fare - walk access         |
|               | pnrdis      | Distance: Home > PnR Lot                 |
|               | pnrtim      | Time: Home > PnR Lot                     |
|               | walktm      | AM walk time in minutes                  |
|               |             |                                          |
| Bank2         | hnwcp1      | HBNW number of persons for C-P Type 1,2  |
|               | hnwcp1      | HNW Car-Person Type 1 trip table         |
|               | hnwcp3      | HBNW number of persons for C-P Type 3    |
|               | hnwcp3      | HNW Car-Person Type 3 trip table         |
|               | hnwcp4      | HBNW number of persons for C-P Type 4    |
|               | hnwcp4      | HNW Car-Person Type 4 trip table         |
|               | hnwcp5      | HBNW number of persons for C-P Type 5    |
|               | hnwcp5      | HNW Car-Person Type 5 trip table         |
|               | hnwcp6      | HBNW number of persons for C-P Type 6    |
|               | hnwcp6      | HNW Car-Person Type 6 trip table         |
|               | hvygcs      | MD Heavy trucks generalized cost         |
|               | hvytim      | MD Heavy trucks travel times             |
|               | lgtgcs      | MD Light trucks generalized cost         |
|               | lgttim      | MD Light trucks travel times             |
|               | ma1cs1      | MD HBW GCost skim - Inc 1                |
|               | ma1cs2      | MD HBW GCost skim - Inc 2                |
|               | ma1cs3      | MD HBW GCost skim - Inc 3                |
|               | ma1cs4      | MD HBW GCost skim - Inc 4                |
|               | md2btm      | Mid-Day CP2 bidirectional time           |
|               | md3btm      | Mid-Day CP3+ bidirectional time          |
|               | mdsbtm      | Mid-Day SOV bidirectional time           |
|               | medgcs      | MD Medium trucks generalized cost        |
|               | medtim      | MD Medium trucks travel times            |
|               | mh1bcs      | Mid-Day HBW SOV 1 bidirectional cost     |
|               | mh2bcs      | Mid-Day HBW SOV 2 bidirectional cost     |
|               | mh3bcs      | Mid-Day HBW SOV 3 bidirectional cost     |
|               | mh4bcs      | Mid-Day HBW SOV 4 bidirectional cost     |
|               | mhbw1v      | MD HBW auto trips - Inc 1                |
|               | mhbw2v      | MD HBW auto trips - Inc 2                |
|               | mhbw3v      | MD HBW auto trips - Inc 3                |
|               | mhbw4v      | MD HBW auto trips - Inc 4                |
|               | nwbktm      | HBNW bike travel time in min.            |
|               | nwwktm      | HBNW walk travel time in minutes         |
|               | oauxwa      | OP aux transit time - walk               |
|               | obrdwa      | OP boarding time - walk                  |
|               | off1cs      | Off-Peak auto 1p travel cost             |
|               | off1ds      | Off-Peak auto 1p travel distance in mi.  |
|               | off1tm      | Off-Peak auto 1p travel time in min.     |
|               | off2cs      | Off-Peak auto 2+p travel cost            |
|               | off2tm      | Off-Peak auto 2+p travel time in min.    |
|               | off3cs      | Off-peak Share-ride 3+ travel cost       |
|               | off3tm      | Off-peak Share-ride 3+ travel time       |
|               | ohvtrk      | Off-peak heavy trucks                    |
|               | oivtwa      | OP in-vehicle time - walk                |
|               | olttrk      | Off-peak light trucks                    |
|               | omdtrk      | Off-peak medium trucks                   |
|               | onbdwa      | OP number of boardings - walk            |
|               | opbike      | Off-peak biking pers trips               |
|               | opfara      | Off-peak fare - auto access (PB)         |
|               | opfarw      | OP fare - walk access (PB)               |
|               | opwalk      | Off-peak walking pers trips              |
|               | otrnst      | Off-peak transit pers trips              |
|               | otrtwa      | OP total transit time - walk             |
|               | otwtwa      | OP total wait time - walk                |
|               | ovehda      | Off-peak drive-alone vehicle trips       |
|               | ovehs2      | Off-Peak share-ride 2 vehicle trips      |
|               | ovehs3      | Off-peak share-ride 3+ vehicle trips     |
|               | owt1wa      | OP initial wait time - walk              |
|               |             |                                          |
| Bank3         | au1dis      | Single vehicle to work travel distance   |
|               | ea1cs1      | EV HBW GCost skim - Inc 1                |
|               | ea1cs2      | EV HBW GCost skim - Inc 2                |
|               | ea1cs3      | EV HBW GCost skim - Inc 3                |
|               | ea1cs4      | EV HBW GCost skim - Inc 4                |
|               | eau1cs      | EV Single vehicle travel cost            |
|               | eau1ds      | EV Single vehicle travel distance        |
|               | eau1tm      | EV Single vehicle travel time            |
|               | eau2cs      | EV Share-Ride 2p travel cost             |
|               | eau2tm      | EV Share-Ride 2p travel time             |
|               | eau3cs      | EV Share-Ride 3+p travel cost            |
|               | eau3tm      | EV Share-Ride 3+p travel time            |
|               | ebiket      | EV Bike travel time                      |
|               | ehbw1v      | EV HBW auto trips - Inc 1                |
|               | ehbw2v      | EV HBW auto trips - Inc 2                |
|               | ehbw3v      | EV HBW auto trips - Inc 3                |
|               | ehbw4v      | EV HBW auto trips - Inc 4                |
|               | ehvtrk      | EV heavy trucks                          |
|               | ehvycs      | Heavy trucks EV Gen cost                 |
|               | ehvytm      | Heavy trucks EV travel times             |
|               | elgtcs      | Light trucks EV Gen cost                 |
|               | elgttm      | Light trucks EV travel times             |
|               | elttrk      | EV light trucks                          |
|               | emdtrk      | EV medium trucks                         |
|               | emedcs      | Medium trucks EV Gen cost                |
|               | emedtm      | Medium trucks EV travel times            |
|               | etrnst      | EV transit person trip table             |
|               | evbike      | EV biking person trips                   |
|               | evehda      | EV period drive-alone vehicle trips      |
|               | evehs2      | EV period share-ride 2 vehicle trips     |
|               | evehs3      | EV period share-ride 3+ vehicle trips    |
|               | evwalk      | EV walking person trips                  |
|               | ewlktm      | EV AM walk time in minutes               |
|               | na1cs1      | NI HBW GCost skim - Inc 1                |
|               | na1cs2      | NI HBW GCost skim - Inc 2                |
|               | na1cs3      | NI HBW GCost skim - Inc 3                |
|               | na1cs4      | NI HBW GCost skim - Inc 4                |
|               | nau1cs      | MT Single vehicle travel cost            |
|               | nau1ds      | NT Single vehicle travel distance        |
|               | nau1tm      | NT Single vehicle travel time            |
|               | nau2cs      | NT Share-Ride 2p travel cost             |
|               | nau2tm      | NT Share-Ride 2p travel time             |
|               | nau3cs      | NT Share-Ride 3+p travel cost            |
|               | nau3tm      | NT Share-Ride 3+p travel time            |
|               | nbiket      | NT Bike travel time                      |
|               | nhbw1v      | NI HBW auto trips - Inc 1                |
|               | nhbw2v      | NI HBW auto trips - Inc 2                |
|               | nhbw3v      | NI HBW auto trips - Inc 3                |
|               | nhbw4v      | NI HBW auto trips - Inc 4                |
|               | nhvtrk      | NI heavy trucks                          |
|               | nhvycs      | Heavy trucks NI Gen cost                 |
|               | nhvytm      | Heavy trucks NI travel times             |
|               | nibike      | NT biking person trips                   |
|               | niwalk      | NT walking person trips                  |
|               | nlgtcs      | Light trucks NI Gen cost                 |
|               | nlgttm      | Light trucks NI travel times             |
|               | nlttrk      | NI light trucks                          |
|               | nmdtrk      | NI medium trucks                         |
|               | nmedcs      | Medium trucks NI Gen cost                |
|               | nmedtm      | Medium trucks NI travel times            |
|               | ntrnst      | NT transit person trip table             |
|               | nvehda      | NT period drive-alone vehicle trips      |
|               | nvehs2      | NT period share-ride 2 vehicle trips     |
|               | nvehs3      | NT period share-ride 3+ vehicle trips    |
|               | nwlktm      | NT AM walk time in minutes               |
|               | pa1cs1      | PM HBW GCost skim - Inc 1                |
|               | pa1cs2      | PM HBW GCost skim - Inc 2                |
|               | pa1cs3      | PM HBW GCost skim - Inc 3                |
|               | pa1cs4      | PM HBW GCost skim - Inc 4                |
|               | pau1cs      | PM Single vehicle travel cost            |
|               | pau1ds      | PM Single vehicle travel distance        |
|               | pau1tm      | PM Single vehicle travel time            |
|               | pau2cs      | PM Share-Ride 2p travel cost             |
|               | pau2tm      | PM Share-Ride 2p travel time             |
|               | pau3cs      | PM Share-Ride 3+p travel cost            |
|               | pau3tm      | PM Share-Ride 3+p travel time            |
|               | pau4cs      | Vanpool travel cost                      |
|               | pau4tm      | PM Vanpool to work travel times          |
|               | pbiket      | PM Bike travel time                      |
|               | phbw1v      | PM HBW auto trips - Inc 1                |
|               | phbw2v      | PM HBW auto trips - Inc 2                |
|               | phbw3v      | PM HBW auto trips - Inc 3                |
|               | phbw4v      | PM HBW auto trips - Inc 4                |
|               | phvtrk      | PM heavy trucks                          |
|               | phvycs      | Heavy trucks PM Gen cost                 |
|               | phvytm      | Heavy trucks PM travel times             |
|               | plgtcs      | Light trucks PM Gen cost                 |
|               | plgttm      | Light trucks PM travel times             |
|               | plttrk      | PM light trucks                          |
|               | pmbike      | PM biking person trips                   |
|               | pmdtrk      | PM medium trucks                         |
|               | pmedcs      | Medium trucks PM Gen cost                |
|               | pmedtm      | Medium trucks PM travel times            |
|               | pmwalk      | PM walking person trips                  |
|               | ptrnst      | PM transit person trip table             |
|               | pvehda      | PM PK period drive-alone vehicle trips   |
|               | pvehs2      | PM PK period share-ride 2 vehicle trips  |
|               | pvehs3      | PM PK period share-ride 3+ vehicle trips |
|               | pvpool      | PM PK period vanpool vehicle trips       |
|               | pwlktm      | PM AM walk time in minutes               |
|               |             |                                          |
| CostBenTool   | am1tim      | AM Time (from GC) for Non-Work SOV       |
| (called Bank4 | am1tl1      | AM Toll (from GC) for HBW (1)            |
| in tool)      | am1tl2      | AM Toll (from GC) for HBW (2)            |
|               | am1tl3      | AM Toll (from GC) for HBW (3)            |
|               | am1tl4      | AM Toll (from GC) for HBW (4)            |
|               | am1tm1      | AM Time (from GC) for HBW (1)            |
|               | am1tm2      | AM Time (from GC) for HBW (2)            |
|               | am1tm3      | AM Time (from GC) for HBW (3)            |
|               | am1tm4      | AM Time (from GC) for HBW (4)            |
|               | am1tol      | AM Toll (from GC) for Non-Work SOV       |
|               | am1uc1      | AM UC Pen (from GC) for HBW (1)          |
|               | am1uc2      | AM UC Pen (from GC) for HBW (2)          |
|               | am1uc3      | AM UC Pen (from GC) for HBW (3)          |
|               | am1uc4      | AM UC Pen (from GC) for HBW (4)          |
|               | am1unc      | AM UC Pen (from GC) for Non-Work SOV     |
|               | am2tim      | AM Time (from GC) for HOV 2              |
|               | am2tol      | AM Toll (from GC) for HOV 2              |
|               | am2unc      | AM UC Pen (from GC) for HOV 2            |
|               | am3tim      | AM Time (from GC) for HOV 3+             |
|               | am3tol      | AM Toll (from GC) for HOV 3+             |
|               | am3unc      | AM UC Pen (from GC) for HOV 3+           |
|               | am4tim      | AM Time (from GC) for Vanpools           |
|               | am4tol      | AM Toll (from GC) for Vanpools           |
|               | am4unc      | AM UC Pen (from GC) for Vanpools         |
|               | amhtim      | AM Time (from GC) for Heavy Trucks       |
|               | amhtol      | AM Toll (from GC) for Heavy Trucks       |
|               | amhunc      | AM UC Pen (from GC) for Heavy Trucks     |
|               | amltim      | AM Time (from GC) for Light Trucks       |
|               | amltol      | AM Toll (from GC) for Light Trucks       |
|               | amlunc      | AM UC Pen (from GC) for Light Trucks     |
|               | ammtim      | AM Time (from GC) for Medium Trucks      |
|               | ammtol      | AM Toll (from GC) for Medium Trucks      |
|               | ammunc      | AM UC Pen (from GC) for Medium Trucks    |
|               | em1tim      | EV Time (from GC) for Non-Work SOV       |
|               | em1tl1      | EV Toll (from GC) for HBW (1)            |
|               | em1tl2      | EV Toll (from GC) for HBW (2)            |
|               | em1tl3      | EV Toll (from GC) for HBW (3)            |
|               | em1tl4      | EV Toll (from GC) for HBW (4)            |
|               | em1tm1      | EV Time (from GC) for HBW (1)            |
|               | em1tm2      | EV Time (from GC) for HBW (2)            |
|               | em1tm3      | EV Time (from GC) for HBW (3)            |
|               | em1tm4      | EV Time (from GC) for HBW (4)            |
|               | em1tol      | EV Toll (from GC) for Non-Work SOV       |
|               | em1uc1      | EV UC Pen (from GC) for HBW (1)          |
|               | em1uc2      | EV UC Pen (from GC) for HBW (2)          |
|               | em1uc3      | EV UC Pen (from GC) for HBW (3)          |
|               | em1uc4      | EV UC Pen (from GC) for HBW (4)          |
|               | em1unc      | EV UC Pen (from GC) for Non-Work SOV     |
|               | em2tim      | EV Time (from GC) for HOV 2              |
|               | em2tol      | EV Toll (from GC) for HOV 2              |
|               | em2unc      | EV UC Pen (from GC) for HOV 2            |
|               | em3tim      | EV Time (from GC) for HOV 3+             |
|               | em3tol      | EV Toll (from GC) for HOV 3+             |
|               | em3unc      | EV UC Pen (from GC) for HOV 3+           |
|               | emhtim      | EV Time (from GC) for Heavy Trucks       |
|               | emhtol      | EV Toll (from GC) for Heavy Trucks       |
|               | emhunc      | EV UC Pen (from GC) for Heavy Trucks     |
|               | emltim      | EV Time (from GC) for Light Trucks       |
|               | emltol      | EV Toll (from GC) for Light Trucks       |
|               | emlunc      | EV UC Pen (from GC) for Light Trucks     |
|               | emmtim      | EV Time (from GC) for Medium Trucks      |
|               | emmtol      | EV Toll (from GC) for Medium Trucks      |
|               | emmunc      | EV UC Pen (from GC) for Medium Trucks    |
|               | mm1tim      | MD Time (from GC) for Non-Work SOV       |
|               | mm1tl1      | MD Toll (from GC) for HBW (1)            |
|               | mm1tl2      | MD Toll (from GC) for HBW (2)            |
|               | mm1tl3      | MD Toll (from GC) for HBW (3)            |
|               | mm1tl4      | MD Toll (from GC) for HBW (4)            |
|               | mm1tm1      | MD Time (from GC) for HBW (1)            |
|               | mm1tm2      | MD Time (from GC) for HBW (2)            |
|               | mm1tm3      | MD Time (from GC) for HBW (3)            |
|               | mm1tm4      | MD Time (from GC) for HBW (4)            |
|               | mm1tol      | MD Toll (from GC) for Non-Work SOV       |
|               | mm1uc1      | MD UC Pen (from GC) for HBW (1)          |
|               | mm1uc2      | MD UC Pen (from GC) for HBW (2)          |
|               | mm1uc3      | MD UC Pen (from GC) for HBW (3)          |
|               | mm1uc4      | MD UC Pen (from GC) for HBW (4)          |
|               | mm1unc      | MD UC Pen (from GC) for Non-Work SOV     |
|               | mm2tim      | MD Time (from GC) for HOV 2              |
|               | mm2tol      | MD Toll (from GC) for HOV 2              |
|               | mm2unc      | MD UC Pen (from GC) for HOV 2            |
|               | mm3tim      | MD Time (from GC) for HOV 3+             |
|               | mm3tol      | MD Toll (from GC) for HOV 3+             |
|               | mm3unc      | MD UC Pen (from GC) for HOV 3+           |
|               | mmhtim      | MD Time (from GC) for Heavy Trucks       |
|               | mmhtol      | MD Toll (from GC) for Heavy Trucks       |
|               | mmhunc      | MD UC Pen (from GC) for Heavy Trucks     |
|               | mmltim      | MD Time (from GC) for Light Trucks       |
|               | mmltol      | MD Toll (from GC) for Light Trucks       |
|               | mmlunc      | MD UC Pen (from GC) for Light Trucks     |
|               | mmmtim      | MD Time (from GC) for Medium Trucks      |
|               | mmmtol      | MD Toll (from GC) for Medium Trucks      |
|               | mmmunc      | MD UC Pen (from GC) for Medium Trucks    |
|               | nm1tim      | NI Time (from GC) for Non-Work SOV       |
|               | nm1tl1      | NI Toll (from GC) for HBW (1)            |
|               | nm1tl2      | NI Toll (from GC) for HBW (2)            |
|               | nm1tl3      | NI Toll (from GC) for HBW (3)            |
|               | nm1tl4      | NI Toll (from GC) for HBW (4)            |
|               | nm1tm1      | NI Time (from GC) for HBW (1)            |
|               | nm1tm2      | NI Time (from GC) for HBW (2)            |
|               | nm1tm3      | NI Time (from GC) for HBW (3)            |
|               | nm1tm4      | NI Time (from GC) for HBW (4)            |
|               | nm1tol      | NI Toll (from GC) for Non-Work SOV       |
|               | nm1uc1      | NI UC Pen (from GC) for HBW (1)          |
|               | nm1uc2      | NI UC Pen (from GC) for HBW (2)          |
|               | nm1uc3      | NI UC Pen (from GC) for HBW (3)          |
|               | nm1uc4      | NI UC Pen (from GC) for HBW (4)          |
|               | nm1unc      | NI UC Pen (from GC) for Non-Work SOV     |
|               | nm2tim      | NI Time (from GC) for HOV 2              |
|               | nm2tol      | NI Toll (from GC) for HOV 2              |
|               | nm2unc      | NI UC Pen (from GC) for HOV 2            |
|               | nm3tim      | NI Time (from GC) for HOV 3+             |
|               | nm3tol      | NI Toll (from GC) for HOV 3+             |
|               | nm3unc      | NI UC Pen (from GC) for HOV 3+           |
|               | nmhtim      | NI Time (from GC) for Heavy Trucks       |
|               | nmhtol      | NI Toll (from GC) for Heavy Trucks       |
|               | nmhunc      | NI UC Pen (from GC) for Heavy Trucks     |
|               | nmltim      | NI Time (from GC) for Light Trucks       |
|               | nmltol      | NI Toll (from GC) for Light Trucks       |
|               | nmlunc      | NI UC Pen (from GC) for Light Trucks     |
|               | nmmtim      | NI Time (from GC) for Medium Trucks      |
|               | nmmtol      | NI Toll (from GC) for Medium Trucks      |
|               | nmmunc      | NI UC Pen (from GC) for Medium Trucks    |
|               | pm1tim      | PM Time (from GC) for Non-Work SOV       |
|               | pm1tl1      | PM Toll (from GC) for HBW (1)            |
|               | pm1tl2      | PM Toll (from GC) for HBW (2)            |
|               | pm1tl3      | PM Toll (from GC) for HBW (3)            |
|               | pm1tl4      | PM Toll (from GC) for HBW (4)            |
|               | pm1tm1      | PM Time (from GC) for HBW (1)            |
|               | pm1tm2      | PM Time (from GC) for HBW (2)            |
|               | pm1tm3      | PM Time (from GC) for HBW (3)            |
|               | pm1tm4      | PM Time (from GC) for HBW (4)            |
|               | pm1tol      | PM Toll (from GC) for Non-Work SOV       |
|               | pm1uc1      | PM UC Pen (from GC) for HBW (1)          |
|               | pm1uc2      | PM UC Pen (from GC) for HBW (2)          |
|               | pm1uc3      | PM UC Pen (from GC) for HBW (3)          |
|               | pm1uc4      | PM UC Pen (from GC) for HBW (4)          |
|               | pm1unc      | PM UC Pen (from GC) for Non-Work SOV     |
|               | pm2tim      | PM Time (from GC) for HOV 2              |
|               | pm2tol      | PM Toll (from GC) for HOV 2              |
|               | pm2unc      | PM UC Pen (from GC) for HOV 2            |
|               | pm3tim      | PM Time (from GC) for HOV 3+             |
|               | pm3tol      | PM Toll (from GC) for HOV 3+             |
|               | pm3unc      | PM UC Pen (from GC) for HOV 3+           |
|               | pm4tim      | PM Time (from GC) for Vanpools           |
|               | pm4tol      | PM Toll (from GC) for Vanpools           |
|               | pm4unc      | PM UC Pen (from GC) for Vanpools         |
|               | pmhtim      | PM Time (from GC) for Heavy Trucks       |
|               | pmhtol      | PM Toll (from GC) for Heavy Trucks       |
|               | pmhunc      | PM UC Pen (from GC) for Heavy Trucks     |
|               | pmltim      | PM Time (from GC) for Light Trucks       |
|               | pmltol      | PM Toll (from GC) for Light Trucks       |
|               | pmlunc      | PM UC Pen (from GC) for Light Trucks     |
|               | pmmtim      | PM Time (from GC) for Medium Trucks      |
|               | pmmtol      | PM Toll (from GC) for Medium Trucks      |
|               | pmmunc      | PM UC Pen (from GC) for Medium Trucks    |
