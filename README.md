# VIGRAH AI — Visual Intelligence & Geospatial Response Hub
### Unified Multi-Model CCTV Intelligence, Forensic Re-Identification & Tactical Response Platform

VIGRAH AI is an open-source, local intelligence system designed for municipal security, CCTV forensic investigation, and smart-city situational response. The platform ingests multi-camera live feeds (Webcam, RTSP, Video Footage), runs multi-model YOLO detection with temporal confirmation filters, performs vector appearance Re-Identification for Missing Persons and Vehicles, reconstructs incident progression vectors, and enables rapid tactical dispatch across an interactive geospatial interface.

---

## 🏛️ System Architecture — 4 Operational Layers

```
                                  VIGRAH AI PLATFORM
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │  1. SENSE (Surveillance)                                                         │
 │     • Multi-camera stream ingestion (Webcam, RTSP, Video feeds)                  │
 │     • Multi-model YOLO inference (Fire/Smoke, Accidents, Fighting, Pedestrians) │
 │     • Temporal confirmation filters & auto DVR incident recording (10s clips)    │
 ├──────────────────────────────────────────────────────────────────────────────────┤
 │  2. UNDERSTAND (GIS)                                                             │
 │     • Geospatial situational map (Leaflet dark topology)                         │
 │     • Distributed camera node telemetry & active threat markers                  │
 ├──────────────────────────────────────────────────────────────────────────────────┤
 │  3. IDENTIFY (Forensics & Re-ID)                                                 │
 │     • Missing Person Video Re-ID: Sampled frame tracking & 128-D vector search   │
 │     • Vehicle Finder: License plate lookup, visual attribute search & flagging   │
 │     • Incident Audit Log: Verified evidence lifecycle and telemetry records      │
 ├──────────────────────────────────────────────────────────────────────────────────┤
 │  4. RESPOND (Tactical Action)                                                    │
 │     • Event Reconstruction Engine: Multi-modal escape & spread vector prediction │
 │     • Tactical Dispatch: Perimeter lockdowns, emergency alerts & containment     │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Highlights & Core Capabilities

- **Missing Person Video Re-ID**:
  - Ingests recorded CCTV video evidence files (`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`).
  - Samples frames at 2–3 FPS, tracks individuals across time clusters (`TRK-001`, `TRK-002`), and saves verified person crops.
  - Generates 128-D normalized hybrid appearance vectors (HSV spatial histogram + Sobel texture gradients).
  - Performs cosine similarity ranking with strict Top-5 best matches, minimum similarity threshold slider, and source feed filtering.
  - Side-by-side forensic profile comparison (Query Photo vs Matched CCTV Video Crop) with occurrence timeline.

- **Vehicle Identification & Re-ID**:
  - License plate query search & visual attribute filtering (color, make, type).
  - Real-time vehicle stolen/flagged status toggle with audit logging.
  - Last spotted location coordinates and sighting timestamps.

- **Event Reconstruction & Path Prediction Engine**:
  - Multi-modal analysis calibrated by threat class:
    - **Vehicle Incidents** (Hit & Run, Stolen Car): High-speed arterial highways, ring roads, traffic bottlenecks.
    - **Pedestrian Incidents** (Fighting, Robbery, Panic): Subway exits, pedestrian corridors, metro transit gates.
    - **Physical Hazards** (Fire, Smoke, Gas): Thermal spread vectors, evacuation containment perimeters.
  - Calculates escape likelihood percentages, estimated transit times, and intercept camera nodes.

- **Hardware Optimized**:
  - Tuned for low-latency edge inference with FP16 half-precision and automatic CPU fallback.
  - Zero paid dependencies: PyTorch, Ultralytics YOLO, FastAPI, SQLite, React, Vite, and Leaflet.

---

## 📂 Repository Structure

```
fantastic-octo-potato/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI server & REST/Evidence endpoints
│   │   ├── database.py              # SQLite engine & session management
│   │   ├── models.py                # Database models (Cameras, Events, Videos, Tracks, Sightings)
│   │   ├── schemas.py               # Pydantic request/response schemas
│   │   ├── detection.py             # YOLO multi-model detector & temporal tracker
│   │   ├── stream_manager.py        # Multi-camera worker pool & MJPEG streaming
│   │   ├── video_person_engine.py   # Video sampling, person tracking, 128-D Re-ID & vector search
│   │   ├── reconstruction_engine.py # Multi-modal path prediction & escape vector engine
│   │   ├── vehicle_service.py       # Vehicle metadata, plate search & flagging
│   │   └── seed_data.py             # Database seeder & default camera network
│   ├── evidence/                    # Stored person crop evidence images
│   ├── sample_media/                # CCTV demo videos (CSMT, MG Road, Marine Drive, etc.)
│   ├── snapshots/                   # Automated incident snapshots
│   ├── test_person_finder_video_reid.py # Automated test suite for Person Re-ID
│   ├── test_distributed_reconstruction_suite.py # Automated test suite for Path Prediction
│   └── requirements.txt             # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx           # Telemetry header & status bar
│   │   │   ├── Navigation.jsx       # 4-layer navigation menu
│   │   │   ├── SurveillanceConsole.jsx # Layer 1: Live surveillance feeds & threat alerts
│   │   │   ├── GisConsole.jsx       # Layer 2: Geospatial map & camera nodes
│   │   │   ├── IdentifyConsole.jsx  # Layer 3: Person Finder, Vehicle Finder & Audit Log
│   │   │   ├── RespondConsole.jsx   # Layer 4: Event Reconstruction & Tactical Dispatch
│   │   │   └── ReconstructionMap.jsx# GIS path prediction visualization
│   │   ├── api/
│   │   │   ├── client.js            # Base HTTP client with timeout management
│   │   │   ├── cameras.js           # Camera API client
│   │   │   ├── events.js            # Events & incidents API client
│   │   │   ├── persons.js           # Video evidence & Person Re-ID client
│   │   │   ├── vehicles.js          # Vehicle search & flagging client
│   │   │   └── reconstruction.js    # Event Reconstruction client
│   │   ├── App.jsx                  # Main application router & state
│   │   └── index.css                # Dark mode tactical CSS design system
│   ├── package.json
│   └── vite.config.js               # Proxy configuration (/api, /evidence, /stream)
├── .env.example             # Example environment variables template
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Configuration

