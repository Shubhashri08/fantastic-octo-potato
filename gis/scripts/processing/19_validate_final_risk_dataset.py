from pathlib import Path
import pandas as pd
import numpy as np


# =============================================================================
# VIGRAH — C3.4 FINAL RISK DATASET VALIDATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "road_ml_risk_profiles.parquet"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
)

REPORT = (
    OUTPUT_DIR
    / "c3_4_final_risk_validation_report.txt"
)


def section(title):
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def fail(message):
    print("\nVALIDATION FAILED")
    print(message)
    raise RuntimeError(message)


def main():

    print("=" * 80)
    print("VIGRAH — C3.4 FINAL RISK DATASET VALIDATION")
    print("=" * 80)

    print("\nInput:")
    print(INPUT)

    if not INPUT.exists():
        fail(
            f"Final risk dataset does not exist:\n{INPUT}"
        )

    # =========================================================================
    # LOAD
    # =========================================================================

    section("LOADING FINAL ML RISK DATASET")

    df = pd.read_parquet(INPUT)

    print(f"Records: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # =========================================================================
    # 1. REQUIRED SCHEMA
    # =========================================================================

    section("1. REQUIRED SCHEMA VALIDATION")

    required_columns = [

        # Identification
        "city",
        "road_id",
        "road_name",
        "highway",

        # Spatial / CCTV-derived
        "spatial_confidence_norm",
        "cctv_count_norm",

        # Baseline risk
        "baseline_risk_score",
        "confidence_adjusted_risk_score",

        # ML
        "ml_anomaly_score",
        "ml_anomaly_intensity",
        "ml_risk_profile",
        "ml_profile_level",
        "ml_profile_confidence",
        "ml_enhanced_risk_score",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    print(
        f"Required columns: "
        f"{len(required_columns) - len(missing)} / "
        f"{len(required_columns)}"
    )

    if missing:

        print("\nMissing columns:")

        for col in missing:
            print(f"  {col}")

        print("\nAvailable columns:")

        for col in df.columns:
            print(f"  {col}")

        fail(
            "Final risk dataset schema validation failed."
        )

    print("PASS")

    # =========================================================================
    # 2. RECORD COUNT
    # =========================================================================

    section("2. RECORD COUNT")

    print("Expected: 844")
    print(f"Actual:   {len(df)}")

    if len(df) != 844:

        fail(
            "Expected exactly 844 road-level records."
        )

    print("PASS")

    # =========================================================================
    # 3. ROAD UNIQUENESS
    # =========================================================================

    section("3. ROAD UNIQUENESS")

    duplicate_count = (
        df
        .duplicated(
            subset=["city", "road_id"]
        )
        .sum()
    )

    unique_roads = (
        df[
            ["city", "road_id"]
        ]
        .drop_duplicates()
        .shape[0]
    )

    print(
        f"Unique city-road pairs: "
        f"{unique_roads:,}"
    )

    print(
        f"Duplicate rows: "
        f"{duplicate_count:,}"
    )

    if duplicate_count != 0:

        fail(
            "Duplicate city-road records detected."
        )

    print("PASS")

    # =========================================================================
    # 4. CITY VALIDATION
    # =========================================================================

    section("4. CITY VALIDATION")

    expected_cities = {
        "Mumbai",
        "Bengaluru"
    }

    actual_cities = set(
        df["city"]
        .dropna()
        .unique()
    )

    print(
        f"Cities found: "
        f"{sorted(actual_cities)}"
    )

    if actual_cities != expected_cities:

        fail(
            f"Unexpected city set.\n"
            f"Expected: {expected_cities}\n"
            f"Actual:   {actual_cities}"
        )

    city_counts = (
        df["city"]
        .value_counts()
    )

    for city in [
        "Mumbai",
        "Bengaluru"
    ]:

        print(
            f"{city}: "
            f"{city_counts.get(city, 0):,}"
        )

    print("PASS")

    # =========================================================================
    # 5. NUMERIC VALIDATION
    # =========================================================================

    section("5. NUMERIC FEATURE VALIDATION")

    numeric_columns = [

        "baseline_risk_score",
        "confidence_adjusted_risk_score",

        "ml_anomaly_score",
        "ml_anomaly_intensity",

        "spatial_confidence_norm",
        "cctv_count_norm",

        "ml_profile_confidence",
        "ml_enhanced_risk_score",
    ]

    numeric_failed = False

    for column in numeric_columns:

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid = int(
            values.isna().sum()
        )

        infinite = int(
            np.isinf(
                values.to_numpy(
                    dtype=float
                )
            ).sum()
        )

        print(
            f"{column:<38}"
            f" invalid={invalid:>3}"
            f" infinite={infinite:>3}"
        )

        if (
            invalid > 0
            or infinite > 0
        ):

            numeric_failed = True

    if numeric_failed:

        fail(
            "Invalid or infinite numeric "
            "values detected."
        )

    print("PASS")

    # =========================================================================
    # 6. SCORE RANGE VALIDATION
    # =========================================================================

    section("6. RISK SCORE RANGE VALIDATION")

    range_checks = {

        "baseline_risk_score":
            (0, 100),

        "confidence_adjusted_risk_score":
            (0, 100),

        "ml_anomaly_intensity":
            (0, 1),

        "spatial_confidence_norm":
            (0, 1),

        "cctv_count_norm":
            (0, 1),

        "ml_profile_confidence":
            (0, 1),

        "ml_enhanced_risk_score":
            (0, 100),
    }

    range_failed = False

    for column, (
        minimum,
        maximum
    ) in range_checks.items():

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        actual_min = series.min()
        actual_max = series.max()

        valid = (
            actual_min >= minimum
            and actual_max <= maximum
        )

        print(
            f"{column:<38}"
            f"{actual_min:>8.3f}"
            f" → {actual_max:<8.3f}"
            f" {'PASS' if valid else 'FAIL'}"
        )

        if not valid:
            range_failed = True

    if range_failed:

        fail(
            "One or more risk features "
            "are outside the permitted range."
        )

    print("PASS")

    # =========================================================================
    # 7. ML ANOMALY VALIDATION
    # =========================================================================

    section("7. ML ANOMALY VALIDATION")

    anomaly_intensity = pd.to_numeric(
        df["ml_anomaly_intensity"],
        errors="coerce"
    )

    anomalous_count = int(
        (
            anomaly_intensity >= 0.70
        ).sum()
    )

    print(
        f"Anomaly intensity minimum: "
        f"{anomaly_intensity.min():.3f}"
    )

    print(
        f"Anomaly intensity maximum: "
        f"{anomaly_intensity.max():.3f}"
    )

    print(
        f"Strong anomaly roads (>=0.70): "
        f"{anomalous_count}"
    )

    print("PASS")

    # =========================================================================
    # 8. ML RISK PROFILE VALIDATION
    # =========================================================================

    section("8. ML RISK PROFILE VALIDATION")

    allowed_profiles = {

        "MODERATE_PROFILE",
        "LOW_RISK_PROFILE",

        "ANOMALOUS_LOW_BASELINE",

        "HIGH_RISK_ANOMALOUS",

        "MODERATE_RISK_ANOMALOUS",

        "HIGH_BASELINE_RISK",
    }

    actual_profiles = set(
        df["ml_risk_profile"]
        .dropna()
        .unique()
    )

    print("Profiles found:")

    profile_counts = (
        df["ml_risk_profile"]
        .value_counts()
    )

    for profile, count in (
        profile_counts.items()
    ):

        print(
            f"  {profile:<32}"
            f"{count:>5}"
        )

    unexpected_profiles = (
        actual_profiles
        - allowed_profiles
    )

    if unexpected_profiles:

        fail(
            "Unexpected ML risk profiles:\n"
            f"{unexpected_profiles}"
        )

    print("PASS")

    # =========================================================================
    # 9. PROFILE LEVEL VALIDATION
    # =========================================================================

    section("9. ML PROFILE LEVEL VALIDATION")

    allowed_levels = {
        "LOW",
        "MODERATE",
        "HIGH",
    }

    actual_levels = set(
        df["ml_profile_level"]
        .dropna()
        .unique()
    )

    print(
        f"Levels found: "
        f"{sorted(actual_levels)}"
    )

    unexpected_levels = (
        actual_levels
        - allowed_levels
    )

    if unexpected_levels:

        fail(
            "Unexpected ML profile levels:\n"
            f"{unexpected_levels}"
        )

    print("\nDistribution:")

    level_counts = (
        df["ml_profile_level"]
        .value_counts()
    )

    for level, count in (
        level_counts.items()
    ):

        print(
            f"  {level:<10}"
            f"{count:>5}"
        )

    print("PASS")

    # =========================================================================
    # 10. ML PROFILE CONFIDENCE
    # =========================================================================

    section("10. ML PROFILE CONFIDENCE")

    confidence = pd.to_numeric(
        df["ml_profile_confidence"],
        errors="coerce"
    )

    print(
        f"Minimum: "
        f"{confidence.min():.3f}"
    )

    print(
        f"Mean:    "
        f"{confidence.mean():.3f}"
    )

    print(
        f"Maximum: "
        f"{confidence.max():.3f}"
    )

    if (
        confidence.min() < 0
        or confidence.max() > 1
    ):

        fail(
            "ML profile confidence outside 0–1."
        )

    print("PASS")

    # =========================================================================
    # 11. FINAL SCORE DISTRIBUTION
    # =========================================================================

    section("11. FINAL ML-ENHANCED SCORE DISTRIBUTION")

    score = df[
        "ml_enhanced_risk_score"
    ]

    print(
        score.describe().to_string()
    )

    print(
        f"\nUnique final scores: "
        f"{score.nunique()}"
    )

    # =========================================================================
    # 12. CITY-WISE SUMMARY
    # =========================================================================

    section("12. CITY-WISE FINAL RISK SUMMARY")

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
                "ml_anomaly_intensity",
                lambda x:
                int(
                    (x >= 0.70).sum()
                )
            ),

            high_profile_roads=(
                "ml_profile_level",
                lambda x:
                int(
                    (x == "HIGH").sum()
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

    # =========================================================================
    # 13. TOP RISK ROADS
    # =========================================================================

    section("13. TOP FINAL RISK CANDIDATES")

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
        [
            top_columns
        ]
        .head(20)
    )

    print(
        top.to_string(
            index=False
        )
    )

    # =========================================================================
    # 14. HIGH BASELINE + STRONG ANOMALY
    # =========================================================================

    section(
        "14. HIGH BASELINE + STRONG ML ANOMALY"
    )

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

    # =========================================================================
    # 15. HIGH-RISK ROAD SUMMARY
    # =========================================================================

    section("15. HIGH-RISK PROFILE SUMMARY")

    high_mask = (
        df["ml_profile_level"]
        == "HIGH"
    )

    high_roads = df.loc[
        high_mask
    ]

    print(
        f"High-profile roads: "
        f"{len(high_roads)}"
    )

    if len(high_roads) > 0:

        print(
            high_roads[
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

    # =========================================================================
    # 16. SEMANTIC SAFETY
    # =========================================================================

    section("16. METHODOLOGICAL SEMANTICS")

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
        "ML-enhanced score:"
    )
    print(
        "  Diagnostic prioritization indicator."
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
        "Supervised probability:"
    )
    print(
        "  NOT claimed."
    )

    # Check crime semantics if present
    if "crime_not_road_level" in df.columns:

        values = (
            df[
                "crime_not_road_level"
            ]
            .dropna()
            .unique()
        )

        print(
            f"\ncrime_not_road_level: "
            f"{values}"
        )

        if not df[
            "crime_not_road_level"
        ].all():

            fail(
                "Crime context is not consistently "
                "marked as non-road-level."
            )

    print("PASS")

    # =========================================================================
    # 17. SAVE REPORT
    # =========================================================================

    section("17. SAVING VALIDATION REPORT")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    report_lines = [

        "VIGRAH — C3.4 FINAL RISK DATASET VALIDATION",
        "=" * 80,

        "",

        f"Records: {len(df)}",
        f"Columns: {len(df.columns)}",
        f"Unique city-road pairs: {unique_roads}",

        "",

        f"Strong anomaly roads: {anomalous_count}",
        f"High profile roads: {len(high_roads)}",
        f"High baseline + strong anomaly: {len(intersection)}",

        "",

        "CITY SUMMARY",

        city_summary.to_string(
            index=False
        ),

        "",

        "TOP RISK CANDIDATES",

        top.to_string(
            index=False
        ),

        "",

        "HIGH BASELINE + STRONG ML ANOMALY",

        intersection[
            top_columns
        ]
        .sort_values(
            "ml_enhanced_risk_score",
            ascending=False
        )
        .to_string(
            index=False
        ),

        "",

        "METHODOLOGICAL INTERPRETATION",

        "Baseline risk = contextual benchmark.",

        "ML anomaly = unsupervised structural signal.",

        "ML-enhanced score = diagnostic prioritization indicator.",

        "Accident data = contextual, NOT road-level.",

        "Crime data = contextual, NOT road-level.",

        "Supervised probability = NOT claimed.",

        "",

        "FINAL STATUS: PASS",
    ]

    REPORT.write_text(
        "\n".join(report_lines),
        encoding="utf-8"
    )

    print(
        f"Report saved:\n{REPORT}"
    )

    # =========================================================================
    # COMPLETE
    # =========================================================================

    print("\n" + "=" * 80)
    print("C3.4 VALIDATION COMPLETE")
    print("=" * 80)

    print(
        "\nPHASE C — RISK ENGINE: PASSED"
    )

    print(
        f"\nRoads validated: "
        f"{len(df):,}"
    )

    print(
        f"Strong ML anomalies: "
        f"{anomalous_count:,}"
    )

    print(
        f"High-risk profiles: "
        f"{len(high_roads):,}"
    )

    print(
        f"High baseline + strong anomaly: "
        f"{len(intersection):,}"
    )

    print(
        f"\nReport:\n{REPORT}"
    )

    print(
        "\nNEXT → PHASE D — VIGRAH INTEGRATION"
    )


if __name__ == "__main__":
    main()