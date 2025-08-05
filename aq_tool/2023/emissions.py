import os, shutil
import pandas as pd
import polars as pl
from sqlalchemy import create_engine

pd.options.mode.chained_assignment = None


def grams_to_tons(value):
    """Convert grams to tons."""

    value = value / 453.592
    value = value / 2000

    return value


def calculate_interzonal_vmt(df, input_settings, summary_settings):
    """Calcualte inter-zonal running emission rates from network outputs"""

    # Load link-level volumes by time of day
    # df = pd.read_csv(r"outputs/network/network_results.csv")

    # Remove links with facility type = 0 from the calculation
    df["facility_type"] = df["data3"].copy()  # Rename for human readability
    df = df[df["facility_type"] > 0]

    # Calculate VMT by bus, SOV, HOV2, HOV3+, medium truck, heavy truck
    df["sov_vol"] = df["@sov_inc1"] + df["@sov_inc2"] + df["@sov_inc3"]
    df["sov_vmt"] = df["sov_vol"] * df["length"]
    df["hov2_vol"] = df["@hov2_inc1"] + df["@hov2_inc2"] + df["@hov2_inc3"]
    df["hov2_vmt"] = df["hov2_vol"] * df["length"]
    df["hov3_vol"] = df["@hov3_inc1"] + df["@hov3_inc2"] + df["@hov3_inc3"]
    df["hov3_vmt"] = df["hov3_vol"] * df["length"]
    if input_settings["include_tnc_emissions"]:
        df["tnc_vmt"] = df["@tnc_inc1"] + df["@tnc_inc2"] + df["@tnc_inc3"]
    else:
        df["tnc_vmt"] = 0
    df["bus_vmt"] = df["@bveh"] * df["length"]
    df["medium_truck_vmt"] = df["@mveh"] * df["length"]
    df["heavy_truck_vmt"] = df["@hveh"] * df["length"]

    # Convert TOD periods into hours used in emission rate files
    df["hourId"] = df["tod"].map(summary_settings["tod_lookup"]).astype("int")

    # Calculate congested speed to separate time-of-day link results into speed bins
    df["congested_speed"] = (df["length"] / df["auto_time"]) * 60
    df["avgspeedbinId"] = pd.cut(
        df["congested_speed"],
        summary_settings["speed_bins"],
        labels=range(1, len(summary_settings["speed_bins"])),
    ).astype("int")

    # Relate soundcast facility types to emission rate definitions (e.g., minor arterial, freeway)
    df["roadtypeId"] = (
        df["facility_type"]
        .map({int(k): v for k, v in summary_settings["fac_type_lookup"].items()})
        .astype("int")
    )

    # Take total across columns where distinct emission rate are available
    # This calculates total VMT, by vehicle type (e.g., HOV3 VMT for hour 8, freeway, 55-59 mph)
    join_cols = ["avgspeedbinId", "roadtypeId", "hourId"]
    agg_cols = [
            "sov_vmt",
            "hov2_vmt",
            "hov3_vmt",
            "tnc_vmt",
            "bus_vmt",
            "medium_truck_vmt",
            "heavy_truck_vmt",
        ]
    df = df[join_cols+agg_cols].groupby(join_cols).sum()[agg_cols]
    df = df.reset_index()

    # Write this file for calculation with different emission rates
    # df.to_csv(r"outputs/emissions/interzonal_vmt_grouped.csv", index=False)

    return df


def finalize_emissions(df, col_suffix=""):
    """
    Compute PM10 and PM2.5 totals, sort index by pollutant value, and pollutant name.
    For total columns add col_suffix (e.g., col_suffix='intrazonal_tons')
    """

    pm10 = (
        df[df["pollutantID"].isin([100, 106, 107])]
        .groupby("veh_type")
        .sum()
        .reset_index()
    )
    pm10["pollutantID"] = "PM10"
    pm25 = (
        df[df["pollutantID"].isin([110, 116, 117])]
        .groupby("veh_type")
        .sum()
        .reset_index()
    )
    pm25["pollutantID"] = "PM25"
    df = pd.concat([df, pm10])
    df = pd.concat([df, pm25])

    return df