Copy the `.env.example` template to `.env` in the root directory:

```bash
cp .env.example .env
```

### Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./vigrah.db` | SQLAlchemy database URL (SQLite or PostgreSQL / Neon DB) |
| `MEDIA_STORAGE_DIR` | `./recordings` | Directory path for auto-saved 10s incident MP4 clips |
| `SNAPSHOTS_STORAGE_DIR` | `./snapshots` | Directory path for verified incident JPEG snapshots |
| `EVIDENCE_STORAGE_DIR` | `./evidence` | Directory path for extracted Person Re-ID crops |
| `HOST` | `127.0.0.1` | Backend server host interface |
| `PORT` | `8000` | Backend server port |
| `CONF_THRESHOLD` | `0.35` | Minimum YOLO detection confidence threshold |
| `TEMPORAL_PERSISTENCE_FRAMES` | `3` | Number of consecutive frames needed to confirm an incident |
| `INCIDENT_COOLDOWN_SECONDS` | `10` | Cooldown period between duplicate alert triggers |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+ and `npm`

---

### 1. Start Backend Server

Open a terminal in `backend/`:

```bash
cd backend

# (Optional) Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend runs at `http://127.0.0.1:8000`. On startup, it automatically creates the database schema, seeds distributed camera nodes, and indexes sample video evidence.

---

### 2. Start Frontend Server

Open a second terminal in `frontend/`:

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Running Automated Test Suites

The backend includes test suites verifying data integrity, vector search, and path prediction:

```bash
# 1. Person Finder & Video Evidence Re-ID Test Suite
python3 backend/test_person_finder_video_reid.py

# 2. Distributed Event Reconstruction & Path Prediction Test Suite
python3 backend/test_distributed_reconstruction_suite.py
```

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cameras` | List all registered camera nodes |
| `GET` | `/api/events` | List recorded incidents (filter by type/severity/camera) |
| `GET` | `/stream/{camera_id}` | Live low-latency MJPEG video stream |
| `POST` | `/api/start_detection` | Start/restart stream worker and detection engine |
| `GET` | `/api/status` | System status, active workers, and engine telemetry |
| `GET` | `/api/person/videos` | List indexed video evidence sources with track statistics |
| `POST` | `/api/person/videos/upload` | Upload and process CCTV video footage |
| `DELETE` | `/api/person/videos/{source_id}` | Delete a video evidence source and associated tracks |
| `POST` | `/api/person/search` | Missing Person Re-ID search by query image (Top-5 ranked) |
| `GET` | `/api/person/evidence/{source_id}/{track_id}` | Direct endpoint serving verified representative crop image |
| `GET` | `/api/person/evidence/{source_id}/{track_id}/{filename}` | Direct endpoint serving specific sighting crop image |
| `GET` | `/api/vehicles/search` | Search vehicles by plate number or visual attributes |
| `POST` | `/api/vehicles/flag` | Flag or unflag a vehicle with reason and priority |
| `POST` | `/api/reconstruction/analyze` | Multi-modal path prediction and escape vector analysis |

---

## 🛡️ License

This project is open-source under the MIT License.
