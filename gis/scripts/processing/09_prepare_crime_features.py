from pathlib import Path
import pandas as pd


# ============================================================
# VIGRAH — B4.2 NCRB CRIME FEATURE PREPARATION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

CRIME_DIR = (
    ROOT
    / "data"
    / "raw"
    / "ncrb"
    / "crime"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTPUT_DIR
    / "crime_city_context.parquet"
)


print("=" * 80)
print("VIGRAH — B4.2 NCRB CRIME FEATURE PREPARATION")
print("=" * 80)


# ============================================================
# SOURCE FILES
# ============================================================

WOMEN_FILE = (
    CRIME_DIR
    / "NCRB_WOMEN_STATE_2023.csv"
)

CHILDREN_FILE = (
    CRIME_DIR
    / "NCRB_CHILDREN_STATE_2023.csv"
)


if not WOMEN_FILE.exists():
    raise FileNotFoundError(
        f"Missing:\n{WOMEN_FILE}"
    )


if not CHILDREN_FILE.exists():
    raise FileNotFoundError(
        f"Missing:\n{CHILDREN_FILE}"
    )


print("\nUsing authoritative aggregate datasets:")

print(
    f"  Women:    {WOMEN_FILE.name}"
)

print(
    f"  Children: {CHILDREN_FILE.name}"
)


# ============================================================
# TARGET STATE → PROJECT CITY
# ============================================================

STATE_TO_CITY = {
    "Maharashtra": "Mumbai",
    "Karnataka": "Bengaluru",
}


# ============================================================
# HELPERS
# ============================================================

def find_state_column(df):

    for col in df.columns:

        if (
            str(col)
            .strip()
            .lower()
            == "state/ut"
        ):

            return col

    for col in df.columns:

        if "state" in str(col).lower():

            return col

    raise RuntimeError(
        "Could not identify State/UT column."
    )


def find_column_containing(
    df,
    required_terms
):

    matches = []

    for col in df.columns:

        text = str(col).lower()

        if all(
            term.lower() in text
            for term in required_terms
        ):

            matches.append(col)

    if len(matches) == 1:

        return matches[0]

    if len(matches) > 1:

        # Prefer shortest matching header.
        matches.sort(
            key=lambda x: len(str(x))
        )

        return matches[0]

    return None


def get_state_value(
    df,
    state_col,
    state,
    source_col
):

    rows = df[
        df[state_col]
        .astype(str)
        .str.strip()
        .str.lower()
        == state.lower()
    ]

    if len(rows) != 1:

        raise RuntimeError(
            f"Expected exactly one row for "
            f"{state}; found {len(rows)}."
        )

    value = pd.to_numeric(
        rows.iloc[0][source_col],
        errors="coerce"
    )

    if pd.isna(value):

        raise RuntimeError(
            f"Missing numeric value for "
            f"{state} in column:\n"
            f"{source_col}"
        )

    return float(value)


# ============================================================
# LOAD
# ============================================================

print("\n" + "-" * 80)
print("LOADING DATASETS")
print("-" * 80)


women = pd.read_csv(
    WOMEN_FILE,
    low_memory=False
)

children = pd.read_csv(
    CHILDREN_FILE,
    low_memory=False
)


print(
    f"\nWomen rows:    {len(women):,}"
)

print(
    f"Women columns: {len(women.columns):,}"
)

print(
    f"Children rows: {len(children):,}"
)

print(
    f"Children columns: {len(children.columns):,}"
)


# ============================================================
# STATE COLUMNS
# ============================================================

women_state_col = find_state_column(
    women
)

children_state_col = find_state_column(
    children
)


print(
    f"\nWomen state column: "
    f"{women_state_col}"
)

print(
    f"Children state column: "
    f"{children_state_col}"
)


# ============================================================
# FIND AUTHORITATIVE TOTAL WOMEN CRIME
# ============================================================

print("\n" + "-" * 80)
print("SOURCE COLUMN DETECTION")
print("-" * 80)


women_total_col = find_column_containing(
    women,
    [
        "total crime against women",
        "ipc+sll",
        "i",
    ]
)


print(
    "\nTotal Crime against Women:"
)

print(
    women_total_col
)


# ============================================================
# FIND AUTHORITATIVE TOTAL CHILDREN CRIME
# ============================================================

