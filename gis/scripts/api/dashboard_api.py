from pathlib import Path
from typing import Optional

import math
import pandas as pd

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# =============================================================================
# VIGRAH — D4.3 FASTAPI DASHBOARD API
# =============================================================================


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATASET = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "dashboard_alerts.parquet"
)


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="VIGRAH Dashboard API",
    description=(
        "API layer for the VIGRAH "
        "event → road → risk → alert pipeline."
    ),
    version="1.0.0",
)


# =============================================================================
# CORS
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# DASHBOARD API CONTRACT
# =============================================================================

API_FIELDS = [
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


# =============================================================================
# DATA LOADING
# =============================================================================

def load_alerts() -> pd.DataFrame:
    """
    Load the latest dashboard-ready alert dataset.

    The dataset is loaded for every request so that newly generated
    D3/D4.1 data is automatically reflected by the API.
    """

    if not DATASET.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Dashboard alert dataset not found: "
                f"{DATASET}"
            ),
        )

    try:
        df = pd.read_parquet(DATASET)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load dashboard dataset: {exc}",
        )

    return df


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

def validate_api_schema(df: pd.DataFrame):
    """
    Verify that the dashboard dataset satisfies the D4.2 API contract.
    """

    missing = [
        column
        for column in API_FIELDS
        if column not in df.columns
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Dashboard dataset schema is invalid.",
                "missing_columns": missing,
            },
        )


# =============================================================================
# JSON VALUE CLEANING
# =============================================================================

def clean_value(value):
    """
    Convert pandas / NumPy values into JSON-safe Python values.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    return value


def records_from_dataframe(df: pd.DataFrame):
    """
    Convert DataFrame rows into JSON-safe dictionaries.
    """

    records = df.to_dict(orient="records")

    cleaned = []

    for record in records:
        cleaned_record = {
            key: clean_value(value)
            for key, value in record.items()
        }

        cleaned.append(cleaned_record)

    return cleaned


# =============================================================================
# PRIORITY ORDER
# =============================================================================

ALERT_PRIORITY = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def sort_alerts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort alerts by alert severity and then alert score.
    """

    if df.empty:
        return df

    result = df.copy()

    result["_priority"] = (
        result["alert_level"]
        .astype(str)
        .str.upper()
        .map(ALERT_PRIORITY)
        .fillna(0)
    )

    result = (
        result
        .sort_values(
            by=["_priority", "alert_score"],
            ascending=[False, False],
        )
        .drop(columns=["_priority"])
    )

    return result


# =============================================================================
# ROOT
# =============================================================================

@app.get("/")
def root():
    """
    API information and available endpoints.
    """

    return {
        "project": "VIGRAH",
        "service": "Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "dataset": str(DATASET),
        "endpoints": [
            "GET /",
            "GET /health",
            "GET /api/alerts",
            "GET /api/alerts/summary",
            "GET /api/alerts/city/{city}",
            "GET /api/alerts/{alert_id}",
        ],
    }


# =============================================================================
# HEALTH
# =============================================================================

@app.get("/health")
def health():
    """
    Basic API health check.
    """

    return {
        "status": "ok",
        "service": "vigrah-dashboard-api",
        "dataset_available": DATASET.exists(),
    }


# =============================================================================
# GET ALL ALERTS
# =============================================================================

@app.get("/api/alerts")
def get_alerts(
    city: Optional[str] = Query(
        default=None,
        description="Filter by operational city.",
    ),
    alert_level: Optional[str] = Query(
        default=None,
        description="Filter by CRITICAL/HIGH/MEDIUM/LOW.",
    ),
    dashboard_status: Optional[str] = Query(
        default=None,
        description="Filter by ACTION_REQUIRED/INFORMATIONAL.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of alerts.",
    ),
):
    """
    Return dashboard-ready alerts.

    Examples:

        /api/alerts

        /api/alerts?city=Mumbai

        /api/alerts?alert_level=CRITICAL

        /api/alerts?dashboard_status=ACTION_REQUIRED
    """

    df = load_alerts()

    validate_api_schema(df)

    filtered = df.copy()

    # -------------------------------------------------------------------------
    # CITY FILTER
    # -------------------------------------------------------------------------

    if city:
        filtered = filtered[
            filtered["city"]
            .astype(str)
            .str.lower()
            == city.lower()
        ]

    # -------------------------------------------------------------------------
    # ALERT LEVEL FILTER
    # -------------------------------------------------------------------------

    if alert_level:
        filtered = filtered[
            filtered["alert_level"]
            .astype(str)
            .str.upper()
            == alert_level.upper()
        ]

    # -------------------------------------------------------------------------
    # DASHBOARD STATUS FILTER
    # -------------------------------------------------------------------------

    if dashboard_status:
        filtered = filtered[
            filtered["dashboard_status"]
            .astype(str)
            .str.upper()
            == dashboard_status.upper()
        ]

    # -------------------------------------------------------------------------
    # SORT + LIMIT
    # -------------------------------------------------------------------------

    filtered = sort_alerts(filtered)

    filtered = filtered.head(limit)

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    records = records_from_dataframe(
        filtered[API_FIELDS]
    )

    return {
        "count": len(records),
        "alerts": records,
    }


