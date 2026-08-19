# 📦 Master System & Feature Handoff Specification

**Project / Module Name:** VIGRAH AI — Layer 5 RESPOND / Decision Support
**Contributor / Owner:** Sakshi
**Readiness Level:** Backend functional and verified; frontend integration pending; Layer 3/Layer 4 production endpoints remain external dependencies.
**Tech Stack & Runtime:** Python 3.10+, FastAPI, SQLAlchemy (async/asyncpg), PostgreSQL with PostGIS extension, Google GenAI SDK (`google-genai`), JWT auth with passlib (bcrypt), Uvicorn.

---

## 1. 🏗️ Architecture, Execution Path & Flow

### High-Level Purpose
The Layer 5 RESPOND backend serves as the decision support center for VIGRAH AI. It ingests connected event graphs (from Layer 3) and geo-historical risk context (from Layer 4), calculates alert priority levels, manages the alert lifecycle (NEW -> ACKNOWLEDGED -> RESOLVED), and facilitates natural-language evidence-based investigation queries through a Gemini AI assistant linked to secure upstream data retrieval clients.

### Complete File/Directory Map
* `app/`
  * `auth/`
    * `dependencies.py`: FastAPI security dependencies (JWT parsing, RBAC validation)
    * `jwt.py`: Password hashing (bcrypt) and JWT signing/verification
  * `crud/`
    * `alert.py`: CRUD methods for alerts (atomic idempotent insert and status transitions)
    * `audit.py`: Audit log record management
    * `investigation.py`: Storing and listing assistant query logs
    * `user.py`: CRUD for user accounts and RBAC bootstrapping seeding logic
  * `integrations/`
    * `base_client.py`: HTTP request wrapper for upstream services (handling authorization tokens, correlation headers, network timeouts, and HTTP exception conversions)
    * `layer3_client.py`: Integration client connecting to Layer 3 REST endpoints
    * `layer4_client.py`: Integration client connecting to Layer 4 REST endpoints
  * `models/`
    * `alert.py`: SQLAlchemy ORM model for Alerts (with PostGIS coordinates tracking)
    * `audit.py`: SQLAlchemy ORM model for Audit trails
    * `base.py`: Declares base metadata object
    * `investigation.py`: SQLAlchemy ORM model for AI query traces and evidence snapshots
    * `user.py`: SQLAlchemy ORM model for Users
  * `routers/`
    * `alerts.py`: Alert endpoints (ingest evaluation, listing, updates)
    * `auth.py`: Authentication session endpoints (login and profile check)
    * `investigation.py`: Investigation assistant query endpoints
    * `users.py`: Management endpoints for users
  * `schemas/`
    * `alert.py`: Ingest request schemas, GeoJSON point formats, and responses
    * `auth.py`: Login models and JWT token wrappers
    * `integration.py`: Upstream schema definitions (entity tracking, timelogs, cameras, GIS)
    * `investigation.py`: Query requests and output schemas
    * `user.py`: Profile structures, creation, and update models
  * `services/`
    * `alert_engine.py`: Evaluates alert priorities and checks geographic discrepancy tolerance limits
    * `llm_service.py`: Uses Gemini GenAI SDK to parse user intents and generate reports
    * `query_executor.py`: Validates parameter ranges and routes queries to correct clients
  * `config.py`: Global environment settings and validation
  * `database.py`: SQLAlchemy async session engine
  * `main.py`: Lifespan hooks (startup migrations & seeding), CORS config, and ASGI routes mapping
* `tests/`: Fully isolated testing suite

### Backend Entry Points & Execution Mode
* **Entry Point**: `app.main:app` (FastAPI instance) run via `uvicorn app.main:app --port 8000`.
* **Execution Mode**: Asynchronous event loop (`async`/`await`) utilizing `asyncpg` for database queries and `httpx.AsyncClient` for upstream integrations.
* **Latency Characteristics**:
  * Root, Auth, and Alert Operations: Low Latency (< 50ms) as they run local database transactions.
  * AI Investigation Assistant (`POST /investigation/query`): Medium/High Latency (1 - 4s) due to calling the Gemini AI models and fetching data dynamically from upstream HTTP servers.

