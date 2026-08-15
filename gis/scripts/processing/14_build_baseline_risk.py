from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# VIGRAH — C2 BASELINE RISK ENGINE
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
    / "road_level_features.parquet"
)

OUTPUT = (
    FEATURE_DIR
    / "road_risk_baseline.parquet"
)


print("=" * 80)
print("VIGRAH — C2 BASELINE RISK ENGINE")
print("=" * 80)


# ============================================================
# INPUT
# ============================================================

print("\nInput:")
print(INPUT)

if not INPUT.exists():
    raise FileNotFoundError(
        f"Road-level feature dataset not found:\n{INPUT}"
    )


# ============================================================
# LOAD
# ============================================================

print("\n" + "-" * 80)
print("LOADING ROAD-LEVEL FEATURES")
print("-" * 80)

df = pd.read_parquet(INPUT)

print(
    f"Road records: {len(df):,}"
)

print(
    f"Columns: {len(df.columns)}"
)


# ============================================================
# REQUIRED FEATURES
# ============================================================

required = [
    "city",
    "road_id",
    "road_name",
    "highway",

    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "city_accident_fatality_rate",

    "total_crime_against_women",
    "total_crime_against_children",

    "spatial_confidence",
    "crime_not_road_level",
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
        "Required C2 columns are missing."
    )

print("PASS")


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [
    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "city_accident_fatality_rate",
    "total_crime_against_women",
    "total_crime_against_children",
    "spatial_confidence",
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# CHECK MISSING VALUES
# ============================================================

print("\n" + "-" * 80)
print("INPUT FEATURE COMPLETENESS")
print("-" * 80)

missing_counts = (
    df[numeric_columns]
    .isna()
    .sum()
)

print(
    missing_counts.to_string()
)

if missing_counts.sum() != 0:

    raise RuntimeError(
        "Missing values found in risk features."
    )

print("\nPASS")


# ============================================================
# CONTEXT SEMANTICS
# ============================================================

print("\n" + "-" * 80)
print("CONTEXT SEMANTICS")
print("-" * 80)


crime_flags = (
    df["crime_not_road_level"]
    .dropna()
    .unique()
    .tolist()
)

print(
    f"Crime explicitly non-road-level: "
    f"{crime_flags}"
)

if crime_flags != [True]:

    raise RuntimeError(
        "Crime semantic safeguard failed."
    )

print("PASS")


# ============================================================
# MIN-MAX NORMALIZATION
# ============================================================

def minmax(series):
    """
    Normalize a numeric series to [0, 1].

    If every value is identical, return 0.5
    because the feature has no discriminatory
    power across roads.
    """

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            0.5,
            index=series.index
        )

    return (
        (series - minimum)
        /
        (maximum - minimum)
    )


# ============================================================
# NORMALIZED FEATURES
# ============================================================

print("\n" + "-" * 80)
print("NORMALIZING RISK INDICATORS")
print("-" * 80)


# ------------------------------------------------------------
# Accident context
# ------------------------------------------------------------

df[
    "accident_context_norm"
] = minmax(
    df["road_accidents_2023"]
)


# ------------------------------------------------------------
# Fatality severity
# ------------------------------------------------------------

df[
    "fatality_context_norm"
] = minmax(
    df["city_accident_fatality_rate"]
)


# ------------------------------------------------------------
# Women crime context
# ------------------------------------------------------------

df[
    "women_crime_context_norm"
] = minmax(
    df["total_crime_against_women"]
)


# ------------------------------------------------------------
# Children crime context
# ------------------------------------------------------------

df[
    "children_crime_context_norm"
] = minmax(
    df["total_crime_against_children"]
)


print(
    "Normalized features created:"
)

for column in [
    "accident_context_norm",
    "fatality_context_norm",
    "women_crime_context_norm",
    "children_crime_context_norm",
]:

    print(
        f"  {column}"
    )


# ============================================================
# BASELINE WEIGHTS
# ============================================================

