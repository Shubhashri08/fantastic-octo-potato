# VIGRAH AI (Visual Intelligence & Geospatial Response Hub)
### Real-Time Video Analytics, Multi-Model Incident Detection & Forensic Person Re-ID Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C.svg?style=flat&logo=PyTorch&logoColor=white)](https://pytorch.org)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg?style=flat&logo=React&logoColor=black)](https://reactjs.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

VIGRAH AI is an open-source, local visual intelligence platform designed for municipal and smart-city surveillance. It processes multi-camera feeds (Webcam, RTSP, and Video Files), performs real-time multi-model YOLO inference for incident detection (Fire/Smoke, Accidents, Violence/Fighting, Vehicles, Pedestrians), applies temporal confirmation filters to eliminate false alarms, provides forensic Person Re-Identification (Re-ID) tracking, and streams live MJPEG video feeds to a geospatial React dashboard.

---

## ⚡ Key Highlights

- **Multi-Model Incident Detection**: Real-time YOLO detection tuned for high accuracy across traffic accidents, fires, violent altercations, and density anomalies.
- **Forensic Person Re-Identification (Re-ID)**: Multi-camera person tracking using state-of-the-art **TransReID (ViT-Base)** and **OSNet** embeddings, integrated with BYTETracker.
- **Hardware Optimized**: Tuned for CUDA (NVIDIA GPU), Apple Silicon (MPS), and automatic CPU fallback with FP16 precision.
- **Zero Paid Services**: 100% free open-source stack using PyTorch, Ultralytics YOLO, FastAPI, SQLite / PostgreSQL + pgvector, and Leaflet.
- **Temporal Confirmation**: Incidents are confirmed only when detected in $\ge 3$ consecutive sampled frames with automated snapshot storage.
- **Geospatial Intelligence**: Interactive dark-themed Leaflet map showing CCTV camera nodes, GPS coordinates, and real-time alert telemetry.

---

## 📂 Project Structure

```
fantastic-octo-potato/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application & REST/streaming endpoints
│   │   ├── database.py              # PostgreSQL (pgvector) / SQLite engine configuration
│   │   ├── models.py                # Camera, Event, and Person Re-ID database models
│   │   ├── schemas.py               # Pydantic validation schemas
│   │   ├── detection.py             # Multi-model YOLO detection core & temporal tracker
│   │   ├── stream_manager.py        # Multi-camera worker pool & MJPEG generator
│   │   ├── video_person_engine.py   # Person Re-ID indexing and search engine
│   │   ├── person_reid/             # TransReID (ViT-Base) & OSNet Re-ID backends
│   │   └── tracking/                # BYTETracker and crop quality filtering
│   ├── main.py                      # Uvicorn server entrypoint
│   ├── sample_media/                # Demo and sample CCTV video feeds
│   ├── weights/                     # Pretrained weights directory (.gitkeep)
│   └── requirements.txt             # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx           # Telemetry bar & status indicators
│   │   │   ├── LiveStreamGrid.jsx   # MJPEG live video feeds with source switching
│   │   │   ├── CameraMap.jsx        # Leaflet interactive map with camera markers
│   │   │   ├── EventTable.jsx       # Real-time incident log table with filters
│   │   │   ├── IdentifyConsole.jsx  # Forensic Person Re-ID search console
│   │   │   └── SnapshotModal.jsx    # Verification lightbox for captured incidents
│   │   ├── App.jsx                  # Main dashboard composition
│   │   ├── index.css                # Glassmorphism dark mode styling
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js               # Proxy configuration to backend
├── docs/                            # Architectural specifications and benchmarks
├── .env.example                     # Template environment configuration
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy configuration file
cp ../.env.example .env

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The backend API and Swagger documentation will be available at `http://localhost:8000/docs`.

### 3. Frontend Setup

In a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## ⚙️ Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./vigrah.db` | Database connection (SQLite or PostgreSQL `postgresql://...`) |
| `PERSON_REID_MODEL` | `transreid` | Person Re-ID backend (`transreid` or `osnet`) |
| `PERSON_REID_CHECKPOINT` | `None` | Optional path to custom Re-ID `.pth` checkpoint |
| `MEDIA_STORAGE_DIR` | `./recordings` | Directory for incident video recordings |
| `SNAPSHOTS_STORAGE_DIR` | `./snapshots` | Directory for saved incident snapshots |
| `CONF_THRESHOLD` | `0.35` | Detection confidence threshold (0.0 – 1.0) |
| `TEMPORAL_PERSISTENCE_FRAMES`| `3` | Consecutive frames required to confirm an incident |

---

## 🔌 API Endpoints Reference

### Surveillance & Incidents
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cameras` | List all registered camera nodes |
| `POST` | `/api/cameras` | Register a new camera node |
| `PUT` | `/api/cameras/{id}` | Update camera source or GPS coordinates |
| `GET` | `/api/events` | List recorded incidents (filter by type/severity/camera) |
| `GET` | `/stream/{camera_id}` | Live MJPEG video stream |
| `POST` | `/api/start_detection` | Start detection worker for a camera |
| `POST` | `/api/stop_detection` | Pause detection worker for a camera |
| `GET` | `/api/status` | Hardware/GPU telemetry and active worker status |

### Person Re-Identification (Re-ID)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/person/videos` | List indexed video evidence feeds |
| `POST` | `/api/person/index_video` | Process & index a CCTV video with Person Re-ID |
| `POST` | `/api/person/search` | Search gallery by reference photo/crop |
| `GET` | `/api/person/track/{track_id}` | Get detailed trajectory and sightings for a track |

---

## 📄 License
This project is open-source under the Apache 2.0 License.
