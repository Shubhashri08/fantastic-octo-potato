from pathlib import Path
import pandas as pd
import numpy as np


# =============================================================================
# VIGRAH — D3 ALERT GENERATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "event_risk_enrichment.parquet"
)

OUTPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "vigrah_alerts.parquet"
)

REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "d3_alert_generation_report.txt"
)


# =============================================================================
# CONFIGURATION
# =============================================================================

SEVERITY_SCORES = {
    "low": 25,
    "medium": 55,
    "high": 85,
    "critical": 100,
}

MATCH_QUALITY_MULTIPLIER = {
    "high": 1.00,
    "good": 0.95,
    "medium": 0.90,
    "low": 0.75,
    "review": 0.60,
}

HISTORICAL_RISK_WEIGHT = 0.40
EVENT_WEIGHT = 0.60

ALERT_THRESHOLDS = {
    "CRITICAL": 80,
    "HIGH": 60,
    "MEDIUM": 40,
}

ALERT_PRIORITY = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
}


# =============================================================================
# HELPERS
# =============================================================================

def fail(message):
    raise RuntimeError(message)


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def classify_alert(score):

    if score >= ALERT_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"

    if score >= ALERT_THRESHOLDS["HIGH"]:
        return "HIGH"

    if score >= ALERT_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"

    return "LOW"


