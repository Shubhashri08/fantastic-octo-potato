from pathlib import Path
import pandas as pd


# ============================================================
# VIGRAH — B4.3 CRIME CONTEXT ENRICHMENT
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

FEATURE_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

HISTORICAL_INPUT = (
    FEATURE_DIR
    / "historical_cctv_features.parquet"
)

CRIME_INPUT = (
    FEATURE_DIR
    / "crime_city_context.parquet"
)

OUTPUT = (
    FEATURE_DIR
    / "historical_cctv_crime_features.parquet"
)


print("=" * 80)
print("VIGRAH — B4.3 NCRB CRIME CONTEXT ENRICHMENT")
print("=" * 80)


# ============================================================
# CHECK INPUTS
# ============================================================

print("\nInput files:")

print(
    f"Historical features:\n"
    f"{HISTORICAL_INPUT}"
)

print(
    f"\nCrime context:\n"
    f"{CRIME_INPUT}"
)


if not HISTORICAL_INPUT.exists():

    raise FileNotFoundError(
        f"Historical feature table not found:\n"
        f"{HISTORICAL_INPUT}"
    )


if not CRIME_INPUT.exists():

    raise FileNotFoundError(
        f"Crime context table not found:\n"
        f"{CRIME_INPUT}"
    )


# ============================================================
# LOAD
# ============================================================

print("\n" + "-" * 80)
print("LOADING INPUT DATA")
print("-" * 80)


historical = pd.read_parquet(
    HISTORICAL_INPUT
)

crime = pd.read_parquet(
    CRIME_INPUT
)


print(
    f"\nHistorical CCTV records: "
    f"{len(historical):,}"
)

print(
    f"Crime context records: "
    f"{len(crime):,}"
)


# ============================================================
# REQUIRED COLUMN VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("SCHEMA VALIDATION")
print("-" * 80)


required_historical = [
    "city",
]

required_crime = [
    "city",
    "state",
    "crime_data_year",
    "crime_data_level",
    "data_provenance",
    "total_crime_against_women",
    "total_crime_against_children",
]


missing_historical = [
    col
    for col in required_historical
    if col not in historical.columns
]


missing_crime = [
    col
    for col in required_crime
    if col not in crime.columns
]


if missing_historical:

    raise RuntimeError(
        "Missing historical columns:\n"
        + "\n".join(
            missing_historical
        )
    )


if missing_crime:

    raise RuntimeError(
        "Missing crime columns:\n"
        + "\n".join(
            missing_crime
        )
    )


print(
    "Historical schema: PASS"
)

print(
    "Crime schema: PASS"
)


# ============================================================
# CITY VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("CITY VALIDATION")
print("-" * 80)


expected_cities = {
    "Mumbai",
    "Bengaluru",
}


historical_cities = set(
    historical["city"]
    .dropna()
    .unique()
)


crime_cities = set(
    crime["city"]
    .dropna()
    .unique()
)


print(
    f"Historical cities: "
    f"{sorted(historical_cities)}"
)

print(
    f"Crime cities: "
    f"{sorted(crime_cities)}"
)


if not expected_cities.issubset(
    historical_cities
):

    raise RuntimeError(
        "Historical dataset does not contain "
        "both required cities."
    )


if crime_cities != expected_cities:

    raise RuntimeError(
        "Crime context does not contain "
        "exactly Mumbai and Bengaluru."
    )


print(
    "City coverage: PASS"
)


# ============================================================
# CRIME CONTEXT UNIQUENESS
# ============================================================

print("\n" + "-" * 80)
print("CRIME CONTEXT UNIQUENESS")
print("-" * 80)


duplicate_crime_cities = (
    crime["city"]
    .duplicated()
    .sum()
)


print(
    f"Duplicate city records: "
    f"{duplicate_crime_cities}"
)


if duplicate_crime_cities != 0:

    raise RuntimeError(
        "Crime context contains duplicate "
        "city records."
    )


print(
    "Crime context uniqueness: PASS"
)


# ============================================================
# MERGE
# ============================================================

print("\n" + "-" * 80)
print("ATTACHING CRIME CONTEXT")
print("-" * 80)


crime_columns = [
    "city",
    "state",
    "crime_data_year",
    "crime_data_level",
    "data_provenance",
    "total_crime_against_women",
    "total_crime_against_children",
]


crime_context = crime[
    crime_columns
].copy()


