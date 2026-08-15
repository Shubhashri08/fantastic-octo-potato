from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# VIGRAH — PHASE A / A4.2
# CCTV → Nearest OSM Road Matching
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

CCTV_FILE = (
    ROOT
    / "data"
    / "processed"
    / "cctv"
    / "cctv_points.parquet"
)

OSM_DIR = (
    ROOT
    / "data"
    / "processed"
    / "osm"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTPUT_DIR
    / "cctv_road_mapping.parquet"
)


CITY_CONFIG = {
    "Mumbai": {
        "roads": OSM_DIR / "mumbai_roads.parquet",
        "crs": "EPSG:32643",
    },

    "Bengaluru": {
        "roads": OSM_DIR / "bengaluru_roads.parquet",
        "crs": "EPSG:32643",
    },
}


print("=" * 80)
print("VIGRAH — A4.2 CCTV → OSM ROAD MATCHING")
print("=" * 80)


# ------------------------------------------------------------
# Load CCTV
# ------------------------------------------------------------

if not CCTV_FILE.exists():

    raise FileNotFoundError(
        f"CCTV dataset not found:\n{CCTV_FILE}"
    )


print("\nLoading CCTV points...")

cctv = gpd.read_parquet(
    CCTV_FILE
)

print(
    f"CCTV records loaded: "
    f"{len(cctv):,}"
)


# ------------------------------------------------------------
# Basic check
# ------------------------------------------------------------

expected_total = 1551

if len(cctv) != expected_total:

    raise ValueError(
        f"Expected {expected_total} CCTV points, "
        f"found {len(cctv)}."
    )


# ------------------------------------------------------------
# Process city separately
# ------------------------------------------------------------

matched_city_results = []


for city, config in CITY_CONFIG.items():

    print("\n" + "=" * 80)
    print(f"MATCHING — {city.upper()}")
    print("=" * 80)

    roads_file = config["roads"]

    if not roads_file.exists():

        raise FileNotFoundError(
            f"Road dataset not found:\n{roads_file}"
        )


    # --------------------------------------------------------
    # Select CCTV
    # --------------------------------------------------------

    city_cctv = cctv[
        cctv["city"] == city
    ].copy()

    print(
        f"CCTV points: "
        f"{len(city_cctv):,}"
    )


    # --------------------------------------------------------
    # Load roads
    # --------------------------------------------------------

    print("\nLoading OSM roads...")

    roads = gpd.read_parquet(
        roads_file
    )

    print(
        f"Road features: "
        f"{len(roads):,}"
    )


    # --------------------------------------------------------
    # Ensure CRS
    # --------------------------------------------------------

    if roads.crs is None:

        raise ValueError(
            f"{city} road dataset has no CRS."
        )

    if city_cctv.crs is None:

        raise ValueError(
            f"{city} CCTV dataset has no CRS."
        )


    # --------------------------------------------------------
    # Reproject to metric CRS
    # --------------------------------------------------------

    metric_crs = config["crs"]

    print(
        f"\nProjecting to metric CRS: "
        f"{metric_crs}"
    )

    city_cctv_metric = (
        city_cctv
        .to_crs(metric_crs)
        .copy()
    )

    roads_metric = (
        roads
        .to_crs(metric_crs)
        .copy()
    )


    # --------------------------------------------------------
    # Nearest spatial join
    # --------------------------------------------------------

    print(
        "\nFinding nearest road for every CCTV point..."
    )

    matched = gpd.sjoin_nearest(
        city_cctv_metric,
        roads_metric[
            [
                "road_id",
                "road_name",
                "highway",
                "oneway",
                "lanes",
                "maxspeed",
                "surface",
                "bridge",
                "tunnel",
                "geometry",
            ]
        ],
        how="left",
        distance_col="distance_to_road_m",
    )


    # --------------------------------------------------------
    # Handle duplicate nearest matches
    # --------------------------------------------------------

    # A CCTV point can theoretically have multiple roads
    # at exactly the same minimum distance.
    #
    # Keep one deterministic match per camera.

    matched = (
        matched
        .sort_values(
            [
                "camera_id",
                "distance_to_road_m",
                "road_id",
            ]
        )
        .drop_duplicates(
            subset=["camera_id"],
            keep="first"
        )
        .copy()
    )


    # --------------------------------------------------------
    # Restore geographic CRS
    # --------------------------------------------------------

    matched = matched.to_crs(
        "EPSG:4326"
    )


    # --------------------------------------------------------
    # Remove spatial join helper columns
    # --------------------------------------------------------

    if "index_right" in matched.columns:

        matched = matched.drop(
            columns=["index_right"]
        )


    # --------------------------------------------------------
    # Add matching metadata
    # --------------------------------------------------------

    matched["match_method"] = (
        "nearest_osm_road"
    )

    matched["matching_crs"] = (
        metric_crs
    )


    matched_city_results.append(
        matched
    )


    # --------------------------------------------------------
    # City statistics
    # --------------------------------------------------------

    print("\n--- Matching statistics ---")

    print(
        f"CCTV points: "
        f"{len(city_cctv):,}"
    )

    print(
        f"Matched: "
        f"{matched['road_id'].notna().sum():,}"
    )

    print(
        f"Unmatched: "
        f"{matched['road_id'].isna().sum():,}"
    )

    if matched["distance_to_road_m"].notna().any():

        distances = (
            matched["distance_to_road_m"]
            .dropna()
        )

        print(
            f"Mean distance: "
            f"{distances.mean():.2f} m"
        )

        print(
            f"Median distance: "
            f"{distances.median():.2f} m"
        )

        print(
            f"Maximum distance: "
            f"{distances.max():.2f} m"
        )

        print(
            f">10 m: "
            f"{(distances > 10).sum():,}"
        )

        print(
            f">25 m: "
            f"{(distances > 25).sum():,}"
        )

        print(
            f">50 m: "
            f"{(distances > 50).sum():,}"
        )


# ------------------------------------------------------------
# Combine cities
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("COMBINING CITY RESULTS")
print("=" * 80)

result = gpd.GeoDataFrame(
    pd.concat(
        matched_city_results,
        ignore_index=True
    ),
    geometry="geometry",
    crs="EPSG:4326"
)


# ------------------------------------------------------------
# Final validation
# ------------------------------------------------------------

print("\nFinal CCTV records:")

print(
    result["city"]
    .value_counts()
    .to_string()
)

print(
    f"\nTotal: "
    f"{len(result):,}"
)


# Ensure exactly one result per camera

unique_cameras = (
    result["camera_id"]
    .nunique()
)

print(
    f"Unique cameras: "
    f"{unique_cameras:,}"
)

if unique_cameras != 1551:

    raise ValueError(
        "Camera count changed during road matching."
    )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

print("\nSaving:")
print(OUTPUT)

result.to_parquet(
    OUTPUT,
    index=False
)


print("\nOutput size:")

print(
    f"{OUTPUT.stat().st_size / (1024 * 1024):.2f} MB"
)


print("\n" + "=" * 80)
print("A4.2 COMPLETE")
print("=" * 80)