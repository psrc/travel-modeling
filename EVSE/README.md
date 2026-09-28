# EVSE Data and Analysis

## Overview

This directory contains data and analysis supporting the regional electric vehicle supply equipment (EVSE) site evaluation tool. The datasets were prepared by the Puget Sound Regional Council (PSRC) for use in the regional EVSE planning effort led by the Puget Sound Clean Air Agency. 

The data are from PSRC's regional travel demand model Soundcast, and include information on vehicle trip patterns at the block level, dwell times, and projected electric vehicle fleet shares.

The datasets support several aspects of EVSE planning:

* **Charging opportunity:** Identify locations where vehicles spend time between trips, including the percentage of dwell time falling within different duration thresholds.
* **Destination popularity:** Characterize the relative popularity of locations using vehicle trip and dwell data.
* **Future demand:** Examine how travel patterns and electric vehicle adoption may change over time, consistent with the 2026-2050 Regional Transportation Plan.

## Data Sources and Model Years

The datasets include outputs for three regional travel model years:

| Model year | Description            |
| ---------- | ---------------------- |
| 2023       | Base-year model data   |
| 2035       | Future-year model data |
| 2050       | Future-year model data |

The geographic datasets use Census 2020 geography identifiers. Depending on the dataset, data are available at the census block or census tract level, or between TAZs.

Electric vehicle fleet share projections are provided by county.

## Datasets

### 1. Dwell Time by Census Geography

These datasets describe the distribution of vehicle dwell times at destinations. They include measures of the percentage of dwell time associated with different duration thresholds.

#### All trips

**Filename pattern:**

`dwell_by_tract_all_trips_census2020[geog]_[year].csv`

Contains dwell time measures for all trips to a geography, including trips with a purpose of returning home.

#### Non-home trips

**Filename pattern:**

`dwell_by_tract_nonhome_trips_census2020[geog]_[year].csv`

Contains the same dwell time measures as the all-trips dataset, excluding trips with a purpose of returning home.

#### Geographic coverage

Both datasets are available for census blocks and census tracts, for model years 2023, 2035, and 2050.

The files include the following measures:

| Variable                            | Description                                                               |
| ----------------------------------- | ------------------------------------------------------------------------- |
| `Percent_dwell_time_4plus_hours`    | Percentage of dwell time associated with durations of four hours or more. |
| `percent_dwell_time_less_than_1_hr` | Percentage of dwell time associated with durations of less than one hour. |

The dwell time data can be used to characterize how long vehicles remain at destinations and to identify locations that may be suitable for different types of charging activity.

For the EVSE site evaluation tool, dwell time can also be summarized using a two-hour threshold. The percentage of dwell time under two hours is one of the indicators used to characterize charging site suitability.

### 2. Vehicle Trips by Destination Geography

**Filename pattern:**

`work_trips_dest_by_census2020[geog]_[year].csv`

Contains vehicle trips to each geography, by model year.

These data provide a measure of destination activity and can be used to characterize the relative popularity of locations. In the EVSE site evaluation tool, total destination activity supports the calculation of a relative indicator of site popularity.

The datasets are provided using Census 2020 geography identifiers.

### 3. Electric Vehicle Fleet Share Projections

**Filename pattern:**

`[county]_ev_fleet_shares_by_vehicle_type.csv`

Contains county-specific projections of electric vehicle fleet shares over time, by vehicle type.

The projections are based on:

* 2023 vehicle registrations.
* The existing vehicle age distribution.
* Assumptions about Washington State electric vehicle policies in place by 2035.

These data provide a basis for examining projected EV adoption across counties and vehicle types.

### 4. Single-Occupant Vehicle Distance Skim

**Filename:** `Sov_distance_skim.csv`

Contains distances between TAZs based on the single-occupant vehicle (SOV) assignment results.

This dataset can be used to examine travel distances between zones and support analysis of longer-distance travel.

### 5. Daily Vehicle Trip Table

**Filename:** `Vehicle_daily_trip_table.csv`

Contains total daily trips between zones for the following vehicle types:

* Single-occupant vehicles (SOV)
* High-occupancy vehicles (HOV)
* Transportation network company (TNC) vehicles

The table includes trips between all zones, including external stations and park-and-ride lots.

These data support analysis of regional vehicle travel patterns and longer-distance trips.

### 6. Truck Trip Table

**Filename:** `Truck_trip_table.csv`

Contains daily trips between zones for medium- and heavy-duty trucks combined.

The table has the same general geographic coverage as the daily vehicle trip table, including external stations and park-and-ride lots.

These data can be used to examine truck travel patterns separately from passenger and other vehicle travel.

### 7. External and Park-and-Ride Zone Map

**Filename:** `Externals1.pdf`

Map showing the locations of external-internal TAZs, numbered 3733–3750.

TAZ numbering conventions:

| TAZ range         | Description             |
| ----------------- | ----------------------- |
| 1–3700            | Internal zones          |
| 3733–3750         | External-internal zones |
| Greater than 3750 | Park-and-ride lots      |

The map provides geographic context for interpreting the zone-based trip tables and identifying trips involving external stations.

## Geographic Units

The datasets use several geographic units:

* **Census blocks:** Fine-grained geography for analyzing destination activity and dwell time.
* **Census tracts:** Larger geographic units for summarizing destination activity and dwell time.
* **Traffic analysis zones (TAZs):** Regional travel model geography used for distance skims and interzonal trip tables.
* **Counties:** Geographic units used for electric vehicle fleet share projections.

Census-based datasets reference Census 2020 geography.

## Application to EVSE Site Evaluation

The data support two principal indicators used in the EVSE site evaluation tool.

### Relative destination popularity

Vehicle trip and dwell data can be used to calculate a relative indicator of site popularity. This provides a measure of destination activity that can help distinguish locations with different levels of vehicle activity.

### Dwell time under two hours

The percentage of dwell time under two hours provides information about the duration of vehicle stops at a location. This measure can be used to characterize the types of charging opportunities associated with a site.

The site evaluation tool is designed to use GIS data layers that can be updated as the underlying data are revised.

## Data Updates

The travel model data are tied to PSRC's long-range forecast development cycle. Updates to the underlying data are expected to follow the availability of new base-year model development, approximately every four years.

Future updates may include revised dwell time measures, destination activity, and vehicle travel data, as well as updated electric vehicle fleet projections.

## Notes and Limitations

* The 2035 and 2050 datasets represent modeled future conditions, not observed vehicle activity.
* Electric vehicle fleet share projections depend on the vehicle registration data, vehicle age distribution, and policy assumptions used to develop them.
* Dwell time measures describe modeled vehicle activity and should not be interpreted as direct observations of charging behavior or charging demand.
* The dwell time thresholds and trip purposes included in a dataset should be considered when comparing results across files.
* Census-based data are provided using Census 2020 geography, while trip tables and distance skims use the regional travel model's TAZ system.
* The external and park-and-ride zone map should be consulted when interpreting trips involving zones outside the internal regional model area.