# Rename metadata fields so they are clearly
# distinguishable from other datasets.

crime_context = crime_context.rename(
    columns={
        "state":
            "crime_context_state",

        "crime_data_year":
            "crime_context_year",

        "crime_data_level":
            "crime_context_level",

        "data_provenance":
            "crime_data_provenance",
    }
)


# Merge using city only.
#
# IMPORTANT:
# This is contextual enrichment.
# It does NOT mean crime occurred on the road.

enriched = historical.merge(
    crime_context,
    on="city",
    how="left",
    validate="many_to_one",
)


print(
    f"Records before merge: "
    f"{len(historical):,}"
)

print(
    f"Records after merge:  "
    f"{len(enriched):,}"
)


# ============================================================
# RECORD COUNT VALIDATION
# ============================================================

if len(enriched) != len(historical):

    raise RuntimeError(
        "Record count changed during crime merge."
    )


print(
    "Record count preservation: PASS"
)


# ============================================================
# MERGE COMPLETENESS
# ============================================================

print("\n" + "-" * 80)
print("MERGE COMPLETENESS")
print("-" * 80)


crime_feature_columns = [
    "crime_context_state",
    "crime_context_year",
    "crime_context_level",
    "crime_data_provenance",
    "total_crime_against_women",
    "total_crime_against_children",
]


missing_by_column = (
    enriched[
        crime_feature_columns
    ]
    .isna()
    .sum()
)


print(
    missing_by_column.to_string()
)


total_missing = (
    missing_by_column.sum()
)


if total_missing != 0:

    raise RuntimeError(
        "Some CCTV records failed to receive "
        "crime context."
    )


print(
    "\nCrime context attached to all records."
)

print(
    "Merge completeness: PASS"
)


# ============================================================
# CITY-WISE VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("CITY-WISE CRIME CONTEXT")
print("-" * 80)


city_summary = (
    enriched
    .groupby("city")
    .agg(
        cctv_records=("city", "size"),

        crime_context_state=(
            "crime_context_state",
            "first"
        ),

        crime_year=(
            "crime_context_year",
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
    city_summary.to_string(
        index=False
    )
)


# ============================================================
# CHECK VALUES ARE CONSTANT WITHIN CITY
# ============================================================

for city in expected_cities:

    city_rows = enriched[
        enriched["city"] == city
    ]

    women_unique = (
        city_rows[
            "total_crime_against_women"
        ]
        .nunique()
    )

    children_unique = (
        city_rows[
            "total_crime_against_children"
        ]
        .nunique()
    )

    if women_unique != 1:

        raise RuntimeError(
            f"Women crime context varies "
            f"within {city}."
        )

    if children_unique != 1:

        raise RuntimeError(
            f"Children crime context varies "
            f"within {city}."
        )


print(
    "\nCity-level context consistency: PASS"
)


# ============================================================
# SEMANTIC METADATA
# ============================================================

enriched[
    "crime_context_spatial_scope"
] = "state_level_context"

enriched[
    "crime_context_not_road_level"
] = True


# ============================================================
# FINAL SCHEMA CHECK
# ============================================================

print("\n" + "-" * 80)
print("FINAL SCHEMA")
print("-" * 80)


print(
    f"Total columns: "
    f"{len(enriched.columns)}"
)

print(
    f"Total records: "
    f"{len(enriched):,}"
)


print("\nCrime-related columns:")

for col in enriched.columns:

    if (
        "crime" in col.lower()
        or "women" in col.lower()
        or "children" in col.lower()
    ):

        print(
            f"  {col}"
        )


# ============================================================
# SAVE
# ============================================================

print("\n" + "-" * 80)
print("SAVING")
print("-" * 80)


print(
    OUTPUT
)


enriched.to_parquet(
    OUTPUT,
    index=False
)


print(
    f"\nOutput size: "
    f"{OUTPUT.stat().st_size / 1024:.2f} KB"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("B4.3 COMPLETE")
print("=" * 80)


print(
    "\nCrime context successfully attached "
    "to CCTV-road records."
)

print(
    "Crime remains explicitly "
    "state-level contextual information."
)

print(
    "No road-level crime attribution "
    "was performed."
)

print(
    "\nRecords:"
)

print(
    f"  {len(enriched):,}"
)

print(
    "\nOutput:"
)

print(
    OUTPUT
)

print(
    "\nNEXT → B4.4 VALIDATION"
)