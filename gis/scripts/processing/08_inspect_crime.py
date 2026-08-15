from pathlib import Path
import pandas as pd


# ============================================================
# VIGRAH — B4.1 NCRB CRIME INSPECTION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

CRIME_DIR = (
    ROOT
    / "data"
    / "raw"
    / "ncrb"
    / "crime"
)


print("=" * 80)
print("VIGRAH — B4.1 NCRB CRIME DATASET INSPECTION")
print("=" * 80)

print("\nDirectory:")
print(CRIME_DIR)


files = sorted(
    CRIME_DIR.glob("*.csv")
)

if not files:
    raise FileNotFoundError(
        f"No CSV files found in:\n{CRIME_DIR}"
    )


for file in files:

    print("\n" + "=" * 80)
    print(f"FILE: {file.name}")
    print("=" * 80)

    df = pd.read_csv(
        file,
        low_memory=False
    )

    print(
        f"\nRows: {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns):,}"
    )

    print("\nColumns:")

    for col in df.columns:

        print(
            f"  {col}"
        )

    print("\nFirst 5 rows:")

    print(
        df.head(5)
        .to_string(index=False)
    )

    print("\nPotential state columns:")

    for col in df.columns:

        name = str(col).lower()

        if (
            "state" in name
            or "ut" in name
            or "city" in name
            or "region" in name
        ):

            print(
                f"  {col}"
            )

    print("\nPotential numeric crime columns:")

    for col in df.columns:

        if pd.api.types.is_numeric_dtype(
            df[col]
        ):

            print(
                f"  {col}"
            )


print("\n" + "=" * 80)
print("B4.1 INSPECTION COMPLETE")
print("=" * 80)