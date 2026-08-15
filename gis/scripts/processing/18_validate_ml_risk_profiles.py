from pathlib import Path
import numpy as np
import pandas as pd


# =============================================================================
# VIGRAH — C3.3 ML RISK PROFILE VALIDATION / GENERATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "road_ml_patterns.parquet"
)

OUTPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "road_ml_risk_profiles.parquet"
)

REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "c3_3_ml_risk_profile_report.txt"
)


print("=" * 80)
print("VIGRAH — C3.3 ML RISK PROFILE VALIDATION / GENERATION")
print("=" * 80)

print("\nInput:")
print(INPUT)


# =============================================================================
# 1. LOAD DATASET
# =============================================================================

if not INPUT.exists():
    raise FileNotFoundError(
        f"\nC3.2 output not found:\n{INPUT}"
    )

df = pd.read_parquet(INPUT)

print("\n" + "-" * 80)
print("LOADING ML PATTERN DATASET")
print("-" * 80)

print(f"Records: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# =============================================================================
# 2. REQUIRED COLUMN VALIDATION
# =============================================================================

required = [
    "city",
    "road_id",
    "road_name",
    "highway",

    # C2 baseline benchmark
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "risk_level",

    # C3.2 ML outputs
    "road_profile_cluster",
    "ml_anomaly_score",
    "ml_anomaly_label",

    # C3.1 normalized spatial confidence
    "spatial_confidence_norm",
]

missing = [
    column
    for column in required
    if column not in df.columns
]

print("\n" + "-" * 80)
print("SCHEMA VALIDATION")
print("-" * 80)

if missing:

    print("Missing columns:")

    for column in missing:
        print(f"  {column}")

    print("\nAvailable columns:")

    for column in df.columns:
        print(f"  {column}")

    raise RuntimeError(
        "C3.3 schema validation failed."
    )

print(
    f"Required columns: "
    f"{len(required)} / {len(required)}"
)

print("PASS")


# =============================================================================
# 3. RECORD / ROAD UNIQUENESS VALIDATION
# =============================================================================

print("\n" + "-" * 80)
print("RECORD VALIDATION")
print("-" * 80)

if df["road_id"].isna().any():

    raise RuntimeError(
        "Null road IDs detected."
    )

duplicate_count = int(
    df["road_id"].duplicated().sum()
)

print(
    f"Unique roads: "
    f"{df['road_id'].nunique():,}"
)

print(
    f"Duplicate road rows: "
    f"{duplicate_count}"
)

if duplicate_count > 0:

    raise RuntimeError(
        "Duplicate road IDs detected."
    )

print("PASS")


# =============================================================================
# 4. NUMERIC VALIDATION
# =============================================================================

numeric_columns = [
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "ml_anomaly_score",
    "spatial_confidence_norm",
]

print("\n" + "-" * 80)
print("NUMERIC VALIDATION")
print("-" * 80)

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    invalid = int(
        df[column].isna().sum()
    )

    infinite = int(
        np.isinf(
            df[column].to_numpy(
                dtype=float
            )
        ).sum()
    )

    print(
        f"{column:40s}"
        f" invalid={invalid:3d}"
        f" infinite={infinite:3d}"
    )

    if invalid > 0 or infinite > 0:

        raise RuntimeError(
            f"Invalid numeric values found in "
            f"{column}"
        )

print("PASS")


# =============================================================================
# 5. SPATIAL CONFIDENCE VALIDATION
# =============================================================================

print("\n" + "-" * 80)
print("SPATIAL CONFIDENCE VALIDATION")
print("-" * 80)

spatial_min = df[
    "spatial_confidence_norm"
].min()

spatial_max = df[
    "spatial_confidence_norm"
].max()

print(
    f"Minimum: {spatial_min:.3f}"
)

print(
    f"Maximum: {spatial_max:.3f}"
)

if spatial_min < 0 or spatial_max > 1:

    raise RuntimeError(
        "Spatial confidence is outside "
        "the expected 0–1 range."
    )

print("Range: 0–1")
print("PASS")


# =============================================================================
# 6. ML ANOMALY NORMALIZATION
# =============================================================================

print("\n" + "-" * 80)
print("ML ANOMALY NORMALIZATION")
print("-" * 80)

#
# Isolation Forest score interpretation:
#
# More negative → more anomalous.
#
# Therefore we invert and normalize the raw score:
#
# 0 = least anomalous
# 1 = most anomalous
#

min_score = df[
    "ml_anomaly_score"
].min()

max_score = df[
    "ml_anomaly_score"
].max()

if max_score == min_score:

    df[
        "ml_anomaly_intensity"
    ] = 0.0

else:

    df[
        "ml_anomaly_intensity"
    ] = (
        max_score
        - df["ml_anomaly_score"]
    ) / (
        max_score
        - min_score
    )

df[
    "ml_anomaly_intensity"
] = (
    df["ml_anomaly_intensity"]
    .clip(0, 1)
)

print(
    f"Anomaly score range:"
    f" {min_score:.6f}"
    f" → {max_score:.6f}"
)

print(
    f"Anomaly intensity range:"
    f" {df['ml_anomaly_intensity'].min():.3f}"
    f" → {df['ml_anomaly_intensity'].max():.3f}"
)

print("PASS")


# =============================================================================
# 7. ANOMALY LABEL VALIDATION
# =============================================================================

print("\n" + "-" * 80)
print("ANOMALY LABEL VALIDATION")
print("-" * 80)

valid_labels = {-1, 1}

actual_labels = set(
    df["ml_anomaly_label"]
    .dropna()
    .astype(int)
    .unique()
)

print(
    f"Labels found: "
    f"{sorted(actual_labels)}"
)

if not actual_labels.issubset(
    valid_labels
):

    raise RuntimeError(
        "Unexpected Isolation Forest labels."
    )

anomalous_roads = int(
    (
        df["ml_anomaly_label"]
        == -1
    ).sum()
)

normal_roads = int(
    (
        df["ml_anomaly_label"]
        == 1
    ).sum()
)

print(
    f"Normal roads: {normal_roads:,}"
)

print(
    f"Anomalous roads: {anomalous_roads:,}"
)

print("PASS")


# =============================================================================
# 8. CREATE ML ROAD PROFILE
# =============================================================================

print("\n" + "-" * 80)
print("CREATING ML ROAD PROFILES")
print("-" * 80)


def classify_profile(row):

    baseline = float(
        row[
            "confidence_adjusted_risk_score"
        ]
    )

    anomaly = float(
        row[
            "ml_anomaly_intensity"
        ]
    )

    # Strong contextual baseline
    # AND strong ML anomaly.
    if (
        baseline >= 60
        and anomaly >= 0.70
    ):

        return "HIGH_RISK_ANOMALOUS"

    # Strong baseline but not strongly anomalous.
    if baseline >= 60:

        return "HIGH_BASELINE_RISK"

    # Moderate baseline + strong anomaly.
    if (
        baseline >= 40
        and anomaly >= 0.70
    ):

        return "MODERATE_RISK_ANOMALOUS"

    # Strong anomaly despite lower baseline.
    if anomaly >= 0.70:

        return "ANOMALOUS_LOW_BASELINE"

    # Normal contextual profile.
    if baseline >= 30:

        return "MODERATE_PROFILE"

    return "LOW_RISK_PROFILE"


df[
    "ml_risk_profile"
] = df.apply(
    classify_profile,
    axis=1
)

print(
    "ML risk profiles created."
)


# =============================================================================
# 9. ML-ENHANCED DIAGNOSTIC SCORE
# =============================================================================

print("\n" + "-" * 80)
print("CALCULATING ML-ENHANCED RISK INDICATOR")
print("-" * 80)

#
# IMPORTANT:
#
# This is NOT:
#   - an accident probability
#   - a crime probability
#   - a supervised prediction
#
# It is a diagnostic prioritization indicator.
#
# 80% = contextual baseline
# 20% = unsupervised ML anomaly signal
#

df[
    "ml_enhanced_risk_score"
] = (
    0.80
    * df[
        "confidence_adjusted_risk_score"
    ]
    +
    0.20
    * (
        df[
            "ml_anomaly_intensity"
        ]
        * 100
    )
)

df[
    "ml_enhanced_risk_score"
] = (
    df[
        "ml_enhanced_risk_score"
    ]
    .clip(0, 100)
)

print(
    "Formula:"
)

print(
    "  80% contextual baseline"
)

print(
    "  20% ML anomaly intensity"
)

print(
    f"Score range:"
    f" {df['ml_enhanced_risk_score'].min():.2f}"
    f" → {df['ml_enhanced_risk_score'].max():.2f}"
)

print("PASS")


# =============================================================================
# 10. FINAL ML PROFILE LEVEL
# =============================================================================

print("\n" + "-" * 80)
print("CREATING FINAL ML PROFILE LEVEL")
print("-" * 80)


def final_profile(row):

    score = float(
        row[
            "ml_enhanced_risk_score"
        ]
    )

    anomaly = float(
        row[
            "ml_anomaly_intensity"
        ]
    )

    if (
        score >= 70
        and anomaly >= 0.70
    ):

        return "CRITICAL_CANDIDATE"

    if score >= 60:

        return "HIGH"

    if score >= 35:

        return "MODERATE"

    return "LOW"


df[
    "ml_profile_level"
] = df.apply(
    final_profile,
    axis=1
)

print(
    "Profile levels created."
)


# =============================================================================
# 11. ML PROFILE CONFIDENCE
# =============================================================================

print("\n" + "-" * 80)
print("CALCULATING ML PROFILE CONFIDENCE")
print("-" * 80)

#
# Profile confidence combines:
#
# 70% spatial confidence
# 30% anomaly strength
#
# This is NOT a probability.
#

df[
    "ml_profile_confidence"
] = (
    0.70
    * df[
        "spatial_confidence_norm"
    ]
    +
    0.30
    * df[
        "ml_anomaly_intensity"
    ]
)

df[
    "ml_profile_confidence"
] = (
    df[
        "ml_profile_confidence"
    ]
    .clip(0, 1)
)

print(
    f"Confidence range:"
    f" {df['ml_profile_confidence'].min():.3f}"
    f" → {df['ml_profile_confidence'].max():.3f}"
)

print("PASS")


# =============================================================================
# 12. OUTPUT RANGE VALIDATION
# =============================================================================

print("\n" + "-" * 80)
print("OUTPUT RANGE VALIDATION")
print("-" * 80)

range_checks = {

    "ml_anomaly_intensity":
        (0, 1),

    "ml_enhanced_risk_score":
        (0, 100),

    "ml_profile_confidence":
        (0, 1),
}


for column, (
    lower,
    upper
) in range_checks.items():

    actual_min = df[
        column
    ].min()

    actual_max = df[
        column
    ].max()

    valid = (
        actual_min >= lower
        and actual_max <= upper
    )

    print(
        f"{column:35s}"
        f"{actual_min:.3f}"
        f" → {actual_max:.3f}"
        f"   "
        f"{'PASS' if valid else 'FAIL'}"
    )

    if not valid:

        raise RuntimeError(
            f"Range validation failed "
            f"for {column}"
        )

print("PASS")


# =============================================================================
# 13. ML RISK PROFILE DISTRIBUTION
# =============================================================================

print("\n" + "-" * 80)
print("ML RISK PROFILE DISTRIBUTION")
print("-" * 80)

profile_distribution = (
    df[
        "ml_risk_profile"
    ]
    .value_counts()
)

print(
    profile_distribution.to_string()
)


# =============================================================================
# 14. ML PROFILE LEVEL DISTRIBUTION
# =============================================================================

print("\n" + "-" * 80)
print("ML PROFILE LEVEL DISTRIBUTION")
print("-" * 80)

level_distribution = (
    df[
        "ml_profile_level"
    ]
    .value_counts()
)

print(
    level_distribution.to_string()
)


# =============================================================================
# 15. CITY-WISE SUMMARY
# =============================================================================

print("\n" + "-" * 80)
print("CITY-WISE ML SUMMARY")
print("-" * 80)

city_summary = (
    df
    .groupby("city")
    .agg(

        roads=(
            "road_id",
            "count"
        ),

        mean_baseline_risk=(
            "confidence_adjusted_risk_score",
            "mean"
        ),

        mean_ml_score=(
            "ml_enhanced_risk_score",
            "mean"
        ),

        anomalous_roads=(
            "ml_anomaly_label",
            lambda x:
                int(
                    (x == -1).sum()
                )
        ),

        high_profile_roads=(
            "ml_profile_level",
            lambda x:
                int(
                    (x == "HIGH").sum()
                )
        ),

        critical_candidates=(
            "ml_profile_level",
            lambda x:
                int(
                    (
                        x
                        == "CRITICAL_CANDIDATE"
                    ).sum()
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


# =============================================================================
# 16. TOP ML-ENHANCED RISK ROADS
# =============================================================================

print("\n" + "-" * 80)
print("TOP ML-ENHANCED RISK CANDIDATES")
print("-" * 80)

top_columns = [

    "city",

    "road_id",

    "road_name",

    "highway",

    "confidence_adjusted_risk_score",

    "ml_anomaly_intensity",

    "ml_enhanced_risk_score",

    "ml_risk_profile",

    "ml_profile_level",

    "ml_profile_confidence",
]


top = (
    df
    .sort_values(
        "ml_enhanced_risk_score",
        ascending=False
    )
    .head(20)
)

print(
    top[
        top_columns
    ].to_string(
        index=False
    )
)


# =============================================================================
# 17. HIGH BASELINE + ML ANOMALY INTERSECTION
# =============================================================================

print("\n" + "-" * 80)
print("HIGH BASELINE + ML ANOMALY INTERSECTION")
print("-" * 80)

intersection = df[
    (
        df[
            "confidence_adjusted_risk_score"
        ] >= 60
    )
    &
    (
        df[
            "ml_anomaly_intensity"
        ] >= 0.70
    )
]

print(
    f"Candidate roads: "
    f"{len(intersection)}"
)

if len(intersection) > 0:

    print(
        intersection[
            top_columns
        ]
        .sort_values(
            "ml_enhanced_risk_score",
            ascending=False
        )
        .to_string(
            index=False
        )
    )

else:

    print(
        "No roads currently satisfy "
        "both high baseline risk and "
        "strong ML anomaly."
    )


# =============================================================================
# 18. ANOMALOUS LOW-BASELINE ROADS
# =============================================================================

print("\n" + "-" * 80)
print("ANOMALOUS ROADS WITH LOWER BASELINE")
print("-" * 80)

anomalous_low_baseline = df[
    (
        df[
            "ml_anomaly_intensity"
        ] >= 0.70
    )
    &
    (
        df[
            "confidence_adjusted_risk_score"
        ] < 60
    )
]

print(
    f"Candidate roads: "
    f"{len(anomalous_low_baseline)}"
)

if len(anomalous_low_baseline) > 0:

    print(
        anomalous_low_baseline[
            top_columns
        ]
        .sort_values(
            "ml_anomaly_intensity",
            ascending=False
        )
        .head(20)
        .to_string(
            index=False
        )
    )


# =============================================================================
# 19. ROAD PROFILE × CITY
# =============================================================================

print("\n" + "-" * 80)
print("CITY × ML PROFILE")
print("-" * 80)

city_profile = (
    df
    .groupby(
        [
            "city",
            "ml_risk_profile",
        ]
    )
    .size()
    .reset_index(
        name="roads"
    )
)

print(
    city_profile.to_string(
        index=False
    )
)


# =============================================================================
# 20. SEMANTIC SAFETY CHECK
# =============================================================================

print("\n" + "-" * 80)
print("SEMANTIC SAFETY CHECK")
print("-" * 80)

print(
    "Baseline risk:"
)

print(
    "  Contextual benchmark."
)

print(
    "ML anomaly:"
)

print(
    "  Unsupervised structural signal."
)

print(
    "Accident data:"
)

print(
    "  Contextual, NOT road-level."
)

print(
    "Crime data:"
)

print(
    "  Contextual, NOT road-level."
)

print(
    "ML-enhanced score:"
)

print(
    "  Diagnostic prioritization indicator."
)

print(
    "Supervised probability:"
)

print(
    "  NOT claimed."
)

print("PASS")


# =============================================================================
# 21. SAVE OUTPUT
# =============================================================================

print("\n" + "-" * 80)
print("SAVING ML RISK PROFILE DATASET")
print("-" * 80)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_parquet(
    OUTPUT,
    index=False
)

print(
    "Output:"
)

print(
    OUTPUT
)

print(
    f"Output size:"
    f" {OUTPUT.stat().st_size / 1024:.2f} KB"
)


# =============================================================================
# 22. SAVE VALIDATION REPORT
# =============================================================================

report_lines = []

report_lines.append(
    "VIGRAH — C3.3 ML RISK PROFILE REPORT"
)

report_lines.append(
    "=" * 70
)

report_lines.append(
    f"Road records: {len(df):,}"
)

report_lines.append(
    f"Anomalous roads: "
    f"{anomalous_roads:,}"
)

report_lines.append(
    f"Critical candidates: "
    f"{int((df['ml_profile_level'] == 'CRITICAL_CANDIDATE').sum()):,}"
)

report_lines.append("")

report_lines.append(
    "ML RISK PROFILE DISTRIBUTION"
)

report_lines.append(
    profile_distribution.to_string()
)

report_lines.append("")

report_lines.append(
    "ML PROFILE LEVEL DISTRIBUTION"
)

report_lines.append(
    level_distribution.to_string()
)

report_lines.append("")

report_lines.append(
    "CITY SUMMARY"
)

report_lines.append(
    city_summary.to_string(
        index=False
    )
)

report_lines.append("")

report_lines.append(
    "CITY × ML PROFILE"
)

report_lines.append(
    city_profile.to_string(
        index=False
    )
)

report_lines.append("")

report_lines.append(
    "HIGH BASELINE + ML ANOMALY"
)

report_lines.append(
    f"Candidate roads: "
    f"{len(intersection)}"
)

report_lines.append("")

report_lines.append(
    "SEMANTIC INTERPRETATION"
)

report_lines.append(
    "Baseline risk is a contextual benchmark."
)

report_lines.append(
    "ML anomaly is an unsupervised structural signal."
)

report_lines.append(
    "Accident data remains contextual."
)

report_lines.append(
    "Crime data remains contextual."
)

report_lines.append(
    "ML-enhanced score is a diagnostic prioritization indicator."
)

report_lines.append(
    "It is NOT a supervised accident/crime probability."
)


REPORT.write_text(
    "\n".join(report_lines),
    encoding="utf-8"
)


# =============================================================================
# COMPLETE
# =============================================================================

print("\n" + "=" * 80)
print("C3.3 COMPLETE")
print("=" * 80)

print(
    "\nML risk profile generation completed."
)

print(
    f"Roads evaluated: "
    f"{len(df):,}"
)

print(
    f"Anomalous roads: "
    f"{anomalous_roads:,}"
)

print(
    f"Critical candidates: "
    f"{int((df['ml_profile_level'] == 'CRITICAL_CANDIDATE').sum()):,}"
)

print(
    "\nOutput:"
)

print(
    OUTPUT
)

print(
    "\nReport:"
)

print(
    REPORT
)

print(
    "\nNEXT → C3.4 FINAL RISK DATASET VALIDATION"
)