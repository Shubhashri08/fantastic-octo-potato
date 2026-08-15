from pathlib import Path
import pandas as pd
import json


# ============================================================
# VIGRAH — PHASE B / B1
# Accident Dataset Inspection
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

ACCIDENT_DIR = (
    ROOT
    / "data"
    / "raw"
    / "ncrb"
    / "accidents"
)


print("=" * 80)
print("VIGRAH — B1 ACCIDENT DATASET INSPECTION")
print("=" * 80)

print("\nAccident directory:")
print(ACCIDENT_DIR)


if not ACCIDENT_DIR.exists():
    raise FileNotFoundError(
        f"Accident directory does not exist:\n{ACCIDENT_DIR}"
    )


# ------------------------------------------------------------
# Find candidate files
# ------------------------------------------------------------

extensions = {
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".parquet",
}

files = [
    f
    for f in ACCIDENT_DIR.rglob("*")
    if f.is_file()
    and f.suffix.lower() in extensions
]


if not files:
    raise FileNotFoundError(
        f"No accident data files found under:\n{ACCIDENT_DIR}"
    )


print("\nFiles found:")

for i, file in enumerate(files, start=1):

    size_mb = (
        file.stat().st_size
        / (1024 * 1024)
    )

    print(
        f"  {i}. {file.name}"
        f"  ({size_mb:.2f} MB)"
    )


# ------------------------------------------------------------
# Inspect each file
# ------------------------------------------------------------

for file in files:

    print("\n" + "=" * 80)
    print(f"FILE: {file.name}")
    print("=" * 80)

    suffix = file.suffix.lower()

    try:

        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        if suffix == ".csv":

            df = pd.read_csv(
                file,
                low_memory=False
            )


        # ----------------------------------------------------
        # Excel
        # ----------------------------------------------------

        elif suffix in {".xlsx", ".xls"}:

            excel = pd.ExcelFile(file)

            print("\nExcel sheets:")

            for sheet in excel.sheet_names:
                print(f"  - {sheet}")

            # Inspect first sheet
            df = pd.read_excel(
                file,
                sheet_name=excel.sheet_names[0]
            )


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        elif suffix == ".json":

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            if isinstance(data, list):

                df = pd.json_normalize(data)

            elif isinstance(data, dict):

                # Try to identify a list inside the JSON
                list_values = [
                    value
                    for value in data.values()
                    if isinstance(value, list)
                ]

                if list_values:

                    df = pd.json_normalize(
                        list_values[0]
                    )

                else:

                    df = pd.json_normalize(
                        data
                    )

            else:

                print(
                    "Unsupported JSON structure."
                )

                continue


        # ----------------------------------------------------
        # Parquet
        # ----------------------------------------------------

        elif suffix == ".parquet":

            df = pd.read_parquet(file)


        else:

            print(
                f"Unsupported extension: {suffix}"
            )

            continue


    except Exception as e:

        print("\nERROR reading file:")
        print(type(e).__name__)
        print(str(e))

        continue


    # --------------------------------------------------------
    # Dataset overview
    # --------------------------------------------------------

    print("\n--- Dataset overview ---")

    print(
        f"Rows: "
        f"{len(df):,}"
    )

    print(
        f"Columns: "
        f"{len(df.columns):,}"
    )


    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    print("\n--- Columns ---")

    for column in df.columns:

        dtype = df[column].dtype

        non_null = (
            df[column]
            .notna()
            .sum()
        )

        missing = (
            df[column]
            .isna()
            .sum()
        )

        unique = (
            df[column]
            .nunique(dropna=True)
        )

        print(
            f"\n{column}"
        )

        print(
            f"  dtype:      {dtype}"
        )

        print(
            f"  non-null:   {non_null:,}"
        )

        print(
            f"  missing:    {missing:,}"
        )

        print(
            f"  unique:     {unique:,}"
        )


    # --------------------------------------------------------
    # Sample records
    # --------------------------------------------------------

    print("\n--- First 5 records ---")

    print(
        df.head(5)
        .to_string(index=False)
    )


    # --------------------------------------------------------
    # Potential spatial columns
    # --------------------------------------------------------

    print("\n--- Potential spatial columns ---")

    spatial_keywords = [
        "lat",
        "latitude",
        "lon",
        "lng",
        "longitude",
        "coord",
        "location",
        "geo",
    ]

    spatial_candidates = [
        column
        for column in df.columns
        if any(
            keyword in str(column).lower()
            for keyword in spatial_keywords
        )
    ]

    if spatial_candidates:

        for column in spatial_candidates:
            print(f"  ✓ {column}")

    else:

        print(
            "  No obvious latitude/longitude "
            "columns detected."
        )


    # --------------------------------------------------------
    # Potential date/time columns
    # --------------------------------------------------------

    print("\n--- Potential date/time columns ---")

    datetime_keywords = [
        "date",
        "year",
        "month",
        "time",
        "timestamp",
    ]

    datetime_candidates = [
        column
        for column in df.columns
        if any(
            keyword in str(column).lower()
            for keyword in datetime_keywords
        )
    ]

    if datetime_candidates:

        for column in datetime_candidates:
            print(f"  ✓ {column}")

    else:

        print(
            "  No obvious date/time columns detected."
        )


    # --------------------------------------------------------
    # Potential accident severity columns
    # --------------------------------------------------------

    print("\n--- Potential severity columns ---")

    severity_keywords = [
        "death",
        "died",
        "fatal",
        "fatality",
        "injured",
        "injury",
        "severity",
        "cases",
        "accident",
        "crash",
    ]

    severity_candidates = [
        column
        for column in df.columns
        if any(
            keyword in str(column).lower()
            for keyword in severity_keywords
        )
    ]

    if severity_candidates:

        for column in severity_candidates:
            print(f"  ✓ {column}")

    else:

        print(
            "  No obvious accident/severity "
            "columns detected."
        )


    # --------------------------------------------------------
    # Geographic values
    # --------------------------------------------------------

    print("\n--- Potential geographic coverage ---")

    for column in df.columns:

        column_lower = str(column).lower()

        if any(
            keyword in column_lower
            for keyword in [
                "city",
                "district",
                "state",
                "region",
                "location",
            ]
        ):

            unique_values = (
                df[column]
                .dropna()
                .astype(str)
                .unique()
            )

            print(
                f"\n{column}: "
                f"{len(unique_values):,} unique values"
            )

            if len(unique_values) <= 30:

                print(
                    list(unique_values)
                )


print("\n" + "=" * 80)
print("B1 INSPECTION COMPLETE")
print("=" * 80)

print(
    "\nNo source files were modified."
)