def calculate_interzonal_emissions(df, df_rates):
    """Calculate link emissions using rates unique to speed, road type, hour, and vehicle type."""

    df.rename(
        columns={
            "avgspeedbinId": "avgSpeedBinID",
            "roadtypeId": "roadTypeID",
            "hourId": "hourID",
        },
        inplace=True,
    )

    # Calculate total VMT by vehicle group
    df["light"] = df["sov_vmt"] + df["hov2_vmt"] + df["hov3_vmt"] + df["tnc_vmt"]
    df["medium"] = df["medium_truck_vmt"]
    df["heavy"] = df["heavy_truck_vmt"]
    df["transit"] = df["bus_vmt"]
    # What about buses??
    df.drop(
        [
            "sov_vmt",
            "hov2_vmt",
            "hov3_vmt",
            "tnc_vmt",
            "medium_truck_vmt",
            "heavy_truck_vmt",
            "bus_vmt",
        ],
        inplace=True,
        axis=1,
    )

    # Melt to pivot vmt by vehicle type columns as rows
    df = pd.melt(
        df,
        id_vars=["avgSpeedBinID", "roadTypeID", "hourID"],
        var_name="veh_type",
        value_name="vmt",
    )

    df = pd.merge(
        df,
        df_rates,
        on=["avgSpeedBinID", "roadTypeID", "hourID", "veh_type"],
        how="left",
        left_index=False,
    )
    # Calculate total grams of emission
    df["grams_tot"] = df["grams_per_mile"] * df["vmt"]
    df["tons_tot"] = grams_to_tons(df["grams_tot"])

    # df.to_csv(r"outputs\emissions\interzonal_emissions.csv", index=False)

    return df


def calculate_intrazonal_vmt(summary_settings, df_iz):
    # df_iz = pd.read_csv(r"outputs/network/iz_vol.csv")

    # Sum up SOV, HOV2, and HOV3 volumes across user classes 1, 2, and 3 by time of day
    df_results = pd.DataFrame()
    for tod in summary_settings["tod_lookup"].keys():
        df = pd.DataFrame()
        df["taz"] = df_iz['taz']
        df["sov"] = df_iz[["sov_inc1_" + tod,"sov_inc2_" + tod,"sov_inc3_" + tod]].sum(axis=1)
        df["hov2"] = df_iz[["hov2_inc1_" + tod,"hov2_inc2_" + tod,"hov2_inc3_" + tod]].sum(axis=1)
        df["hov3"] = df_iz[["hov3_inc1_" + tod,"hov3_inc2_" + tod,"hov3_inc3_" + tod]].sum(axis=1)
        df["mediumtruck"] = df_iz[["medium_truck_" + tod]].copy()
        df["heavytruck"] = df_iz["heavy_truck_" + tod].copy()
        df["tod"] = tod

        df_results = pd.concat([df_results, df])

    df = pd.melt(
        df_results,
        value_vars=["sov", "hov2", "hov3", "mediumtruck", "heavytruck"],
        id_vars=["taz","tod"],
        var_name="vehicle_type",
        value_name="vol",
    )

    # Calculate VMT from zonal distance and volume
    df = df.merge(
        df_iz[["taz", "izdist"]], how="left", on="taz"
    )
    df['VMT'] = df['vol'] * df['izdist']
    df = df.groupby(['tod','vehicle_type']).sum()[['VMT']].reset_index()
    # Use hourly periods from emission rate files
    df["hourId"] = df["tod"].map(summary_settings["tod_lookup"]).astype("int")
    
    # Export this file for use with other rate calculations
    # Includes total VMT for each group for which rates are available
    df = df[['VMT','tod','vehicle_type','hourId']]
    # df.to_csv(r"outputs/emissions/intrazonal_vmt_grouped.csv", index=False)

    return df


def calculate_intrazonal_emissions(df_intra, df_running_rates):
    """Summarize intrazonal emissions by vehicle type."""

    df_intra.rename(
        columns={
            "vehicle_type": "veh_type",
            "VMT": "vmt",
            "hourId": "hourID",
        },
        inplace=True,
    )
    df_intra.drop("tod", axis=1, inplace=True)

    df_intra_light = df_intra[df_intra["veh_type"].isin(["sov", "hov2", "hov3"])]
    df_intra_light = (
        df_intra_light.groupby(["hourID"]).sum()[["vmt"]].reset_index()
    )
    df_intra_light.loc[:, "veh_type"] = "light"

    df_intra_medium = df_intra[df_intra["veh_type"] == "mediumtruck"]
    df_intra_medium.loc[:, "veh_type"] = "medium"
    df_intra_heavy = df_intra[df_intra["veh_type"] == "heavytruck"]
    df_intra_heavy.loc[:, "veh_type"] = "heavy"

    df_intra = pd.concat([df_intra_light, df_intra_medium])
    df_intra = pd.concat([df_intra, df_intra_heavy])

    # For intrazonals, assume standard speed bin and roadway type for all intrazonal trips
    speedbin = 4
    roadtype = 5

    iz_rates = df_running_rates[
        (df_running_rates["avgSpeedBinID"] == speedbin)
        & (df_running_rates["roadTypeID"] == roadtype)
    ]

    df_intra = pd.merge(
        df_intra,
        iz_rates,
        on=["hourID", "veh_type"],
        how="left",
        left_index=False,
    )

    # Calculate total grams of emission
    df_intra["grams_tot"] = df_intra["grams_per_mile"] * df_intra["vmt"]
    df_intra["tons_tot"] = grams_to_tons(df_intra["grams_tot"])

    # Write raw output to file
    # df_intra.to_csv(r"outputs/emissions/intrazonal_emissions.csv", index=False)

    return df_intra

