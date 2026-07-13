import os
import pandas as pd

pd.options.mode.chained_assignment = None


def grams_to_tons(value):
    """Convert grams to tons."""

    value = value / 453.592
    value = value / 2000

    return value


def calculate_interzonal_vmt(df, input_settings, summary_settings):
    """Calcualte inter-zonal running emission rates from network outputs"""

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


def finalize_emissions(df, group_col="veh_type"):
    """
    Compute PM10 and PM2.5 totals, sort index by pollutant value, and pollutant name.
    For total columns add col_suffix (e.g., col_suffix='intrazonal_tons')
    """

    pm10 = (
        df[df["pollutantID"].isin([100, 106, 107])]
        .groupby(group_col)
        .sum()
        .reset_index()
    )
    pm10["pollutantID"] = "PM10"
    pm25 = (
        df[df["pollutantID"].isin([110, 116, 117])]
        .groupby(group_col)
        .sum()
        .reset_index()
    )
    pm25["pollutantID"] = "PM25"
    df = pd.concat([df, pm10])
    df = pd.concat([df, pm25])

    return df


def calculate_interzonal_emissions(df, df_rates, include_light_modes=False):
    """Calculate link emissions using rates unique to speed, road type, hour, and vehicle type."""

    df.rename(
        columns={
            "avgspeedbinId": "avgSpeedBinID",
            "roadtypeId": "roadTypeID",
            "hourId": "hourID",
        },
        inplace=True,
    )

    if include_light_modes:
        df["sov"] = df["sov_vmt"].copy()
        df["hov2"] = df["hov2_vmt"].copy() + df["tnc_vmt"].copy()    # Group TNC with HOV2
        df["hov3"] = df["hov3_vmt"].copy()
    else:
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
        var_name="mode",
        value_name="vmt",
    )

    # Map vehicle type names to those used in emission rates
    df["veh_type"] = df["mode"].map(
        {'sov': 'light',
         'hov2': 'light',
         'hov3': 'light',
         'light': 'light',
         'medium': 'medium',
         'heavy': 'heavy',
         'transit': 'transit'})
    

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


def calculate_intrazonal_vmt(summary_settings, df_iz, hpms_scale=1.0):
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
    df['VMT'] = df['vol'] * df['izdist']*hpms_scale
    df = df.groupby(['tod','vehicle_type']).sum()[['VMT']].reset_index()
    # Use hourly periods from emission rate files
    df["hourId"] = df["tod"].map(summary_settings["tod_lookup"]).astype("int")
    
    # Export this file for use with other rate calculations
    # Includes total VMT for each group for which rates are available
    df = df[['VMT','tod','vehicle_type','hourId']]
    # df.to_csv(r"outputs/emissions/intrazonal_vmt_grouped.csv", index=False)

    return df


def calculate_intrazonal_emissions(df_intra, df_running_rates, config):
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

    df_intra_medium = df_intra[df_intra["veh_type"] == "mediumtruck"]
    df_intra_medium.loc[:, "veh_type"] = "medium"
    df_intra_medium.loc[:, "mode"] = "medium"
    df_intra_heavy = df_intra[df_intra["veh_type"] == "heavytruck"]
    df_intra_heavy.loc[:, "veh_type"] = "heavy"
    df_intra_heavy.loc[:, "mode"] = "heavy"

    if config["include_light_modes"]:
        df_intra_sov = df_intra[df_intra["veh_type"] == "sov"]
        df_intra_sov.loc[:, "veh_type"] = "light"
        df_intra_sov.loc[:, "mode"] = "sov"
        df_intra_hov2 = df_intra[df_intra["veh_type"] == "hov2"]
        df_intra_hov2.loc[:, "veh_type"] = "light"
        df_intra_hov2.loc[:, "mode"] = "hov2"
        df_intra_hov3 = df_intra[df_intra["veh_type"] == "hov3"]
        df_intra_hov3.loc[:, "veh_type"] = "light"
        df_intra_hov3.loc[:, "mode"] = "hov3"
        df_intra = pd.concat([df_intra_sov, df_intra_hov2, df_intra_hov3, df_intra_medium, df_intra_heavy])
    else:
        df_intra_light = df_intra[df_intra["veh_type"].isin(["sov", "hov2", "hov3"])]
        df_intra_light = (
            df_intra_light.groupby(["hourID"]).sum()[["vmt"]].reset_index()
        )
        df_intra_light.loc[:, "veh_type"] = "light"
        df_intra_light.loc[:, "mode"] = "light"
        df_intra = pd.concat([df_intra_light, df_intra_medium, df_intra_heavy])

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

