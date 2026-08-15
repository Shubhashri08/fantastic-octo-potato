"""
VIGRAH Layer 4 - Raw Data Validation
-------------------------------------
Run this script from the VIGRAH repository root:

    python scripts/validation/validate_raw_data.py

Purpose:
- Confirm all expected raw files exist.
- Inspect CSV/XLSX structure.
- Check whether target states appear.
- Report missing values and duplicate rows.
- Inspect the district boundary shapefile.
- Check OSM PBF file presence/size.

This script DOES NOT modify any raw data.
"""

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

TARGET_STATES = [
    "Maharashtra",
    "West Bengal",
    "Uttar Pradesh",
    "Bihar",
]

EXPECTED_FILES = {
    "NCRB IPC": RAW / "ncrb/crime/NCRB_IPC_STATE_2023.csv",
    "NCRB SLL": RAW / "ncrb/crime/NCRB_SLL_STATE_2023.csv",
    "NCRB Women": RAW / "ncrb/crime/NCRB_WOMEN_STATE_2023.csv",
    "NCRB Children": RAW / "ncrb/crime/NCRB_CHILDREN_STATE_2023.csv",
    "NCRB Accident Road Class": RAW / "ncrb/accidents/NCRB_ACCIDENTS_ROAD_CLASS_2023.csv",
    "NCRB Accident Monthly": RAW / "ncrb/accidents/NCRB_ACCIDENTS_MONTHLY_2023.csv",
    "Census Population": RAW / "population/CENSUS_POPULATION_2011.xlsx",
    "District Boundaries (.shp)": RAW / "boundaries/INDIA_DISTRICTS_2020.shp",
    "District Boundaries (.shx)": RAW / "boundaries/INDIA_DISTRICTS_2020.shx",
    "District Boundaries (.dbf)": RAW / "boundaries/INDIA_DISTRICTS_2020.dbf",
    "District Boundaries (.prj)": RAW / "boundaries/INDIA_DISTRICTS_2020.prj",
    "OSM Western": RAW / "osm/OSM_WESTERN_ZONE_LATEST.osm.pbf",
    "OSM Eastern": RAW / "osm/OSM_EASTERN_ZONE_LATEST.osm.pbf",
    "OSM Central": RAW / "osm/OSM_CENTRAL_ZONE_LATEST.osm.pbf",
}


def size_mb(path):
    return path.stat().st_size / (1024 * 1024)


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def validate_files():
    print_header("1. FILE EXISTENCE CHECK")
    missing = []
    for label, path in EXPECTED_FILES.items():
        if path.exists():
            print(f"[OK]      {label:<28} {size_mb(path):>10.2f} MB")
        else:
            print(f"[MISSING] {label:<28} {path}")
            missing.append(label)

    if missing:
        print(f"\nMissing {len(missing)} expected file(s).")
    else:
        print("\nAll expected raw files are present.")

    return missing


def find_state_column(columns):
    normalized = {
        str(c).strip().lower().replace(" ", "").replace("_", ""): c
        for c in columns
    }

    candidates = [
        "state",
        "statename",
        "stateut",
        "stateutname",
        "stateutname",
        "state/ut",
        "state/utname",
    ]

    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalized:
            return normalized[key]

    # Fallback: any column containing "state"
    for c in columns:
        if "state" in str(c).lower():
            return c

    return None


def inspect_csv(label, path):
    print_header(f"CSV: {label}")

    try:
        import pandas as pd
    except ImportError:
        print("[ERROR] pandas is not installed. Run: pip install pandas")
        return

    try:
        # Read header first.
        preview = pd.read_csv(path, nrows=5, encoding_errors="replace")
        print(f"Columns detected: {len(preview.columns)}")
        print("First columns:")
        for c in list(preview.columns)[:25]:
            print(f"  - {c}")

        # Full load for validation.
        df = pd.read_csv(path, encoding_errors="replace", low_memory=False)

        print(f"\nRows: {len(df):,}")
        print(f"Columns: {len(df.columns):,}")
        print(f"Duplicate rows: {df.duplicated().sum():,}")

        state_col = find_state_column(df.columns)

        if state_col:
            values = (
                df[state_col]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
            )
            print(f"\nState column: {state_col}")
            print("Target-state coverage:")
            for state in TARGET_STATES:
                found = any(state.lower() == str(v).lower() for v in values)
                print(f"  {'[YES]' if found else '[NO] '} {state}")
            print(f"Unique values in state column: {len(values)}")
        else:
            print("\n[WARNING] No obvious state column detected.")

        missing_pct = (df.isna().mean() * 100).sort_values(ascending=False)
        print("\nTop 10 columns by missing percentage:")
        for col, pct in missing_pct.head(10).items():
            print(f"  {pct:6.2f}%  {col}")

    except Exception as exc:
        print(f"[ERROR] Could not inspect {path.name}: {exc}")


