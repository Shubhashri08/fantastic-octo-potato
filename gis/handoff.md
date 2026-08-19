# 📦 Master System & Feature Handoff Specification

**Project / Module Name:** VIGRAH — Visual Intelligence & GIS Risk Assessment Hub (GIS & Alert Engine)  
**Contributor / Owner:** Geospatial & Risk Intelligence Engineering Team  
**Readiness Level:** Production-Ready (Verified on Mumbai & Bengaluru, Neon DB Integrated)  
**Tech Stack & Runtime:** Python 3.13 / FastAPI, Uvicorn, Neon PostgreSQL (PostGIS), GeoPandas, PyArrow, Leaflet.js  

---

## 1. 🏗️ Architecture, Execution Path & Flow

### High-Level Purpose
VIGRAH is an end-to-end geospatial intelligence, road-level risk profiling, CCTV mapping, and real-time surveillance alerting engine. It ingests Layer-3 incident events, snaps them via spatial nearest-neighbor algorithms to OpenStreetMap (OSM) road networks, enriches them with unsupervised machine learning risk profiles ($50$ features across $844$ road segments), and serves prioritized, dashboard-ready alerts via a REST API.

### File & Directory Map
* **Backend API & Ingestion:**
  * [`gis/scripts/api/dashboard_api.py`](gis/scripts/api/dashboard_api.py) → FastAPI application serving `/api/alerts`, `/api/alerts/summary`, `/api/alerts/city/{city}`, and `/api/alerts/{alert_id}`.
  * [`gis/dashboard/index.html`](gis/dashboard/index.html) → Leaflet.js GIS Command Center frontend with live alert feed and telemetry inspection.
* **Core Processing Pipeline (`gis/scripts/processing/`):**
  * `01_extract_roads.py` → Extracts and standardizes OSM road networks for Mumbai & Bengaluru.
  * `02_prepare_cctv.py` & `03_match_cctv_roads.py` → Standardizes 1,551 CCTV camera locations and snaps them to roads.
  * `06_prepare_accident_features.py` & `09_prepare_crime_features.py` → Computes contextual macro-benchmarks from NCRB 2023 & Census 2011.
  * `14_build_baseline_risk.py` & `17_evaluate_ml_patterns.py` → Isolation Forest anomaly detection & 50-feature road profiling.
  * `20_map_events_to_roads.py` → Snaps live incident events to road vectors.
  * `21_enrich_events_with_risk.py` → Enriches live events with road risk profiles.
  * `22_generate_alerts.py` → Computes dynamic hybrid alert score: $\text{Score} = 0.60 \times (\text{Event}) + 0.40 \times (\text{Road Risk})$.
  * `23_prepare_dashboard_alerts.py` → Enforces schema and UI presentation formatting.
  * `24_validate_dashboard_contract.py` → Strict JSON contract validation.
* **Storage & Database:**
  * `gis/data/processed/features/dashboard_alerts.parquet` → Processed alert dataset.
  * `gis/data/processed/features/dashboard_api_contract.json` → JSON API contract.
  * Neon PostgreSQL (`public.alerts`) → Cloud relational persistence layer.

### Execution Mode & Latency Profile
* **Type:** Instant Synchronous REST (< 50ms per request) with file-backed / DB-backed real-time caching.
* **Estimated Latency:** ~15–35ms average response time for full alert queries and summary aggregates.

### Data Flow Lifecycle
```
[ Incoming Incident / Layer-3 JSON ]
               │
               ▼
[ 20_map_events_to_roads.py ] (Spatial Snapping to nearest OSM Road Vector)
               │
               ▼
[ 21_enrich_events_with_risk.py ] (Join with 844 Road ML Risk Profiles)
               │
               ▼
[ 22_generate_alerts.py ] (Calculate Hybrid Alert Score: 60% Event + 40% Risk)
               │
               ▼
[ 23_prepare_dashboard_alerts.py ] (Enforce Schema & Status Flags)
               │
               ▼
[ Neon PostgreSQL 'alerts' Table & Parquet Store ]
               │
               ▼
[ FastAPI Server: dashboard_api.py (Port 8000) ]
               │
               ▼
[ Frontend UI: Leaflet.js Dashboard (Port 3000) ]
```

---

## 2. 📋 Strict Data Contracts & Schemas

### A. Input Query Parameters (What Frontend Sends)

#### Endpoint: `GET /api/alerts`
```typescript
interface AlertQueryParams {
  city?: 'Mumbai' | 'Bengaluru' | string;       // Optional city filter
  severity?: 'high' | 'medium' | 'low' | string;// Filter by event severity
  alert_level?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'; // Filter by priority level
  status?: 'ACTION_REQUIRED' | 'INFORMATIONAL'; // Filter by operational status
  limit?: number;                              // Maximum records to return (Default: all)
}
```

