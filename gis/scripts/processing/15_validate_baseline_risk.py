from pathlib import Path
import pandas as pd


# ============================================================
# VIGRAH — C2.1 BASELINE RISK VALIDATION
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
    / "road_risk_baseline.parquet"
)

REPORT = (
    FEATURE_DIR
    / "c2_1_risk_validation_report.txt"
)


print("=" * 80)
print("VIGRAH — C2.1 BASELINE RISK VALIDATION")
print("=" * 80)


# ============================================================
# LOAD
# ============================================================

print("\nInput:")
print(INPUT)

if not INPUT.exists():
    raise FileNotFoundError(
        f"Baseline risk dataset not found:\n{INPUT}"
    )

df = pd.read_parquet(INPUT)

print(
    f"\nRoad records: {len(df):,}"
)

print(
    f"Columns: {len(df.columns)}"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required = [
    "city",
    "road_id",
    "road_name",
    "highway",
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "risk_level",
    "spatial_confidence",
    "road_accidents_2023",
    "city_accident_fatality_rate",
    "total_crime_against_women",
    "total_crime_against_children",
]

missing = [
    col for col in required
    if col not in df.columns
]

print("\n" + "-" * 80)
print("1. SCHEMA")
print("-" * 80)

if missing:
    print("Missing:")
    for col in missing:
        print(f"  {col}")

    raise RuntimeError(
        "Required risk columns missing."
    )

print("PASS")


# ============================================================
# RECORD COUNT
# ============================================================

print("\n" + "-" * 80)
print("2. RECORD COUNT")
print("-" * 80)

print(
    f"Expected: 844"
)

print(
    f"Actual:   {len(df)}"
)

if len(df) != 844:
    raise RuntimeError(
        "Unexpected road count."
    )

print("PASS")


# ============================================================
# SCORE STATISTICS
# ============================================================

print("\n" + "-" * 80)
print("3. OVERALL SCORE DISTRIBUTION")
print("-" * 80)

score = df[
    "confidence_adjusted_risk_score"
]

print(
    score.describe().to_string()
)

print(
    f"\nUnique risk scores: "
    f"{score.nunique()}"
)

print(
    f"Unique risk levels: "
    f"{df['risk_level'].nunique()}"
)


# ============================================================
# CITY-WISE SCORE VARIANCE
# ============================================================

print("\n" + "-" * 80)
print("4. CITY-WISE SCORE DISCRIMINATION")
print("-" * 80)


city_stats = (
    df
    .groupby("city")
    .agg(
        roads=(
            "road_id",
            "nunique"
        ),

        unique_scores=(
            "confidence_adjusted_risk_score",
            "nunique"
        ),

        minimum_score=(
            "confidence_adjusted_risk_score",
            "min"
        ),

        maximum_score=(
            "confidence_adjusted_risk_score",
            "max"
        ),

        mean_score=(
            "confidence_adjusted_risk_score",
            "mean"
        ),

        standard_deviation=(
            "confidence_adjusted_risk_score",
            "std"
        ),
    )
    .reset_index()
)


print(
    city_stats.to_string(
        index=False
    )
)


# ============================================================
# HIGHWAY-WISE SCORE VARIATION
# ============================================================

print("\n" + "-" * 80)
print("5. HIGHWAY CLASS SCORE VARIATION")
print("-" * 80)


highway_stats = (
    df
    .groupby("highway")
    .agg(
        roads=(
            "road_id",
            "nunique"
        ),

        unique_scores=(
            "confidence_adjusted_risk_score",
            "nunique"
        ),

        mean_score=(
            "confidence_adjusted_risk_score",
            "mean"
        ),

        minimum_score=(
            "confidence_adjusted_risk_score",
            "min"
        ),

        maximum_score=(
            "confidence_adjusted_risk_score",
            "max"
        ),
    )
    .sort_values(
        "mean_score",
        ascending=False
    )
)


print(
    highway_stats.to_string()
)


# ============================================================
# INPUT FEATURE VARIATION
# ============================================================

print("\n" + "-" * 80)
print("6. INPUT FEATURE VARIATION")
print("-" * 80)


features = [
    "road_accidents_2023",
    "city_accident_fatality_rate",
    "total_crime_against_women",
    "total_crime_against_children",
    "spatial_confidence",
]


for column in features:

    print(
        f"\n{column}"
    )

    print(
        f"  Unique values: "
        f"{df[column].nunique()}"
    )

    print(
        f"  Min: "
        f"{df[column].min()}"
    )

    print(
        f"  Max: "
        f"{df[column].max()}"
    )


# ============================================================
# CITY-LEVEL CONTEXT WARNING
# ============================================================

print("\n" + "-" * 80)
print("7. CONTEXTUAL FEATURE DIAGNOSTIC")
print("-" * 80)


context_features = [
    "road_accidents_2023",
    "city_accident_fatality_rate",
    "total_crime_against_women",
    "total_crime_against_children",
]


for city in sorted(
    df["city"].unique()
):

    city_df = df[
        df["city"] == city
    ]

    print(
        f"\n{city}"
    )

    for column in context_features:

        unique = (
            city_df[column]
            .nunique()
        )

        print(
            f"  {column}: "
            f"{unique} unique value(s)"
        )


# ============================================================
# INTERPRETATION
# ============================================================

print("\n" + "-" * 80)
print("8. METHODOLOGICAL INTERPRETATION")
print("-" * 80)


bengaluru = df[
    df["city"] == "Bengaluru"
]

mumbai = df[
    df["city"] == "Mumbai"
]


bengaluru_unique = (
    bengaluru[
        "confidence_adjusted_risk_score"
    ]
    .nunique()
)

mumbai_unique = (
    mumbai[
        "confidence_adjusted_risk_score"
    ]
    .nunique()
)


if bengaluru_unique <= 2:

    print(
        "WARNING:"
    )

    print(
        "Bengaluru road-level risk "
        "discrimination is currently weak."
    )

    print(
        "Most contextual historical "
        "features are constant within "
        "the city."
    )

else:

    print(
        "Bengaluru shows meaningful "
        "score variation."
    )


if mumbai_unique <= 2:

    print(
        "\nWARNING:"
    )

    print(
        "Mumbai road-level variation "
        "is primarily driven by "
        "spatial confidence."
    )


print(
    "\nIMPORTANT:"
)

print(
    "Current accident/crime values "
    "must remain labelled as contextual."
)

print(
    "They must NOT be interpreted as "
    "road-level historical accident/crime counts."
)


# ============================================================
# TOP ROADS
# ============================================================

print("\n" + "-" * 80)
print("9. TOP RISK ROADS")
print("-" * 80)


top = (
    df
    .sort_values(
        "confidence_adjusted_risk_score",
        ascending=False
    )
    .head(10)
)


print(
    top[
        [
            "city",
            "road_id",
            "road_name",
            "highway",
            "baseline_risk_score",
            "confidence_adjusted_risk_score",
            "spatial_confidence",
            "risk_level",
        ]
    ]
    .to_string(
        index=False
    )
)


# ============================================================
# REPORT
# ============================================================

report = []

report.append(
    "VIGRAH — C2.1 BASELINE RISK VALIDATION"
)

report.append(
    "=" * 60
)

report.append(
    f"Road records: {len(df):,}"
)

report.append(
    f"Unique risk scores: {score.nunique()}"
)

report.append("")

report.append(
    city_stats.to_string(
        index=False
    )
)

report.append("")

report.append(
    "Methodological note:"
)

report.append(
    "Accident and NCRB crime values are "
    "contextual city/state indicators."
)

report.append(
    "They are not road-level historical "
    "incident counts."
)

report.append("")

if bengaluru_unique <= 2:

    report.append(
        "WARNING: Bengaluru risk "
        "discrimination is weak."
    )

else:

    report.append(
        "Bengaluru risk discrimination "
        "shows variation."
    )


REPORT.write_text(
    "\n".join(report),
    encoding="utf-8"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 80)
print("C2.1 VALIDATION COMPLETE")
print("=" * 80)

print(
    "\nReport:"
)

print(
    REPORT
)