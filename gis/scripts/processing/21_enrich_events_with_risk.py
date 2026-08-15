from pathlib import Path

import pandas as pd


# =============================================================================
# VIGRAH — D2 EVENT → ROAD → RISK ENRICHMENT
# =============================================================================
#
# Purpose:
#   Enrich Layer-3 events mapped to OSM roads with the historical/ML risk
#   profile available for that road.
#
# Important semantic rule:
#   D1 uses the FULL OSM road network.
#   C3 currently contains only roads represented in the CCTV-derived
#   road-level risk dataset.
#
# Therefore:
#
#   Event → OSM road → C3 profile       = matched
#   Event → OSM road → no C3 profile    = no_historical_profile
#
# Events are NEVER dropped merely because a C3 risk profile is unavailable.
#
# This script does NOT:
#   - invent risk values
#   - assign city/state crime numbers to roads
#   - create historical accident counts for individual roads
#   - modify source datasets
#
# =============================================================================


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

EVENT_ROAD_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "event_road_mapping.parquet"
)

RISK_FILE = (
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

OUTPUT_FILE = (
    OUTPUT_DIR
    / "event_risk_enrichment.parquet"
)


# =============================================================================
# REQUIRED COLUMNS
# =============================================================================

EVENT_COLUMNS = [
    "event_id",
    "timestamp",
    "latitude",
    "longitude",
    "event_type",
    "severity",
    "confidence",
    "city",
    "road_id",
    "road_name",
    "highway",
    "event_to_road_distance_m",
    "event_road_match_quality",
]


RISK_COLUMNS = [
    "city",
    "road_id",
    "road_name",
    "highway",
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "risk_level",
]


# =============================================================================
# HELPER
# =============================================================================

def fail(message):
    print("\nERROR:")
    print(message)
    raise RuntimeError(message)


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 80)
    print("VIGRAH — D2 EVENT → ROAD → RISK ENRICHMENT")
    print("=" * 80)

    # =========================================================================
    # LOAD D1 EVENT → ROAD DATA
    # =========================================================================

    print("\n" + "-" * 80)
    print("LOADING D1 EVENT → ROAD DATA")
    print("-" * 80)

    print("Input:")
    print(EVENT_ROAD_FILE)

    if not EVENT_ROAD_FILE.exists():
        fail(
            f"D1 dataset does not exist:\n{EVENT_ROAD_FILE}"
        )

    events = pd.read_parquet(EVENT_ROAD_FILE)

    print(
        f"Event-road records: {len(events):,}"
    )

    missing = [
        column
        for column in EVENT_COLUMNS
        if column not in events.columns
    ]

    if missing:
        fail(
            "D1 schema validation failed.\n"
            f"Missing columns: {missing}"
        )

    print("D1 schema: PASS")

    # =========================================================================
    # LOAD C3 RISK DATASET
    # =========================================================================

    print("\n" + "-" * 80)
    print("LOADING C3 RISK DATASET")
    print("-" * 80)

    print("Input:")
    print(RISK_FILE)

    if not RISK_FILE.exists():
        fail(
            f"Risk dataset does not exist:\n{RISK_FILE}"
        )

    risk = pd.read_parquet(RISK_FILE)

    print(
        f"Road risk records: {len(risk):,}"
    )

    missing = [
        column
        for column in RISK_COLUMNS
        if column not in risk.columns
    ]

    if missing:
        fail(
            "Risk dataset schema validation failed.\n"
            f"Missing columns: {missing}"
        )

    print("Risk schema: PASS")

    # =========================================================================
    # BASIC EVENT VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("BASIC EVENT VALIDATION")
    print("-" * 80)

    event_count = len(events)

    unique_events = (
        events["event_id"]
        .nunique()
    )

    print(
        f"Input event rows:   {event_count:,}"
    )

    print(
        f"Unique event IDs:    {unique_events:,}"
    )

    if event_count != unique_events:
        fail(
            "Duplicate event IDs detected in D1 output."
        )

    print("Event uniqueness: PASS")

    # =========================================================================
    # ROAD ID NORMALIZATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("NORMALIZING ROAD IDENTIFIERS")
    print("-" * 80)

    events["road_id"] = (
        events["road_id"]
        .astype("string")
        .str.strip()
    )

    risk["road_id"] = (
        risk["road_id"]
        .astype("string")
        .str.strip()
    )

    print("Road ID normalization: PASS")

    # =========================================================================
    # CHECK NULL ROAD IDS
    # =========================================================================

    print("\n" + "-" * 80)
    print("ROAD ID VALIDATION")
    print("-" * 80)

    null_event_roads = (
        events["road_id"]
        .isna()
        .sum()
    )

    null_risk_roads = (
        risk["road_id"]
        .isna()
        .sum()
    )

    print(
        f"Null event road IDs: {null_event_roads}"
    )

    print(
        f"Null risk road IDs:  {null_risk_roads}"
    )

    if null_event_roads > 0:
        fail(
            "D1 contains events without a road ID."
        )

    if null_risk_roads > 0:
        fail(
            "C3 risk dataset contains null road IDs."
        )

    print("Road IDs: PASS")

    # =========================================================================
    # RISK ROAD UNIQUENESS
    # =========================================================================

    print("\n" + "-" * 80)
    print("VALIDATING ROAD RISK UNIQUENESS")
    print("-" * 80)

    duplicate_risk_roads = (
        risk["road_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate road IDs: {duplicate_risk_roads:,}"
    )

    if duplicate_risk_roads > 0:

        duplicate_rows = risk[
            risk["road_id"]
            .duplicated(keep=False)
        ]

        print("\nDuplicate examples:")

        print(
            duplicate_rows[
                [
                    "city",
                    "road_id",
                    "road_name",
                    "highway",
                ]
            ]
            .head(20)
            .to_string(index=False)
        )

        fail(
            "Risk dataset contains duplicate road IDs."
        )

    print("Road uniqueness: PASS")

    # =========================================================================
    # EVENT ROAD COVERAGE
    # =========================================================================

    print("\n" + "-" * 80)
    print("CHECKING EVENT ROAD COVERAGE")
    print("-" * 80)

    risk_road_ids = set(
        risk["road_id"]
        .dropna()
        .tolist()
    )

    event_road_ids = set(
        events["road_id"]
        .dropna()
        .tolist()
    )

    missing_roads = (
        event_road_ids
        - risk_road_ids
    )

    print(
        f"Unique event roads: {len(event_road_ids):,}"
    )

    print(
        f"Risk roads:         {len(risk_road_ids):,}"
    )

    print(
        "Event roads missing from C3 risk dataset: "
        f"{len(missing_roads):,}"
    )

    if missing_roads:

        print("\nNOTE:")
        print(
            "Some event roads do not have a C3 historical "
            "risk profile."
        )

        print(
            "This is expected because C3 currently contains "
            "CCTV-observed roads only."
        )

        print(
            "\nThese events WILL be preserved."
        )

        print("\nMissing road IDs:")

        for road_id in sorted(
            list(missing_roads)
        )[:50]:

            print(
                f"  {road_id}"
            )

    else:

        print(
            "All event roads have C3 risk profiles."
        )

    print("\nRoad coverage check: PASS")

    # =========================================================================
    # SELECT RISK ATTRIBUTES
    # =========================================================================

    print("\n" + "-" * 80)
    print("SELECTING RISK ATTRIBUTES")
    print("-" * 80)

    risk_lookup_columns = [
        "road_id",
        "baseline_risk_score",
        "confidence_adjusted_risk_score",
        "risk_level",
    ]

    risk_lookup = risk[
        risk_lookup_columns
    ].copy()

    print("Risk attributes attached:")

    for column in risk_lookup_columns[1:]:
        print(
            f"  {column}"
        )

    # =========================================================================
    # EVENT → RISK MERGE
    # =========================================================================

    print("\n" + "-" * 80)
    print("ATTACHING ROAD RISK")
    print("-" * 80)

    enriched = events.merge(
        risk_lookup,
        on="road_id",
        how="left",
        validate="many_to_one",
        sort=False,
    )

    print(
        f"Records before merge: {len(events):,}"
    )

    print(
        f"Records after merge:  {len(enriched):,}"
    )

    # =========================================================================
    # RECORD PRESERVATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("RECORD PRESERVATION")
    print("-" * 80)

    if len(enriched) != event_count:
        fail(
            "Event record count changed during risk enrichment."
        )

    unique_enriched_events = (
        enriched["event_id"]
        .nunique()
    )

    print(
        f"Input events:        {event_count:,}"
    )

    print(
        f"Output rows:         {len(enriched):,}"
    )

    print(
        f"Unique output events:{unique_enriched_events:>10,}"
    )

    if unique_enriched_events != event_count:
        fail(
            "Unique event count changed during enrichment."
        )

    print("Record count preservation: PASS")

    # =========================================================================
    # RISK ENRICHMENT STATUS
    # =========================================================================

    print("\n" + "-" * 80)
    print("RISK ENRICHMENT STATUS")
    print("-" * 80)

    enriched["risk_enrichment_status"] = (
        enriched["baseline_risk_score"]
        .notna()
        .map(
            {
                True: "matched",
                False: "no_historical_profile",
            }
        )
    )

    status_counts = (
        enriched["risk_enrichment_status"]
        .value_counts()
    )

    print(
        status_counts.to_string()
    )

    matched_count = (
        enriched["risk_enrichment_status"]
        .eq("matched")
        .sum()
    )

    no_profile_count = (
        enriched["risk_enrichment_status"]
        .eq("no_historical_profile")
        .sum()
    )

    print(
        f"\nEvents with historical risk: "
        f"{matched_count:,}"
    )

    print(
        f"Events without historical risk: "
        f"{no_profile_count:,}"
    )

    if (
        matched_count
        + no_profile_count
        != event_count
    ):
        fail(
            "Risk enrichment status does not account "
            "for every event."
        )

    print(
        "\nRisk enrichment status: PASS"
    )

    # =========================================================================
    # RISK COMPLETENESS
    # =========================================================================

    print("\n" + "-" * 80)
    print("RISK COMPLETENESS")
    print("-" * 80)

    risk_fields = [
        "baseline_risk_score",
        "confidence_adjusted_risk_score",
        "risk_level",
    ]

    matched_events = enriched[
        enriched["risk_enrichment_status"]
        == "matched"
    ]

    unmatched_events = enriched[
        enriched["risk_enrichment_status"]
        == "no_historical_profile"
    ]

    print(
        f"Matched events:       {len(matched_events):,}"
    )

    print(
        f"No-profile events:    {len(unmatched_events):,}"
    )

    if len(matched_events) > 0:

        missing_counts = (
            matched_events[risk_fields]
            .isna()
            .sum()
        )

        print(
            "\nMissing values among matched events:"
        )

        print(
            missing_counts.to_string()
        )

        if missing_counts.sum() > 0:
            fail(
                "Matched events contain incomplete "
                "risk profiles."
            )

    print(
        "\nRisk completeness: PASS"
    )

    # =========================================================================
    # RISK NUMERIC VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("RISK VALUE VALIDATION")
    print("-" * 80)

    numeric_risk_fields = [
        "baseline_risk_score",
        "confidence_adjusted_risk_score",
    ]

    if len(matched_events) == 0:

        print(
            "No matched historical risk profiles "
            "available for numeric validation."
        )

    else:

        for column in numeric_risk_fields:

            values = pd.to_numeric(
                matched_events[column],
                errors="coerce",
            )

            invalid = (
                values.isna()
                .sum()
            )

            negative = (
                values < 0
            ).sum()

            above_100 = (
                values > 100
            ).sum()

            print(f"\n{column}")

            print(
                f"  Invalid:    {invalid}"
            )

            print(
                f"  Negative:   {negative}"
            )

            print(
                f"  Above 100:  {above_100}"
            )

            print(
                f"  Min:        {values.min():.2f}"
            )

            print(
                f"  Max:        {values.max():.2f}"
            )

            if (
                invalid > 0
                or negative > 0
                or above_100 > 0
            ):
                fail(
                    f"Invalid values detected in "
                    f"{column}."
                )

    print(
        "\nRisk numeric validation: PASS"
    )

    # =========================================================================
    # RISK LEVEL VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("RISK LEVEL VALIDATION")
    print("-" * 80)

    allowed_levels = {
        "LOW",
        "MODERATE",
        "HIGH",
        "CRITICAL",
    }

    if len(matched_events) > 0:

        risk_level_counts = (
            matched_events[
                "risk_level"
            ]
            .value_counts()
        )

        print(
            risk_level_counts.to_string()
        )

        observed_levels = set(
            matched_events[
                "risk_level"
            ]
            .dropna()
            .astype(str)
            .str.upper()
            .unique()
        )

        unexpected_levels = (
            observed_levels
            - allowed_levels
        )

        if unexpected_levels:
            fail(
                "Unexpected risk levels found: "
                f"{unexpected_levels}"
            )

    else:

        print(
            "No matched risk profiles available."
        )

    print(
        "Risk levels: PASS"
    )

    # =========================================================================
    # CITY CONSISTENCY
    # =========================================================================

    print("\n" + "-" * 80)
    print("CITY-WISE ENRICHMENT SUMMARY")
    print("-" * 80)

    city_summary = (
        enriched
        .groupby("city")
        .agg(
            events=(
                "event_id",
                "count",
            ),
            roads=(
                "road_id",
                "nunique",
            ),
            matched_risk_profiles=(
                "risk_enrichment_status",
                lambda x: (
                    x == "matched"
                ).sum(),
            ),
            missing_risk_profiles=(
                "risk_enrichment_status",
                lambda x: (
                    x == "no_historical_profile"
                ).sum(),
            ),
            mean_risk=(
                "confidence_adjusted_risk_score",
                "mean",
            ),
            maximum_risk=(
                "confidence_adjusted_risk_score",
                "max",
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
    # RISK SEMANTICS
    # =========================================================================

    print("\n" + "-" * 80)
    print("SETTING RISK SEMANTICS")
    print("-" * 80)

    enriched[
        "historical_risk_source"
    ] = "VIGRAH_C3"

    enriched[
        "risk_is_historical_context"
    ] = True

    enriched[
        "event_is_current_observation"
    ] = True

    enriched[
        "crime_data_not_road_level"
    ] = True

    print(
        "Historical risk source: VIGRAH_C3"
    )

    print(
        "Historical risk remains contextual: True"
    )

    print(
        "Current event remains separate: True"
    )

    print(
        "Crime data remains non-road-level: True"
    )

    # =========================================================================
    # EVENT → ROAD → RISK SUMMARY
    # =========================================================================

    print("\n" + "-" * 80)
    print("EVENT → ROAD → RISK SUMMARY")
    print("-" * 80)

    summary_columns = [
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
        "risk_level",
    ]

    print(
        enriched[
            summary_columns
        ]
        .to_string(index=False)
    )

    # =========================================================================
    # FINAL DATASET VALIDATION
    # =========================================================================

    print("\n" + "-" * 80)
    print("FINAL DATASET VALIDATION")
    print("-" * 80)

    # Required D2 columns
    required_output_columns = [
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
        "risk_level",
        "historical_risk_source",
        "risk_is_historical_context",
        "event_is_current_observation",
        "crime_data_not_road_level",
    ]

    missing_output_columns = [
        column
        for column in required_output_columns
        if column not in enriched.columns
    ]

    if missing_output_columns:
        fail(
            "Final D2 schema validation failed.\n"
            f"Missing columns: {missing_output_columns}"
        )

    print(
        f"Required columns: "
        f"{len(required_output_columns)} / "
        f"{len(required_output_columns)}"
    )

    print("PASS")

    # =========================================================================
    # SAVE
    # =========================================================================

    print("\n" + "-" * 80)
    print("SAVING D2 DATASET")
    print("-" * 80)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    enriched.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Saved:\n{OUTPUT_FILE}"
    )

    print(
        f"Output size: "
        f"{OUTPUT_FILE.stat().st_size / 1024:.2f} KB"
    )

    # =========================================================================
    # FINAL COMPLETION
    # =========================================================================

    print("\n" + "=" * 80)
    print("D2 COMPLETE")
    print("=" * 80)

    print(
        f"\nEvents processed: "
        f"{event_count:,}"
    )

    print(
        f"Events with C3 risk: "
        f"{matched_count:,}"
    )

    print(
        f"Events without C3 risk: "
        f"{no_profile_count:,}"
    )

    print(
        f"Unique roads involved: "
        f"{enriched['road_id'].nunique():,}"
    )

    print(
        "\nEvent → Road → Historical Risk: PASS"
    )

    print(
        "\nImportant:"
    )

    print(
        "Events without C3 profiles were preserved "
        "and marked as 'no_historical_profile'."
    )

    print(
        "No historical risk was artificially assigned."
    )

    print(
        "\nOutput:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nNEXT → D3 ALERT GENERATION"
    )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()