#### Endpoint: `GET /api/alerts/{alert_id}`
* **Path Parameter:** `alert_id` (e.g. `"VIGRAH-TEST-EVT-001"`)

---

### B. Output Response Schemas (What Backend Returns)

#### 1. Alert Collection Response: `GET /api/alerts`
```typescript
interface AlertListResponse {
  count: number;
  alerts: AlertRecord[];
}

interface AlertRecord {
  alert_id: string;                      // e.g. "VIGRAH-TEST-EVT-001"
  event_id: string;                      // e.g. "TEST-EVT-001"
  city: 'Mumbai' | 'Bengaluru';          // City name
  road_id: number;                       // OSM Road identifier (e.g. 22848180)
  road_display_name: string;             // Human-readable road name (e.g. "Road No 19")
  event_type_label: string;              // Formatted label (e.g. "Suspicious Activity")
  severity_label: 'High' | 'Medium' | 'Low'; // Formatted severity
  confidence: number;                    // Detection probability (0.00 to 1.00)
  event_to_road_distance_m: number;      // Distance in meters to snapped road
  alert_score: number;                   // Hybrid score (0.00 to 100.00)
  alert_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'; // Action tier
  dashboard_status: 'ACTION_REQUIRED' | 'INFORMATIONAL'; // Operator requirement
  historical_profile_available: boolean; // True if historical road risk profile exists
  alert_context_status: string;          // e.g. "event_only_no_historical_profile"
  map_latitude: number;                  // WGS84 Latitude
  map_longitude: number;                 // WGS84 Longitude
}
```

#### 2. System KPI Summary Response: `GET /api/alerts/summary`
```typescript
interface AlertSummaryResponse {
  total_alert_records: number;           // Total alerts registered
  action_required: number;               // Count of ACTION_REQUIRED alerts
  informational: number;                 // Count of INFORMATIONAL alerts
  historical_profiles_available: number; // Alerts enriched with historical profiles
  event_only_records: number;            // Alerts using 100% current event evidence
  alert_levels: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  dashboard_status: {
    ACTION_REQUIRED: number;
    INFORMATIONAL: number;
  };
  mean_alert_score: number;              // Average alert score across all events
  maximum_alert_score: number;           // Maximum alert score
}
```

---

## 3. 🖥️ UI State Machine & Component Requirements

### Alert Severity & Priority Visual Tokens

| Priority Level | Visual Badge / Dot Color | Action Requirement | Threshold Formula |
| :--- | :--- | :--- | :--- |
| **`CRITICAL`** | Red (`#ef4444` / Crimson Glow) | Immediate Dispatch (`ACTION_REQUIRED`) | Score $\ge 75.0$ |
| **`HIGH`** | Orange (`#f97316` / Amber Glow) | Officer Review (`ACTION_REQUIRED`) | Score $60.0 - 74.9$ |
| **`MEDIUM`** | Yellow / Amber (`#eab308`) | Surveillance Monitor (`ACTION_REQUIRED`) | Score $45.0 - 59.9$ |
| **`LOW`** | Blue (`#3b82f6` / Slate) | Logged only (`INFORMATIONAL`) | Score $< 45.0$ |

### UI State Machine

```
[ INITIALIZING ]
       │
       ▼ (Fetch /api/alerts/summary & /api/alerts)
[ DATA_LOADED ] ◄────────────────────────────────────────┐
       │                                                 │
       ├───────────────► [ FILTERING_CITY ] (Mumbai/Blr) ─┤
       │                                                 │
       ├───────────────► [ FILTERING_PRIORITY ] (Crit..) ─┤
       │                                                 │
       └───────────────► [ INSPECTING_ALERT ] (Modal/Pin)─┘
```

---

## 4. 🔄 Data Transformers & Adapters

```typescript
/**
 * Transforms raw API alert records into UI Map Marker view models.
 */
export function transformAlertToMapMarker(alert: AlertRecord) {
  return {
    id: alert.alert_id,
    coordinates: [alert.map_latitude, alert.map_longitude] as [number, number],
    title: `${alert.alert_level}: ${alert.event_type_label}`,
    subtitle: `${alert.road_display_name}, ${alert.city}`,
    color: alert.alert_level === 'CRITICAL' ? '#ef4444' :
           alert.alert_level === 'HIGH' ? '#f97316' :
           alert.alert_level === 'MEDIUM' ? '#eab308' : '#3b82f6',
    score: alert.alert_score,
    requiresAction: alert.dashboard_status === 'ACTION_REQUIRED',
    popupHtml: `
      <div class="vigrah-popup">
        <h4 style="color: ${alert.alert_level === 'CRITICAL' ? '#ef4444' : '#f97316'}">
          ${alert.alert_level} ALERT (${alert.alert_score}/100)
        </h4>
        <p><strong>Event:</strong> ${alert.event_type_label}</p>
        <p><strong>Location:</strong> ${alert.road_display_name} (${alert.city})</p>
        <p><strong>Confidence:</strong> ${(alert.confidence * 100).toFixed(1)}%</p>
        <p><strong>Road Distance:</strong> ${alert.event_to_road_distance_m.toFixed(1)}m</p>
        <p><strong>Status:</strong> ${alert.dashboard_status}</p>
      </div>
    `
  };
}
```