def historical_profile_available(row):

    status = normalize_text(
        row.get("risk_enrichment_status")
    )

    if status == "historical_profile_available":
        return True

    if status in {
        "no_historical_profile",
        "missing",
        "unavailable",
        "",
    }:
        return False

    return pd.notna(
        row.get("confidence_adjusted_risk_score")
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 80)
    print("VIGRAH — D3 ALERT GENERATION")
    print("=" * 80)

    # =========================================================================
    # LOAD
    # =========================================================================

    print("\n" + "-" * 80)
    print("LOADING D2 EVENT → ROAD → RISK DATA")
    print("-" * 80)

    print(f"Input:\n{INPUT}")

    if not INPUT.exists():
        fail(
            f"D2 input dataset does not exist:\n{INPUT}"
        )

    df = pd.read_parquet(INPUT)

    input_record_count = len(df)

    print(f"Records loaded: {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    # =========================================================================
    # SCHEMA
    # =========================================================================

    print("\n" + "-" * 80)
    print("SCHEMA VALIDATION")
    print("-" * 80)

    required_columns = [
        "event_id",
        "city",
        "road_id",
        "road_name",
        "event_type",
        "severity",
        "confidence",
        "event_to_road_distance_m",
        "event_road_match_quality",
        "risk_enrichment_status",
        "baseline_risk_score",
        "confidence_adjusted_risk_score",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:

        print("Missing columns:")

        for col in missing:
            print(f"  {col}")

        fail("D3 schema validation failed.")

    print(
        f"Required columns: "
        f"{len(required_columns)} / "
        f"{len(required_columns)}"
    )

    print("PASS")

    # =========================================================================
    # BASIC VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("BASIC VALIDATION")
    print("-" * 80)

    duplicate_events = (
        df["event_id"]
        .duplicated()
        .sum()
    )

    print(f"Event records: {len(df)}")
    print(f"Duplicate event IDs: {duplicate_events}")

    if duplicate_events != 0:
        fail("Duplicate event IDs detected.")

    if len(df) == 0:
        fail("D2 dataset contains no events.")

    print("Event uniqueness: PASS")

    # =========================================================================
    # NORMALIZE EVENT ATTRIBUTES
    # =========================================================================

    print("\n" + "-" * 80)
    print("NORMALIZING EVENT ATTRIBUTES")
    print("-" * 80)

    df["severity_normalized"] = (
        df["severity"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["event_road_match_quality_normalized"] = (
        df["event_road_match_quality"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["risk_enrichment_status_normalized"] = (
        df["risk_enrichment_status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # =========================================================================
    # CURRENT EVENT SCORE
    # =========================================================================

    print("\n" + "-" * 80)
    print("CALCULATING CURRENT EVENT SCORE")
    print("-" * 80)

    df["event_severity_score"] = (
        df["severity_normalized"]
        .map(SEVERITY_SCORES)
        .fillna(0)
        .astype(float)
    )

    df["event_confidence"] = pd.to_numeric(
        df["confidence"],
        errors="coerce",
    ).fillna(0)

    df["event_confidence"] = (
        df["event_confidence"]
        .clip(0, 1)
    )

    df["event_confidence_score"] = (
        df["event_confidence"] * 100
    )

    # 70% severity
    # 30% source/model confidence

    df["event_evidence_score"] = (
        0.70 * df["event_severity_score"]
        +
        0.30 * df["event_confidence_score"]
    )

    # =========================================================================
    # ROAD MATCH QUALITY
    # =========================================================================

    print("\n" + "-" * 80)
    print("APPLYING ROAD MATCH QUALITY")
    print("-" * 80)

    df["road_match_multiplier"] = (
        df["event_road_match_quality_normalized"]
        .map(MATCH_QUALITY_MULTIPLIER)
        .fillna(0.75)
        .astype(float)
    )

    df["event_spatial_score"] = (
        df["event_evidence_score"]
        *
        df["road_match_multiplier"]
    )

    print(
        "Match multipliers applied according to "
        "event → road mapping quality."
    )

    # =========================================================================
    # HISTORICAL RISK
    # =========================================================================

    print("\n" + "-" * 80)
    print("PROCESSING HISTORICAL RISK")
    print("-" * 80)

    df["historical_profile_available"] = (
        df.apply(
            historical_profile_available,
            axis=1,
        )
    )

    historical_count = int(
        df["historical_profile_available"]
        .sum()
    )

    no_historical_count = (
        len(df) - historical_count
    )

    print(
        f"Historical profiles available: "
        f"{historical_count}"
    )

    print(
        f"No historical profiles:         "
        f"{no_historical_count}"
    )

    df["historical_risk_score"] = pd.to_numeric(
        df["confidence_adjusted_risk_score"],
        errors="coerce",
    )

    # =========================================================================
    # ALERT SCORE
    # =========================================================================

    print("\n" + "-" * 80)
    print("CALCULATING ALERT PRIORITY SCORE")
    print("-" * 80)

    df["alert_score"] = np.nan

    historical_mask = (
        df["historical_profile_available"]
    )

    # When historical profile exists:
    #
    # 60% current event
    # 40% historical road risk

    df.loc[
        historical_mask,
        "alert_score"
    ] = (
        EVENT_WEIGHT
        *
        df.loc[
            historical_mask,
            "event_spatial_score"
        ]
        +
        HISTORICAL_RISK_WEIGHT
        *
        df.loc[
            historical_mask,
            "historical_risk_score"
        ]
    )

    # When historical profile does not exist:
    #
    # 100% current event evidence

    df.loc[
        ~historical_mask,
        "alert_score"
    ] = (
        df.loc[
            ~historical_mask,
            "event_spatial_score"
        ]
    )

    df["alert_score"] = (
        df["alert_score"]
        .clip(0, 100)
        .round(2)
    )

    print(
        "Historical profile available → "
        "60% event + 40% historical risk"
    )

    print(
        "Historical profile unavailable → "
        "100% current event evidence"
    )

    # =========================================================================
    # ALERT LEVEL
    # =========================================================================

    print("\n" + "-" * 80)
    print("CLASSIFYING ALERT LEVEL")
    print("-" * 80)

    df["alert_level"] = (
        df["alert_score"]
        .apply(classify_alert)
    )

    df["alert_required"] = (
        df["alert_level"]
        .isin(
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
            ]
        )
    )

    # =========================================================================
    # ALERT PRIORITY
    # =========================================================================
    #
    # THIS IS THE PART THAT FIXES YOUR ERROR.
    #
    # We explicitly create alert_priority BEFORE the generated-alert
    # display/sort operation.
    #
    # =========================================================================

    df["alert_priority"] = (
        df["alert_level"]
        .map(ALERT_PRIORITY)
    )

    if df["alert_priority"].isna().any():
        fail(
            "Alert priority could not be assigned "
            "to one or more alert levels."
        )

    df["alert_priority"] = (
        df["alert_priority"]
        .astype(int)
    )

    # =========================================================================
    # ALERT TYPE
    # =========================================================================

    def determine_alert_type(row):

        if row["alert_level"] == "CRITICAL":
            return "critical_event_alert"

        if row["alert_level"] == "HIGH":
            return "high_priority_event_alert"

        if row["alert_level"] == "MEDIUM":
            return "medium_priority_event_alert"

        return "event_logged"

    df["alert_type"] = (
        df.apply(
            determine_alert_type,
            axis=1,
        )
    )

    # =========================================================================
    # CONTEXT STATUS
    # =========================================================================

    df["alert_context_status"] = np.where(
        df["historical_profile_available"],
        "historical_risk_available",
        "event_only_no_historical_profile",
    )

    # =========================================================================
    # ALERT MESSAGE
    # =========================================================================

    def generate_message(row):

        city = row["city"]

        road_name = row["road_name"]

        if (
            pd.isna(road_name)
            or str(road_name).strip() == ""
        ):
            road_name = "Unnamed road"

        event_type = row["event_type"]
        level = row["alert_level"]

        if row["historical_profile_available"]:

            risk = row["historical_risk_score"]

            return (
                f"{level} alert in {city}: "
                f"{event_type} detected on "
                f"{road_name}. "
                f"Historical road risk score: "
                f"{risk:.1f}."
            )

        return (
            f"{level} alert in {city}: "
            f"{event_type} detected on "
            f"{road_name}. "
            f"No historical road risk profile "
            f"is available; alert is based on "
            f"current event evidence only."
        )

    df["alert_message"] = (
        df.apply(
            generate_message,
            axis=1,
        )
    )

    # =========================================================================
    # ALERT ID
    # =========================================================================

    df["alert_id"] = (
        "VIGRAH-"
        +
        df["event_id"].astype(str)
    )

    # =========================================================================
    # FINAL VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("FINAL ALERT VALIDATION")
    print("-" * 80)

    if len(df) != input_record_count:
        fail(
            "Record count changed during D3."
        )

    if (
        df["event_id"]
        .nunique()
        != input_record_count
    ):
        fail(
            "One-event → one-alert rule violated."
        )

    if df["alert_id"].duplicated().any():
        fail(
            "Duplicate alert IDs detected."
        )

    if df["alert_score"].isna().any():
        fail(
            "Alert score contains null values."
        )

    if (
        (df["alert_score"] < 0)
        |
        (df["alert_score"] > 100)
    ).any():
        fail(
            "Alert score outside 0–100 range."
        )

    if df["alert_priority"].isna().any():
        fail(
            "Alert priority contains null values."
        )

    print("Record preservation: PASS")
    print("Alert ID uniqueness: PASS")
    print("Alert score range: PASS")
    print("Alert priority generation: PASS")

    # =========================================================================
    # SEMANTIC VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("SEMANTIC VALIDATION")
    print("-" * 80)

    no_profile = (
        ~df["historical_profile_available"]
    )

    invalid_no_profile = (
        no_profile
        &
        df["historical_risk_score"].notna()
    )

    if invalid_no_profile.any():

        print(
            "WARNING: historical score exists for "
            "records marked as no historical profile."
        )

    df["historical_risk_is_road_level"] = (
        df["historical_profile_available"]
    )

    print(
        "No-profile events use event evidence only: PASS"
    )

    # =========================================================================
    # DISTRIBUTION
    # =========================================================================

    print("\n" + "-" * 80)
    print("ALERT DISTRIBUTION")
    print("-" * 80)

    print(
        df["alert_level"]
        .value_counts()
        .reindex(
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW",
            ],
            fill_value=0,
        )
    )

    print("\nAlert-required distribution:")

    print(
        df["alert_required"]
        .value_counts()
    )

    # =========================================================================
    # CITY SUMMARY
    # =========================================================================

    print("\n" + "-" * 80)
    print("CITY-WISE ALERT SUMMARY")
    print("-" * 80)

    city_summary = (
        df.groupby("city")
        .agg(
            events=("event_id", "count"),
            alerts=("alert_required", "sum"),
            mean_alert_score=(
                "alert_score",
                "mean",
            ),
            maximum_alert_score=(
                "alert_score",
                "max",
            ),
            historical_profiles=(
                "historical_profile_available",
                "sum",
            ),
        )
        .reset_index()
    )

    print(
        city_summary
        .to_string(index=False)
    )

      # =========================================================================
    # GENERATED ALERTS
    # =========================================================================

    print("\n" + "-" * 80)
    print("GENERATED ALERTS")
    print("-" * 80)

    # Sort the FULL dataframe first.
    # alert_priority exists in df.
    sorted_df = (
        df.sort_values(
            by=[
                "alert_priority",
                "alert_score",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .copy()
    )

    display_columns = [
        "alert_id",
        "event_id",
        "city",
        "road_id",
        "road_name",
        "event_type",
        "severity",
        "confidence",
        "event_road_match_quality",
        "historical_profile_available",
        "alert_score",
        "alert_level",
        "alert_required",
        "alert_context_status",
    ]

    # Select display columns AFTER sorting.
    display_df = sorted_df[display_columns]

    print(
        display_df.to_string(index=False)
    )

    # =========================================================================
    # SAVE
    # =========================================================================

    print("\n" + "-" * 80)
    print("SAVING D3 ALERT DATASET")
    print("-" * 80)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        OUTPUT,
        index=False,
    )

    print(
        f"Saved:\n{OUTPUT}"
    )

    # =========================================================================
    # REPORT
    # =========================================================================

    report_lines = []

    report_lines.append(
        "VIGRAH — D3 ALERT GENERATION REPORT"
    )

    report_lines.append(
        "=" * 80
    )

    report_lines.append("")

    report_lines.append(
        f"Input records: {len(df)}"
    )

    report_lines.append(
        f"Unique events: "
        f"{df['event_id'].nunique()}"
    )

    report_lines.append(
        f"Historical profiles: "
        f"{historical_count}"
    )

    report_lines.append(
        f"No historical profiles: "
        f"{no_historical_count}"
    )

    report_lines.append("")

    report_lines.append(
        "ALERT DISTRIBUTION"
    )

    report_lines.append(
        "-" * 40
    )

    for level in [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]:

        count = int(
            (
                df["alert_level"]
                == level
            ).sum()
        )

        report_lines.append(
            f"{level}: {count}"
        )

    report_lines.append("")

    report_lines.append(
        "METHODOLOGY"
    )

    report_lines.append(
        "-" * 40
    )

    report_lines.append(
        "Historical profile available:"
    )

    report_lines.append(
        "  60% current event evidence"
    )

    report_lines.append(
        "  40% historical road risk"
    )

    report_lines.append("")

    report_lines.append(
        "Historical profile unavailable:"
    )

    report_lines.append(
        "  100% current event evidence"
    )

    report_lines.append("")

    report_lines.append(
        "No road-level historical risk was "
        "artificially assigned."
    )

    REPORT.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(
        f"\nReport:\n{REPORT}"
    )

    # =========================================================================
    # COMPLETE
    # =========================================================================

    print("\n" + "=" * 80)
    print("D3 COMPLETE")
    print("=" * 80)

    print(
        f"\nEvents processed: {len(df)}"
    )

    print(
        f"Alerts generated: "
        f"{int(df['alert_required'].sum())}"
    )

    print(
        f"Historical profiles available: "
        f"{historical_count}"
    )

    print(
        f"Event-only alerts: "
        f"{no_historical_count}"
    )

    print(
        "\nCurrent event evidence and historical "
        "risk remain explicitly separated."
    )

    print("\nOutput:")
    print(OUTPUT)

    print(
        "\nNEXT → D4 DASHBOARD / ALERT PRESENTATION"
    )


if __name__ == "__main__":
    main()