from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# VIGRAH — PHASE B / B3
# Build CCTV + OSM + Accident Context Feature Table
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

CCTV_ROAD_FILE = (
    ROOT
    / "data"
    / "processed"
    / "features"
    / "cctv_road_mapping.parquet"
)

ACCIDENT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "features"
    / "accident_city_features.parquet"
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
    / "historical_cctv_features.parquet"
)


print("=" * 80)
print("VIGRAH — B3 HISTORICAL FEATURE TABLE")
print("=" * 80)


# ------------------------------------------------------------
# Load CCTV → road mapping
# ------------------------------------------------------------

print("\nLoading CCTV-road mapping...")

cctv = gpd.read_parquet(
    CCTV_ROAD_FILE
)

print(
    f"CCTV-road records: {len(cctv):,}"
)


if len(cctv) != 1551:
    raise ValueError(
        f"Expected 1551 CCTV records, "
        f"found {len(cctv)}."
    )


# ------------------------------------------------------------
# Load accident context
# ------------------------------------------------------------

print("\nLoading accident context...")

accidents = pd.read_parquet(
    ACCIDENT_FILE
)

print(
    f"Accident context records: "
    f"{len(accidents):,}"
)


if set(accidents["city"]) != {
    "Mumbai",
    "Bengaluru",
}:
    raise ValueError(
        "Unexpected city values in accident context."
    )


# ------------------------------------------------------------
# Select relevant accident fields
# ------------------------------------------------------------

accident_columns = [
    "city",

    # City-level
    "road_accidents_2023",
    "railway_crossing_accidents_2023",
    "railway_accidents_2023",
    "total_traffic_accidents_2023",

    # State-level
    "nh_accident_cases_2023",
    "nh_injured_2023",
    "nh_died_2023",

    "sh_accident_cases_2023",
    "sh_injured_2023",
    "sh_died_2023",

    "expressway_accident_cases_2023",
    "expressway_injured_2023",
    "expressway_died_2023",

    "other_road_accident_cases_2023",
    "other_road_injured_2023",
    "other_road_died_2023",

    "state_total_accident_cases_2023",
    "state_total_injured_2023",
    "state_total_died_2023",

    # Derived
    "city_accident_fatality_rate",
    "city_accident_injury_rate",

    # Provenance
    "monthly_source_level",
    "monthly_source_year",
    "road_class_source_level",
    "road_class_source_year",
    "road_class_source_state",
]


accident_context = accidents[
    accident_columns
].copy()


# ------------------------------------------------------------
# Merge by city
# ------------------------------------------------------------

print("\nAttaching accident context by city...")

result = cctv.merge(
    accident_context,
    on="city",
    how="left",
    validate="many_to_one",
)


# ------------------------------------------------------------
# Validate merge
# ------------------------------------------------------------

print(
    f"Records after merge: "
    f"{len(result):,}"
)

if len(result) != len(cctv):
    raise ValueError(
        "Record count changed during merge."
    )


missing_context = (
    result[
        "road_accidents_2023"
    ]
    .isna()
    .sum()
)

print(
    f"Records missing accident context: "
    f"{missing_context:,}"
)

if missing_context != 0:
    raise ValueError(
        "Some CCTV records have no accident context."
    )


# ------------------------------------------------------------
# Map OSM highway → NCRB road-class context
# ------------------------------------------------------------

print("\nCreating road-class context mapping...")


def classify_road_class(highway):

    if pd.isna(highway):
        return "unknown"

    highway = str(highway).lower().strip()

    if highway in {
        "motorway",
        "motorway_link",
    }:
        return "expressway"

    if highway in {
        "trunk",
        "trunk_link",
    }:
        return "national_highway"

    if highway in {
        "primary",
        "primary_link",
    }:
        return "state_highway"

    return "other_roads"


result[
    "ncrb_road_class_context"
] = (
    result["highway"]
    .apply(classify_road_class)
)


# ------------------------------------------------------------
# Attach corresponding state-level context
# ------------------------------------------------------------

def get_context_value(row, prefix, suffix):

    road_class = row[
        "ncrb_road_class_context"
    ]

    if road_class == "national_highway":

        return row[
            f"nh_{suffix}_2023"
        ]

    if road_class == "state_highway":

        return row[
            f"sh_{suffix}_2023"
        ]

    if road_class == "expressway":

        return row[
            f"expressway_{suffix}_2023"
        ]

    if road_class == "other_roads":

        return row[
            f"other_road_{suffix}_2023"
        ]

    return pd.NA


result[
    "road_class_accident_cases_context"
] = result.apply(
    lambda row:
        get_context_value(
            row,
            "",
            "accident_cases"
        ),
    axis=1
)

result[
    "road_class_injured_context"
] = result.apply(
    lambda row:
        get_context_value(
            row,
            "",
            "injured"
        ),
    axis=1
)

result[
    "road_class_died_context"
] = result.apply(
    lambda row:
        get_context_value(
            row,
            "",
            "died"
        ),
    axis=1
)


# ------------------------------------------------------------
# Road-class context rates
# ------------------------------------------------------------

result[
    "road_class_fatality_context"
] = (
    result[
        "road_class_died_context"
    ]
    /
    result[
        "road_class_accident_cases_context"
    ]
).fillna(0)


result[
    "road_class_injury_context"
] = (
    result[
        "road_class_injured_context"
    ]
    /
    result[
        "road_class_accident_cases_context"
    ]
).fillna(0)


# ------------------------------------------------------------
# QA flag from Phase A
# ------------------------------------------------------------

result[
    "spatial_match_quality"
] = pd.cut(
    result["distance_to_road_m"],
    bins=[
        -float("inf"),
        10,
        25,
        50,
        float("inf"),
    ],
    labels=[
        "high",
        "good",
        "review",
        "low",
    ]
)


# ------------------------------------------------------------
# Historical feature provenance
# ------------------------------------------------------------

result[
    "accident_feature_year"
] = 2023

result[
    "accident_feature_type"
] = (
    "NCRB_city_and_state_context"
)


# ------------------------------------------------------------
# Print summary
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("HISTORICAL FEATURE SUMMARY")
print("-" * 80)


print("\nCity counts:")

print(
    result["city"]
    .value_counts()
    .to_string()
)


print("\nOSM highway classes:")

print(
    result["highway"]
    .value_counts()
    .to_string()
)


print("\nNCRB contextual road classes:")

print(
    result[
        "ncrb_road_class_context"
    ]
    .value_counts()
    .to_string()
)


print("\nSpatial match quality:")

print(
    result[
        "spatial_match_quality"
    ]
    .value_counts()
    .to_string()
)


# ------------------------------------------------------------
# Schema validation
# ------------------------------------------------------------

required = {
    "camera_id",
    "city",
    "road_id",
    "road_name",
    "highway",
    "distance_to_road_m",

    "road_accidents_2023",
    "total_traffic_accidents_2023",

    "state_total_accident_cases_2023",
    "state_total_died_2023",

    "ncrb_road_class_context",
    "road_class_accident_cases_context",

    "spatial_match_quality",
    "accident_feature_year",
}


missing = (
    required
    - set(result.columns)
)

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

print(
    "\nSchema validation: PASS"
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


print(
    f"\nOutput size: "
    f"{OUTPUT.stat().st_size / (1024 * 1024):.2f} MB"
)


print("\n" + "=" * 80)
print("B3 COMPLETE")
print("=" * 80)

print(
    "\nHistorical feature table created."
)

print(
    "NCRB values remain explicitly "
    "contextual rather than falsely "
    "being treated as geolocated accidents."
)