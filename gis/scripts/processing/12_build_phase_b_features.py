from pathlib import Path
import pandas as pd


# ============================================================
# VIGRAH — B5 FINAL HISTORICAL INTELLIGENCE DATASET
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
    / "historical_cctv_crime_features.parquet"
)

OUTPUT = (
    FEATURE_DIR
    / "phase_b_historical_features.parquet"
)


print("=" * 80)
print("VIGRAH — B5 FINAL HISTORICAL INTELLIGENCE DATASET")
print("=" * 80)


# ============================================================
# INPUT CHECK
# ============================================================

print("\nInput:")
print(INPUT)


if not INPUT.exists():

    raise FileNotFoundError(
        f"Input dataset not found:\n{INPUT}"
    )


# ============================================================
# LOAD
# ============================================================

print("\n" + "-" * 80)
print("LOADING HISTORICAL FEATURE TABLE")
print("-" * 80)


df = pd.read_parquet(INPUT)


print(
    f"Records loaded: {len(df):,}"
)

print(
    f"Columns loaded: {len(df.columns)}"
)


# ============================================================
# REQUIRED BASE COLUMNS
# ============================================================

required_columns = [
    "city",
    "road_id",
    "road_name",
    "highway",
    "distance_to_road_m",

    # Accident context
    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "state_total_accident_cases_2023",
    "state_total_died_2023",
    "city_accident_fatality_rate",

    # Crime context
    "crime_context_state",
    "crime_context_year",
    "crime_context_level",
    "crime_data_provenance",
    "total_crime_against_women",
    "total_crime_against_children",

    # Spatial semantics
    "crime_context_spatial_scope",
    "crime_context_not_road_level",
]


print("\n" + "-" * 80)
print("SCHEMA VALIDATION")
print("-" * 80)


missing = [
    col
    for col in required_columns
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
    f"{len(required_columns)} / "
    f"{len(required_columns)}"
)

print("PASS")


# ============================================================
# RECORD COUNT
# ============================================================

print("\n" + "-" * 80)
print("1. RECORD COUNT")
print("-" * 80)


EXPECTED_RECORDS = 1551

print(
    f"Expected: {EXPECTED_RECORDS}"
)

print(
    f"Actual:   {len(df)}"
)


if len(df) != EXPECTED_RECORDS:

    raise RuntimeError(
        "Phase B record count mismatch."
    )


print("PASS")


# ============================================================
# CITY COVERAGE
# ============================================================

print("\n" + "-" * 80)
print("2. CITY COVERAGE")
print("-" * 80)


expected_city_counts = {
    "Mumbai": 10,
    "Bengaluru": 1541,
}


city_counts = (
    df["city"]
    .value_counts()
    .to_dict()
)


for city, expected in expected_city_counts.items():

    actual = city_counts.get(
        city,
        0
    )

    print(
        f"{city}: "
        f"{actual} / {expected}"
    )

    if actual != expected:

        raise RuntimeError(
            f"Incorrect count for {city}."
        )


print("PASS")


# ============================================================
# ACCIDENT CONTEXT VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("3. ACCIDENT CONTEXT")
print("-" * 80)


accident_columns = [
    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "state_total_accident_cases_2023",
    "state_total_died_2023",
    "city_accident_fatality_rate",
]


accident_missing = (
    df[
        accident_columns
    ]
    .isna()
    .sum()
)


print(
    accident_missing.to_string()
)


if accident_missing.sum() != 0:

    raise RuntimeError(
        "Missing accident context detected."
    )


print(
    "\nAccident context completeness: PASS"
)


# ============================================================
# CRIME CONTEXT VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("4. CRIME CONTEXT")
print("-" * 80)


crime_columns = [
    "crime_context_state",
    "crime_context_year",
    "crime_context_level",
    "crime_data_provenance",
    "total_crime_against_women",
    "total_crime_against_children",
]


crime_missing = (
    df[
        crime_columns
    ]
    .isna()
    .sum()
)


print(
    crime_missing.to_string()
)


if crime_missing.sum() != 0:

    raise RuntimeError(
        "Missing crime context detected."
    )


print(
    "\nCrime context completeness: PASS"
)


# ============================================================
# CITY → STATE VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("5. CITY → STATE NORMALIZATION")
print("-" * 80)


expected_states = {
    "Mumbai": "Maharashtra",
    "Bengaluru": "Karnataka",
}


