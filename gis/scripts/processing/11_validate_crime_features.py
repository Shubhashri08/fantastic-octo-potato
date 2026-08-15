from pathlib import Path
import pandas as pd


# ============================================================
# VIGRAH — B4.4 CRIME FEATURE VALIDATION
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

REPORT = (
    FEATURE_DIR
    / "b4_4_crime_validation_report.txt"
)


print("=" * 80)
print("VIGRAH — B4.4 CRIME FEATURE VALIDATION")
print("=" * 80)


# ============================================================
# INPUT CHECK
# ============================================================

print("\nInput:")
print(INPUT)


if not INPUT.exists():
    raise FileNotFoundError(
        f"Crime-enriched feature table not found:\n{INPUT}"
    )


# ============================================================
# LOAD
# ============================================================

print("\n" + "-" * 80)
print("LOADING DATASET")
print("-" * 80)


df = pd.read_parquet(INPUT)

print(
    f"Records loaded: {len(df):,}"
)

print(
    f"Columns: {len(df.columns)}"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "city",
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
print("1. REQUIRED COLUMN VALIDATION")
print("-" * 80)


missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]


if missing_columns:
    print("Missing columns:")
    for col in missing_columns:
        print(f"  {col}")

    raise RuntimeError(
        "Required crime columns are missing."
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
print("2. RECORD COUNT")
print("-" * 80)


EXPECTED_RECORDS = 1551

actual_records = len(df)

print(
    f"Expected: {EXPECTED_RECORDS}"
)

print(
    f"Actual:   {actual_records}"
)


if actual_records != EXPECTED_RECORDS:
    raise RuntimeError(
        "Record count changed."
    )


print("PASS")


# ============================================================
# CITY COUNTS
# ============================================================

print("\n" + "-" * 80)
print("3. CITY COUNTS")
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
            f"City count mismatch for {city}."
        )


print("PASS")


# ============================================================
# CRIME CONTEXT COMPLETENESS
# ============================================================

print("\n" + "-" * 80)
print("4. CRIME CONTEXT COMPLETENESS")
print("-" * 80)


crime_columns = [
    "crime_context_state",
    "crime_context_year",
    "crime_context_level",
    "crime_data_provenance",
    "total_crime_against_women",
    "total_crime_against_children",
]


missing_counts = (
    df[crime_columns]
    .isna()
    .sum()
)


print(
    missing_counts.to_string()
)


total_missing = (
    missing_counts.sum()
)


if total_missing != 0:
    raise RuntimeError(
        "Missing crime context values detected."
    )


print(
    "\nMissing crime values: 0"
)

print("PASS")


# ============================================================
# CITY → STATE MAPPING
# ============================================================

print("\n" + "-" * 80)
print("5. CITY → STATE CONTEXT VALIDATION")
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
            f"Incorrect state context for {city}."
        )


print("PASS")


# ============================================================
# YEAR VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("6. CRIME DATA YEAR")
print("-" * 80)


years = (
    df["crime_context_year"]
    .dropna()
    .unique()
    .tolist()
)


print(
    f"Years found: {years}"
)


if years != [2023]:

    raise RuntimeError(
        "Unexpected crime data year."
    )


print("PASS")


# ============================================================
# CONTEXT LEVEL VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("7. CRIME DATA LEVEL")
print("-" * 80)


levels = (
    df["crime_context_level"]
    .dropna()
    .unique()
    .tolist()
)


print(
    f"Levels found: {levels}"
)


if levels != ["state_context"]:

    raise RuntimeError(
        "Crime data level is not "
        "'state_context'."
    )


print("PASS")


# ============================================================
# PROVENANCE VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("8. DATA PROVENANCE")
print("-" * 80)


provenance = (
    df["crime_data_provenance"]
    .dropna()
    .unique()
    .tolist()
)


print(
    f"Provenance: {provenance}"
)


if provenance != ["NCRB"]:

    raise RuntimeError(
        "Unexpected crime data provenance."
    )


print("PASS")


# ============================================================
# CRIME VALUE VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("9. CRIME VALUE VALIDATION")
print("-" * 80)