---

## 5. 🛡️ Mock Fallback Data (For Offline / Isolated Frontend Testing)

```typescript
export const MOCK_ALERTS_FALLBACK: AlertListResponse = {
  count: 4,
  alerts: [
    {
      alert_id: "VIGRAH-TEST-EVT-001",
      event_id: "TEST-EVT-001",
      city: "Mumbai",
      road_id: 22848180,
      road_display_name: "Road No 19",
      event_type_label: "Suspicious Activity",
      severity_label: "High",
      confidence: 0.91,
      event_to_road_distance_m: 4.73,
      alert_score: 86.8,
      alert_level: "CRITICAL",
      dashboard_status: "ACTION_REQUIRED",
      historical_profile_available: false,
      alert_context_status: "event_only_no_historical_profile",
      map_latitude: 19.0176,
      map_longitude: 72.8562
    },
    {
      alert_id: "VIGRAH-TEST-EVT-003",
      event_id: "TEST-EVT-003",
      city: "Bengaluru",
      road_id: 1238638853,
      road_display_name: "Vittal Mallya Road",
      event_type_label: "Suspicious Activity",
      severity_label: "High",
      confidence: 0.88,
      event_to_road_distance_m: 29.44,
      alert_score: 64.42,
      alert_level: "HIGH",
      dashboard_status: "ACTION_REQUIRED",
      historical_profile_available: false,
      alert_context_status: "event_only_no_historical_profile",
      map_latitude: 12.9716,
      map_longitude: 77.5946
    },
    {
      alert_id: "VIGRAH-TEST-EVT-002",
      event_id: "TEST-EVT-002",
      city: "Mumbai",
      road_id: 102178070,
      road_display_name: "Dr Babasaheb Ambedkar Marg (Vincent Road)",
      event_type_label: "Crowd Anomaly",
      severity_label: "Medium",
      confidence: 0.84,
      event_to_road_distance_m: 49.39,
      alert_score: 47.78,
      alert_level: "MEDIUM",
      dashboard_status: "ACTION_REQUIRED",
      historical_profile_available: false,
      alert_context_status: "event_only_no_historical_profile",
      map_latitude: 19.0188,
      map_longitude: 72.8478
    },
    {
      alert_id: "VIGRAH-TEST-EVT-004",
      event_id: "TEST-EVT-004",
      city: "Bengaluru",
      road_id: 226972108,
      road_display_name: "Unnamed road",
      event_type_label: "Vehicle Anomaly",
      severity_label: "Low",
      confidence: 0.76,
      event_to_road_distance_m: 40.66,
      alert_score: 30.22,
      alert_level: "LOW",
      dashboard_status: "INFORMATIONAL",
      historical_profile_available: false,
      alert_context_status: "event_only_no_historical_profile",
      map_latitude: 12.9750,
      map_longitude: 77.5990
    }
  ]
};
```

---

## 6. ⚙️ Environment Variables & Wiring

### Environment Variables
Place in `gis/.env`:
```env
# Neon PostgreSQL Database Connection (Must remain private, excluded in .gitignore)
DATABASE_URL=postgresql://neondb_owner:[PASSWORD]@[HOST]/neondb?sslmode=require

# Backend API Configuration
API_PORT=8000
API_HOST=127.0.0.1
CORS_ORIGINS=*
```

### Local Execution Instructions
```bash
# 1. Install runtime dependencies
pip install fastapi uvicorn pandas pyarrow geopandas psycopg2-binary

# 2. Launch FastAPI Backend Service
python3 -m uvicorn dashboard_api:app --app-dir gis/scripts/api --host 127.0.0.1 --port 8000 --reload

# 3. Launch Frontend Web Server
python3 -m http.server 3000 --directory gis/dashboard
```

### Direct Endpoints
* **Frontend Web Dashboard:** `http://localhost:3000`
* **Backend REST API:** `http://127.0.0.1:8000`
* **Swagger API Documentation:** `http://127.0.0.1:8000/docs`