# =============================================================================
# ALERT SUMMARY
# IMPORTANT:
# This route MUST appear before /api/alerts/{alert_id}
# =============================================================================

@app.get("/api/alerts/summary")
def get_alert_summary():
    """
    Return dashboard-level alert statistics.
    """

    df = load_alerts()

    validate_api_schema(df)

    total = len(df)

    # -------------------------------------------------------------------------
    # ALERT LEVEL DISTRIBUTION
    # -------------------------------------------------------------------------

    level_counts = (
        df["alert_level"]
        .astype(str)
        .str.upper()
        .value_counts()
        .to_dict()
    )

    # -------------------------------------------------------------------------
    # DASHBOARD STATUS DISTRIBUTION
    # -------------------------------------------------------------------------

    status_counts = (
        df["dashboard_status"]
        .astype(str)
        .str.upper()
        .value_counts()
        .to_dict()
    )

    # -------------------------------------------------------------------------
    # HISTORICAL PROFILE COUNT
    # -------------------------------------------------------------------------

    historical_available = int(
        df["historical_profile_available"]
        .astype(bool)
        .sum()
    )

    event_only_records = (
        total - historical_available
    )

    # -------------------------------------------------------------------------
    # ACTION REQUIRED COUNT
    # -------------------------------------------------------------------------

    action_required = int(
        (
            df["dashboard_status"]
            .astype(str)
            .str.upper()
            == "ACTION_REQUIRED"
        ).sum()
    )

    informational = (
        total - action_required
    )

    # -------------------------------------------------------------------------
    # SCORE STATISTICS
    # -------------------------------------------------------------------------

    if total > 0:
        mean_alert_score = round(
            float(df["alert_score"].mean()),
            2,
        )

        maximum_alert_score = round(
            float(df["alert_score"].max()),
            2,
        )

    else:
        mean_alert_score = None
        maximum_alert_score = None

    # -------------------------------------------------------------------------
    # RESPONSE
    # -------------------------------------------------------------------------

    return {
        "total_alert_records": total,
        "action_required": action_required,
        "informational": informational,
        "historical_profiles_available": historical_available,
        "event_only_records": event_only_records,
        "alert_levels": level_counts,
        "dashboard_status": status_counts,
        "mean_alert_score": mean_alert_score,
        "maximum_alert_score": maximum_alert_score,
    }


# =============================================================================
# CITY-SPECIFIC ALERTS
# IMPORTANT:
# This route also appears before /api/alerts/{alert_id}
# =============================================================================

@app.get("/api/alerts/city/{city}")
def get_city_alerts(
    city: str,
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of alerts.",
    ),
):
    """
    Return alerts belonging to one operational city.
    """

    df = load_alerts()

    validate_api_schema(df)

    filtered = df[
        df["city"]
        .astype(str)
        .str.lower()
        == city.lower()
    ].copy()

    if filtered.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No alerts found for city '{city}'.",
        )

    filtered = sort_alerts(filtered)

    filtered = filtered.head(limit)

    records = records_from_dataframe(
        filtered[API_FIELDS]
    )

    return {
        "city": city,
        "count": len(records),
        "alerts": records,
    }


# =============================================================================
# GET SINGLE ALERT
# IMPORTANT:
# Parameterized route MUST COME AFTER static routes.
# =============================================================================

@app.get("/api/alerts/{alert_id}")
def get_alert(alert_id: str):
    """
    Return one alert by alert ID.
    """

    df = load_alerts()

    validate_api_schema(df)

    matches = df[
        df["alert_id"].astype(str)
        == str(alert_id)
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Alert '{alert_id}' not found.",
        )

    record = records_from_dataframe(
        matches[API_FIELDS]
    )[0]

    return {
        "alert": record,
    }


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "dashboard_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )