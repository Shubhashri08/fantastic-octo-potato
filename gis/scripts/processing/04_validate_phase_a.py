from pathlib import Path
import geopandas as gpd
import pandas as pd


# ============================================================
# VIGRAH — PHASE A / A4.3
# Final Phase A Validation
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data"
    / "processed"
    / "features"
    / "cctv_road_mapping.parquet"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

SUSPICIOUS_OUTPUT = (
    OUTPUT_DIR
    / "cctv_road_review.parquet"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "phase_a_validation_report.txt"
)


EXPECTED_COUNTS = {
    "Mumbai": 10,
    "Bengaluru": 1541,
}


print("=" * 80)
print("VIGRAH — PHASE A VALIDATION")
print("=" * 80)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

if not INPUT.exists():
    raise FileNotFoundError(
        f"Input not found:\n{INPUT}"
    )

print("\nLoading:")
print(INPUT)

gdf = gpd.read_parquet(INPUT)

print(
    f"\nRecords loaded: {len(gdf):,}"
)


# ------------------------------------------------------------
# 1. Total record check
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("1. RECORD COUNTS")
print("-" * 80)

total = len(gdf)

print(
    f"Expected: 1551"
)

print(
    f"Actual:   {total}"
)

if total != 1551:

    raise ValueError(
        f"Expected 1551 records, got {total}."
    )

print("PASS")


# ------------------------------------------------------------
# 2. City counts
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("2. CITY COUNTS")
print("-" * 80)

city_counts = (
    gdf["city"]
    .value_counts()
)

for city, expected in EXPECTED_COUNTS.items():

    actual = int(
        city_counts.get(city, 0)
    )

    print(
        f"{city}: "
        f"{actual} / {expected}"
    )

    if actual != expected:

        raise ValueError(
            f"{city} count mismatch."
        )

print("PASS")


# ------------------------------------------------------------
# 3. Unique camera IDs
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("3. CAMERA UNIQUENESS")
print("-" * 80)

unique_cameras = (
    gdf["camera_id"]
    .nunique()
)

print(
    f"Unique cameras: "
    f"{unique_cameras:,}"
)

if unique_cameras != 1551:

    raise ValueError(
        "Camera IDs are not unique."
    )

duplicate_rows = (
    gdf["camera_id"]
    .duplicated()
    .sum()
)

print(
    f"Duplicate camera rows: "
    f"{duplicate_rows}"
)

if duplicate_rows != 0:

    raise ValueError(
        "Duplicate camera mappings detected."
    )

print("PASS")


# ------------------------------------------------------------
# 4. Road matching
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("4. ROAD MATCHING")
print("-" * 80)

matched = (
    gdf["road_id"]
    .notna()
)

matched_count = int(
    matched.sum()
)

unmatched_count = int(
    (~matched).sum()
)

print(
    f"Matched:   {matched_count:,}"
)

print(
    f"Unmatched: {unmatched_count:,}"
)

if unmatched_count != 0:

    print(
        "\nWARNING: Some CCTV points "
        "have no road match."
    )

else:

    print("PASS")


# ------------------------------------------------------------
# 5. Distance validation
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("5. ROAD DISTANCE VALIDATION")
print("-" * 80)

distance = (
    pd.to_numeric(
        gdf["distance_to_road_m"],
        errors="coerce"
    )
)

print(
    f"Missing distances: "
    f"{distance.isna().sum():,}"
)

if distance.isna().any():

    raise ValueError(
        "Some matched cameras have no distance."
    )


print(
    f"Mean:   {distance.mean():.2f} m"
)

print(
    f"Median: {distance.median():.2f} m"
)

print(
    f"Max:    {distance.max():.2f} m"
)


# ------------------------------------------------------------
# Distance bands
# ------------------------------------------------------------

bands = pd.cut(
    distance,
    bins=[
        -float("inf"),
        10,
        25,
        50,
        100,
        float("inf"),
    ],
    labels=[
        "0-10m",
        "10-25m",
        "25-50m",
        "50-100m",
        ">100m",
    ]
)

band_counts = (
    bands
    .value_counts()
    .sort_index()
)

print("\nDistance bands:")

print(
    band_counts.to_string()
)


# ------------------------------------------------------------
# City-wise distance statistics
# ------------------------------------------------------------

print("\nCity-wise distance statistics:")

