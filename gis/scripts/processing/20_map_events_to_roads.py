from pathlib import Path
import json

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


# =============================================================================
# VIGRAH — D1 EVENT → OSM ROAD MAPPING
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

EVENT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "events"
    / "sample_layer3_events.json"
)

ROAD_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "osm"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "event_road_mapping.parquet"
)


CITY_ROADS = {
    "Mumbai":
        ROAD_DIR / "mumbai_roads.parquet",

    "Bengaluru":
        ROAD_DIR / "bengaluru_roads.parquet",
}


SOURCE_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32643"


# =============================================================================
# LOAD EVENTS
# =============================================================================

def load_events():

    print("Loading events...")
    print(f"Input: {EVENT_FILE}")

    if not EVENT_FILE.exists():

        raise FileNotFoundError(
            f"Event file does not exist:\n{EVENT_FILE}"
        )

    with open(
        EVENT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if not isinstance(data, list):

        raise RuntimeError(
            "Event JSON must contain a list of events."
        )

    df = pd.DataFrame(data)

    required_columns = [
        "event_id",
        "timestamp",
        "latitude",
        "longitude",
        "event_type",
        "severity",
        "confidence",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise RuntimeError(
            f"Missing event columns: {missing}"
        )

    print(
        f"Events loaded: {len(df)}"
    )

    return df


# =============================================================================
# EVENT VALIDATION
# =============================================================================

def validate_events(df):

    print("\n" + "-" * 80)
    print("EVENT VALIDATION")
    print("-" * 80)

    print(
        f"Event records: {len(df)}"
    )

    duplicate_ids = (
        df["event_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate event IDs: {duplicate_ids}"
    )

    if duplicate_ids > 0:

        raise RuntimeError(
            "Duplicate event IDs detected."
        )

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    df["confidence"] = pd.to_numeric(
        df["confidence"],
        errors="coerce"
    )

    if df[
        [
            "latitude",
            "longitude",
            "confidence"
        ]
    ].isna().any().any():

        raise RuntimeError(
            "Invalid numeric event values detected."
        )

    if (
        (df["latitude"] < -90).any()
        or
        (df["latitude"] > 90).any()
    ):

        raise RuntimeError(
            "Invalid latitude detected."
        )

    if (
        (df["longitude"] < -180).any()
        or
        (df["longitude"] > 180).any()
    ):

        raise RuntimeError(
            "Invalid longitude detected."
        )

    if (
        (df["confidence"] < 0).any()
        or
        (df["confidence"] > 1).any()
    ):

        raise RuntimeError(
            "Event confidence must be between 0 and 1."
        )

    print("Event schema: PASS")


# =============================================================================
# LOAD ROADS
# =============================================================================

def load_roads():

    print("\n" + "-" * 80)
    print("LOADING ROAD DATASETS")
    print("-" * 80)

    roads = {}

    for city, path in CITY_ROADS.items():

        print(f"\n{city}:")
        print(f"  {path}")

        if not path.exists():

            raise FileNotFoundError(
                f"Road dataset missing:\n{path}"
            )

        road_gdf = gpd.read_parquet(path)

        print(
            f"  Roads: {len(road_gdf):,}"
        )

        if road_gdf.crs is None:

            raise RuntimeError(
                f"{city} roads have no CRS."
            )

        print(
            f"  CRS: {road_gdf.crs}"
        )

        required_road_columns = [
            "road_id",
            "road_name",
            "highway",
            "geometry",
        ]

        missing = [
            column
            for column in required_road_columns
            if column not in road_gdf.columns
        ]

        if missing:

            raise RuntimeError(
                f"{city} road dataset is missing: {missing}"
            )

        roads[city] = road_gdf

    return roads


# =============================================================================
# DETERMINE CITY
# =============================================================================

def assign_city(events, roads):

    print("\n" + "-" * 80)
    print("DETERMINING EVENT CITY")
    print("-" * 80)

    # Use road coverage bounds.
    city_bounds = {}

    for city, road_gdf in roads.items():

        boundary = (
            road_gdf
            .to_crs(SOURCE_CRS)
            .geometry
            .union_all()
            .convex_hull
        )

        city_bounds[city] = boundary

    def find_city(point):

        for city, boundary in city_bounds.items():

            if boundary.contains(point):

                return city

        return None

    events["city"] = (
        events.geometry.apply(find_city)
    )

    print(
        events["city"]
        .value_counts(dropna=False)
    )

    outside = (
        events["city"]
        .isna()
        .sum()
    )

    print(
        f"Events outside operational areas: {outside}"
    )

    return events


# =============================================================================
# MATCH EVENTS TO ROADS
# =============================================================================

def match_city_events(
    city,
    city_events,
    city_roads
):

    print(f"\nMatching {city}:")
    print(
        f"  Events: {len(city_events):,}"
    )

    print(
        f"  Roads:  {len(city_roads):,}"
    )

    # Project into metric CRS.
    events_metric = (
        city_events
        .to_crs(METRIC_CRS)
        .copy()
    )

    roads_metric = (
        city_roads
        .to_crs(METRIC_CRS)
        .copy()
    )

    # -------------------------------------------------------------------------
    # IMPORTANT
    #
    # sjoin_nearest can return multiple roads when two roads are equally near.
    #
    # Therefore we deliberately create a temporary event row identifier.
    # We then sort by:
    #
    #   1. event_id
    #   2. distance
    #   3. road_id
    #
    # and retain exactly ONE road per event.
    # -------------------------------------------------------------------------

    events_metric["_event_row_id"] = range(
        len(events_metric)
    )

    road_columns = [
        "road_id",
        "road_name",
        "highway",
        "geometry",
    ]

    roads_metric = roads_metric[
        road_columns
    ].copy()

    matched = gpd.sjoin_nearest(
        events_metric,
        roads_metric,
        how="left",
        distance_col="event_to_road_distance_m"
    )

    print(
        f"  Raw nearest matches: {len(matched):,}"
    )

    # -------------------------------------------------------------------------
    # Detect ties / multiple nearest roads.
    # -------------------------------------------------------------------------

    duplicate_event_rows = (
        matched
        .duplicated(
            subset=["event_id"],
            keep=False
        )
    )

    tie_count = (
        duplicate_event_rows
        .sum()
    )

    if tie_count > 0:

        tied_events = (
            matched.loc[
                duplicate_event_rows,
                "event_id"
            ]
            .nunique()
        )

        print(
            f"  Events with multiple nearest roads: "
            f"{tied_events}"
        )

        print(
            "  Applying deterministic road selection..."
        )

    # Convert road_id to string for stable sorting.
    matched["_road_id_sort"] = (
        matched["road_id"]
        .astype(str)
    )

    matched = (
        matched
        .sort_values(
            [
                "event_id",
                "event_to_road_distance_m",
                "_road_id_sort",
            ],
            kind="stable"
        )
        .drop_duplicates(
            subset=["event_id"],
            keep="first"
        )
    )

    # Remove temporary columns.
    matched = matched.drop(
        columns=[
            "_event_row_id",
            "_road_id_sort",
            "index_right",
        ],
        errors="ignore"
    )

    matched["city"] = city

    print(
        f"  Final matches: {len(matched):,}"
    )

    unmatched = (
        matched["road_id"]
        .isna()
        .sum()
    )

    print(
        f"  Unmatched: {unmatched:,}"
    )

    if (
        matched[
            "event_to_road_distance_m"
        ]
        .notna()
        .any()
    ):

        distance = matched[
            "event_to_road_distance_m"
        ]

        print(
            f"  Mean distance: "
            f"{distance.mean():.2f} m"
        )

        print(
            f"  Median distance: "
            f"{distance.median():.2f} m"
        )

        print(
            f"  Maximum distance: "
            f"{distance.max():.2f} m"
        )

    return matched


# =============================================================================
# QUALITY CLASSIFICATION
# =============================================================================

def classify_quality(distance):

    if pd.isna(distance):

        return "unmatched"

    if distance <= 10:

        return "high"

    if distance <= 25:

        return "good"

    if distance <= 50:

        return "low"

    return "review"


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 80)
    print("VIGRAH — D1 EVENT → OSM ROAD MAPPING")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # EVENTS
    # -------------------------------------------------------------------------

    events = load_events()

    validate_events(events)

    input_event_count = len(events)

    # -------------------------------------------------------------------------
    # GEOMETRY
    # -------------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("CREATING EVENT POINTS")
    print("-" * 80)

    geometry = [
        Point(
            longitude,
            latitude
        )
        for longitude, latitude
        in zip(
            events["longitude"],
            events["latitude"]
        )
    ]

    events = gpd.GeoDataFrame(
        events,
        geometry=geometry,
        crs=SOURCE_CRS
    )

    # -------------------------------------------------------------------------
    # ROADS
    # -------------------------------------------------------------------------

    roads = load_roads()

    # -------------------------------------------------------------------------
    # CITY ASSIGNMENT
    # -------------------------------------------------------------------------

    events = assign_city(
        events,
        roads
    )

    # -------------------------------------------------------------------------
    # MATCH
    # -------------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("EVENT → ROAD MATCHING")
    print("-" * 80)

    results = []

    for city in [
        "Mumbai",
        "Bengaluru"
    ]:

        city_events = events[
            events["city"] == city
        ].copy()

        if city_events.empty:

            continue

        matched = match_city_events(
            city,
            city_events,
            roads[city]
        )

        results.append(
            matched
        )

    if not results:

        raise RuntimeError(
            "No events were matched."
        )

    # -------------------------------------------------------------------------
    # COMBINE
    # -------------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("COMBINING RESULTS")
    print("-" * 80)

    result = pd.concat(
        results,
        ignore_index=True
    )

    result = result.drop(
        columns=[
            "index_right"
        ],
        errors="ignore"
    )

    # -------------------------------------------------------------------------
    # QUALITY
    # -------------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("CLASSIFYING ROAD MATCH QUALITY")
    print("-" * 80)

    result[
        "event_road_match_quality"
    ] = (
        result[
            "event_to_road_distance_m"
        ]
        .apply(
            classify_quality
        )
    )

    print(
        result[
            "event_road_match_quality"
        ]
        .value_counts()
    )

    # -------------------------------------------------------------------------
    # OUTPUT SCHEMA
    # -------------------------------------------------------------------------

    output_columns = [

        "event_id",
        "timestamp",

        "latitude",
        "longitude",

        "event_type",
        "severity",
        "confidence",

        "city",

        "road_id",
        "road_name",
        "highway",

        "event_to_road_distance_m",

        "event_road_match_quality",
    ]

    result = result[
        output_columns
    ]

    # -------------------------------------------------------------------------
    # FINAL VALIDATION
    # -------------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("FINAL VALIDATION")
    print("-" * 80)

    output_event_count = (
        result["event_id"]
        .nunique()
    )

    print(
        f"Input events:  {input_event_count}"
    )

    print(
        f"Output rows:   {len(result)}"
    )

    print(
        f"Unique events: {output_event_count}"
    )

    if (
        output_event_count
        != input_event_count
    ):

        raise RuntimeError(
            "Unique event count changed during mapping."
        )

    if (
        result["event_id"]
        .duplicated()
        .any()
    ):

        raise RuntimeError(
            "Duplicate event IDs remain after road selection."
        )

    matched_count = (
        result["road_id"]
        .notna()
        .sum()
    )

    unmatched_count = (
        result["road_id"]
        .isna()
        .sum()
    )

    print(
        f"Matched:       {matched_count}"
    )

    print(
        f"Unmatched:     {unmatched_count}"
    )

    if matched_count == 0:

        raise RuntimeError(
            "Zero events matched to roads."
        )

    print("Record count preservation: PASS")
    print("One-event → one-road rule: PASS")

    # -------------------------------------------------------------------------
    # SAVE
    # -------------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("SAVING EVENT → ROAD DATASET")
    print("-" * 80)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_parquet(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved:\n{OUTPUT_FILE}"
    )

    print(
        f"Output size: "
        f"{OUTPUT_FILE.stat().st_size / 1024:.2f} KB"
    )

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("D1 COMPLETE")
    print("=" * 80)

    print(
        f"\nEvents processed: {input_event_count}"
    )

    print(
        f"Roads matched:    {matched_count}"
    )

    print(
        f"Unmatched:        {unmatched_count}"
    )

    print("\nCity distribution:")

    print(
        result[
            "city"
        ]
        .value_counts()
    )

    print("\nMatch quality:")

    print(
        result[
            "event_road_match_quality"
        ]
        .value_counts()
    )

    print(
        f"\nOutput:\n{OUTPUT_FILE}"
    )

    print(
        "\nNEXT → D2 ROAD → HISTORICAL RISK ENRICHMENT"
    )


if __name__ == "__main__":
    main()