def calculate_start_emissions(input_settings, start_rates_df, hh_veh_year, summary_settings, df_bus_veh, conn):
    """Calculate start emissions based on vehicle population by year."""

    df_veh = pd.read_sql(
        "SELECT * FROM vehicle_population WHERE year=="
        + input_settings["base_year"],
        con=conn,
    )
    df_veh = df_veh.groupby(['type']).sum()[['vehicles']].reset_index()

    # # Scale all vehicles by difference between base year and model total vehicles owned from auto ownership model
    # df_hh = pl.read_csv(r"outputs/daysim/_household.tsv", separator="\t",)
    # tot_veh = df_hh["hhvehs"].sum()
    tot_veh = hh_veh_year.copy()

    # Scale vehicles by change in household vehicle ownership model versus base year
    veh_scale = 1.0 + (tot_veh - summary_settings["tot_veh_model_base_year"]) / summary_settings["tot_veh_model_base_year"]
    df_veh["vehicles"] = df_veh["vehicles"] * veh_scale

    # Join with rates to calculate total emissions
    # start_rates_df = load_starting_rates(input_settings, summary_settings, conn)

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
    tot_buses = df_bus_veh["bus_vehicles_in_service"].sum()

    df_bus = start_rates_df[start_rates_df["veh_type"] == "transit"]
    df_bus["start_grams"] = df_bus["ratePerVehicle"] * tot_buses
    df_bus["start_tons"] = grams_to_tons(df_bus["start_grams"])
    df_bus["veh_type"] = "transit"

    df = pd.concat([df, df_bus])

    # df.to_csv(r"outputs/emissions/start_emissions.csv", index=False)

    return df


def load_running_rates(model_year, summary_settings, conn):
    """Load running emission rates by vehicle type, for the model year"""

    # FIXME: log which rates are used

    if summary_settings["emissions_scenario"] == "standard":
        df_running_rates = pd.read_sql(
            "SELECT * FROM running_emission_rates_by_veh_type WHERE year=="
            + model_year,
            con=conn,
        )
        print("Using standard running rates.")
    else:
        df_running_rates = pd.read_csv(os.path.join(
            summary_settings["emissions_scenario"],
            "running_emission_rates_by_veh_type.csv")
        )
        df_running_rates = df_running_rates[df_running_rates['year'] == int(model_year)]
        print("Using scenario running rates specified in summary_configuration.toml.")

    df_running_rates.rename(columns={"ratePerDistance": "grams_per_mile"}, inplace=True)
    df_running_rates["year"] = df_running_rates["year"].astype("str")

    df_summer = df_running_rates[
    df_running_rates["pollutantID"].isin(summary_settings["summer_list"])
    ]
    df_summer = df_summer[df_summer["monthID"] == 7]
    df_winter = df_running_rates[
        ~df_running_rates["pollutantID"].isin(summary_settings["summer_list"])
    ]
    df_winter = df_winter[df_winter["monthID"] == 1]
    df_running_rates = pd.concat([df_winter, df_summer])

    return df_running_rates

def load_starting_rates(model_year, summary_settings, conn):
    """Load starting emission rates by vehicle type, for the model year"""

    if summary_settings["emissions_scenario"] == "standard":
        df_starting_rates = pd.read_sql(
            "SELECT * FROM start_emission_rates_by_veh_type WHERE year=="
            + model_year,
            con=conn,
        )
        print("Using standard start rates.")
    else:
        df_starting_rates = pd.read_csv(os.path.join(
            summary_settings["emissions_scenario"],
            "start_emission_rates_by_veh_type.csv")
        )
        df_starting_rates = df_starting_rates[df_starting_rates['year'] == int(model_year)]
        print("Using scenario start rates specified in summary_configuration.toml.")

    return df_starting_rates

