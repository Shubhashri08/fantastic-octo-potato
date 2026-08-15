from pathlib import Path
import geopandas as gpd
import pandas as pd


# ============================================================
# VIGRAH — PHASE A / A2
# Prepare Mumbai and Bengaluru operational boundaries
# ============================================================

# Project root:
# gis/
ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "boundaries"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 1. Find the district shapefile automatically
# ------------------------------------------------------------

shapefiles = list(RAW_DIR.rglob("*.shp"))

if not shapefiles:
    raise FileNotFoundError(
        f"No .shp file found anywhere under:\n{RAW_DIR}"
    )

print("=" * 70)
print("VIGRAH — A2 BOUNDARY PREPARATION")
print("=" * 70)

print("\nShapefiles found:")

for shp in shapefiles:
    print("  ", shp)


# Prefer the India districts dataset if multiple shapefiles exist
preferred = [
    shp for shp in shapefiles
    if "INDIA_DISTRICTS_2020" in shp.name.upper()
]

if preferred:
    source_file = preferred[0]
else:
    source_file = shapefiles[0]

print("\nUsing:")
print(source_file)


# ------------------------------------------------------------
# 2. Read shapefile
# ------------------------------------------------------------

print("\nReading boundary dataset...")

gdf = gpd.read_file(source_file)

print(f"Features loaded: {len(gdf):,}")
print(f"CRS: {gdf.crs}")

print("\nColumns:")
print(list(gdf.columns))


# ------------------------------------------------------------
# 3. Check required fields
# ------------------------------------------------------------

required_columns = {"dtname", "stname"}

missing = required_columns - set(gdf.columns)

if missing:
    raise ValueError(
        f"Required columns missing: {missing}\n"
        f"Available columns: {list(gdf.columns)}"
    )


# ------------------------------------------------------------
# 4. Display relevant Maharashtra/Karnataka districts
# ------------------------------------------------------------

print("\nRelevant Maharashtra districts:")

mh = gdf[
    gdf["stname"]
    .astype(str)
    .str.strip()
    .str.casefold()
    == "maharashtra"
]

print(
    mh[["dtname", "stname"]]
    .drop_duplicates()
    .to_string(index=False)
)


print("\nRelevant Karnataka districts:")

ka = gdf[
    gdf["stname"]
    .astype(str)
    .str.strip()
    .str.casefold()
    == "karnataka"
]

print(
    ka[["dtname", "stname"]]
    .drop_duplicates()
    .to_string(index=False)
)


# ------------------------------------------------------------
# 5. Extract Mumbai districts
# ------------------------------------------------------------

mumbai_names = {
    "mumbai",
    "mumbai suburban",
}

mumbai = gdf[
    gdf["stname"]
    .astype(str)
    .str.strip()
    .str.casefold()
    .eq("maharashtra")
    &
    gdf["dtname"]
    .astype(str)
    .str.strip()
    .str.casefold()
    .isin(mumbai_names)
].copy()


if mumbai.empty:
    raise ValueError(
        "Mumbai / Mumbai Suburban were not found."
    )


print("\nMumbai districts selected:")

print(
    mumbai[["dtname", "stname"]]
    .drop_duplicates()
    .to_string(index=False)
)


# ------------------------------------------------------------
# 6. Extract Bengaluru urban district
# ------------------------------------------------------------

# Source dataset uses "Bangalore".
# We canonicalize it to "Bengaluru Urban".

bengaluru = gdf[
    gdf["stname"]
    .astype(str)
    .str.strip()
    .str.casefold()
    .eq("karnataka")
    &
    gdf["dtname"]
    .astype(str)
    .str.strip()
    .str.casefold()
    .eq("bangalore")
].copy()


if bengaluru.empty:
    raise ValueError(
        "Bangalore district was not found in Karnataka."
    )


print("\nBengaluru district selected:")

print(
    bengaluru[["dtname", "stname"]]
    .drop_duplicates()
    .to_string(index=False)
)


# ------------------------------------------------------------
# 7. Ensure geographic CRS is EPSG:4326
# ------------------------------------------------------------

if gdf.crs is None:
    raise ValueError(
        "Source boundary dataset has no CRS."
    )