### Complete Data Lifecycle
* **Layer 3 -> Layer 5**: External trigger pushes a Layer 3 event (containing `event_id`, `camera_id`, `event_type`, `timestamp`, coordinates `geom`, confidence, severity, optional `bbox` and `is_verified` boolean).
* **Layer 4 -> Layer 5**: Together with the Layer 3 event, the evaluation request pushes the Layer 4 context (containing coordinates `geom`, `risk_score`, `hotspot`, `historical_incident_count`, `dominant_incident_type`, `peak_time`).
* **Layer 5 -> database**: The Alert Engine validates geographic coordinates consistency (difference must be <= 0.001 degrees). The priority is calculated (`HIGH`/`MEDIUM`/`LOW`). The database checks for duplicate `event_id` (idempotency unique index). If it's a new event, it creates a new alert record (status `NEW`, generated `correlation_id` from transport header `X-Correlation-ID`) and logs the ingest action in `audit_logs`.
* **Layer 5 -> investigation/LLM**: User asks a query. LLM parses the natural language question to a structured `ExtractedIntent` object. The parameter limits (bounds) are checked. The integration clients (`Layer3Client` / `Layer4Client`) retrieve real-time verification data from upstream services. The verified data is stored as a snapshot in `investigation_queries.verified_data`. The LLM synthesizes a markdown report strictly based on this snapshot and returns it to the client.
* **Layer 5 -> frontend/API consumer**: Serving list/detail alerts, timelines, user RBAC, and assistant markdown reports over JWT authenticated JSON endpoints.

---

## 2. 📋 Strict Data Contracts & Schemas

### API Authorization Headers
* **Protected Routes**: Require `Authorization: Bearer <JWT_ACCESS_TOKEN>` header.
* **Correlation Header**: Requests propagate context via `X-Correlation-ID: <string>` header (automatically generated by backend if missing).

### Endpoints Contract Reference

#### POST `/auth/login` (OAuth2 Password flow)
* **Auth**: Public
* **Request**: Form Data (`username`, `password`)
* **Response (HTTP 200)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
* **Error (HTTP 401)**: Incorrect username or password

#### GET `/auth/me`
* **Auth**: Authenticated (JWT)
* **Response (HTTP 200)** *(Note: The values below are illustrative examples only and not production data)*:
  ```json
  {
    "id": "u487da075-8178-4e89-be2a-4a25be256d01",
    "username": "operator_demo",
    "is_active": true,
    "created_at": "2026-08-16T20:30:00"
  }
  ```

#### POST `/alerts/evaluate`
* **Auth**: Upstream ingestion endpoint; authentication/integration policy depends on deployment configuration.
* **Request Body (`AlertEvaluationRequest`)** *(Note: The values below are illustrative examples only and not production data)*:
  ```json
  {
    "event": {
      "event_id": "848da075-8178-4e89-be2a-4a25be256d01",
      "camera_id": "CAM_03",
      "event_type": "accident",
      "timestamp": "2026-08-19T20:31:00Z",
      "geom": {
        "type": "Point",
        "coordinates": [72.456, 19.123]
      },
      "confidence": 0.94,
      "severity": "HIGH",
      "bbox": [100.2, 50.4, 200.5, 150.1],
      "is_verified": false,
      "metadata": null
    },
    "context": {
      "geom": {
        "type": "Point",
        "coordinates": [72.456, 19.123]
      },
      "risk_score": 0.82,
      "hotspot": true,
      "historical_incident_count": 42,
      "dominant_incident_type": "accident",
      "peak_time": "18:00-22:00",
      "gis_context": null
    }
  }
  ```
* **Response (HTTP 201 Created on new, HTTP 200 OK on duplicate ingestion)** *(Note: The values below are illustrative examples only and not production data)*:
  ```json
  {
    "id": "a98da075-8178-4e89-be2a-4a25be256d01",
    "event_id": "848da075-8178-4e89-be2a-4a25be256d01",
    "camera_id": "CAM_03",
    "event_type": "accident",
    "timestamp": "2026-08-19T20:31:00",
    "latitude": 19.123,
    "longitude": 72.456,
    "confidence": 0.94,
    "severity": "HIGH",
    "bbox": [100.2, 50.4, 200.5, 150.1],
    "is_verified": false,
    "risk_score": 0.82,
    "hotspot": true,
    "historical_incident_count": 42,
    "dominant_incident_type": "accident",
    "peak_time": "18:00-22:00",
    "priority": "HIGH",
    "status": "NEW",
    "correlation_id": "CORR_L5_abc123xyz789",
    "acknowledged_by": null,
    "acknowledged_at": null,
    "resolved_by": null,
    "resolved_at": null,
    "created_at": "2026-08-19T08:15:00",
    "updated_at": "2026-08-19T08:15:00"
  }
  ```
