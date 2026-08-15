from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# VIGRAH — C1 ROAD-LEVEL FEATURE CONSTRUCTION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

FEATURE_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

INPUT = (
    FEATURE_DIR
    / "phase_b_historical_features.parquet"
)

OUTPUT = (
    FEATURE_DIR
    / "road_level_features.parquet"
)


print("=" * 80)
print("VIGRAH — C1 ROAD-LEVEL FEATURE CONSTRUCTION")
print("=" * 80)


# ============================================================
# INPUT CHECK
# ============================================================

print("\nInput:")
print(INPUT)

if not INPUT.exists():
    raise FileNotFoundError(
        f"Phase B dataset not found:\n{INPUT}"
    )


# ============================================================
# LOAD
# ============================================================

print("\n" + "-" * 80)
print("LOADING PHASE B DATASET")
print("-" * 80)

df = pd.read_parquet(INPUT)

print(
    f"Records loaded: {len(df):,}"
)

print(
    f"Columns loaded: {len(df.columns)}"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required = [
    "city",
    "road_id",
    "road_name",
    "highway",
    "distance_to_road_m",

    "spatial_match_quality",

    # Accident context
    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "city_accident_fatality_rate",

    # Crime context
    "crime_context_state",
    "crime_context_year",
    "crime_context_level",
    "crime_data_provenance",
    "total_crime_against_women",
    "total_crime_against_children",
    "crime_context_spatial_scope",
    "crime_context_not_road_level",
]


print("\n" + "-" * 80)
print("SCHEMA VALIDATION")
print("-" * 80)

missing = [
    col
    for col in required
    if col not in df.columns
]

if missing:

    print("Missing columns:")

    for col in missing:
        print(f"  {col}")

    raise RuntimeError(
        "Required Phase B columns are missing."
    )

print(
    f"Required columns: "
    f"{len(required)} / {len(required)}"
)

print("PASS")


# ============================================================
# BASIC CLEANING
# ============================================================

print("\n" + "-" * 80)
print("PREPARING SOURCE FEATURES")
print("-" * 80)


# Ensure road ID is usable
df["road_id"] = df["road_id"].astype(str)


# Numeric conversion
df["distance_to_road_m"] = pd.to_numeric(
    df["distance_to_road_m"],
    errors="coerce"
)


df["road_accidents_2023"] = pd.to_numeric(
    df["road_accidents_2023"],
    errors="coerce"
)


df["total_traffic_accidents_2023"] = pd.to_numeric(
    df["total_traffic_accidents_2023"],
    errors="coerce"
)


df["city_accident_fatality_rate"] = pd.to_numeric(
    df["city_accident_fatality_rate"],
    errors="coerce"
)


df["total_crime_against_women"] = pd.to_numeric(
    df["total_crime_against_women"],
    errors="coerce"
)


df["total_crime_against_children"] = pd.to_numeric(
    df["total_crime_against_children"],
    errors="coerce"
)


# ============================================================
# REMOVE INVALID ROAD IDs
# ============================================================

invalid_road_ids = (
    df["road_id"].isna()
    |
    df["road_id"].isin(
        ["", "nan", "None"]
    )
).sum()


print(
    f"Invalid road IDs: {invalid_road_ids}"
)


if invalid_road_ids > 0:

    raise RuntimeError(
        "Invalid road IDs detected."
    )


print("PASS")


# ============================================================
# SOURCE ROAD OBSERVATION SUMMARY
# ============================================================

print("\n" + "-" * 80)
print("SOURCE ROAD OBSERVATION SUMMARY")
print("-" * 80)


unique_roads = (
    df[
        ["city", "road_id"]
    ]
    .drop_duplicates()
)


print(
    f"Unique city-road pairs: "
    f"{len(unique_roads):,}"
)


print(
    "\nRoads by city:"
)

print(
    unique_roads["city"]
    .value_counts()
    .to_string()
)


# ============================================================
# ROAD-LEVEL AGGREGATION
# ============================================================

print("\n" + "-" * 80)
print("AGGREGATING CCTV OBSERVATIONS TO ROADS")
print("-" * 80)


road_features = (
    df
    .groupby(
        ["city", "road_id"],
        as_index=False
    )
    .agg(

        # ----------------------------------------------------
        # ROAD IDENTITY
        # ----------------------------------------------------

        road_name=(
            "road_name",
            lambda x: (
                x.dropna()
                .astype(str)
                .replace(
                    {
                        "": np.nan,
                        "Unnamed road": np.nan,
                        "nan": np.nan
                    }
                )
                .dropna()
                .iloc[0]
                if len(
                    x.dropna()
                    .astype(str)
                    .replace(
                        {
                            "": np.nan,
                            "Unnamed road": np.nan,
                            "nan": np.nan
                        }
                    )
                    .dropna()
                ) > 0
                else "Unnamed road"
            )
        ),

        highway=(
            "highway",
            "first"
        ),

        # ----------------------------------------------------
        # CCTV FEATURES
        # ----------------------------------------------------

        cctv_count=(
            "road_id",
            "size"
        ),

        mean_camera_distance_m=(
            "distance_to_road_m",
            "mean"
        ),

        median_camera_distance_m=(
            "distance_to_road_m",
            "median"
        ),

        max_camera_distance_m=(
            "distance_to_road_m",
            "max"
        ),

        min_camera_distance_m=(
            "distance_to_road_m",
            "min"
        ),

        # ----------------------------------------------------
        # MATCH QUALITY
        # ----------------------------------------------------

        high_quality_matches=(
            "spatial_match_quality",
            lambda x: (
                x.astype(str)
                .eq("high")
                .sum()
            )
        ),

        good_quality_matches=(
            "spatial_match_quality",
            lambda x: (
                x.astype(str)
                .eq("good")
                .sum()
            )
        ),

        low_quality_matches=(
            "spatial_match_quality",
            lambda x: (
                x.astype(str)
                .eq("low")
                .sum()
            )
        ),

        review_matches=(
            "spatial_match_quality",
            lambda x: (
                x.astype(str)
                .eq("review")
                .sum()
            )
        ),

        # ----------------------------------------------------
        # CONTEXTUAL ACCIDENT FEATURES
        # ----------------------------------------------------

        road_accidents_2023=(
            "road_accidents_2023",
            "first"
        ),

        total_traffic_accidents_2023=(
            "total_traffic_accidents_2023",
            "first"
        ),

        city_accident_fatality_rate=(
            "city_accident_fatality_rate",
            "first"
        ),

        # ----------------------------------------------------
        # CONTEXTUAL CRIME FEATURES
        # ----------------------------------------------------

        crime_context_state=(
            "crime_context_state",
            "first"
        ),

        crime_context_year=(
            "crime_context_year",
            "first"
        ),

        crime_context_level=(
            "crime_context_level",
            "first"
        ),

        crime_data_provenance=(
            "crime_data_provenance",
            "first"
        ),

        total_crime_against_women=(
            "total_crime_against_women",
            "first"
        ),

        total_crime_against_children=(
            "total_crime_against_children",
            "first"
        ),

        crime_context_spatial_scope=(
            "crime_context_spatial_scope",
            "first"
        ),

        crime_context_not_road_level=(
            "crime_context_not_road_level",
            "first"
        ),
    )
)


print(
    f"Road-level records created: "
    f"{len(road_features):,}"
)


# ============================================================
# CCTV COVERAGE METRICS
# ============================================================

print("\n" + "-" * 80)
print("CALCULATING CCTV COVERAGE FEATURES")
print("-" * 80)


# Camera density category
road_features[
    "cctv_coverage_level"
] = pd.cut(
    road_features["cctv_count"],
    bins=[
        0,
        1,
        2,
        5,
        np.inf
    ],
    labels=[
        "single",
        "low",
        "moderate",
        "high"
    ],
    include_lowest=True
)


# Match quality ratio
road_features[
    "high_quality_match_ratio"
] = (
    road_features["high_quality_matches"]
    /
    road_features["cctv_count"]
)


road_features[
    "review_match_ratio"
] = (
    road_features["review_matches"]
    /
    road_features["cctv_count"]
)


# ============================================================
# SPATIAL CONFIDENCE SCORE
# ============================================================

print("\n" + "-" * 80)
print("CALCULATING SPATIAL CONFIDENCE")
print("-" * 80)


# Score based on observed CCTV-road matching quality.
#
# high   = 1.00
# good   = 0.75
# low    = 0.40
# review = 0.15

road_features[
    "spatial_confidence"
] = (

    (
        road_features[
            "high_quality_matches"
        ]
        * 1.00
    )

    +

    (
        road_features[
            "good_quality_matches"
        ]
        * 0.75
    )

    +

    (
        road_features[
            "low_quality_matches"
        ]
        * 0.40
    )

    +

    (
        road_features[
            "review_matches"
        ]
        * 0.15
    )

) / road_features["cctv_count"]


print(
    "Spatial confidence range:"
)

print(
    f"  Min: "
    f"{road_features['spatial_confidence'].min():.3f}"
)

print(
    f"  Mean: "
    f"{road_features['spatial_confidence'].mean():.3f}"
)

print(
    f"  Max: "
    f"{road_features['spatial_confidence'].max():.3f}"
)


# ============================================================
# ROAD-LEVEL FEATURE FLAGS
# ============================================================

road_features[
    "has_multiple_cctvs"
] = (
    road_features["cctv_count"] > 1
)


road_features[
    "has_high_quality_match"
] = (
    road_features["high_quality_matches"] > 0
)


road_features[
    "requires_spatial_review"
] = (
    road_features["review_matches"] > 0
)


# ============================================================
# DATA SEMANTICS
# ============================================================

road_features[
    "accident_data_spatial_scope"
] = (
    "city_state_context"
)


road_features[
    "crime_data_spatial_scope"
] = (
    "state_level_context"
)


road_features[
    "crime_not_road_level"
] = (
    True
)


# ============================================================
# FEATURE VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("ROAD-LEVEL FEATURE VALIDATION")
print("-" * 80)


# Numeric columns
numeric_columns = [
    "cctv_count",
    "mean_camera_distance_m",
    "median_camera_distance_m",
    "max_camera_distance_m",
    "min_camera_distance_m",
    "high_quality_matches",
    "good_quality_matches",
    "low_quality_matches",
    "review_matches",
    "high_quality_match_ratio",
    "review_match_ratio",
    "spatial_confidence",
]


for column in numeric_columns:

    values = pd.to_numeric(
        road_features[column],
        errors="coerce"
    )

    invalid = values.isna().sum()

    negative = (
        values < 0
    ).sum()

    if invalid > 0:

        raise RuntimeError(
            f"Invalid values in {column}: "
            f"{invalid}"
        )

    if negative > 0:

        raise RuntimeError(
            f"Negative values in {column}: "
            f"{negative}"
        )


print(
    "Numeric features: PASS"
)


# Confidence must be 0–1
confidence = road_features[
    "spatial_confidence"
]


if (
    (confidence < 0)
    |
    (confidence > 1)
).any():

    raise RuntimeError(
        "Spatial confidence outside [0,1]."
    )


print(
    "Spatial confidence range: PASS"
)


# CCTV count must be >= 1
if (
    road_features["cctv_count"] < 1
).any():

    raise RuntimeError(
        "Road with zero CCTV count detected."
    )


print(
    "CCTV coverage counts: PASS"
)


# ============================================================
# CITY SUMMARY
# ============================================================

print("\n" + "-" * 80)
print("ROAD-LEVEL CITY SUMMARY")
print("-" * 80)


summary = (
    road_features
    .groupby("city")
    .agg(

        unique_roads=(
            "road_id",
            "nunique"
        ),

        total_cctvs=(
            "cctv_count",
            "sum"
        ),

        mean_cctv_per_road=(
            "cctv_count",
            "mean"
        ),

        mean_spatial_confidence=(
            "spatial_confidence",
            "mean"
        ),

        roads_requiring_review=(
            "requires_spatial_review",
            "sum"
        ),
    )
    .reset_index()
)


print(
    summary.to_string(
        index=False
    )
)


# ============================================================
# HIGHWAY SUMMARY
# ============================================================

print("\n" + "-" * 80)
print("ROAD-LEVEL HIGHWAY DISTRIBUTION")
print("-" * 80)


highway_summary = (
    road_features[
        "highway"
    ]
    .value_counts()
)


print(
    highway_summary.to_string()
)


# ============================================================
# SORT
# ============================================================

road_features = road_features.sort_values(
    [
        "city",
        "road_id"
    ]
).reset_index(
    drop=True
)


# ============================================================
# SAVE
# ============================================================

print("\n" + "-" * 80)
print("SAVING ROAD-LEVEL FEATURES")
print("-" * 80)


road_features.to_parquet(
    OUTPUT,
    index=False
)


print(
    f"Output size: "
    f"{OUTPUT.stat().st_size / 1024:.2f} KB"
)


# ============================================================
# FINAL INFORMATION
# ============================================================

print("\n" + "-" * 80)
print("FINAL DATASET")
print("-" * 80)


print(
    f"Road-level records: "
    f"{len(road_features):,}"
)


print(
    f"Columns: "
    f"{len(road_features.columns)}"
)


print(
    "\nColumns:"
)

for column in road_features.columns:

    print(
        f"  {column}"
    )


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 80)
print("C1 COMPLETE")
print("=" * 80)


print(
    "\nPHASE C1 — ROAD-LEVEL FEATURES: PASSED"
)


print(
    "\nInput CCTV records:"
)

print(
    f"  {len(df):,}"
)


print(
    "\nOutput road records:"
)

print(
    f"  {len(road_features):,}"
)


print(
    "\nOutput:"
)

print(
    OUTPUT
)


print(
    "\nNEXT → C2 BASELINE RISK SCORE"
)