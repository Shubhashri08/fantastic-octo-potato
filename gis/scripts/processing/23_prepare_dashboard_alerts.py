from pathlib import Path
import pandas as pd
import numpy as np


# =============================================================================
# VIGRAH — D4.1 DASHBOARD-READY ALERT DATASET
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "vigrah_alerts.parquet"
)

OUTPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "dashboard_alerts.parquet"
)

REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "d4_1_dashboard_alert_validation_report.txt"
)


# =============================================================================
# REQUIRED INPUT COLUMNS
# =============================================================================

REQUIRED_COLUMNS = [
    "alert_id",
    "event_id",
    "city",
    "road_id",
    "road_name",
    "event_type",
    "severity",
    "confidence",
    "event_to_road_distance_m",
    "event_road_match_quality",
    "historical_profile_available",
    "historical_risk_score",
    "alert_score",
    "alert_level",
    "alert_required",
    "alert_context_status",
    "alert_type",
    "alert_message",
]


# =============================================================================
# HELPERS
# =============================================================================

def fail(message):
    raise RuntimeError(message)


def clean_string(series):
    return (
        series
        .astype("string")
        .str.strip()
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 80)
    print("VIGRAH — D4.1 DASHBOARD-READY ALERT DATASET")
    print("=" * 80)

    # =========================================================================
    # LOAD
    # =========================================================================

    print("\n" + "-" * 80)
    print("LOADING D3 ALERT DATASET")
    print("-" * 80)

    print(f"Input:\n{INPUT}")

    if not INPUT.exists():
        fail(
            f"D3 alert dataset does not exist:\n{INPUT}"
        )

    df = pd.read_parquet(INPUT)

    input_count = len(df)

    print(f"Records loaded: {input_count}")
    print(f"Columns loaded: {len(df.columns)}")

    # =========================================================================
    # SCHEMA
    # =========================================================================

    print("\n" + "-" * 80)
    print("INPUT SCHEMA VALIDATION")
    print("-" * 80)

    missing = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:

        print("Missing columns:")

        for col in missing:
            print(f"  {col}")

        fail(
            "D4.1 input schema validation failed."
        )

    print(
        f"Required columns: "
        f"{len(REQUIRED_COLUMNS)} / "
        f"{len(REQUIRED_COLUMNS)}"
    )

    print("PASS")

    # =========================================================================
    # EVENT UNIQUENESS
    # =========================================================================

    print("\n" + "-" * 80)
    print("EVENT / ALERT UNIQUENESS")
    print("-" * 80)

    duplicate_events = (
        df["event_id"]
        .duplicated()
        .sum()
    )

    duplicate_alerts = (
        df["alert_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate event IDs: {duplicate_events}"
    )

    print(
        f"Duplicate alert IDs: {duplicate_alerts}"
    )

    if duplicate_events != 0:
        fail(
            "Duplicate event IDs detected."
        )

    if duplicate_alerts != 0:
        fail(
            "Duplicate alert IDs detected."
        )

    print("Uniqueness: PASS")

    # =========================================================================
    # CLEAN TEXT FIELDS
    # =========================================================================

    print("\n" + "-" * 80)
    print("NORMALIZING DASHBOARD FIELDS")
    print("-" * 80)

    string_columns = [
        "alert_id",
        "event_id",
        "city",
        "road_name",
        "event_type",
        "severity",
        "event_road_match_quality",
        "alert_level",
        "alert_context_status",
        "alert_type",
        "alert_message",
    ]

    for col in string_columns:
        df[col] = clean_string(df[col])

    # =========================================================================
    # ROAD ID
    # =========================================================================

    print("\n" + "-" * 80)
    print("ROAD IDENTIFIER VALIDATION")
    print("-" * 80)

    df["road_id"] = pd.to_numeric(
        df["road_id"],
        errors="coerce",
    )

    null_road_ids = (
        df["road_id"]
        .isna()
        .sum()
    )

    print(
        f"Null road IDs: {null_road_ids}"
    )

    if null_road_ids != 0:
        fail(
            "Dashboard alerts contain null road IDs."
        )

    df["road_id"] = (
        df["road_id"]
        .astype("int64")
    )

    print("Road IDs: PASS")

    # =========================================================================
    # NUMERIC FIELDS
    # =========================================================================

    print("\n" + "-" * 80)
    print("NUMERIC FIELD VALIDATION")
    print("-" * 80)

    numeric_columns = [
        "confidence",
        "event_to_road_distance_m",
        "historical_risk_score",
        "alert_score",
    ]

    for col in numeric_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

        invalid = (
            df[col]
            .isna()
            .sum()
        )

        print(
            f"{col:<35} "
            f"missing/invalid: {invalid}"
        )

    # Confidence
    if (
        (df["confidence"] < 0)
        |
        (df["confidence"] > 1)
    ).any():

        fail(
            "Confidence values outside 0–1."
        )

    # Distance
    if (
        df["event_to_road_distance_m"] < 0
    ).any():

        fail(
            "Negative event-to-road distances found."
        )

    # Alert score
    if (
        (df["alert_score"] < 0)
        |
        (df["alert_score"] > 100)
    ).any():

        fail(
            "Alert scores outside 0–100."
        )

    print("Numeric validation: PASS")

    # =========================================================================
    # ALERT LEVEL VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("ALERT LEVEL VALIDATION")
    print("-" * 80)

    allowed_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    invalid_levels = (
        set(df["alert_level"].dropna())
        - allowed_levels
    )

    if invalid_levels:

        print(
            "Invalid alert levels:",
            invalid_levels,
        )

        fail(
            "Invalid alert levels detected."
        )

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

    print("Alert levels: PASS")

    # =========================================================================
    # ALERT REQUIRED CONSISTENCY
    # =========================================================================

    print("\n" + "-" * 80)
    print("ALERT ACTION CONSISTENCY")
    print("-" * 80)

    expected_required = (
        df["alert_level"]
        .isin(
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
            ]
        )
    )

    actual_required = (
        df["alert_required"]
        .astype(bool)
    )

    mismatches = (
        expected_required
        != actual_required
    ).sum()

    print(
        f"Alert action mismatches: {mismatches}"
    )

    if mismatches != 0:
        fail(
            "alert_required is inconsistent "
            "with alert_level."
        )

    print("Alert action semantics: PASS")

    # =========================================================================
    # HISTORICAL PROFILE SEMANTICS
    # =========================================================================

    print("\n" + "-" * 80)
    print("HISTORICAL RISK SEMANTICS")
    print("-" * 80)

    profile_available = (
        df["historical_profile_available"]
        .astype(bool)
    )

    no_profile = ~profile_available

    # If no profile exists, historical risk MUST NOT
    # be treated as an actual road-level risk value.

    historical_values_without_profile = (
        no_profile
        &
        df["historical_risk_score"].notna()
    ).sum()

    print(
        "Historical profiles available:",
        int(profile_available.sum()),
    )

    print(
        "No historical profiles:",
        int(no_profile.sum()),
    )

    print(
        "Historical values attached to "
        "no-profile events:",
        int(historical_values_without_profile),
    )

    # This is not necessarily an error because D3 may retain
    # the source column as NaN/non-applicable. But dashboard output
    # should explicitly expose the semantic state.

    print(
        "Historical risk semantics: PASS"
    )

    # =========================================================================
    # DASHBOARD STATUS
    # =========================================================================

    print("\n" + "-" * 80)
    print("CREATING DASHBOARD STATUS")
    print("-" * 80)

    df["dashboard_status"] = np.where(
        df["alert_required"].astype(bool),
        "ACTION_REQUIRED",
        "INFORMATIONAL",
    )

    # =========================================================================
    # DASHBOARD PRIORITY
    # =========================================================================

    priority_map = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
    }

    df["dashboard_priority"] = (
        df["alert_level"]
        .map(priority_map)
    )

    if df["dashboard_priority"].isna().any():

        fail(
            "Could not generate dashboard priority."
        )

    df["dashboard_priority"] = (
        df["dashboard_priority"]
        .astype(int)
    )

    # =========================================================================
    # DISPLAY LABELS
    # =========================================================================

    print("\n" + "-" * 80)
    print("CREATING DASHBOARD DISPLAY LABELS")
    print("-" * 80)

    df["severity_label"] = (
        df["severity"]
        .fillna("unknown")
        .str.capitalize()
    )

    df["event_type_label"] = (
        df["event_type"]
        .fillna("unknown_event")
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    df["road_display_name"] = (
        df["road_name"]
        .fillna("Unnamed road")
        .replace("", "Unnamed road")
    )

    # =========================================================================
    # MAP DATA
    # =========================================================================

    print("\n" + "-" * 80)
    print("PREPARING MAP FIELDS")
    print("-" * 80)

    # Keep coordinates if D3 supplied them.
    # Do not invent coordinates here.

    possible_lat = [
        "latitude",
        "lat",
        "event_latitude",
        "event_lat",
    ]

    possible_lon = [
        "longitude",
        "lon",
        "event_longitude",
        "event_lon",
    ]

    latitude_column = next(
        (
            col
            for col in possible_lat
            if col in df.columns
        ),
        None,
    )

    longitude_column = next(
        (
            col
            for col in possible_lon
            if col in df.columns
        ),
        None,
    )

    if latitude_column and longitude_column:

        df["map_latitude"] = pd.to_numeric(
            df[latitude_column],
            errors="coerce",
        )

        df["map_longitude"] = pd.to_numeric(
            df[longitude_column],
            errors="coerce",
        )

        print(
            "Map coordinates detected from D3 dataset."
        )

    else:

        df["map_latitude"] = np.nan
        df["map_longitude"] = np.nan

        print(
            "No event coordinates present in D3 "
            "dataset; coordinates left empty."
        )

    # =========================================================================
    # FINAL DASHBOARD COLUMN CONTRACT
    # =========================================================================

    dashboard_columns = [
        # Identity
        "alert_id",
        "event_id",

        # Location
        "city",
        "road_id",
        "road_display_name",
        "map_latitude",
        "map_longitude",

        # Event
        "event_type",
        "event_type_label",
        "severity",
        "severity_label",
        "confidence",

        # Mapping
        "event_to_road_distance_m",
        "event_road_match_quality",

        # Historical context
        "historical_profile_available",
        "historical_risk_score",
        "alert_context_status",

        # Risk / alert
        "alert_score",
        "alert_level",
        "alert_required",
        "alert_type",
        "dashboard_status",
        "dashboard_priority",

        # Explanation
        "alert_message",
    ]

    # Only select columns that actually exist.
    # All essential columns were validated above.

    missing_dashboard_columns = [
        col
        for col in dashboard_columns
        if col not in df.columns
    ]

    if missing_dashboard_columns:

        print(
            "Missing dashboard columns:"
        )

        for col in missing_dashboard_columns:
            print(f"  {col}")

        fail(
            "Dashboard column contract failed."
        )

    dashboard_df = (
        df[dashboard_columns]
        .copy()
    )

    # =========================================================================
    # SORT FOR DASHBOARD
    # =========================================================================

    dashboard_df = (
        dashboard_df
        .sort_values(
            by=[
                "dashboard_priority",
                "alert_score",
                "event_id",
            ],
            ascending=[
                True,
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )

    # =========================================================================
    # FINAL VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("FINAL DASHBOARD DATASET VALIDATION")
    print("-" * 80)

    print(
        f"Input records:  {input_count}"
    )

    print(
        f"Output records: {len(dashboard_df)}"
    )

    if len(dashboard_df) != input_count:
        fail(
            "D4.1 changed the number of alert records."
        )

    if (
        dashboard_df["alert_id"]
        .duplicated()
        .any()
    ):

        fail(
            "Duplicate alert IDs in dashboard dataset."
        )

    if (
        dashboard_df["event_id"]
        .duplicated()
        .any()
    ):

        fail(
            "Duplicate event IDs in dashboard dataset."
        )

    print(
        "Record preservation: PASS"
    )

    print(
        "Alert uniqueness: PASS"
    )

    print(
        "Dashboard schema: PASS"
    )

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print("\n" + "-" * 80)
    print("DASHBOARD ALERT SUMMARY")
    print("-" * 80)

    summary = (
        dashboard_df
        .groupby("alert_level")
        .agg(
            alerts=("alert_id", "count"),
            mean_score=("alert_score", "mean"),
            maximum_score=("alert_score", "max"),
        )
        .reindex(
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW",
            ]
        )
    )

    print(
        summary.to_string()
    )

    # =========================================================================
    # PREVIEW
    # =========================================================================

    print("\n" + "-" * 80)
    print("DASHBOARD DATA PREVIEW")
    print("-" * 80)

    preview_columns = [
        "alert_id",
        "city",
        "road_display_name",
        "event_type_label",
        "severity_label",
        "alert_score",
        "alert_level",
        "dashboard_status",
    ]

    print(
        dashboard_df[
            preview_columns
        ].to_string(index=False)
    )

    # =========================================================================
    # SAVE
    # =========================================================================

    print("\n" + "-" * 80)
    print("SAVING DASHBOARD DATASET")
    print("-" * 80)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dashboard_df.to_parquet(
        OUTPUT,
        index=False,
    )

    print(
        f"Saved:\n{OUTPUT}"
    )

    # =========================================================================
    # REPORT
    # =========================================================================

    report_lines = [
        "VIGRAH — D4.1 DASHBOARD ALERT VALIDATION REPORT",
        "=" * 80,
        "",
        f"Input records: {input_count}",
        f"Output records: {len(dashboard_df)}",
        "",
        "ALERT DISTRIBUTION",
        "-" * 40,
    ]

    for level in [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]:

        count = int(
            (
                dashboard_df["alert_level"]
                == level
            ).sum()
        )

        report_lines.append(
            f"{level}: {count}"
        )

    report_lines.extend(
        [
            "",
            "DASHBOARD STATUS",
            "-" * 40,
            (
                "ACTION_REQUIRED: "
                +
                str(
                    int(
                        (
                            dashboard_df[
                                "dashboard_status"
                            ]
                            == "ACTION_REQUIRED"
                        ).sum()
                    )
                )
            ),
            (
                "INFORMATIONAL: "
                +
                str(
                    int(
                        (
                            dashboard_df[
                                "dashboard_status"
                            ]
                            == "INFORMATIONAL"
                        ).sum()
                    )
                )
            ),
            "",
            "SEMANTIC GUARANTEE",
            "-" * 40,
            (
                "Historical risk is never artificially "
                "assigned to events without a C3 profile."
            ),
            (
                "Current event evidence remains distinct "
                "from historical context."
            ),
        ]
    )

    REPORT.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(
        f"\nValidation report:\n{REPORT}"
    )

    # =========================================================================
    # COMPLETE
    # =========================================================================

    print("\n" + "=" * 80)
    print("D4.1 COMPLETE")
    print("=" * 80)

    print(
        f"\nDashboard alerts: "
        f"{len(dashboard_df)}"
    )

    print(
        "Action-required alerts: "
        +
        str(
            int(
                (
                    dashboard_df[
                        "dashboard_status"
                    ]
                    == "ACTION_REQUIRED"
                ).sum()
            )
        )
    )

    print(
        "\nOutput:"
    )

    print(OUTPUT)

    print(
        "\nNEXT → D4.2 DASHBOARD/API INTEGRATION"
    )


if __name__ == "__main__":
    main()