* **Validation Check**: Checks coordinate discrepancy: $|event.geom.lat - context.geom.lat| \le 0.001$ and $|event.geom.lon - context.geom.lon| \le 0.001$.
* **Error (HTTP 400 Bad Request)**: Geographic tolerance exceeded.

#### GET `/alerts`
* **Auth**: Authenticated.
* **Params**: `status` (NEW, ACKNOWLEDGED, RESOLVED), `priority` (HIGH, MEDIUM, LOW), `skip`, `limit`
* **Response (HTTP 200)**: List of `AlertResponse` items

#### PATCH `/alerts/{alert_id}`
* **Auth**: Authenticated.
* **Request Body**:
  ```json
  {
    "status": "ACKNOWLEDGED"
  }
  ```
* **Response (HTTP 200)**: Updated `AlertResponse` mapping user ID in `acknowledged_by`/`resolved_by` and stamping timing attributes.

#### POST `/investigation/query`
* **Auth**: Authenticated.
* **Request Body** *(Note: The values below are illustrative examples only and not production data)*:
  ```json
  {
    "question": "Show historical patterns for coordinate 19.123 and 72.456"
  }
  ```
* **Response (HTTP 200)** *(Note: The values below are illustrative examples only and not production data)*:
  ```json
  {
    "id": "q98da075-8178-4e89-be2a-4a25be256d01",
    "user_id": "u487da075-8178-4e89-be2a-4a25be256d01",
    "user_question": "Show historical patterns for coordinate 19.123 and 72.456",
    "llm_intent": {
      "operation": "GET_HISTORICAL_PATTERN",
      "parameters": {
        "latitude": 19.123,
        "longitude": 72.456
      }
    },
    "validation_status": "VALIDATED",
    "query_executed": "Operation: GET_HISTORICAL_PATTERN",
    "verified_data": {
      "geom": {
        "type": "Point",
        "coordinates": [72.456, 19.123]
      },
      "dominant_incident_type": "accident",
      "peak_hours": "18:00-22:00",
      "patterns": [
        {"hour_of_day": 19, "incident_count": 25, "avg_risk_score": 0.82}
      ]
    },
    "llm_response": "### Location Risk Pattern Report\nVerified records show that **accident** is the dominant incident type...",
    "created_at": "2026-08-19T08:16:00"
  }
  ```
* **Error status mapping on upstream dependencies fail**:
  * Timeout $\rightarrow$ `504 Gateway Timeout`
  * Connection failure or invalid upstream schema JSON $\rightarrow$ `502 Bad Gateway`
  * Validation parameters error (e.g. coordinates out of range) $\rightarrow$ `400 Bad Request`

---

### TypeScript Client Interfaces

```typescript
export interface GeoJsonPoint {
  type: "Point";
  coordinates: [number, number]; // [longitude, latitude]
}

export interface UserResponse {
  id: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface AlertResponse {
  id: string;
  event_id: string;
  camera_id: string;
  event_type: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  confidence: number;
  severity: string;
  bbox?: number[] | null;
  is_verified: boolean;
  risk_score: number;
  hotspot: boolean;
  historical_incident_count: number;
  dominant_incident_type: string;
  peak_time: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  status: "NEW" | "ACKNOWLEDGED" | "RESOLVED";
  correlation_id: string;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface QueryResponse {
  id: string;
  user_id: string;
  user_question: string;
  llm_intent?: {
    operation: string;
    parameters: Record<string, any>;
  } | null;
  validation_status: "VALIDATED" | "REJECTED";
  query_executed?: string | null;
  verified_data?: Record<string, any> | null;
  llm_response?: string | null;
  created_at: string;
}
```

---

## 3. 🔄 UI State Machines

The frontend UI must track state transitions accurately:

### Alert Resolution Panel State Flow
* **IDLE** --(User clicks status update toggle)--> **PATCHING / LOADING**
* **PATCHING / LOADING** --(Success Response)--> **SUCCESS** (State updates in-place)
* **PATCHING / LOADING** --(403 Response)--> **FORBIDDEN ERROR** (Toast notification)