def calculate_start_emissions_city(conn, intersect_gdf, model_year, input_settings, summary_settings):
    """ Calculate start emissions based on vehicle population by county and year. """

    # Load observed base year vehicle populations by county
    df_veh = pd.read_sql('SELECT * FROM vehicle_population WHERE year=='+input_settings['base_year'], con=conn)
    
    # Load parcel to county geographic lookup
    parcel_geog = pd.read_sql("SELECT ParcelID, CountyName FROM parcel_"+str(input_settings['base_year'])+"_geography", con=conn) 
    # Scale all vehicles by difference between base year and modeled total vehicles owned from auto onwership model
    df_hh = pl.read_csv(r'outputs/daysim/_household.tsv', separator='\t').to_pandas()
    tot_veh = df_hh['hhvehs'].sum()

    # Scale total county vehicles owned to match model
    tot_veh_model_base_year = summary_settings['tot_veh_model_base_year']
    veh_scale = 1.0+(tot_veh - tot_veh_model_base_year)/tot_veh_model_base_year
    df_veh['vehicles'] = df_veh['vehicles']*veh_scale

    # Select total vehicles by county within the intersected geographies
    # This will indetify the shares of vehicles per county from the spatial joined data
    df_hh = df_hh.merge(parcel_geog, left_on='hhparcel', right_on='ParcelID')    # join hh data to parcels
    _df_hh = df_hh[df_hh['hhparcel'].isin(intersect_gdf['parcelid'])]    # Intersect with filtered geographic data
    _hh_vehs = _df_hh.groupby('CountyName').sum()[['hhvehs']]    # Get total vehicles by county within filtered geog
    
    # Calculate percent of vehicles in each county for filtered geog versus full results by county
    county_tot_vehs = df_hh.groupby('CountyName').sum()[['hhvehs']].reset_index()
    subset_vehs = _df_hh.groupby('CountyName').sum()[['hhvehs']].reset_index()
    county_subset_shares = county_tot_vehs.merge(subset_vehs, on='CountyName', how='left', suffixes=['_tot', '_subset']).fillna(0)
    county_subset_shares['hhvehs_share'] = county_subset_shares['hhvehs_subset']/county_subset_shares['hhvehs_tot']
    county_subset_shares['CountyName'] = county_subset_shares['CountyName'].str.lower()
    
    # Apply shares to the total vehicles df; results are scaled # of vehicles from filtered geog within each county
    df_veh = df_veh.merge(county_subset_shares[['CountyName','hhvehs_share']], left_on='county', right_on='CountyName', how='left')
    df_veh['vehicles'] = df_veh['vehicles'] *df_veh['hhvehs_share']

    df_veh = df_veh[df_veh['vehicles'] > 0]

    # Join with rates to calculate total emissions
    start_rates_df = pd.read_sql('SELECT * FROM start_emission_rates_by_veh_type WHERE year=='+model_year, con=conn)
    
    # Select winter rates for pollutants other than those listed in summer_list
    df_summer = start_rates_df[start_rates_df['pollutantID'].isin(summary_settings['summer_list'])]
    df_summer = df_summer[df_summer['monthID'] == 7]
    df_winter = start_rates_df[~start_rates_df['pollutantID'].isin(summary_settings['summer_list'])]
    df_winter = df_winter[df_winter['monthID'] == 1]
    start_rates_df = pd.concat([df_winter,df_summer])
    
    # Sum total emissions across all times of day, by county, for each pollutant
    start_rates_df = start_rates_df.groupby(['pollutantID','veh_type']).sum()[['ratePerVehicle']].reset_index()
    df = pd.merge(df_veh, start_rates_df, left_on=['type'],right_on=['veh_type'])
    df['start_grams'] = df['vehicles']*df['ratePerVehicle'] 
    df['start_tons'] = grams_to_tons(df['start_grams'])
    df = df.groupby(['pollutantID','veh_type','county']).sum().reset_index()

    return df