def inspect_excel(path):
    print_header("XLSX: Census Population")

    try:
        import pandas as pd
    except ImportError:
        print("[ERROR] pandas is not installed.")
        return

    try:
        xls = pd.ExcelFile(path)
        print("Sheets:")
        for sheet in xls.sheet_names:
            print(f"  - {sheet}")

        for sheet in xls.sheet_names[:5]:
            print(f"\n--- Sheet: {sheet} ---")
            df = pd.read_excel(path, sheet_name=sheet, nrows=5)
            print(f"Preview shape: {df.shape}")
            print("Columns:")
            for c in list(df.columns)[:25]:
                print(f"  - {c}")

    except Exception as exc:
        print(f"[ERROR] Could not inspect XLSX: {exc}")


def inspect_boundaries(path):
    print_header("BOUNDARY SHAPEFILE")

    try:
        import geopandas as gpd
    except ImportError:
        print("[WARNING] geopandas is not installed.")
        print("Install later with: pip install geopandas")
        return

    try:
        gdf = gpd.read_file(path)

        print(f"Features: {len(gdf):,}")
        print(f"CRS: {gdf.crs}")
        print(f"Geometry types: {gdf.geometry.geom_type.value_counts().to_dict()}")

        print("\nAttributes:")
        for c in gdf.columns:
            print(f"  - {c}")

        print("\nFirst 5 rows:")
        print(gdf.head().to_string())

        state_candidates = [
            c for c in gdf.columns
            if "state" in str(c).lower()
        ]

        if state_candidates:
            print("\nPossible state fields:")
            for c in state_candidates:
                print(f"  - {c}")

    except Exception as exc:
        print(f"[ERROR] Could not inspect shapefile: {exc}")


def inspect_osm():
    print_header("OSM PBF CHECK")

    osm_files = [
        RAW / "osm/OSM_WESTERN_ZONE_LATEST.osm.pbf",
        RAW / "osm/OSM_EASTERN_ZONE_LATEST.osm.pbf",
        RAW / "osm/OSM_CENTRAL_ZONE_LATEST.osm.pbf",
    ]

    for path in osm_files:
        if path.exists():
            print(f"[OK] {path.name:<35} {size_mb(path):,.2f} MB")
        else:
            print(f"[MISSING] {path}")

    print("\nPBF files are only checked for presence/size here.")
    print("Road-feature extraction will be handled in the OSM processing step.")


def main():
    print_header("VIGRAH LAYER 4 - RAW DATA VALIDATION")
    print(f"Repository root: {ROOT}")
    print(f"Raw data root:   {RAW}")
    print("\nIMPORTANT: No raw files will be modified.")

    missing = validate_files()

    csv_files = [
        ("NCRB IPC", EXPECTED_FILES["NCRB IPC"]),
        ("NCRB SLL", EXPECTED_FILES["NCRB SLL"]),
        ("NCRB Women", EXPECTED_FILES["NCRB Women"]),
        ("NCRB Children", EXPECTED_FILES["NCRB Children"]),
        ("NCRB Accident Road Class", EXPECTED_FILES["NCRB Accident Road Class"]),
        ("NCRB Accident Monthly", EXPECTED_FILES["NCRB Accident Monthly"]),
    ]

    for label, path in csv_files:
        if path.exists():
            inspect_csv(label, path)

    census = EXPECTED_FILES["Census Population"]
    if census.exists():
        inspect_excel(census)

    boundary = EXPECTED_FILES["District Boundaries (.shp)"]
    if boundary.exists():
        inspect_boundaries(boundary)

    inspect_osm()

    print_header("VALIDATION COMPLETE")
    if missing:
        print("Status: INCOMPLETE - fix missing files before ETL.")
        sys.exit(1)
    else:
        print("Status: RAW FILES PRESENT.")
        print("Next step: review the validation report and design canonical schemas.")


if __name__ == "__main__":
    main()