### Investigation Assistant Submission Flow
* **IDLE** --(User submits question)--> **SENDING / LOADING**
* **SENDING / LOADING** --(200 Response)--> **SUCCESS** (Render report)
* **SENDING / LOADING** --(400 Response)--> **INTENT FAIL / BAD INPUT** (Show user error)
* **SENDING / LOADING** --(504 Response)--> **TIMEOUT** (Retry option)
* **SENDING / LOADING** --(502 Response)--> **CONNECTION ERROR** (Show warning banner)

---

## 4. 🔌 API Integration Guide

### API Base Endpoint
* `http://localhost:8000` (or set via `VITE_API_BASE_URL` dynamically)

### Fetching Alerts Invalidation Example:
```javascript
const response = await fetch('http://localhost:8000/alerts?status=NEW', {
  headers: { 'Authorization': `Bearer ${token}` }
});
if (response.status === 401) console.error("Unauthorized session");
const alerts = await response.json();
```

---

## 5. 🧩 Data Transformers

1. **Coordinates Mapping**:
   * **Backend format**: Flat `latitude`, `longitude` properties on Alert responses.
   * **Map layer conversion**: Transform properties into standard leaflet/mapbox latlng objects: `L.latLng(alert.latitude, alert.longitude)`.
2. **GeoJSON conversion**:
   * **Input**: `geom: GeoJsonPoint` (`coordinates: [longitude, latitude]`).
   * **Output**: Map visualizer targets `geom.coordinates[1]` for Latitude and `geom.coordinates[0]` for Longitude.
3. **Badge mapping**:
   * Map `priority` levels (`HIGH`, `MEDIUM`, `LOW`) to color badges:
     * `HIGH` -> Deep Crimson (`#DC2626`)
     * `MEDIUM` -> Vivid Amber (`#D97706`)
     * `LOW` -> Slate Gray (`#4B5563`)
4. **Display Timestamp**:
   * Transform ISO string `created_at` to human readable local string: `new Date(alert.timestamp).toLocaleString()`.
5. **Timeline generation**:
   * Map the `timeline` array from `EventTimelineResponse` snapshot records into a visual timeline component rendering date nodes with text descriptions.

---

## 6. 🛡️ Authentication & Security

* **JWT Verification**: Bearer tokens are signed via HS256 utilizing `JWT_SECRET`. Tokens expire after 60 minutes.
* **Authorization Model**: A single-role authentication model is used. All endpoints require a valid authenticated user session (verified via JWT Bearer Token). Distinctions between roles and permissions have been removed.
* **CORS policy**: Configured globally in `main.py` using `allow_origins=["*"]`.
* **LLM Safety and SQL Protection**:
  * The natural language question never touches database query interpreters directly.
  * The LLM maps intents strictly to allowlisted programmatic operations.
  * Extracted parameters undergo type checks and bounding validation inside the `QueryExecutor` before invocation.
* **Audit Trail**: Administrative actions (such as user creation, alert status updates, and query evaluations) write immutable log entries in the database.

---

## 7. 🗄️ Database Architecture

* **Database Technology**: PostgreSQL (with PostGIS extensions).
* **Tables schema**:
  * `users`: `id` (String(36) PK), `username` (String(100) UNIQUE), `hashed_password` (String(255)), `is_active` (Boolean).
  * `alerts`: `id` (String(36) PK), `event_id` (String(100) UNIQUE), `camera_id` (String(50)), `event_type` (String(100)), `timestamp` (DateTime), `latitude` (Float), `longitude` (Float), `confidence` (Float), `severity` (String(50)), `bbox` (JSON - maps to native `JSON` type, not `JSONB`), `is_verified` (Boolean), `risk_score` (Float), `hotspot` (Boolean), `historical_incident_count` (Integer), `dominant_incident_type` (String(100)), `peak_time` (String(50)), `priority` (String(50)), `status` (String(50)), `correlation_id` (String(100) Index), `acknowledged_by` (String(36) FK), `resolved_by` (String(36) FK).
  * `investigation_queries`: `id` (String(36) PK), `user_id` (String(36) FK), `user_question` (Text), `llm_intent` (JSON - maps to native `JSON` type, not `JSONB`), `validation_status` (String(50)), `query_executed` (String(255)), `verified_data` (JSON - maps to native `JSON` type, not `JSONB`), `llm_response` (Text).
  * `audit_logs`: `id` (String(36) PK), `user_id` (String(36)), `action` (String(100) Index), `details` (JSON - maps to native `JSON` type, not `JSONB`), `ip_address` (String(45)), `timestamp` (DateTime).

---

## 8. 🤖 Investigation Assistant