numeric_crime_columns = [
    "total_crime_against_women",
    "total_crime_against_children",
]


for column in numeric_crime_columns:

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
        f"  Invalid numeric: {invalid}"
    )

    print(
        f"  Negative:        {negative}"
    )

    print(
        f"  Min:             {values.min():,.0f}"
    )

    print(
        f"  Max:             {values.max():,.0f}"
    )

    if invalid != 0:
        raise RuntimeError(
            f"Invalid numeric values "
            f"in {column}."
        )

    if negative != 0:
        raise RuntimeError(
            f"Negative values "
            f"in {column}."
        )


print("\nPASS")


# ============================================================
# CITY-LEVEL CONSISTENCY
# ============================================================

print("\n" + "-" * 80)
print("10. CITY-LEVEL CONTEXT CONSISTENCY")
print("-" * 80)


for city in expected_city_counts:

    city_rows = df[
        df["city"] == city
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

    state_unique = (
        city_rows[
            "crime_context_state"
        ]
        .nunique()
    )

    print(
        f"\n{city}"
    )

    print(
        f"  Women crime values:    "
        f"{women_unique}"
    )

    print(
        f"  Children crime values: "
        f"{children_unique}"
    )

    print(
        f"  State values:          "
        f"{state_unique}"
    )

    if women_unique != 1:
        raise RuntimeError(
            f"Women crime context "
            f"varies within {city}."
        )

    if children_unique != 1:
        raise RuntimeError(
            f"Children crime context "
            f"varies within {city}."
        )

    if state_unique != 1:
        raise RuntimeError(
            f"State context varies "
            f"within {city}."
        )


print(
    "\nPASS"
)


# ============================================================
# SPATIAL SEMANTICS VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("11. SPATIAL SEMANTICS")
print("-" * 80)


spatial_scope = (
    df[
        "crime_context_spatial_scope"
    ]
    .dropna()
    .unique()
    .tolist()
)


not_road_level = (
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
    f"Not road-level: {not_road_level}"
)


if spatial_scope != [
    "state_level_context"
]:

    raise RuntimeError(
        "Crime spatial scope is incorrect."
    )


if not_road_level != [True]:

    raise RuntimeError(
        "Crime data is not explicitly "
        "marked as non-road-level."
    )


print("PASS")


# ============================================================
# CITY SUMMARY
# ============================================================

print("\n" + "-" * 80)
print("12. FINAL CITY SUMMARY")
print("-" * 80)


summary = (
    df
    .groupby("city")
    .agg(
        cctv_records=(
            "city",
            "size"
        ),

        state=(
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
    summary.to_string(
        index=False
    )
)


# ============================================================
# REPORT
# ============================================================

report_lines = []

report_lines.append(
    "VIGRAH — B4.4 CRIME FEATURE VALIDATION"
)

report_lines.append(
    "=" * 60
)

report_lines.append(
    f"Input records: {len(df):,}"
)

report_lines.append(
    f"Expected records: {EXPECTED_RECORDS:,}"
)

report_lines.append(
    "Record count: PASS"
)

report_lines.append(
    "Crime context completeness: PASS"
)

report_lines.append(
    "City → State mapping: PASS"
)

report_lines.append(
    "Crime year: 2023"
)

report_lines.append(
    "Crime data level: state_context"
)

report_lines.append(
    "Provenance: NCRB"
)

report_lines.append(
    "Spatial scope: state_level_context"
)

report_lines.append(
    "Road-level attribution: FALSE"
)

report_lines.append(
    ""
)

report_lines.append(
    summary.to_string(
        index=False
    )
)

report_lines.append(
    ""
)

report_lines.append(
    "B4.4 VALIDATION: PASS"
)


REPORT.write_text(
    "\n".join(report_lines),
    encoding="utf-8"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 80)
print("B4.4 VALIDATION COMPLETE")
print("=" * 80)


print(
    "\nPHASE B4 — CRIME CONTEXT: PASSED"
)


print(
    "\nValidation report:"
)

print(
    REPORT
)