from pathlib import Path
import json
import geopandas as gpd
from shapely.geometry import Point


# ============================================================
# VIGRAH — PHASE A / A4.1
# Prepare CCTV point dataset
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RAW_CCTV = (
    ROOT
    / "data"
    / "raw"
    / "cctv"
    / "MUMBAI_BENGALURU_CCTV_DATA.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "cctv"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = OUTPUT_DIR / "cctv_points.parquet"


print("=" * 80)
print("VIGRAH — A4.1 CCTV PREPARATION")
print("=" * 80)

print("\nInput:")
print(RAW_CCTV)


if not RAW_CCTV.exists():
    raise FileNotFoundError(
        f"CCTV JSON not found:\n{RAW_CCTV}"
    )


# ------------------------------------------------------------
# Read JSON
# ------------------------------------------------------------

with open(
    RAW_CCTV,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)


print("\nTop-level keys:")
print(list(data.keys()))


# ------------------------------------------------------------
# Extract city datasets
# ------------------------------------------------------------

records = []


for city_key in ["Mumbai", "Bengaluru"]:

    if city_key not in data:

        raise ValueError(
            f"Missing city in CCTV JSON: {city_key}"
        )

    city_data = data[city_key]

    nodes = city_data.get("nodes", [])

    print(
        f"\n{city_key}: "
        f"{len(nodes):,} nodes"
    )

    for node in nodes:

        records.append(
            {
                "camera_id": node.get("id"),
                "city": city_key,
                "name": node.get("name"),
                "latitude": node.get("lat"),
                "longitude": node.get("lon"),
                "zone": node.get("zone"),
                "status": node.get("status"),
                "video_url": node.get("video_url"),
                "video_filename": node.get(
                    "video_filename"
                ),

                # Explicit provenance
                "data_provenance": (
                    "synthetic"
                    if city_key == "Mumbai"
                    else "provided_dataset"
                ),
            }
        )


# ------------------------------------------------------------
# Create GeoDataFrame
# ------------------------------------------------------------

gdf = gpd.GeoDataFrame(
    records,
    geometry=[
        Point(
            record["longitude"],
            record["latitude"]
        )
        for record in records
    ],
    crs="EPSG:4326"
)


# ------------------------------------------------------------
# Basic validation
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("VALIDATION")
print("-" * 80)

print(
    f"Total CCTV records: "
    f"{len(gdf):,}"
)

expected = {
    "Mumbai": 10,
    "Bengaluru": 1541,
}

for city, expected_count in expected.items():

    actual = (
        gdf["city"]
        .eq(city)
        .sum()
    )

    print(
        f"{city}: "
        f"{actual:,} / {expected_count:,}"
    )

    if actual != expected_count:

        raise ValueError(
            f"{city} count mismatch. "
            f"Expected {expected_count}, got {actual}."
        )


# ------------------------------------------------------------
# Unique IDs
# ------------------------------------------------------------

duplicate_ids = (
    gdf["camera_id"]
    .duplicated()
    .sum()
)

print(
    f"Duplicate camera IDs: "
    f"{duplicate_ids}"
)

if duplicate_ids != 0:

    raise ValueError(
        "Duplicate camera IDs detected."
    )


# ------------------------------------------------------------
# Coordinate validation
# ------------------------------------------------------------

invalid_lat = (
    ~gdf["latitude"]
    .between(-90, 90)
).sum()

invalid_lon = (
    ~gdf["longitude"]
    .between(-180, 180)
).sum()

null_coords = (
    gdf["latitude"].isna()
    |
    gdf["longitude"].isna()
).sum()


print(
    f"Invalid latitude:  "
    f"{invalid_lat}"
)

print(
    f"Invalid longitude: "
    f"{invalid_lon}"
)

print(
    f"Null coordinates:   "
    f"{null_coords}"
)


if (
    invalid_lat
    or invalid_lon
    or null_coords
):

    raise ValueError(
        "Invalid CCTV coordinates detected."
    )


# ------------------------------------------------------------
# Geometry validation
# ------------------------------------------------------------

invalid_geometry = (
    ~gdf.geometry.is_valid
).sum()

print(
    f"Invalid geometries: "
    f"{invalid_geometry}"
)

if invalid_geometry:

    raise ValueError(
        "Invalid CCTV geometries detected."
    )


# ------------------------------------------------------------
# Provenance
# ------------------------------------------------------------

print("\nData provenance:")

print(
    gdf[
        ["city", "data_provenance"]
    ]
    .drop_duplicates()
    .to_string(index=False)
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

print("\nSaving:")
print(OUTPUT)

gdf.to_parquet(
    OUTPUT,
    index=False
)


print("\n" + "=" * 80)
print("A4.1 COMPLETE")
print("=" * 80)

print(
    f"Records saved: "
    f"{len(gdf):,}"
)

print(
    f"Output size: "
    f"{OUTPUT.stat().st_size / (1024 * 1024):.2f} MB"
)