print("\n" + "-" * 80)
print("BASELINE RISK WEIGHTS")
print("-" * 80)


WEIGHTS = {
    "accident_context_norm": 0.35,
    "fatality_context_norm": 0.25,
    "women_crime_context_norm": 0.25,
    "children_crime_context_norm": 0.15,
}


for feature, weight in WEIGHTS.items():

    print(
        f"{feature:<35} "
        f"{weight:.2f}"
    )


weight_sum = sum(
    WEIGHTS.values()
)

if abs(weight_sum - 1.0) > 1e-9:

    raise RuntimeError(
        "Risk weights do not sum to 1."
    )

print(
    f"\nWeight sum: {weight_sum:.2f}"
)

print("PASS")


# ============================================================
# RAW BASELINE RISK
# ============================================================

print("\n" + "-" * 80)
print("CALCULATING BASELINE RISK")
print("-" * 80)


df[
    "baseline_risk_raw"
] = (

    df[
        "accident_context_norm"
    ]
    * WEIGHTS[
        "accident_context_norm"
    ]

    +

    df[
        "fatality_context_norm"
    ]
    * WEIGHTS[
        "fatality_context_norm"
    ]

    +

    df[
        "women_crime_context_norm"
    ]
    * WEIGHTS[
        "women_crime_context_norm"
    ]

    +

    df[
        "children_crime_context_norm"
    ]
    * WEIGHTS[
        "children_crime_context_norm"
    ]
)


# Convert to 0–100
df[
    "baseline_risk_score"
] = (
    df["baseline_risk_raw"]
    * 100
)


# ============================================================
# CONFIDENCE-AWARE SCORE
# ============================================================

print("\n" + "-" * 80)
print("APPLYING SPATIAL CONFIDENCE")
print("-" * 80)


df[
    "confidence_adjusted_risk_score"
] = (

    df["baseline_risk_score"]
    *
    df["spatial_confidence"]
)


print(
    "Confidence-adjusted score created."
)


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def classify_risk(score):

    if score < 25:
        return "LOW"

    elif score < 50:
        return "MODERATE"

    elif score < 75:
        return "HIGH"

    else:
        return "CRITICAL"


df[
    "risk_level"
] = (
    df[
        "confidence_adjusted_risk_score"
    ]
    .apply(classify_risk)
)


# ============================================================
# RISK RANK
# ============================================================

