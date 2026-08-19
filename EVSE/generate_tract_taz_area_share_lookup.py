"""Generate TAZ-to-tract lookup with area shares.

This script creates one row per intersecting TAZ/tract pair and computes the
share of each TAZ's area that falls within each tract.
"""

import os

import geopandas as gpd
import psrcelmerpy
import toml


OUTPUT_FILE = "taz_tract_area_share_lookup.csv"


def main() -> None:
    config = toml.load("config.toml")
    eg_conn = psrcelmerpy.ElmerGeoConn()

    taz_gdf = eg_conn.read_geolayer("taz2010_no_water")
    tract_gdf = eg_conn.read_geolayer("tract2020_nowater")

    taz_gdf = taz_gdf.to_crs(epsg=config["project_epsg"])
    tract_gdf = tract_gdf.to_crs(epsg=config["project_epsg"])

    # Keep only columns needed for output and area calculations.
    taz_work = taz_gdf[["taz", "geometry"]].copy()
    tract_work = tract_gdf[["geoid20", "geometry"]].copy()

    taz_work["taz_total_area"] = taz_work.geometry.area

    intersections = gpd.overlay(
        taz_work,
        tract_work,
        how="intersection",
        keep_geom_type=True,
    )
    intersections["intersection_area"] = intersections.geometry.area

    output_df = intersections[["taz", "geoid20", "intersection_area", "taz_total_area"]].copy()
    output_df["taz"] = output_df["taz"].astype(int)
    output_df["taz_area_share_in_tract"] = (
        output_df["intersection_area"] / output_df["taz_total_area"]
    )

    output_path = os.path.join(config["working_dir"], OUTPUT_FILE)
    output_df.to_csv(output_path, index=False)

    # QA: check whether shares sum close to 1.0 by TAZ.
    share_sums = output_df.groupby("taz", as_index=False)["taz_area_share_in_tract"].sum()
    outliers = share_sums[
        (share_sums["taz_area_share_in_tract"] < 0.99)
        | (share_sums["taz_area_share_in_tract"] > 1.01)
    ]

    print(f"Wrote {len(output_df):,} rows to {output_path}")
    print(f"TAZ count in area-share table: {share_sums['taz'].nunique():,}")
    if outliers.empty:
        print("All TAZ area-share sums are within [0.99, 1.01].")
    else:
        print(
            "Found "
            f"{len(outliers):,} TAZs with share sums outside [0.99, 1.01]. "
            "Review boundary/sliver cases."
        )


if __name__ == "__main__":
    main()