def calculate_start_emissions(parcel_intersect_gdf, input_settings, summary_settings, conn):
    """Calculate start emissions based on vehicle population by year."""

    df_veh = pd.read_sql(
        "SELECT * FROM vehicle_population WHERE year=="
        + input_settings["base_year"],
        con=conn,
    )
    df_veh = df_veh.groupby(['type']).sum()[['vehicles']].reset_index()

    # Scale all vehicles by difference between base year and model total vehicles owned from auto ownership model
    df_hh = pl.read_csv(r"outputs/daysim/_household.tsv", separator="\t",)
    tot_veh = df_hh["hhvehs"].sum()

    # Scale vehicles by change in household vehicle ownership model versus base year
    veh_scale = 1.0 + (tot_veh - summary_settings["tot_veh_model_base_year"]) / summary_settings["tot_veh_model_base_year"]
    df_veh["vehicles"] = df_veh["vehicles"] * veh_scale

    # Join with rates to calculate total emissions
    start_rates_df = load_starting_rates(input_settings, summary_settings, conn)

    # Select winter rates for pollutants other than those listed in summer_list
    df_summer = start_rates_df[
        start_rates_df["pollutantID"].isin(summary_settings["summer_list"])
    ]
    df_summer = df_summer[df_summer["monthID"] == 7]
    df_winter = start_rates_df[
        ~start_rates_df["pollutantID"].isin(summary_settings["summer_list"])
    ]
    df_winter = df_winter[df_winter["monthID"] == 1]
    start_rates_df = pd.concat([df_winter, df_summer])

    # Sum total emissions across all times of day, by county, for each pollutant
    start_rates_df = (
        start_rates_df.groupby(["pollutantID", "veh_type"])
        .sum()[["ratePerVehicle"]]
        .reset_index()
    )

    df = pd.merge(
        df_veh,
        start_rates_df,
        left_on=["type"],
        right_on=["veh_type"],
    )
    df["start_grams"] = df["vehicles"] * df["ratePerVehicle"]
    df["start_tons"] = grams_to_tons(df["start_grams"])
    df = df.groupby(["pollutantID", "veh_type"]).sum().reset_index()

    # Calculate bus start emissions
    # Load data taken from NTD that reports number of bus vehicles "operated in maximum service"
    df_bus_veh = pd.read_sql(
        "SELECT * FROM bus_vehicles WHERE year==" + input_settings["base_year"],
        con=conn,
    )
    tot_buses = df_bus_veh["bus_vehicles_in_service"].sum()

    df_bus = start_rates_df[start_rates_df["veh_type"] == "transit"]
    df_bus["start_grams"] = df_bus["ratePerVehicle"] * tot_buses
    df_bus["start_tons"] = grams_to_tons(df_bus["start_grams"])
    df_bus["veh_type"] = "transit"

    df = pd.concat([df, df_bus])

    # df.to_csv(r"outputs/emissions/start_emissions.csv", index=False)

    return df

def load_running_rates(input_settings, summary_settings, conn):
    """Load running emission rates by vehicle type, for the model year"""

    # FIXME: log which rates are used

    if summary_settings["emissions_scenario"] == "standard":
        df_running_rates = pd.read_sql(
            "SELECT * FROM running_emission_rates_by_veh_type WHERE year=="
            + input_settings["model_year"],
            con=conn,
        )
        print("Using standard running rates.")
    else:
        df_running_rates = pd.read_csv(os.path.join(
            summary_settings["emissions_scenario"],
            "running_emission_rates_by_veh_type.csv")
        )
        df_running_rates = df_running_rates[df_running_rates['year'] == int(input_settings["model_year"])]
        print("Using scenario running rates specified in summary_configuration.toml.")

    df_running_rates.rename(columns={"ratePerDistance": "grams_per_mile"}, inplace=True)
    df_running_rates["year"] = df_running_rates["year"].astype("str")

    return df_running_rates

def load_starting_rates(input_settings, summary_settings, conn):
    """Load starting emission rates by vehicle type, for the model year"""

    if summary_settings["emissions_scenario"] == "standard":
        df_starting_rates = pd.read_sql(
            "SELECT * FROM start_emission_rates_by_veh_type WHERE year=="
            + input_settings["model_year"],
            con=conn,
        )
        print("Using standard start rates.")
    else:
        df_starting_rates = pd.read_csv(os.path.join(
            summary_settings["emissions_scenario"],
            "start_emission_rates_by_veh_type.csv")
        )
        df_starting_rates = df_starting_rates[df_starting_rates['year'] == int(input_settings["model_year"])]
        print("Using scenario start rates specified in summary_configuration.toml.")

    return df_starting_rates