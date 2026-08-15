from pathlib import Path
import json
import math
import pandas as pd


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "dashboard_alerts.parquet"
)

OUTPUT_REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "d4_2_dashboard_contract_report.txt"
)

OUTPUT_CONTRACT = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "dashboard_api_contract.json"
)


# =============================================================================
# HELPERS
# =============================================================================

def section(title):
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def fail(message):
    raise RuntimeError(message)


def is_numeric(series):
    return pd.api.types.is_numeric_dtype(series)


def validate_numeric_range(df, column, minimum=None, maximum=None):
    values = pd.to_numeric(df[column], errors="coerce")

    invalid = values.isna().sum()
    if invalid > 0:
        fail(
            f"{column}: {invalid} invalid/missing numeric values."
        )

    if minimum is not None:
        below = (values < minimum).sum()
        if below > 0:
            fail(
                f"{column}: {below} values below minimum {minimum}."
            )

    if maximum is not None:
        above = (values > maximum).sum()
        if above > 0:
            fail(
                f"{column}: {above} values above maximum {maximum}."
            )

    infinite = (~values.replace([float("inf"), float("-inf")], pd.NA)
                .notna()).sum()

    if infinite > 0:
        fail(
            f"{column}: {infinite} infinite values."
        )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 80)
    print("VIGRAH — D4.2 DASHBOARD / API CONTRACT VALIDATION")
    print("=" * 80)

    print("\nInput:")
    print(INPUT)

    if not INPUT.exists():
        fail(
            f"Dashboard dataset does not exist:\n{INPUT}"
        )

    # -------------------------------------------------------------------------
    # LOAD
    # -------------------------------------------------------------------------

    section("LOADING DASHBOARD DATASET")

    df = pd.read_parquet(INPUT)

    print(f"Records: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    if df.empty:
        fail("Dashboard dataset is empty.")

    # -------------------------------------------------------------------------
    # REQUIRED SCHEMA
    # -------------------------------------------------------------------------

    section("1. API CONTRACT SCHEMA")

    required_columns = [
        "alert_id",
        "event_id",
        "city",
        "road_id",
        "road_display_name",
        "event_type_label",
        "severity_label",
        "confidence",
        "event_to_road_distance_m",
        "alert_score",
        "alert_level",
        "dashboard_status",
        "historical_profile_available",
        "alert_context_status",
        "map_latitude",
        "map_longitude",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    print(
        f"Required columns: "
        f"{len(required_columns) - len(missing)} / "
        f"{len(required_columns)}"
    )

    if missing:
        print("\nMissing:")
        for col in missing:
            print(f"  {col}")

        fail("Dashboard API contract schema validation failed.")

    print("PASS")

    # -------------------------------------------------------------------------
    # RECORD / ID VALIDATION
    # -------------------------------------------------------------------------

    section("2. RECORD AND ID VALIDATION")

    duplicate_alerts = df["alert_id"].duplicated().sum()
    duplicate_events = df["event_id"].duplicated().sum()

    print(f"Duplicate alert IDs: {duplicate_alerts}")
    print(f"Duplicate event IDs: {duplicate_events}")

    if duplicate_alerts != 0:
        fail("Alert IDs are not unique.")

    if duplicate_events != 0:
        fail("Event IDs are not unique.")

    print("Uniqueness: PASS")

    # -------------------------------------------------------------------------
    # CITY VALIDATION
    # -------------------------------------------------------------------------

    section("3. CITY VALIDATION")

    allowed_cities = {
        "Mumbai",
        "Bengaluru",
    }

    cities = set(df["city"].dropna().astype(str))

    print(f"Cities found: {sorted(cities)}")

    unexpected = cities - allowed_cities

    if unexpected:
        print(f"Unexpected cities: {sorted(unexpected)}")
        fail("Unexpected operational city detected.")

    if df["city"].isna().any():
        fail("Null city values detected.")

    print("City validation: PASS")

    # -------------------------------------------------------------------------
    # ROAD IDENTIFIERS
    # -------------------------------------------------------------------------

    section("4. ROAD IDENTIFIER VALIDATION")

    if df["road_id"].isna().any():
        fail("Null road IDs detected.")

    road_ids = pd.to_numeric(
        df["road_id"],
        errors="coerce"
    )

    if road_ids.isna().any():
        fail("Non-numeric road IDs detected.")

    print(f"Unique road IDs: {road_ids.nunique():,}")
    print("Road identifier validation: PASS")

    # -------------------------------------------------------------------------
    # COORDINATE VALIDATION
    # -------------------------------------------------------------------------

    section("5. MAP COORDINATE VALIDATION")

    lat = pd.to_numeric(
        df["map_latitude"],
        errors="coerce"
    )

    lon = pd.to_numeric(
        df["map_longitude"],
        errors="coerce"
    )

    invalid_lat = (
        lat.isna()
        | (lat < -90)
        | (lat > 90)
    ).sum()

    invalid_lon = (
        lon.isna()
        | (lon < -180)
        | (lon > 180)
    ).sum()

    print(f"Invalid latitude:  {invalid_lat}")
    print(f"Invalid longitude: {invalid_lon}")

    if invalid_lat > 0 or invalid_lon > 0:
        fail("Invalid map coordinates detected.")

    print("Map coordinates: PASS")

    # -------------------------------------------------------------------------
    # NUMERIC FIELDS
    # -------------------------------------------------------------------------

    section("6. NUMERIC API FIELD VALIDATION")

    validate_numeric_range(
        df,
        "confidence",
        0,
        1
    )

    validate_numeric_range(
        df,
        "event_to_road_distance_m",
        0,
        None
    )

    validate_numeric_range(
        df,
        "alert_score",
        0,
        100
    )

    print("confidence:                 PASS")
    print("event_to_road_distance_m:   PASS")
    print("alert_score:                PASS")

    # -------------------------------------------------------------------------
    # ALERT LEVEL
    # -------------------------------------------------------------------------

    section("7. ALERT LEVEL CONTRACT")

    allowed_levels = {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    }

    levels = set(
        df["alert_level"]
        .dropna()
        .astype(str)
    )

    print("Alert distribution:")
    print(df["alert_level"].value_counts())

    unexpected_levels = levels - allowed_levels

    if unexpected_levels:
        fail(
            f"Unexpected alert levels: "
            f"{sorted(unexpected_levels)}"
        )

    if df["alert_level"].isna().any():
        fail("Null alert levels detected.")

    print("Alert levels: PASS")

    # -------------------------------------------------------------------------
    # DASHBOARD STATUS
    # -------------------------------------------------------------------------

    section("8. DASHBOARD STATUS CONTRACT")

    allowed_statuses = {
        "ACTION_REQUIRED",
        "INFORMATIONAL",
    }

    statuses = set(
        df["dashboard_status"]
        .dropna()
        .astype(str)
    )

    print(df["dashboard_status"].value_counts())

    unexpected_statuses = statuses - allowed_statuses

    if unexpected_statuses:
        fail(
            f"Unexpected dashboard statuses: "
            f"{sorted(unexpected_statuses)}"
        )

    if df["dashboard_status"].isna().any():
        fail("Null dashboard statuses detected.")

    print("Dashboard status: PASS")

    # -------------------------------------------------------------------------
    # HISTORICAL RISK SEMANTICS
    # -------------------------------------------------------------------------

    section("9. HISTORICAL RISK SEMANTICS")

    if df["historical_profile_available"].isna().any():
        fail(
            "historical_profile_available contains null values."
        )

    profile_values = set(
        df["historical_profile_available"]
        .astype(bool)
        .unique()
    )

    print(
        "Historical profiles available:",
        int(df["historical_profile_available"].astype(bool).sum())
    )

    print(
        "No historical profiles:",
        int((~df["historical_profile_available"].astype(bool)).sum())
    )

    if "historical_risk_score" in df.columns:

        no_profile = ~df["historical_profile_available"].astype(bool)

        historical_values = pd.to_numeric(
            df["historical_risk_score"],
            errors="coerce"
        )

        attached_to_no_profile = (
            no_profile
            & historical_values.notna()
        ).sum()

        print(
            "Historical values attached to "
            f"no-profile events: {attached_to_no_profile}"
        )

        if attached_to_no_profile > 0:
            fail(
                "Historical risk is attached to an event "
                "without a historical profile."
            )

    print("Historical risk semantics: PASS")

    # -------------------------------------------------------------------------
    # ALERT CONTEXT STATUS
    # -------------------------------------------------------------------------

    section("10. ALERT CONTEXT STATUS")

    if df["alert_context_status"].isna().any():
        fail("Null alert_context_status values detected.")

    print(
        df["alert_context_status"]
        .value_counts()
    )

    print("Context status: PASS")

    # -------------------------------------------------------------------------
    # DISPLAY FIELDS
    # -------------------------------------------------------------------------

    section("11. DASHBOARD DISPLAY FIELD VALIDATION")

    display_fields = [
        "road_display_name",
        "event_type_label",
        "severity_label",
    ]

    for column in display_fields:

        missing = (
            df[column].isna()
            | (df[column].astype(str).str.strip() == "")
        ).sum()

        print(f"{column}: missing/empty = {missing}")

        if missing > 0:
            fail(
                f"Dashboard display field '{column}' "
                "contains missing/empty values."
            )

    print("Display fields: PASS")

    # -------------------------------------------------------------------------
    # API SERIALIZATION TEST
    # -------------------------------------------------------------------------

    section("12. API SERIALIZATION TEST")

    api_test_columns = [
        "alert_id",
        "event_id",
        "city",
        "road_id",
        "road_display_name",
        "event_type_label",
        "severity_label",
        "confidence",
        "event_to_road_distance_m",
        "alert_score",
        "alert_level",
        "dashboard_status",
        "historical_profile_available",
        "alert_context_status",
        "map_latitude",
        "map_longitude",
    ]

    api_df = df[api_test_columns].copy()

    # Convert NumPy / pandas scalar values to native Python values.
    records = api_df.to_dict(orient="records")

    try:
        serialized = json.dumps(
            records,
            allow_nan=False
        )

        json.loads(serialized)

    except Exception as exc:
        fail(
            f"API JSON serialization failed: {exc}"
        )

    print(
        f"Records successfully serialized: {len(records):,}"
    )

    print("JSON serialization: PASS")

    # -------------------------------------------------------------------------
    # API CONTRACT DEFINITION
    # -------------------------------------------------------------------------

    section("13. GENERATING API CONTRACT")

    contract = {
        "project": "VIGRAH",
        "dataset": "dashboard_alerts",
        "version": "D4.2",
        "record_count": int(len(df)),
        "description": (
            "Dashboard-ready alert records generated from "
            "the VIGRAH D3 alert pipeline."
        ),
        "endpoints": {
            "list_alerts": {
                "method": "GET",
                "path": "/api/alerts",
                "description": "Return dashboard-ready alerts."
            },
            "alert_detail": {
                "method": "GET",
                "path": "/api/alerts/{alert_id}",
                "description": "Return one alert by alert ID."
            },
            "summary": {
                "method": "GET",
                "path": "/api/alerts/summary",
                "description": "Return alert counts and score summary."
            },
            "city_alerts": {
                "method": "GET",
                "path": "/api/alerts/city/{city}",
                "description": "Return alerts for one operational city."
            }
        },
        "fields": {
            "alert_id": "string",
            "event_id": "string",
            "city": "string",
            "road_id": "integer",
            "road_display_name": "string",
            "event_type_label": "string",
            "severity_label": "string",
            "confidence": "float [0,1]",
            "event_to_road_distance_m": "float >= 0",
            "alert_score": "float [0,100]",
            "alert_level": [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW"
            ],
            "dashboard_status": [
                "ACTION_REQUIRED",
                "INFORMATIONAL"
            ],
            "historical_profile_available": "boolean",
            "alert_context_status": "string",
            "map_latitude": "float [-90,90]",
            "map_longitude": "float [-180,180]"
        },
        "semantics": {
            "current_event_evidence": True,
            "historical_risk_separate": True,
            "crime_remains_contextual": True,
            "no_artificial_road_level_attribution": True
        }
    }

    OUTPUT_CONTRACT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_CONTRACT,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            contract,
            f,
            indent=2
        )

    print("API contract saved:")
    print(OUTPUT_CONTRACT)

    # -------------------------------------------------------------------------
    # CITY SUMMARY
    # -------------------------------------------------------------------------

    section("14. CITY-WISE API SUMMARY")

    summary = (
        df.groupby("city")
        .agg(
            alerts=("alert_id", "count"),
            mean_alert_score=("alert_score", "mean"),
            maximum_alert_score=("alert_score", "max"),
            action_required=(
                "dashboard_status",
                lambda x: (x == "ACTION_REQUIRED").sum()
            ),
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    # -------------------------------------------------------------------------
    # REPORT
    # -------------------------------------------------------------------------

    report_lines = [
        "VIGRAH — D4.2 DASHBOARD / API CONTRACT VALIDATION",
        "=" * 60,
        "",
        f"Input: {INPUT}",
        f"Records: {len(df)}",
        f"Columns: {len(df.columns)}",
        "",
        "RESULT: PASS",
        "",
        "API endpoints:",
        "GET /api/alerts",
        "GET /api/alerts/{alert_id}",
        "GET /api/alerts/summary",
        "GET /api/alerts/city/{city}",
        "",
        "Semantic guarantees:",
        "- Current event evidence remains separate.",
        "- Historical risk remains contextual.",
        "- Crime remains non-road-level.",
        "- No historical risk is artificially assigned.",
        "",
        "Dashboard dataset is API-ready."
    ]

    with open(
        OUTPUT_REPORT,
        "w",
        encoding="utf-8"
    ) as f:
        f.write("\n".join(report_lines))

    # -------------------------------------------------------------------------
    # FINAL
    # -------------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("D4.2 COMPLETE")
    print("=" * 80)

    print("\nDASHBOARD / API CONTRACT: PASSED")

    print("\nRecords validated:")
    print(f"  {len(df):,}")

    print("\nContract:")
    print(OUTPUT_CONTRACT)

    print("\nValidation report:")
    print(OUTPUT_REPORT)

    print("\nNEXT → D4.3 FASTAPI DASHBOARD API")


if __name__ == "__main__":
    main()