* **Intents allowed in `query_executor.py`**:
  * `GET_ENTITY_HISTORY`: Requires parameter `entity_id` (string). Queries Layer 3.
  * `GET_EVENT_TIMELINE`: Requires parameter `event_id` (string). Queries Layer 3.
  * `GET_EVENT_ENTITIES`: Requires parameter `event_id` (string). Queries Layer 3.
  * `GET_CAMERA_HISTORY`: Requires parameter `camera_id` (string). Queries Layer 3.
  * `GET_NEARBY_INCIDENTS`: Requires parameters `latitude` and `longitude` within range, and optional positive `radius_meters`. Queries Layer 4.
  * `GET_HISTORICAL_PATTERN`: Requires coordinates. Queries Layer 4.
  * `GET_LOCATION_CONTEXT`: Requires coordinates. Queries Layer 4.
* **LLM Limitations**:
  * The LLM model configuration runs with low temperature (`0.0` for extraction, `0.2` for response generation).
  * It is not allowed to search external databases or guess missing facts; it must generate Markdown text using only the JSON payload in `verified_data`.

---

## 9. 🚨 Alert Engine

* **Priority rules**:
  * **HIGH**: `confidence >= 0.85` AND `severity == "HIGH"`
  * **MEDIUM**: `confidence >= 0.70`
  * **LOW**: All other fallback detections
* **Evaluation Flow**:
  1. The API receives an event and spatial context.
  2. Geographic tolerance limits are validated.
  3. Priority is calculated.
  4. Database inserts Alert atomically checking unique event ID constraints.
  5. The API responds with alert records immediately.

---

## 10. 🧪 Testing & Verification

* **Unit Tests**: Cover JWT auth, alert consistency validation, LLM intent validator checks, and client timeout simulation checks.
* **PostgreSQL Integration Tests**: Live DB testing evaluates unique index constraints and `ST_DWithin` PostGIS functions.
* **Verification Status**:
  * SQLite/Mock unit tests: **18 Passed** (100% Success)
  * PostgreSQL/PostGIS integration was successfully verified against the Neon database: **19 Passed, 0 Failed** (all unit and integration tests passed).

---

## 11. ⚙️ Environment Dependencies

* **Python Version**: `3.10+` (packages listed in `requirements.txt`)
* **PostgreSQL Version**: Neon PostgreSQL `18.4` (local Docker database container uses PostgreSQL `15`)
* **PostGIS Version**: Neon PostGIS `3.6` (local Docker database container uses PostGIS `3.3`)
* **Docker Requirements**: Docker engine running compose version v2.
* **Environment configurations (`.env` placeholders)**:
  ```env
  DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>:<port>/<dbname>
  TEST_DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>:<port>/<test_dbname>
  JWT_SECRET=<secure_signing_key>
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=60
  GEMINI_API_KEY=<gemini_api_key_from_google_ai_studio>
  GEMINI_MODEL=gemini-1.5-flash
  LAYER3_BASE_URL=http://<layer3_host>:<port>
  LAYER3_CLIENT_TOKEN=<token_for_l3_access>
  LAYER4_BASE_URL=http://<layer4_host>:<port>
  LAYER4_CLIENT_TOKEN=<token_for_l4_access>
  INTEGRATION_TIMEOUT_SECONDS=5.0
  GEOGRAPHIC_TOLERANCE=0.001
  ```

---

## 12. 🚀 Frontend Wiring Checklist

- [ ] Configure environment: Set up `.env` with `VITE_API_BASE_URL` pointing to FastAPI.
- [ ] Configure API base URL: Set headers authorization and client timeout behaviors.
- [ ] Configure authentication: Setup login screen and store JWT token in localStorage/cookies.
- [ ] Implement API client: Configure base routes fetching `/alerts` and `/investigation/query`.
- [ ] Implement alert screen: Display high/medium/low priority badges.
- [ ] Implement status transitions: Add options to acknowledge or resolve alerts on card selections.
- [ ] Implement investigation UI: Render markdown responses from Gemini cleanly.
- [ ] Implement loading states: Display skeletons during long AI analysis loops.
- [ ] Implement error states: Handle API gateways timeout (`504`) or connections down (`502`) gracefully.
- [ ] Implement map/geospatial visualization: Display marker layers on Mapbox/Leaflet using the coordinate attributes.
- [ ] Implement timeline: Render historical event chronologies.
- [ ] Implement user session verification: Redirect user to login page if authentication fails or expires.