def intersect_geog(my_gdf_shp, gdf_network):
    
    # Intersect geography this with the network shapefile
    gdf_intersect = gpd.overlay(gdf_network, my_gdf_shp, how="intersection", keep_geom_type=False)

    # # Will need to relaculate the lengths since some were split across the regional geographies
    gdf_intersect['new_length'] = gdf_intersect.geometry.length/5280.0

    # ### IMPORTANT
    # # filter out the polygon results and only keep lines
    gdf_intersect = gdf_intersect[gdf_intersect.geometry.type.isin(['MultiLineString','LineString'])]
    
    return gdf_intersect


def load_network_summary(filepath):
    """Load network-level results using a standard procedure. """
    df = pd.read_csv(filepath)

    # Congested network components by time of day
    df.columns

    # Get freeflow from 20to5 period

    # Exclude trips taken on non-designated facilities (facility_type == 0)
    # These are artificial (weave lanes to connect HOV) or for non-auto uses 
    df = df[df['data3'] != 0]    # data3 represents facility_type

    # calculate total link VMT and VHT
    df['VMT'] = df['@tveh']*df['length']
    df['VHT'] = df['@tveh']*df['auto_time']/60

    # Define facility type
    df.loc[df['data3'].isin([1,2]), 'facility_type'] = 'highway'
    df.loc[df['data3'].isin([3,4,6]), 'facility_type'] = 'arterial'
    df.loc[df['data3'].isin([5]), 'facility_type'] = 'connector'

    # Calculate delay
    # Select links from overnight time of day
    delay_df = df.loc[df['tod'] == '20to5'][['ij','auto_time']]
    delay_df.rename(columns={'auto_time':'freeflow_time'}, inplace=True)

    # Merge delay field back onto network link df
    df = pd.merge(df, delay_df, on='ij', how='left')

    # Calcualte hourly delay
    df['total_delay'] = ((df['auto_time']-df['freeflow_time'])*df['@tveh'])/60    # sum of (volume)*(travtime diff from freeflow)

    df['county'] =df['@countyid'].map({33: 'King',
                                      35: 'Kitsap',
                                      53: 'Pierce',
                                      61: 'Snohomish'})
    
    
    
    return df


