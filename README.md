# VIGRAH AI (Visual Intelligence & Geospatial Response Hub)
### Phase 1 Prototype — Real-Time Video Analytics, Multi-Model Incident Detection & Geospatial Dashboard

VIGRAH AI is an open-source, local intelligence platform designed for municipal and smart-city surveillance. It processes multi-camera feeds (Webcam, RTSP, Video Files), performs real-time multi-model YOLO inference for incident detection (Fire/Smoke, Accidents, Vehicles, Pedestrians), applies temporal confirmation filters to eliminate false alarms, and streams live MJPEG video feeds to a geospatial React dashboard.

---

## ⚡ Key Highlights
- **Hardware Optimized**: Tuned for NVIDIA RTX 2050 (4GB VRAM) with FP16 half-precision and 3-frame subsampling, plus automatic CPU fallback.
- **Zero Paid Services**: 100% free open-source stack using PyTorch, Ultralytics YOLO, Hugging Face models, FastAPI, SQLite, and Leaflet.
- **Temporal Confirmation**: Incidents are confirmed only when detected in $\ge 3$ consecutive sampled frames with automated snapshot storage.
- **Full Live Streaming**: Low-latency MJPEG streaming directly via FastAPI `StreamingResponse`.
- **Geospatial Intelligence**: Interactive dark-themed Leaflet map showing CCTV camera nodes, GPS coordinates, and real-time alert markers.

---

## 📂 Project Structure

```
vigrah-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application & REST/streaming endpoints
│   │   ├── database.py          # SQLite & SQLAlchemy engine configuration
│   │   ├── models.py            # Camera and Event database models
│   │   ├── schemas.py           # Pydantic validation schemas
│   │   ├── detection.py         # Multi-model YOLO detection core & temporal tracker
│   │   ├── stream_manager.py    # Multi-camera worker pool & MJPEG generator
│   │   ├── model_downloader.py  # Automated Hugging Face model loader & fallbacks
│   │   └── seed_data.py         # Auto-seeder for default cameras & test video generator
│   ├── main.py                  # Entrypoint for running `uvicorn main:app --reload`
│   ├── sample_media/            # Local synthetic/demo traffic video files
│   ├── snapshots/               # Auto-saved incident snapshot images
│   ├── weights/                 # Local YOLO model weights
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx           # Top telemetry bar & status indicators
│   │   │   ├── LiveStreamGrid.jsx   # MJPEG live video feeds with source switching
│   │   │   ├── CameraMap.jsx        # Leaflet interactive map with camera markers
│   │   │   ├── EventTable.jsx       # Real-time incident log table with filters
│   │   │   └── SnapshotModal.jsx    # Lightbox verification modal for snapshots
│   │   ├── App.jsx              # Main dashboard composition
│   │   ├── index.css            # Dark mode glassmorphism design system
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js           # Proxy configuration to backend
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup & Run

Open a terminal in the `backend/` directory:

```bash
cd d:/test/sih/backend

# (Optional) Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload
```
The backend will launch at `http://localhost:8000`. On first start, it automatically:
1. Creates `vigrah.db` (SQLite).
2. Generates a synthetic traffic demo video (`traffic_demo.mp4`).
3. Downloads YOLO weights (`yolo11n.pt`, Fire/Smoke models) and loads them onto CUDA/GPU or CPU.
4. Starts stream workers for active cameras.

### 2. Frontend Setup & Run

Open a second terminal in the `frontend/` directory:

```bash
cd d:/test/sih/frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🗄️ Database Schema (SQLite)

- **`cameras`**:
  - `id` (INTEGER, Primary Key)
  - `name` (STRING)
  - `source` (STRING - Webcam `0`, Video Path, or RTSP URL)
  - `source_type` (STRING - `webcam`, `video`, `rtsp`)
  - `lat` (FLOAT), `lon` (FLOAT)
  - `is_active` (BOOLEAN)
  - `created_at` (DATETIME)

- **`events`**:
  - `id` (INTEGER, Primary Key)
  - `camera_id` (INTEGER, Foreign Key)
  - `event_type` (STRING - `Fire`, `Smoke`, `Accident`, `Fighting`, `Vehicle`, `Person`)
  - `confidence` (FLOAT)
  - `timestamp` (DATETIME)
  - `bbox` (TEXT - JSON coordinates `[x1, y1, x2, y2]`)
  - `snapshot_path` (STRING - `/snapshots/...`)
  - `severity` (STRING - `High`, `Medium`, `Low`)

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cameras` | List all registered camera nodes |
| `POST` | `/api/cameras` | Register a new camera node |
| `PUT` | `/api/cameras/{id}` | Update camera source or GPS coordinates |
| `GET` | `/api/events` | List recorded incidents (filter by type/severity/camera) |
| `GET` | `/stream/{camera_id}` | Live MJPEG video stream |
| `POST` | `/api/start_detection` | Start/restart stream and detection worker |
| `POST` | `/api/stop_detection` | Pause camera stream worker |
| `GET` | `/api/status` | Real-time GPU telemetry, engine mode, active workers |
| `GET` | `/snapshots/{filename}`| Static file endpoint for verified snapshot images |

---

## 🎮 Testing Video & Webcam Switching

From the frontend dashboard:
1. Click **Config** on any camera card in the Live Surveillance Grid.
2. Select **WEBCAM** (sets input to `0`), **VIDEO** (selects demo MP4), or **RTSP**.
3. Click **Apply & Stream**.
4. The backend dynamically switches the stream worker and immediately resumes multi-model inference.
