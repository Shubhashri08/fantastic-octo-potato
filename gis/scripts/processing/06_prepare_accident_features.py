from pathlib import Path
import pandas as pd


# ============================================================
# VIGRAH — PHASE B / B2
# Accident Context Feature Preparation
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

ACCIDENT_DIR = (
    ROOT
    / "data"
    / "raw"
    / "ncrb"
    / "accidents"
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

MONTHLY_FILE = (
    ACCIDENT_DIR
    / "NCRB_ACCIDENTS_MONTHLY_2023.csv"
)

ROAD_CLASS_FILE = (
    ACCIDENT_DIR
    / "NCRB_ACCIDENTS_ROAD_CLASS_2023.csv"
)

OUTPUT = (
    OUTPUT_DIR
    / "accident_city_features.parquet"
)


print("=" * 80)
print("VIGRAH — B2 ACCIDENT FEATURE PREPARATION")
print("=" * 80)


# ------------------------------------------------------------
# Load source datasets
# ------------------------------------------------------------

print("\nLoading monthly accident data...")

monthly = pd.read_csv(
    MONTHLY_FILE,
    low_memory=False
)

print(
    f"Monthly rows: {len(monthly):,}"
)


print("\nLoading road-class accident data...")

road_class = pd.read_csv(
    ROAD_CLASS_FILE,
    low_memory=False
)

print(
    f"Road-class rows: {len(road_class):,}"
)


# ------------------------------------------------------------
# Locate city records
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("CITY-LEVEL ACCIDENT DATA")
print("-" * 80)

city_column = "State/UT/City"

print("\nAvailable target records:")

for target in ["Mumbai", "Bengaluru"]:

    matches = monthly[
        monthly[city_column]
        .astype(str)
        .str.strip()
        .str.lower()
        == target.lower()
    ]

    print(
        f"{target}: "
        f"{len(matches)} record(s)"
    )

    if len(matches):

        print(
            matches[city_column]
            .tolist()
        )


# ------------------------------------------------------------
# Exact source names
# ------------------------------------------------------------

target_rows = {
    "Mumbai": "Mumbai",
    "Bengaluru": "Bengaluru",
}


records = []


# ------------------------------------------------------------
# Extract city-level totals
# ------------------------------------------------------------

for city, source_name in target_rows.items():

    row = monthly[
        monthly[city_column]
        .astype(str)
        .str.strip()
        .str.lower()
        == source_name.lower()
    ]

    if len(row) != 1:

        raise ValueError(
            f"Expected exactly one monthly "
            f"record for {city}, found {len(row)}."
        )

    row = row.iloc[0]

    records.append(
        {
            "city": city,

            # ------------------------------------------------
            # Monthly / city-level accident indicators
            # ------------------------------------------------

            "road_accidents_2023": int(
                row[
                    "Road Accidents - Total"
                ]
            ),

            "railway_crossing_accidents_2023": int(
                row[
                    "Railway Crossing Accidents - Total"
                ]
            ),

            "railway_accidents_2023": int(
                row[
                    "Railway Accidents - Total"
                ]
            ),

            "total_traffic_accidents_2023": int(
                row[
                    "Total Traffic Accidents - Total"
                ]
            ),

            # Explicit provenance
            "monthly_source_level": "city",
            "monthly_source_year": 2023,
        }
    )


# ------------------------------------------------------------
# Road-class state-level data
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("ROAD-CLASS ACCIDENT DATA")
print("-" * 80)


state_column = "State/UT"

state_mapping = {
    "Mumbai": "Maharashtra",
    "Bengaluru": "Karnataka",
}


road_features = []


for city, state in state_mapping.items():

    row = road_class[
        road_class[state_column]
        .astype(str)
        .str.strip()
        .str.lower()
        == state.lower()
    ]

    if len(row) != 1:

        raise ValueError(
            f"Expected exactly one road-class "
            f"record for {state}, found {len(row)}."
        )

    row = row.iloc[0]

    road_features.append(
        {
            "city": city,

            # ------------------------------------------------
            # National Highways
            # ------------------------------------------------

            "nh_accident_cases_2023": int(
                row["National Highways - Cases"]
            ),

            "nh_injured_2023": int(
                row["National Highways - Injured"]
            ),

            "nh_died_2023": int(
                row["National Highways - Died"]
            ),

            # ------------------------------------------------
            # State Highways
            # ------------------------------------------------

            "sh_accident_cases_2023": int(
                row["State Highways - Cases"]
            ),

            "sh_injured_2023": int(
                row["State Highways - Injured"]
            ),

            "sh_died_2023": int(
                row["State Highways - Died"]
            ),

            # ------------------------------------------------
            # Expressways
            # ------------------------------------------------

            "expressway_accident_cases_2023": int(
                row["Expressways - Cases"]
            ),

            "expressway_injured_2023": int(
                row["Expressways - Injured"]
            ),

            "expressway_died_2023": int(
                row["Expressways - Died"]
            ),

            # ------------------------------------------------
            # Other roads
            # ------------------------------------------------

            "other_road_accident_cases_2023": int(
                row["Other Roads - Cases"]
            ),

            "other_road_injured_2023": int(
                row["Other Roads - Injured"]
            ),

            "other_road_died_2023": int(
                row["Other Roads - Died"]
            ),

            # ------------------------------------------------
            # State totals
            # ------------------------------------------------

            "state_total_accident_cases_2023": int(
                row["Total - Cases"]
            ),

            "state_total_injured_2023": int(
                row["Total - Injured"]
            ),

            "state_total_died_2023": int(
                row["Total - Died"]
            ),

            # Explicit provenance
            "road_class_source_level": "state",
            "road_class_source_year": 2023,
            "road_class_source_state": state,
        }
    )


# ------------------------------------------------------------
# Combine
# ------------------------------------------------------------

city_df = pd.DataFrame(records)

road_df = pd.DataFrame(road_features)

features = city_df.merge(
    road_df,
    on="city",
    how="inner",
    validate="one_to_one"
)


# ------------------------------------------------------------
# Derived indicators
# ------------------------------------------------------------

print("\n" + "-" * 80)
print("DERIVED ACCIDENT INDICATORS")
print("-" * 80)


# Fatality rate based on cases
features[
    "city_accident_fatality_rate"
] = (
    features[
        "state_total_died_2023"
    ]
    /
    features[
        "state_total_accident_cases_2023"
    ]
)


# Injury rate based on cases
features[
    "city_accident_injury_rate"
] = (
    features[
        "state_total_injured_2023"
    ]
    /
    features[
        "state_total_accident_cases_2023"
    ]
)


# Road-class shares
features[
    "nh_case_share"
] = (
    features["nh_accident_cases_2023"]
    /
    features["state_total_accident_cases_2023"]
)

features[
    "sh_case_share"
] = (
    features["sh_accident_cases_2023"]
    /
    features["state_total_accident_cases_2023"]
)

features[
    "expressway_case_share"
] = (
    features[
        "expressway_accident_cases_2023"
    ]
    /
    features[
        "state_total_accident_cases_2023"
    ]
)

features[
    "other_road_case_share"
] = (
    features[
        "other_road_accident_cases_2023"
    ]
    /
    features[
        "state_total_accident_cases_2023"
    ]
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

print("\nFeature table:")

print(
    features[
        [
            "city",
            "road_accidents_2023",
            "total_traffic_accidents_2023",
            "state_total_accident_cases_2023",
            "state_total_died_2023",
            "city_accident_fatality_rate",
        ]
    ].to_string(index=False)
)


print("\nChecking road-class totals...")

for _, row in features.iterrows():

    component_sum = (
        row["nh_accident_cases_2023"]
        +
        row["sh_accident_cases_2023"]
        +
        row["expressway_accident_cases_2023"]
        +
        row["other_road_accident_cases_2023"]
    )

    total = row[
        "state_total_accident_cases_2023"
    ]

    if component_sum != total:

        raise ValueError(
            f"Road-class case totals do not "
            f"sum for {row['city']}: "
            f"{component_sum} != {total}"
        )

print("Road-class case totals: PASS")


# ------------------------------------------------------------
# Final schema
# ------------------------------------------------------------

print("\nCities:")
print(
    features["city"]
    .tolist()
)

if set(features["city"]) != {
    "Mumbai",
    "Bengaluru",
}:

    raise ValueError(
        "Unexpected city set."
    )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

print("\nSaving:")
print(OUTPUT)

features.to_parquet(
    OUTPUT,
    index=False
)


print(
    f"\nOutput size: "
    f"{OUTPUT.stat().st_size / (1024 * 1024):.2f} MB"
)


print("\n" + "=" * 80)
print("B2 COMPLETE")
print("=" * 80)

print(
    "\nImportant:"
)

print(
    "Accident data is contextual city/state-level "
    "information."
)

print(
    "It has NOT been artificially assigned "
    "to individual OSM roads."
)