def calculate_network_emissions(df_network, df_rates, summary_settings, include_light_modes=False):
    """Calculate emissions for each network row (link) by pollutant.

    Returns a long-form DataFrame with one row per link and pollutant containing
    grams and tons totals.
    """
    df = df_network.copy()

    # preserve a link identifier
    if "ij" in df.columns:
        id_col = "ij"
    else:
        id_col = "link_id"
        df[id_col] = df.index

    # compute vehicle VMT per link using reindex to tolerate missing columns explicitly
    sov_cols = ["@sov_inc1", "@sov_inc2", "@sov_inc3"]
    df["sov_vol"] = df.reindex(columns=sov_cols, fill_value=0).sum(axis=1)
    df["sov_vmt"] = df["sov_vol"] * df["length"]

    hov2_cols = ["@hov2_inc1", "@hov2_inc2", "@hov2_inc3"]
    df["hov2_vol"] = df.reindex(columns=hov2_cols, fill_value=0).sum(axis=1)
    df["hov2_vmt"] = df["hov2_vol"] * df["length"]

    hov3_cols = ["@hov3_inc1", "@hov3_inc2", "@hov3_inc3"]
    df["hov3_vol"] = df.reindex(columns=hov3_cols, fill_value=0).sum(axis=1)
    df["hov3_vmt"] = df["hov3_vol"] * df["length"]

    tnc_cols = ["@tnc_inc1", "@tnc_inc2", "@tnc_inc3"]
    df["tnc_vol"] = df.reindex(columns=tnc_cols, fill_value=0).sum(axis=1)
    df["tnc_vmt"] = df["tnc_vol"] * df["length"]

    # vehicle counts (per-link) * length => VMT
    df["bus_vmt"] = df.reindex(columns=["@bveh"], fill_value=0)["@bveh"] * df["length"]
    df["medium_truck_vmt"] = df.reindex(columns=["@mveh"], fill_value=0)["@mveh"] * df["length"]
    df["heavy_truck_vmt"] = df.reindex(columns=["@hveh"], fill_value=0)["@hveh"] * df["length"]

    # TOD hour mapping
    df["hourID"] = df["tod"].map(summary_settings["tod_lookup"]).astype("int")

    # congested speed and speed bin
    df["congested_speed"] = (df["length"] / df["auto_time"]) * 60
    df["avgSpeedBinID"] = pd.cut(
        df["congested_speed"],
        summary_settings["speed_bins"],
        labels=range(1, len(summary_settings["speed_bins"])),
    ).astype("int")

    # map facility type to road type id
    df["roadTypeID"] = (
        df["data3"].map({int(k): v for k, v in summary_settings["fac_type_lookup"].items()}).astype("int")
    )

    # prepare vehicle group columns
    if include_light_modes:
        df["sov"] = df["sov_vmt"].copy()
        df["hov2"] = df["hov2_vmt"].copy() + df["tnc_vmt"].copy()
        df["hov3"] = df["hov3_vmt"].copy()
    else:
        df["light"] = df["sov_vmt"] + df["hov2_vmt"] + df["hov3_vmt"] + df["tnc_vmt"]
    df["medium"] = df["medium_truck_vmt"]
    df["heavy"] = df["heavy_truck_vmt"]
    df["transit"] = df["bus_vmt"]

    drop_cols = [
        "sov_vmt",
        "hov2_vmt",
        "hov3_vmt",
        "tnc_vmt",
        "medium_truck_vmt",
        "heavy_truck_vmt",
        "bus_vmt",
    ]
    for c in drop_cols:
        if c in df.columns:
            df.drop(c, axis=1, inplace=True)

    # melt so each row is a vehicle group for a link
    id_vars = [id_col, "avgSpeedBinID", "roadTypeID", "hourID"]
    value_vars = [v for v in ["sov", "hov2", "hov3", "light", "medium", "heavy", "transit"] if v in df.columns]

    df_melt = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name="mode", value_name="vmt")

    # map mode to veh_type used by rates
    df_melt["veh_type"] = df_melt["mode"].map(
        {
            "sov": "light",
            "hov2": "light",
            "hov3": "light",
            "light": "light",
            "medium": "medium",
            "heavy": "heavy",
            "transit": "transit",
        }
    )

    # merge with rates
    df_merged = pd.merge(
        df_melt,
        df_rates,
        on=["avgSpeedBinID", "roadTypeID", "hourID", "veh_type"],
        how="left",
        left_index=False,
    )

    # compute totals
    df_merged["grams_tot"] = df_merged["grams_per_mile"] * df_merged["vmt"]
    df_merged["tons_tot"] = grams_to_tons(df_merged["grams_tot"])

    # aggregate per link and pollutant
    df_link_pollutant = (
        df_merged.groupby([id_col, "pollutantID"]).sum()[["grams_tot", "tons_tot"]].reset_index()
    )

    # Merge link length as additional field for analysis
    df_len = df.groupby("ij").first()[["length"]]
    df_link_pollutant = pd.merge(
        df_link_pollutant,
        df_len,
        left_on="ij",
        right_index=True,
        how="left",
    )

    # Compute daily VMT and add as column to df_link_pollutant
    df_daily_vmt = df_melt.groupby(id_col).sum()[["vmt"]].reset_index()
    df_link_pollutant = pd.merge(
        df_link_pollutant,
        df_daily_vmt,
        left_on=id_col,
        right_on=id_col,
        how="left",
    )

    # Convert length to volume, assume equal sides of a cube equal to ij length
    df_link_pollutant["length_meters"] = df_link_pollutant["length"] * 1609.34
    df_link_pollutant["volume_meters"] = df_link_pollutant["length_meters"] ** 3
    # Calculate micrograms per cubic meter using conversion factor of 1 mile = 160934 cm, and 1 gram = 1e9 micrograms, and dividing by length cubed to get concentration
    df_link_pollutant["micrograms"] = df_link_pollutant["grams_tot"] * 1e9
    df_link_pollutant["ug_per_m3"] = df_link_pollutant["micrograms"] / df_link_pollutant["volume_meters"]


    return df_link_pollutant