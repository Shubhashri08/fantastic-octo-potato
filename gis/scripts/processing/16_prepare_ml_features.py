from pathlib import Path

import numpy as np
import pandas as pd


# =============================================================================
# VIGRAH — C3.1 ML FEATURE PREPARATION
# =============================================================================

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

OUTPUT = (
    FEATURE_DIR
    / "road_ml_features.parquet"
)

REPORT = (
    FEATURE_DIR
    / "c3_1_ml_feature_report.txt"
)


print("=" * 80)
print("VIGRAH — C3.1 ML FEATURE PREPARATION")
print("=" * 80)

print("\nInput:")
print(INPUT)


# =============================================================================
# LOAD
# =============================================================================

if not INPUT.exists():
    raise FileNotFoundError(
        f"Input dataset not found:\n{INPUT}"
    )

df = pd.read_parquet(INPUT)

print("\n" + "-" * 80)
print("LOADING DATASET")
print("-" * 80)

print(f"Records: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# =============================================================================
# REQUIRED COLUMNS
# =============================================================================

required = [
    "city",
    "road_id",
    "road_name",
    "highway",

    "cctv_count",

    "mean_camera_distance_m",
    "median_camera_distance_m",
    "max_camera_distance_m",
    "min_camera_distance_m",

    "high_quality_matches",
    "good_quality_matches",
    "low_quality_matches",
    "review_matches",

    "cctv_coverage_level",

    "high_quality_match_ratio",
    "review_match_ratio",

    "spatial_confidence",

    "has_multiple_cctvs",
    "has_high_quality_match",
    "requires_spatial_review",

    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "city_accident_fatality_rate",

    "total_crime_against_women",
    "total_crime_against_children",

    "crime_context_not_road_level",

    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "risk_level",
]


missing = [
    column
    for column in required
    if column not in df.columns
]

if missing:
    print("\nMissing required columns:")

    for column in missing:
        print(f"  {column}")

    raise RuntimeError(
        "Required C3 columns are missing."
    )

print("\nSchema validation: PASS")


# =============================================================================
# BASIC VALIDATION
# =============================================================================

print("\n" + "-" * 80)
print("BASIC VALIDATION")
print("-" * 80)

if df["road_id"].isna().any():
    raise RuntimeError(
        "Null road IDs found."
    )

if df["road_id"].duplicated().any():
    print(
        "WARNING: duplicate road IDs detected."
    )

print(
    f"Unique roads: "
    f"{df['road_id'].nunique():,}"
)


# =============================================================================
# DEFINE FEATURE GROUPS
# =============================================================================

road_level_numeric = [
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


road_level_binary = [
    "has_multiple_cctvs",
    "has_high_quality_match",
    "requires_spatial_review",
]


context_numeric = [
    "road_accidents_2023",
    "total_traffic_accidents_2023",
    "city_accident_fatality_rate",

    "total_crime_against_women",
    "total_crime_against_children",
]


categorical = [
    "highway",
    "city",
]


# =============================================================================
# NUMERIC CONVERSION
# =============================================================================

print("\n" + "-" * 80)
print("NUMERIC FEATURE VALIDATION")
print("-" * 80)

all_numeric = (
    road_level_numeric
    + road_level_binary
    + context_numeric
)

for column in all_numeric:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    invalid = df[column].isna().sum()

    if invalid:
        print(
            f"{column}: "
            f"{invalid} invalid/missing values"
        )

        # Safe imputation for numeric features.
        # This is only for ML preparation.
        median = df[column].median()

        if pd.isna(median):
            median = 0

        df[column] = df[column].fillna(
            median
        )

print("Numeric conversion: PASS")


# =============================================================================
# NORMALIZATION FUNCTION
# =============================================================================

def minmax(series):
    """
    Min-max normalize a series to [0, 1].

    Constant columns are assigned 0.0 rather
    than producing NaN.
    """

    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(
            0.0,
            index=series.index
        )

    if maximum == minimum:
        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    )


# =============================================================================
# CREATE NORMALIZED ROAD-LEVEL FEATURES
# =============================================================================

print("\n" + "-" * 80)
print("CREATING ROAD-LEVEL NORMALIZED FEATURES")
print("-" * 80)


for column in road_level_numeric:

    normalized_name = (
        f"{column}_norm"
    )

    df[normalized_name] = minmax(
        df[column]
    )


# =============================================================================
# CREATE NORMALIZED CONTEXT FEATURES
# =============================================================================

print("\n" + "-" * 80)
print("CREATING CONTEXTUAL NORMALIZED FEATURES")
print("-" * 80)


for column in context_numeric:

    normalized_name = (
        f"{column}_context_norm"
    )

    df[normalized_name] = minmax(
        df[column]
    )


# =============================================================================
# ONE-HOT ENCODE HIGHWAY CLASS
# =============================================================================

print("\n" + "-" * 80)
print("ENCODING CATEGORICAL FEATURES")
print("-" * 80)

highway_dummies = pd.get_dummies(
    df["highway"],
    prefix="highway",
    dtype=int
)

city_dummies = pd.get_dummies(
    df["city"],
    prefix="city",
    dtype=int
)

print(
    f"Highway categories: "
    f"{len(highway_dummies.columns)}"
)

print(
    f"City categories: "
    f"{len(city_dummies.columns)}"
)


# =============================================================================
# BUILD ML FEATURE MATRIX
# =============================================================================

normalized_road_features = [
    f"{column}_norm"
    for column in road_level_numeric
]

normalized_context_features = [
    f"{column}_context_norm"
    for column in context_numeric
]


ml_feature_columns = (
    normalized_road_features
    + road_level_binary
    + normalized_context_features
)


ml_features = df[
    [
        "city",
        "road_id",
        "road_name",
        "highway",
    ]
    + ml_feature_columns
].copy()


ml_features = pd.concat(
    [
        ml_features,
        highway_dummies,
        city_dummies,
    ],
    axis=1
)


# =============================================================================
# BASELINE SCORE AS BENCHMARK
# =============================================================================

print("\n" + "-" * 80)
print("ATTACHING BASELINE BENCHMARK")
print("-" * 80)


benchmark_columns = [
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "risk_level",
]


for column in benchmark_columns:

    ml_features[column] = df[column].values


print(
    "Baseline scores retained as "
    "benchmark/reference only."
)


# =============================================================================
# CONTEXT SEMANTICS
# =============================================================================

print("\n" + "-" * 80)
print("CONTEXT SEMANTICS")
print("-" * 80)


crime_flags = (
    df["crime_context_not_road_level"]
    .astype(bool)
)

print(
    "Crime data marked non-road-level: "
    f"{crime_flags.all()}"
)

if not crime_flags.all():

    raise RuntimeError(
        "Crime spatial semantics violated."
    )

print("PASS")


# =============================================================================
# CHECK FEATURE RANGES
# =============================================================================

print("\n" + "-" * 80)
print("FEATURE RANGE VALIDATION")
print("-" * 80)


normalized_columns = (
    normalized_road_features
    + normalized_context_features
)


range_errors = []

for column in normalized_columns:

    minimum = ml_features[column].min()
    maximum = ml_features[column].max()

    print(
        f"{column:45s} "
        f"{minimum:.3f} → {maximum:.3f}"
    )

    if minimum < 0 or maximum > 1:
        range_errors.append(column)


if range_errors:

    raise RuntimeError(
        "Normalized features outside [0,1]: "
        + ", ".join(range_errors)
    )

print("\nRange validation: PASS")


# =============================================================================
# CHECK FOR NaN / INF
# =============================================================================

print("\n" + "-" * 80)
print("MISSING / INFINITE VALUE VALIDATION")
print("-" * 80)


numeric_ml = ml_features.select_dtypes(
    include=[np.number]
)


nan_count = (
    numeric_ml
    .isna()
    .sum()
    .sum()
)

inf_count = (
    np.isinf(
        numeric_ml.to_numpy(
            dtype=float
        )
    )
    .sum()
)


print(
    f"NaN values: {nan_count}"
)

print(
    f"Infinite values: {inf_count}"
)


if nan_count != 0:
    raise RuntimeError(
        "NaN values remain."
    )

if inf_count != 0:
    raise RuntimeError(
        "Infinite values remain."
    )

print("PASS")


# =============================================================================
# FEATURE GROUP SUMMARY
# =============================================================================

print("\n" + "-" * 80)
print("FEATURE GROUP SUMMARY")
print("-" * 80)


print(
    f"Road-level numeric features: "
    f"{len(road_level_numeric)}"
)

print(
    f"Road-level binary features: "
    f"{len(road_level_binary)}"
)

print(
    f"Contextual numeric features: "
    f"{len(context_numeric)}"
)

print(
    f"Highway one-hot features: "
    f"{len(highway_dummies.columns)}"
)

print(
    f"City one-hot features: "
    f"{len(city_dummies.columns)}"
)

print(
    f"Total ML columns: "
    f"{len(ml_features.columns)}"
)


# =============================================================================
# ROAD-LEVEL VARIATION CHECK
# =============================================================================

print("\n" + "-" * 80)
print("ROAD-LEVEL VARIATION CHECK")
print("-" * 80)


for column in road_level_numeric:

    unique = df[column].nunique()

    print(
        f"{column:40s} "
        f"{unique} unique value(s)"
    )


# =============================================================================
# CONTEXTUAL VARIATION CHECK
# =============================================================================

print("\n" + "-" * 80)
print("CONTEXTUAL VARIATION CHECK")
print("-" * 80)


for column in context_numeric:

    unique = df[column].nunique()

    print(
        f"{column:40s} "
        f"{unique} unique value(s)"
    )


# =============================================================================
# SAVE
# =============================================================================

print("\n" + "-" * 80)
print("SAVING ML FEATURE DATASET")
print("-" * 80)

ml_features.to_parquet(
    OUTPUT,
    index=False
)

print(
    f"\nSaved:\n{OUTPUT}"
)

print(
    f"Output size: "
    f"{OUTPUT.stat().st_size / 1024:.2f} KB"
)


# =============================================================================
# REPORT
# =============================================================================

report_lines = [

    "VIGRAH — C3.1 ML FEATURE PREPARATION",

    "=" * 60,

    f"Input records: {len(df):,}",

    f"ML records: {len(ml_features):,}",

    f"ML columns: {len(ml_features.columns):,}",

    "",

    "ROAD-LEVEL FEATURES",

]

for column in road_level_numeric:

    report_lines.append(
        f"  {column}"
    )


report_lines.extend(
    [
        "",
        "ROAD-LEVEL BINARY FEATURES",
    ]
)


for column in road_level_binary:

    report_lines.append(
        f"  {column}"
    )


report_lines.extend(
    [
        "",
        "CONTEXTUAL FEATURES",
    ]
)


for column in context_numeric:

    report_lines.append(
        f"  {column}"
    )


report_lines.extend(
    [
        "",
        "IMPORTANT SEMANTIC RULE:",
        "Accident and crime indicators remain",
        "contextual features.",
        "They are not road-level incident labels.",
        "",
        "BASELINE RISK:",
        "Retained as benchmark/reference.",
        "It is NOT used as a ground-truth label.",
    ]
)


REPORT.write_text(
    "\n".join(report_lines),
    encoding="utf-8"
)


# =============================================================================
# COMPLETE
# =============================================================================

print("\n" + "=" * 80)
print("C3.1 COMPLETE")
print("=" * 80)

print(
    "\nML feature dataset created."
)

print(
    "Road-level and contextual features "
    "remain explicitly separated."
)

print(
    "\nOutput:"
)

print(
    OUTPUT
)

print(
    "\nNext → C3.2 MODEL / PATTERN EVALUATION"
)