df[
    "risk_rank"
] = (
    df[
        "confidence_adjusted_risk_score"
    ]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("RISK SCORE VALIDATION")
print("-" * 80)


score_columns = [
    "accident_context_norm",
    "fatality_context_norm",
    "women_crime_context_norm",
    "children_crime_context_norm",
    "baseline_risk_raw",
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
]


for column in score_columns:

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    invalid = values.isna().sum()

    if invalid > 0:

        raise RuntimeError(
            f"Invalid values in {column}."
        )


# Normalized indicators
for column in [
    "accident_context_norm",
    "fatality_context_norm",
    "women_crime_context_norm",
    "children_crime_context_norm",
]:

    values = df[column]

    if (
        (values < 0)
        |
        (values > 1)
    ).any():

        raise RuntimeError(
            f"{column} outside [0,1]."
        )


# Raw score
if (
    (df["baseline_risk_raw"] < 0)
    |
    (df["baseline_risk_raw"] > 1)
).any():

    raise RuntimeError(
        "Baseline raw score outside [0,1]."
    )


# 0–100 score
if (
    (df["baseline_risk_score"] < 0)
    |
    (df["baseline_risk_score"] > 100)
).any():

    raise RuntimeError(
        "Baseline risk score outside [0,100]."
    )


# Confidence-adjusted score
if (
    (df["confidence_adjusted_risk_score"] < 0)
    |
    (df["confidence_adjusted_risk_score"] > 100)
).any():

    raise RuntimeError(
        "Confidence-adjusted risk score outside [0,100]."
    )


print(
    "All risk score ranges: PASS"
)


# ============================================================
# RISK DISTRIBUTION
# ============================================================

print("\n" + "-" * 80)
print("RISK LEVEL DISTRIBUTION")
print("-" * 80)


risk_distribution = (
    df[
        "risk_level"
    ]
    .value_counts()
)


print(
    risk_distribution.to_string()
)


# ============================================================
# CITY DISTRIBUTION
# ============================================================

print("\n" + "-" * 80)
print("CITY-WISE RISK SUMMARY")
print("-" * 80)


city_summary = (
    df
    .groupby("city")
    .agg(

        roads=(
            "road_id",
            "nunique"
        ),

        mean_score=(
            "confidence_adjusted_risk_score",
            "mean"
        ),

        median_score=(
            "confidence_adjusted_risk_score",
            "median"
        ),

        maximum_score=(
            "confidence_adjusted_risk_score",
            "max"
        ),

        high_risk_roads=(
            "risk_level",
            lambda x: (
                x.isin(
                    [
                        "HIGH",
                        "CRITICAL"
                    ]
                ).sum()
            )
        ),

        critical_roads=(
            "risk_level",
            lambda x: (
                (x == "CRITICAL")
                .sum()
            )
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
# TOP RISK ROADS
# ============================================================

print("\n" + "-" * 80)
print("TOP 20 RISK ROADS")
print("-" * 80)


top_risk = (
    df
    .sort_values(
        "confidence_adjusted_risk_score",
        ascending=False
    )
    .head(20)
)


display_columns = [
    "city",
    "road_id",
    "road_name",
    "highway",
    "cctv_count",
    "spatial_confidence",
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "risk_level",
    "risk_rank",
]


print(
    top_risk[
        display_columns
    ].to_string(
        index=False
    )
)


# ============================================================
# FEATURE CONTRIBUTIONS
# ============================================================

print("\n" + "-" * 80)
print("FEATURE CONTRIBUTION SUMMARY")
print("-" * 80)


df[
    "accident_risk_contribution"
] = (
    df["accident_context_norm"]
    * 35
)


df[
    "fatality_risk_contribution"
] = (
    df["fatality_context_norm"]
    * 25
)


df[
    "women_crime_risk_contribution"
] = (
    df["women_crime_context_norm"]
    * 25
)


df[
    "children_crime_risk_contribution"
] = (
    df["children_crime_context_norm"]
    * 15
)


print(
    "Contributions created:"
)

for column in [
    "accident_risk_contribution",
    "fatality_risk_contribution",
    "women_crime_risk_contribution",
    "children_crime_risk_contribution",
]:

    print(
        f"  {column}"
    )


# ============================================================
# METADATA
# ============================================================

df[
    "risk_engine_version"
] = "C2_baseline_v1"

df[
    "risk_method"
] = (
    "weighted_contextual_baseline"
)

df[
    "risk_score_range"
] = "0-100"

df[
    "risk_score_not_ml"
] = True

df[
    "historical_context_not_road_level"
] = True


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    [
        "confidence_adjusted_risk_score",
        "city",
        "road_id",
    ],
    ascending=[
        False,
        True,
        True,
    ],
).reset_index(
    drop=True
)


# ============================================================
# SAVE
# ============================================================

print("\n" + "-" * 80)
print("SAVING BASELINE RISK DATASET")
print("-" * 80)


df.to_parquet(
    OUTPUT,
    index=False
)


print(
    f"Output size: "
    f"{OUTPUT.stat().st_size / 1024:.2f} KB"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 80)
print("C2 COMPLETE")
print("=" * 80)


print(
    "\nPHASE C2 — BASELINE RISK ENGINE: PASSED"
)


print(
    f"\nRoads scored: {len(df):,}"
)


print(
    "\nRisk score:"
)

print(
    "  Range: 0–100"
)

print(
    "  Method: weighted contextual baseline"
)

print(
    "  ML: not used"
)


print(
    "\nOutput:"
)

print(
    OUTPUT
)


print(
    "\nNEXT → C2 VALIDATION / C3 ML EVALUATION"
)