for city, expected_state in expected_states.items():

    rows = df[
        df["city"] == city
    ]

    states = (
        rows[
            "crime_context_state"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    print(
        f"{city}: {states}"
    )

    if states != [expected_state]:

        raise RuntimeError(
            f"State normalization failed "
            f"for {city}."
        )


print("PASS")


# ============================================================
# CRIME SEMANTIC VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("6. CRIME SPATIAL SEMANTICS")
print("-" * 80)


spatial_scope = (
    df[
        "crime_context_spatial_scope"
    ]
    .dropna()
    .unique()
    .tolist()
)


road_level_flags = (
    df[
        "crime_context_not_road_level"
    ]
    .dropna()
    .unique()
    .tolist()
)


print(
    f"Spatial scope: {spatial_scope}"
)

print(
    f"Not road level: {road_level_flags}"
)


if spatial_scope != [
    "state_level_context"
]:

    raise RuntimeError(
        "Crime spatial scope is incorrect."
    )


if road_level_flags != [True]:

    raise RuntimeError(
        "Crime road-level semantic flag "
        "is incorrect."
    )


print("PASS")


# ============================================================
# ROAD MATCH QUALITY
# ============================================================

print("\n" + "-" * 80)
print("7. ROAD MATCH QUALITY")
print("-" * 80)


if "spatial_match_quality" in df.columns:

    print(
        df[
            "spatial_match_quality"
        ]
        .value_counts()
        .to_string()
    )

else:

    print(
        "spatial_match_quality column "
        "not present."
    )


if "distance_to_road_m" in df.columns:

    distances = pd.to_numeric(
        df["distance_to_road_m"],
        errors="coerce"
    )

    print(
        f"\nMean distance: "
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

    if distances.isna().sum() != 0:

        raise RuntimeError(
            "Missing CCTV-road distances."
        )


print(
    "\nRoad matching integrity: PASS"
)


# ============================================================
# NUMERIC FEATURE VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("8. NUMERIC FEATURE VALIDATION")
print("-" * 80)


numeric_columns = [
    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "state_total_accident_cases_2023",
    "state_total_died_2023",
    "city_accident_fatality_rate",
    "total_crime_against_women",
    "total_crime_against_children",
]


for column in numeric_columns:

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    invalid = values.isna().sum()

    negative = (
        values < 0
    ).sum()

    print(
        f"\n{column}"
    )

    print(
        f"  Invalid:  {invalid}"
    )

    print(
        f"  Negative: {negative}"
    )

    if invalid != 0:

        raise RuntimeError(
            f"Invalid values in {column}."
        )

    if negative != 0:

        raise RuntimeError(
            f"Negative values in {column}."
        )


print(
    "\nNumeric validation: PASS"
)


# ============================================================
# CITY-LEVEL HISTORICAL SUMMARY
# ============================================================

print("\n" + "-" * 80)
print("9. HISTORICAL CONTEXT SUMMARY")
print("-" * 80)


summary = (
    df
    .groupby("city")
    .agg(
        records=(
            "city",
            "size"
        ),

        road_accidents=(
            "road_accidents_2023",
            "first"
        ),

        traffic_accidents=(
            "total_traffic_accidents_2023",
            "first"
        ),

        accident_fatality_rate=(
            "city_accident_fatality_rate",
            "first"
        ),

        women_crime=(
            "total_crime_against_women",
            "first"
        ),

        children_crime=(
            "total_crime_against_children",
            "first"
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
# ADD PHASE B METADATA
# ============================================================

df[
    "phase_b_status"
] = "validated"

df[
    "phase_b_accident_data_scope"
] = "city_state_context"

df[
    "phase_b_crime_data_scope"
] = "state_context"


# ============================================================
# SAVE
# ============================================================

print("\n" + "-" * 80)
print("SAVING FINAL PHASE B DATASET")
print("-" * 80)


print(
    OUTPUT
)


df.to_parquet(
    OUTPUT,
    index=False
)


print(
    f"\nOutput size: "
    f"{OUTPUT.stat().st_size / 1024:.2f} KB"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 80)
print("B5 COMPLETE")
print("=" * 80)


print(
    "\nPHASE B — HISTORICAL INTELLIGENCE: PASSED"
)


print(
    "\nFinal records:"
)

print(
    f"  {len(df):,}"
)


print(
    "\nFinal columns:"
)

print(
    f"  {len(df.columns)}"
)


print(
    "\nOutput:"
)

print(
    OUTPUT
)


print(
    "\nNEXT → PHASE C — RISK ENGINE"
)