children_total_col = find_column_containing(
    children,
    [
        "total crimes against children",
        "ipc+sll",
        "i",
    ]
)


print(
    "\nTotal Crimes against Children:"
)

print(
    children_total_col
)


# ============================================================
# HARD FAIL
# ============================================================

if women_total_col is None:

    raise RuntimeError(
        "Could not identify the authoritative "
        "Total Crime against Women column."
    )


if children_total_col is None:

    raise RuntimeError(
        "Could not identify the authoritative "
        "Total Crimes against Children column."
    )


print(
    "\nRequired aggregate columns detected."
)

print(
    "PASS"
)


# ============================================================
# BUILD CITY FEATURES
# ============================================================

print("\n" + "-" * 80)
print("EXTRACTING TARGET STATES")
print("-" * 80)


records = []


for state, city in STATE_TO_CITY.items():

    print(
        f"\n{state} → {city}"
    )


    women_value = get_state_value(
        women,
        women_state_col,
        state,
        women_total_col
    )


    children_value = get_state_value(
        children,
        children_state_col,
        state,
        children_total_col
    )


    print(
        f"  Total crime against women: "
        f"{women_value:,.0f}"
    )

    print(
        f"  Total crime against children: "
        f"{children_value:,.0f}"
    )


    records.append(
        {
            "city": city,
            "state": state,

            "crime_data_year": 2023,

            "crime_data_level":
                "state_context",

            "data_provenance":
                "NCRB",

            # Authoritative aggregate indicators
            "total_crime_against_women":
                women_value,

            "total_crime_against_children":
                children_value,

            # Explicit source fields
            "women_source_column":
                str(women_total_col),

            "children_source_column":
                str(children_total_col),
        }
    )


# ============================================================
# CREATE DATAFRAME
# ============================================================

crime_features = pd.DataFrame(
    records
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "-" * 80)
print("VALIDATION")
print("-" * 80)


expected_cities = {
    "Mumbai",
    "Bengaluru",
}


actual_cities = set(
    crime_features["city"]
)


if actual_cities != expected_cities:

    raise RuntimeError(
        f"Unexpected city set.\n"
        f"Expected: {expected_cities}\n"
        f"Actual: {actual_cities}"
    )


print(
    "Cities: PASS"
)


if len(crime_features) != 2:

    raise RuntimeError(
        "Expected exactly 2 records."
    )


print(
    "Record count: 2 / 2 PASS"
)


# ------------------------------------------------------------
# Missing values
# ------------------------------------------------------------

feature_columns = [
    "total_crime_against_women",
    "total_crime_against_children",
]


missing = (
    crime_features[
        feature_columns
    ]
    .isna()
    .sum()
    .sum()
)


if missing != 0:

    raise RuntimeError(
        f"Found {missing} missing values."
    )


print(
    "Missing values: 0 PASS"
)


# ------------------------------------------------------------
# Negative values
# ------------------------------------------------------------

negative = (
    crime_features[
        feature_columns
    ]
    .lt(0)
    .sum()
    .sum()
)


if negative != 0:

    raise RuntimeError(
        "Negative crime values detected."
    )


print(
    "Non-negative values: PASS"
)


# ============================================================
# DISPLAY FINAL TABLE
# ============================================================

print("\n" + "-" * 80)
print("FINAL CRIME CONTEXT TABLE")
print("-" * 80)


print(
    crime_features[
        [
            "city",
            "state",
            "total_crime_against_women",
            "total_crime_against_children",
        ]
    ]
    .to_string(index=False)
)


# ============================================================
# SAVE
# ============================================================

print("\n" + "-" * 80)
print("SAVING")
print("-" * 80)


print(
    OUTPUT
)


crime_features.to_parquet(
    OUTPUT,
    index=False
)


print(
    f"\nOutput size: "
    f"{OUTPUT.stat().st_size / 1024:.2f} KB"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 80)
print("B4.2 COMPLETE")
print("=" * 80)


print(
    "\nCrime context table successfully created."
)

print(
    "Only authoritative NCRB aggregate "
    "crime indicators are used."
)

print(
    "No IPC/SLL component totals were "
    "artificially reconstructed."
)

print(
    "\nOutput:"
)

print(
    OUTPUT
)