if gdf.crs.to_epsg() != 4326:

    print(
        f"\nReprojecting boundaries from "
        f"{gdf.crs} → EPSG:4326"
    )

    mumbai = mumbai.to_crs(epsg=4326)
    bengaluru = bengaluru.to_crs(epsg=4326)

else:
    print("\nSource CRS already EPSG:4326.")


# ------------------------------------------------------------
# 8. Add canonical fields
# ------------------------------------------------------------

mumbai["city"] = "Mumbai"
mumbai["canonical_name"] = (
    mumbai["dtname"]
    .astype(str)
    .str.strip()
)

mumbai["boundary_level"] = "district"

mumbai["source_name"] = (
    mumbai["dtname"]
    .astype(str)
    .str.strip()
)

mumbai["source"] = "INDIA_DISTRICTS_2020"
mumbai["valid_year"] = 2011


bengaluru["city"] = "Bengaluru"
bengaluru["canonical_name"] = "Bengaluru Urban"
bengaluru["boundary_level"] = "district"

bengaluru["source_name"] = (
    bengaluru["dtname"]
    .astype(str)
    .str.strip()
)

bengaluru["source"] = "INDIA_DISTRICTS_2020"
bengaluru["valid_year"] = 2011


# ------------------------------------------------------------
# 9. Save individual district boundaries
# ------------------------------------------------------------

mumbai_district_file = (
    OUTPUT_DIR / "mumbai_districts.gpkg"
)

bengaluru_district_file = (
    OUTPUT_DIR / "bengaluru_district.gpkg"
)

print("\nSaving individual district boundaries...")

mumbai.to_file(
    mumbai_district_file,
    layer="districts",
    driver="GPKG"
)

bengaluru.to_file(
    bengaluru_district_file,
    layer="district",
    driver="GPKG"
)


# ------------------------------------------------------------
# 10. Create operational Mumbai boundary
# ------------------------------------------------------------

print("\nCreating operational Mumbai boundary...")

mumbai_geometry = mumbai.geometry.union_all()

mumbai_operational = gpd.GeoDataFrame(
    [{
        "city": "Mumbai",
        "boundary_level": "operational_city",
        "source": "INDIA_DISTRICTS_2020",
        "valid_year": 2011,
    }],
    geometry=[mumbai_geometry],
    crs="EPSG:4326"
)


# ------------------------------------------------------------
# 11. Create operational Bengaluru boundary
# ------------------------------------------------------------

print("Creating operational Bengaluru boundary...")

bengaluru_geometry = bengaluru.geometry.union_all()

bengaluru_operational = gpd.GeoDataFrame(
    [{
        "city": "Bengaluru",
        "boundary_level": "operational_city",
        "source": "INDIA_DISTRICTS_2020",
        "valid_year": 2011,
    }],
    geometry=[bengaluru_geometry],
    crs="EPSG:4326"
)


# ------------------------------------------------------------
# 12. Save operational boundaries
# ------------------------------------------------------------

mumbai_output = (
    OUTPUT_DIR / "mumbai_boundary.gpkg"
)

bengaluru_output = (
    OUTPUT_DIR / "bengaluru_boundary.gpkg"
)

print("\nSaving operational boundaries...")

mumbai_operational.to_file(
    mumbai_output,
    layer="boundary",
    driver="GPKG"
)

bengaluru_operational.to_file(
    bengaluru_output,
    layer="boundary",
    driver="GPKG"
)


# ------------------------------------------------------------
# 13. Final validation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("A2 COMPLETE")
print("=" * 70)

print("\nMumbai:")
print("  District features:", len(mumbai))
print("  Operational boundary:", mumbai_output)

print("\nBengaluru:")
print("  District features:", len(bengaluru))
print("  Operational boundary:", bengaluru_output)

print("\nCRS:")
print("  Mumbai:", mumbai_operational.crs)
print("  Bengaluru:", bengaluru_operational.crs)

print("\nOutput directory:")
print(OUTPUT_DIR)

print("\nFiles created:")

for file in sorted(OUTPUT_DIR.glob("*.gpkg")):
    print(
        f"  {file.name} "
        f"({file.stat().st_size / 1024:.1f} KB)"
    )

print("\nA2 boundary preparation successful.")