city_distance = (
    gdf
    .groupby("city")["distance_to_road_m"]
    .agg(
        count="count",
        mean="mean",
        median="median",
        maximum="max",
    )
)

print(
    city_distance.to_string()
)


# ------------------------------------------------------------
# 6. Suspicious records
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("6. SUSPICIOUS ROAD MATCHES")
print("-" * 80)

# QA threshold:
# >50m = review
#
# This does NOT mean the match is wrong.
# It means the match deserves investigation.

review = (
    gdf[
        gdf["distance_to_road_m"] > 50
    ]
    .copy()
)

review = review.sort_values(
    "distance_to_road_m",
    ascending=False
)

print(
    f"Records requiring review (>50m): "
    f"{len(review):,}"
)

if len(review) > 0:

    print("\nWorst matches:")

    columns = [
        "camera_id",
        "city",
        "name",
        "latitude",
        "longitude",
        "road_id",
        "road_name",
        "highway",
        "distance_to_road_m",
    ]

    print(
        review[columns]
        .head(20)
        .to_string(index=False)
    )

    review.to_parquet(
        SUSPICIOUS_OUTPUT,
        index=False
    )

    print(
        f"\nReview dataset saved to:\n"
        f"{SUSPICIOUS_OUTPUT}"
    )


# ------------------------------------------------------------
# 7. Required columns
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("7. SCHEMA VALIDATION")
print("-" * 80)

required_columns = {
    "camera_id",
    "city",
    "latitude",
    "longitude",
    "road_id",
    "road_name",
    "highway",
    "distance_to_road_m",
    "geometry",
    "data_provenance",
}

missing_columns = (
    required_columns
    - set(gdf.columns)
)

if missing_columns:

    raise ValueError(
        f"Missing required columns: "
        f"{missing_columns}"
    )

print("All required columns present.")
print("PASS")


# ------------------------------------------------------------
# 8. Provenance validation
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("8. DATA PROVENANCE")
print("-" * 80)

print(
    gdf[
        ["city", "data_provenance"]
    ]
    .drop_duplicates()
    .to_string(index=False)
)


# ------------------------------------------------------------
# 9. Final verdict
# ------------------------------------------------------------

critical_failures = []

if total != 1551:
    critical_failures.append(
        "total record count"
    )

if unique_cameras != 1551:
    critical_failures.append(
        "camera uniqueness"
    )

if matched_count != 1551:
    critical_failures.append(
        "complete road matching"
    )

if missing_columns:
    critical_failures.append(
        "required schema"
    )


print("\n" + "=" * 80)

if critical_failures:

    verdict = "PHASE A FAILED"

    print(verdict)

    print(
        "\nCritical failures:"
    )

    for failure in critical_failures:

        print(
            f"  - {failure}"
        )

else:

    verdict = "PHASE A PASSED — WITH QA FLAGS"

    print(verdict)

    print(
        "\nCore GIS pipeline is operational."
    )

    print(
        f"Road matches: "
        f"{matched_count:,}/{total:,}"
    )

    print(
        f"Matches requiring review (>50m): "
        f"{len(review):,}"
    )


# ------------------------------------------------------------
# Write report
# ------------------------------------------------------------

report_lines = []

report_lines.append(
    "VIGRAH — PHASE A VALIDATION REPORT"
)

report_lines.append(
    "=" * 60
)

report_lines.append(
    f"Total CCTV records: {total}"
)

report_lines.append(
    f"Unique cameras: {unique_cameras}"
)

report_lines.append(
    f"Matched roads: {matched_count}"
)

report_lines.append(
    f"Unmatched roads: {unmatched_count}"
)

report_lines.append(
    f"Mean distance: {distance.mean():.2f} m"
)

report_lines.append(
    f"Median distance: {distance.median():.2f} m"
)

report_lines.append(
    f"Maximum distance: {distance.max():.2f} m"
)

report_lines.append(
    f"Review matches (>50m): {len(review)}"
)

report_lines.append(
    f"Verdict: {verdict}"
)

REPORT_OUTPUT.write_text(
    "\n".join(report_lines),
    encoding="utf-8"
)


print(
    f"\nReport saved:\n"
    f"{REPORT_OUTPUT}"
)

print("\n" + "=" * 80)
print("PHASE A VALIDATION COMPLETE")
print("=" * 80)