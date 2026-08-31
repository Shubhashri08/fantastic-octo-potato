# VIGRAH AI — Comprehensive System Architecture & Engineering Audit

> **Visual Intelligence & Geospatial Response Hub (VIGRAH AI)**  
> **Classification:** Technical Architecture & Developer Reference Manual  
> **Document Version:** 2.0.0  
> **Target Audience:** Full-stack Engineers, Computer Vision Developers, DevOps, and System Architects  

---

## 1. System Overview & Core Philosophy

**VIGRAH AI** is an open-source, local-first intelligence platform built for municipal surveillance, real-time computer vision incident detection, forensic video analysis, and geospatial emergency response coordination. 

The system operates across **4 functional layers** (The 4 Pillars):
1. **Sense (Surveillance Layer):** Multi-channel video stream ingestion (Video files, Webcams, RTSP streams), multi-threaded frame processing, real-time YOLO object & threat inference, IoU spatial conflict analysis, temporal confirmation filters, automated 10-second DVR clip recording, and browser-compatible MJPEG streaming.
2. **Understand (GIS & Reconstruction Layer):** Multi-city interactive Leaflet GIS mapping with 200+ seeded Indian municipal CCTV nodes (Mumbai & Bengaluru), spatial trajectory interpolation, road corridor escape prediction, and emergency containment zone calculation.
3. **Identify (Forensic Re-Identification Layer):**
   - **Vehicle Finder:** SQL-indexed license plate lookup, visual color extraction (HSV), make/model attribute filtering, sighting timeline mapping, and BOLO (Be-On-the-Lookout) watchlist flagging.
   - **Person Re-ID:** Deep Neural Person Re-Identification using **OSNet x1.0** (512-dimensional embeddings), automated video evidence frame sampling (~3 FPS), spatial-temporal pedestrian tracking, high-resolution crop extraction, and ranked Top-K cosine similarity search.
4. **Respond (Tactical Operations Layer):** Real-time incident triage queue, threat severity filtering, high-resolution snapshot lightbox viewer, and tactical dispatch action state management (Patrol Units, Fire Containment, Emergency Medical Services).

---

## 2. High-Level Architecture Topology

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND (React 18 + Vite 5)                          │
│                                                                                         │
│  ┌────────────────────┐  ┌───────────────────────┐  ┌─────────────────────────────────┐ │
│  │   Sense Console    │  │  Understand Console   │  │        Identify Console         │ │
│  │ (LiveStreamGrid)   │  │ (CameraMap + Reconst) │  │  (Vehicle Finder + Person ReID) │ │
│  └─────────┬──────────┘  └───────────┬───────────┘  └────────────────┬────────────────┘ │
│            │                         │                               │                  │
│            │                         │                               │                  │
│            ▼                         ▼                               ▼                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │               API Client Layer (/frontend/src/api - Fetch / AbortController)       │ │
│  └───────────────────────────────────────┬────────────────────────────────────────────┘ │
└──────────────────────────────────────────┼──────────────────────────────────────────────┘
                                           │ HTTP REST / MJPEG Streams (:8000)
┌──────────────────────────────────────────▼──────────────────────────────────────────────┐
│                                   BACKEND (FastAPI + Python 3)                          │
│                                                                                         │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                               FastAPI Application Router (main.py)                 │ │
│  └──────┬──────────────────┬──────────────────────┬────────────────────┬──────────────┘ │
│         │                  │                      │                    │                │
│         ▼                  ▼                      ▼                    ▼                │
│  ┌──────────────┐  ┌──────────────┐       ┌───────────────┐   ┌──────────────────────┐  │
│  │Stream Manager│  │Detection Core│       │Vehicle Service│   │ Video Person Engine  │  │
│  │(OpenCV Pool) │  │ (YOLO11n +   │       │(Plate/HSV/SQL)│   │ (OSNet 512-D Re-ID)  │  │
│  │              │  │  ONNX Model) │       │               │   │                      │  │
│  └──────┬───────┘  └──────┬───────┘       └───────┬───────┘   └──────────┬───────────┘  │
│         │                 │                       │                      │              │
│         ▼                 ▼                       ▼                      ▼              │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                     SQLAlchemy ORM Engine & Session Manager                        │ │
│  └────────────────────────────────────────┬───────────────────────────────────────────┘ │
└───────────────────────────────────────────┼─────────────────────────────────────────────┘
                                            │ SQLite Engine / Neon Postgres
┌───────────────────────────────────────────▼─────────────────────────────────────────────┐
│                                   DATABASE (backend/vigrah.db)                           │
│                                                                                         │
│  ├── cameras (6 nodes)                ├── video_evidence (1 source)                     │
│  ├── events (563 records)             ├── person_video_tracks (5 tracks)                │
│  ├── vehicles (25 profiles)           ├── person_video_sightings (63 crops)             │
│  └── vehicle_sightings (75 points)    └── alerts / entities / mappings                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Directory & File Structure

```
fantastic-octo-potato/
├── architecture.md                     # Comprehensive System Architecture & Audit (This file)
├── progress.md                         # Milestones and operational changelog
├── README.md                           # Quickstart guide and project overview
├── backend/
│   ├── app/
│   │   ├── __init__.py                 # Module initializer
│   │   ├── database.py                 # SQLite & PostgreSQL connection strings & session generator
│   │   ├── detection.py                # YOLO multi-object inference, IoU collisions & temporal tracker
│   │   ├── main.py                     # FastAPI entrypoint, routes, static mounts, MJPEG endpoints
│   │   ├── model_downloader.py         # Lazy neural network model weight loader
│   │   ├── models.py                   # 11 SQLAlchemy ORM model definitions
│   │   ├── person_reid_model.py        # OSNet x1.0 architecture & 512-D embedding extractor
│   │   ├── reconstruction_engine.py    # Geospatial trajectory prediction & corridor generator
│   │   ├── reid_engine.py              # Biometric face extractor & city mesh manager
│   │   ├── schemas.py                  # Pydantic request/response validation schemas
│   │   ├── seed_data.py                # Database seeding routine for cameras, vehicles & events
│   │   ├── stream_manager.py           # Multi-threaded OpenCV camera worker pool
│   │   ├── vehicle_service.py          # Plate normalization, SQL search & HSV image matching
│   │   └── video_person_engine.py      # Video evidence ingestion, tracking & Top-K Re-ID search
│   ├── city_mesh_networks.json         # GeoJSON camera coordinates for Mumbai & Bengaluru
│   ├── evidence/persons/               # Auto-generated person crops (e.g. VIDEO-01/TRK-001/*.jpg)
│   ├── recordings/                     # 10-second MP4 incident evidence clips
│   ├── samples/                        # Local synthetic and CCTV MP4 demo videos
│   ├── snapshots/                      # Annotated incident frame capture JPGs
│   ├── uploads/videos/                 # Uploaded investigation video files
│   ├── vigrah.db                       # Active SQLite database file
│   ├── weights/                        # Neural network weights (yolo11n.pt, osnet weights)
│   ├── requirements.txt                # Python backend dependencies
│   └── yolo11n.pt                      # YOLO11 Nano detection weights (5.6 MB)
├── frontend/
│   ├── package.json                    # Frontend dependencies (React 18, Vite 5, Leaflet, Tailwind)
│   ├── vite.config.js                  # Vite dev server configuration & API proxy
│   ├── index.html                      # HTML5 root template
│   └── src/
│       ├── main.jsx                    # React 18 DOM mount
│       ├── App.jsx                     # Top-level state manager, routing & polling loop
│       ├── index.css                   # Global Tailwind utilities and dark-theme variables
│       ├── api/                        # Centralized API fetch modules
│       │   ├── client.js               # Base fetch wrapper with timeout & AbortController
│       │   ├── cameras.js              # Camera listing, start/stop detection
│       │   ├── events.js               # Incidents API & Reconstruction queries
│       │   ├── persons.js              # Person Re-ID search, video upload/delete
│       │   ├── status.js               # Telemetry and GPU status
│       │   └── vehicles.js             # Vehicle search, image lookup, BOLO flagging
│       ├── components/                 # UI Component Hierarchy
│       │   ├── CameraMap.jsx           # Leaflet GIS Multi-City CCTV node viewer
│       │   ├── EventReconstruction.jsx # Geospatial incident trajectory engine
│       │   ├── Header.jsx              # Status bar, active threat counter, tab badges
│       │   ├── IdentifyConsole.jsx     # Vehicle Finder & Person Re-ID console
│       │   ├── LiveStreamGrid.jsx      # Sense Layer: 3-channel matrix & channel bar
│       │   ├── RespondConsole.jsx      # Incident triage queue & tactical dispatch
│       │   ├── Sidebar.jsx             # Left navigation rail
│       │   ├── SnapshotModal.jsx       # High-resolution evidence viewer modal
│       │   ├── SystemTelemetry.jsx     # Hardware status overlay
│       │   └── UnderstandConsole.jsx   # Tab switcher between Map & Reconstruction
│       └── data/
│           └── city_mesh_data.json     # Client-side backup coordinates for GIS nodes
```

---

## 4. Frontend Architecture & Component Flow

The frontend is built as a Single Page Application (SPA) utilizing **React 18**, **Vite 5**, **TailwindCSS**, **Framer Motion**, and **Leaflet**.

### Component Hierarchy Tree

```
App.jsx (Root State, URL Sync, 4-Second Polling Loop)
├── Header.jsx (Live status telemetry, active threat count, system heartbeat)
├── Sidebar.jsx (Primary 4-layer navigation: Sense, Understand, Identify, Respond)
│
├── [Sense Tab] -> LiveStreamGrid.jsx
│   ├── Stream Grid (3-camera split matrix, 6-view grid, or single maximized view)
│   ├── Quick Channel Selector (CAM-01 through CAM-06)
│   └── Source Configuration Modal (Switch input between Webcam 0, Video path, RTSP)
│
├── [Understand Tab] -> UnderstandConsole.jsx
│   ├── Sub-Tab 'map' -> CameraMap.jsx (Interactive Leaflet map, city selector, CCTV markers)
│   └── Sub-Tab 'reconstruction' -> EventReconstruction.jsx (Incident trajectory, escape paths)
│
├── [Identify Tab] -> IdentifyConsole.jsx
│   ├── Sub-Tab 'vehicle' -> Vehicle Finder
│   │   ├── Plate Search Mode (Exact / Partial plate query)
│   │   ├── Description Search Mode (Model, Color, Location filters)
│   │   ├── Photo / Plate Upload Mode (Visual HSV color extraction)
│   │   ├── Vehicle Dossier Grid (25 registered vehicles)
│   │   ├── Movement Route History Modal (Interactive sighting map)
│   │   └── BOLO Watchlist Flagging Modal
│   └── Sub-Tab 'person' -> Missing Person Re-ID Finder
│       ├── Reference Photo Upload Dropzone
│       ├── Video Evidence Source Manager (Upload MP4, list sources, delete footage)
│       ├── Re-ID Parameter Controls (Similarity threshold, camera source filter)
│       └── Ranked Top-K Matches & Sighting Timeline Crops
│
├── [Respond Tab] -> RespondConsole.jsx
│   ├── Priority Incident Queue (Categorized by Critical, High, Medium)
│   ├── Threat Severity & Category Filter Bar
│   ├── Live Camera HUD & Snapshot Inspection Panel
│   └── Tactical Dispatch Confirmation Modal (Patrol, Fire Containment, EMS)
│
└── SnapshotModal.jsx (Global lightbox modal for high-res incident snapshots & DVR clips)
```

### Route & Navigation Map

| Client URL Path | Layer / Tab | Rendered Component | Connected Backend APIs |
| :--- | :--- | :--- | :--- |
| `/` or `/surveillance` | **Sense** | `LiveStreamGrid.jsx` | `GET /api/cameras`<br>`GET /stream/{camera_id}`<br>`POST /api/start_detection`<br>`POST /api/stop_detection` |
| `/dashboard` or `/map` | **Understand (Map)** | `CameraMap.jsx` | `GET /api/cities`<br>`GET /api/cities/{city}/nodes`<br>`GET /api/events` |
| `/understand/reconstruction` | **Understand (Reconstruction)** | `EventReconstruction.jsx` | `GET /api/events`<br>`GET /api/reconstruction/analyze?event_id={id}` |
| `/identify/vehicle` | **Identify (Vehicle)** | `IdentifyConsole.jsx` | `GET /api/vehicles`<br>`GET /api/vehicles/search`<br>`POST /api/vehicles/search/image`<br>`GET /api/vehicles/{id}/sightings`<br>`POST /api/vehicles/{id}/flag` |
| `/identify/person` | **Identify (Person)** | `IdentifyConsole.jsx` | `GET /api/person/videos`<br>`POST /api/person/videos/upload`<br>`DELETE /api/person/videos/{source_id}`<br>`POST /api/person/search`<br>`GET /api/person/evidence/{source_id}/{track_id}` |
| `/respond` | **Respond** | `RespondConsole.jsx` | `GET /api/events`<br>`GET /api/cameras` |

---

## 5. Backend Architecture & Core Subsystems

Built with **FastAPI**, the backend provides low-latency REST endpoints, multi-threaded video stream processing, and on-demand neural inference.

### 5.1 Stream Manager & Live Video Pipeline (`backend/app/stream_manager.py`)
- Manages an asynchronous worker pool of `CameraWorker` threads.
- Each worker runs an OpenCV `cv2.VideoCapture` loop against a configured source:
  - **Local Video Files:** Loops CCTV MP4 sample files seamlessly.
  - **USB Webcams:** Connects to device index `0` or `1`.
  - **RTSP / HTTP Streams:** Connects to municipal network IP streams.
- **Frame Rate & Inference Throttle:** Employs a frame-skipping mechanism (e.g. processing 1 in every 3 frames for neural inference) while maintaining fluid ~25-30 FPS MJPEG streaming.
- **MJPEG Streaming Generator:** Encodes processed BGR frames to JPEG format and yields them via HTTP `multipart/x-mixed-replace` boundaries.

### 5.2 Real-Time Detection Engine (`backend/app/detection.py`)
- **Primary Detector:** YOLO11n (COCO classes: `0=Person`, `2=Car`, `3=Motorcycle`, `5=Bus`, `7=Truck`).
- **Secondary Threat Detector:** Fine-tuned threat model (`best.onnx` / `best.pt`) for direct violence and fire detection.
- **Heuristic Conflict & Collision Engines:**
  - *Fighting / Violence:* Computes IoU between detected person bounding boxes. When `IoU >= 0.18` between two or more individuals with rapid bounding box variance, flags candidate `Fighting`.
  - *Vehicle Collisions / Accidents:* Computes IoU between vehicles (`IoU >= 0.22`) or between a vehicle and a pedestrian (`IoU >= 0.15`), flagging candidate `Accident` or `Vehicle Collision`.
- **Temporal Confirmation Tracker (`TemporalTracker`):**
  - Eliminates single-frame false positives.
  - Requires a candidate incident to persist across $\ge 3$ consecutive sampled frames before committing an event to the database.
  - Implements a 10-second per-camera cooldown to prevent duplicate alert spam.
- **Automated Evidence Capture:**
  - Captures high-resolution annotated JPEG snapshots to `backend/snapshots/`.
  - Records 10-second MP4 DVR video clips to `backend/recordings/`.

### 5.3 Deep Person Re-Identification Pipeline (`backend/app/person_reid_model.py` & `backend/app/video_person_engine.py`)
- **Neural Architecture:** Implements **OSNet x1.0** (*Omni-Scale Network for Person Re-Identification*, ICCV 2019).
- **Embedding Generation:**
  - Converts person crops to normalized tensors $[1 \times 3 \times 256 \times 128]$ using ImageNet mean and standard deviation.
  - Forward-passes through OSNet feature extractor to obtain a **512-dimensional feature vector**.
  - Applies strict $L_2$-normalization: $\mathbf{e} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$.
- **Video Ingestion & Tracking:**
  - Samples uploaded/CCTV video footage at ~3 FPS.
  - Detects pedestrians with YOLO and tracks bounding boxes across frames using spatial IoU association (`IoU >= 0.20`).
  - Stores individual sighting crops in `backend/evidence/persons/<source_id>/<track_id>/`.
  - Computes the track-level **Mean Embedding Vector** representing the person across varying angles and lighting.
- **Query & Matching:**
  - Accepts user-uploaded probe photographs.
  - Detects and crops the probe subject.
  - Extracts the 512-D probe embedding.
  - Calculates **Cosine Similarity** against all indexed track embeddings:
    $$\text{Similarity}(\mathbf{q}, \mathbf{g}) = \mathbf{q} \cdot \mathbf{g} = \sum_{i=1}^{512} q_i g_i$$
  - Filters matches exceeding `min_similarity` (default $0.50$) and returns ranked Top-K candidates with sighting timestamps and crop URLs.

### 5.4 Vehicle Identification & Search Service (`backend/app/vehicle_service.py`)
- **Plate Normalization:** Cleans alphanumeric strings by stripping spaces, hyphens, periods, and enforcing uppercase (e.g. `"ka-02 zx 1001"` $\rightarrow$ `"KA02ZX1001"`).
- **SQL Search Engine:** Performs multi-clause ILIKE queries across license plates, vehicle types, models, colors, and camera locations.
- **Visual Image Search:**
  - Decodes uploaded vehicle photographs.
  - Extracts dominant HSV color distributions across the vehicle bounding region.
  - Matches dominant hue/saturation against registered database color profiles.
- **BOLO Management:** Toggles vehicle stolen status, records investigator notes, and updates the active grid alert status.

### 5.5 Geospatial Reconstruction & Escape Vector Engine (`backend/app/reconstruction_engine.py`)
- **Input:** Target `event_id` and origin camera GPS coordinates.
- **Observed Path Generation:** Interpolates pre-incident trajectory leading to the event location.
- **Predictive Escape Vectors:** Generates 3 to 5 candidate transit routes along realistic street grids (e.g. Trinity Circle Arterial, Outer Ring Road Link, Richmond Circle Retail Route).
- **Likelihood Scoring:** Normalizes multi-factor scores (road capacity, travel time, direct egress flow, CCTV coverage density) into explainable percentage probabilities summing to $100\%$.
- **CCTV Checkpoint Prediction:** Calculates downstream camera interception nodes and estimated time of arrival (ETA) windows.
- **Thermal Hazard Buffers:** For fire incidents, generates concentric radial hazard containment zones (Immediate Danger, Smoke Buffer, Outer Perimeter).

---

## 6. Database Architecture & Current Data State

The database is powered by **SQLite** (located at `backend/vigrah.db`) via SQLAlchemy ORM, with native configuration support for PostgreSQL / Neon DB.

### 6.1 Database Schema & Entity Relationship

```
 ┌──────────────────────┐         ┌──────────────────────────┐
 │       cameras        │         │          events          │
 ├──────────────────────┤         ├──────────────────────────┤
 │ id (PK, INT)         │         │ id (PK, INT)             │
 │ name (VARCHAR)       │         │ camera_id (INT)          │
 │ source (VARCHAR)     │◄────────┤ event_type (VARCHAR)     │
 │ source_type (VARCHAR)│         │ confidence (FLOAT)       │
 │ lat (FLOAT)          │         │ timestamp (DATETIME)     │
 │ lon (FLOAT)          │         │ bbox (TEXT)              │
 │ is_active (BOOLEAN)  │         │ snapshot_path (VARCHAR)  │
 │ created_at (DATETIME)│         │ video_clip_path (VARCHAR)│
 └──────────────────────┘         │ severity (VARCHAR)       │
                                  │ status (VARCHAR)         │
                                  └──────────────────────────┘

 ┌──────────────────────┐         ┌──────────────────────────┐
 │       vehicles       │         │     vehicle_sightings    │
 ├──────────────────────┤         ├──────────────────────────┤
 │ vehicle_id (PK, STR) │◄───┐    │ id (PK, INT)             │
 │ plate_number (STR)   │    └───-│ vehicle_id (FK, STR)     │
 │ plate_confidence     │         │ camera_id (STR)          │
 │ vehicle_type (STR)   │         │ location (STR)           │
 │ vehicle_model (STR)  │         │ city (STR)               │
 │ vehicle_color (STR)  │         │ latitude (FLOAT)         │
 │ is_stolen (BOOLEAN)  │         │ longitude (FLOAT)        │
 │ bolo_status (STR)    │         │ speed_kmh (FLOAT)        │
 │ flag_reason (STR)    │         │ timestamp (DATETIME)     │
 └──────────────────────┘         │ evidence_image (VARCHAR) │
                                  └──────────────────────────┘

 ┌──────────────────────┐         ┌──────────────────────────┐         ┌──────────────────────────┐
 │    video_evidence    │         │   person_video_tracks    │         │  person_video_sightings  │
 ├──────────────────────┤         ├──────────────────────────┤         ├──────────────────────────┤
 │ id (PK, INT)         │◄───┐    │ id (PK, INT)             │◄───┐    │ id (PK, INT)             │
 │ source_id (UQ, STR)  │    └───-│ source_id (STR)          │    └───-│ sighting_id (UQ, STR)    │
 │ filename (VARCHAR)   │         │ track_id (STR)           │         │ track_id (STR)           │
 │ file_path (VARCHAR)  │         │ start_time_sec (FLOAT)   │         │ source_id (STR)          │
 │ status (VARCHAR)     │         │ end_time_sec (FLOAT)     │         │ timestamp_sec (FLOAT)    │
 │ track_count (INT)    │         │ representative_crop_path │         │ crop_path (VARCHAR)      │
 │ sighting_count (INT) │         │ average_embedding (JSON) │         │ bbox (VARCHAR)           │
 └──────────────────────┘         └──────────────────────────┘         │ embedding (JSON)         │
                                                                       └──────────────────────────┘
```

### 6.2 Complete Table Inventory & Row Counts

An inspection of `backend/vigrah.db` yields the following exact live database state:

| Table Name | Row Count | Primary Purpose | Sample Data / Key Fields |
| :--- | :--- | :--- | :--- |
| **`cameras`** | **6 rows** | Registered surveillance nodes & live feeds | `CAM-01` (Mumbai CSMT), `CAM-02` (Bengaluru MG Rd), `CAM-03` (Marine Drive RTSP), `CAM-04`, `CAM-05`, `CAM-06` |
| **`events`** | **563 rows** | Detected real-time incidents & alerts | 459 `Fighting` (Critical), 98 `Accident` (High), 2 `Vehicle Collision` (Critical), 1 `Fire` (Critical), 1 `Smoke` (Med), 1 `Person`, 1 `Vehicle` |
| **`vehicles`** | **25 rows** | Registered vehicle dossiers | `VEH-0001` (KA 02 ZX 1001 - Stolen), `VEH-0002` (KA 02 ZX 1002), `VEH-0003` (KA 02 AB 1003 - Stolen), etc. |
| **`vehicle_sightings`**| **75 rows** | Historical vehicle trajectory sightings | 3 sightings per vehicle across Transit Corridor Entry Gate 1, Expressway Midway, and MG Road Commercial Corridor |
| **`video_evidence`** | **1 row** | Ingested video evidence sources | `VIDEO-01` (`VIDEO-01_11.mp4`, 159 total frames, 5.3s duration, 30 FPS, status `ready`, 5 tracks, 63 sightings) |
| **`person_video_tracks`**| **5 rows** | Clustered pedestrian tracks | `TRK-001` to `TRK-005` with representative crop paths and 512-D JSON embeddings |
| **`person_video_sightings`**| **63 rows** | Individual timestamped person crops | High-resolution crops with frame timestamps (`00:00` to `00:05`), bounding boxes, confidence $> 0.90$, and 512-D embeddings |
| **`alerts`** | **0 rows** | High-level system alert dispatcher table | Schema defined for cross-incident correlation |
| **`entities`** | **0 rows** | Unified multi-modal entity tracking | Schema defined for combined vehicle/person entities |
| **`entity_sightings`** | **0 rows** | Unified spatial-temporal sighting records | Schema defined for entity correlation |
| **`event_entity_mapping`**| **0 rows** | Incident-to-suspect proximity associations | Schema defined for suspect/witness mapping |

### 6.3 Sample Record Breakdown

#### `cameras` Table:
```json
[
  {"id": 1, "name": "CAM-01: Mumbai CSMT Concourse Altercation", "source": ".../backend/samples/fight_1.mp4", "source_type": "video", "lat": 18.9401, "lon": 72.8351, "is_active": true},
  {"id": 2, "name": "CAM-02: Bengaluru MG Road Commercial Corridor", "source": ".../backend/samples/fire_1.mp4", "source_type": "video", "lat": 12.9756, "lon": 77.6067, "is_active": true},
  {"id": 3, "name": "CAM-03: Mumbai Marine Drive Coastal Unit", "source": "http://172.19.253.69:8080/video", "source_type": "rtsp", "lat": 18.9438, "lon": 72.8233, "is_active": true},
  {"id": 4, "name": "CAM-04: Bengaluru Trinity Circle Transit Node", "source": ".../backend/samples/fire_1.mp4", "source_type": "video", "lat": 12.9725, "lon": 77.6200, "is_active": false},
  {"id": 5, "name": "CAM-05: Bengaluru Outer Ring Road Hub", "source": ".../backend/samples/fight_1.mp4", "source_type": "video", "lat": 12.9820, "lon": 77.6200, "is_active": false},
  {"id": 6, "name": "CAM-06: Mumbai Worli Sea Face Intercept", "source": ".../backend/samples/fight_1.mp4", "source_type": "video", "lat": 18.9650, "lon": 72.8180, "is_active": false}
]
```

#### `vehicles` Table (Excerpt):
```json
{
  "vehicle_id": "VEH-0001",
  "plate_number": "KA 02 ZX 1001",
  "plate_confidence": 0.95,
  "vehicle_type": "Car (Sedan)",
  "vehicle_model": "Toyota Corolla Sedan",
  "vehicle_color": "Green",
  "is_stolen": true,
  "bolo_status": "CRITICAL BOLO: STOLEN VEHICLE"
}
```

---

## 7. AI Models & Computer Vision Integration

The system integrates a multi-tiered artificial intelligence pipeline spanning deep neural networks and deterministic computer vision algorithms:

| Model / Subsystem | Architecture / Framework | Weights / Artifacts | Location in Code | Operational Role & Usage |
| :--- | :--- | :--- | :--- | :--- |
| **YOLO11n COCO Multi-Object Detector** | Ultralytics YOLO11 Nano (PyTorch / ONNX) | `yolo11n.pt` (5.6 MB) | `backend/app/detection.py`<br>`backend/app/video_person_engine.py` | Detects pedestrians (`cls=0`) and vehicles (cars, motorcycles, buses, trucks) in real-time CCTV feeds and video evidence. |
| **Fine-Tuned Threat Model** | YOLO Object Detection (ONNX / PyTorch) | `weights/best.onnx` or `weights/best.pt` | `backend/app/model_downloader.py`<br>`backend/app/detection.py` | Custom-trained network for direct classification of `Fighting`, `Fire`, and `Smoke` patterns in video frames. |
| **OSNet x1.0 Person Re-ID Model** | Omni-Scale Deep CNN with Channel Gating (PyTorch) | `osnet_x1_0_market1501.pth` (Market-1501 dataset) | `backend/app/person_reid_model.py` | Extracts 512-dimensional $L_2$-normalized appearance embeddings from human body crops for person re-identification. |
| **Facial Biometric & Landmark Extractor** | OpenCV Haar Cascade Classifier | `haarcascade_frontalface_default.xml` | `backend/app/reid_engine.py` | Isolates facial structures and computes 64-D Sobel gradient orientation histograms invariant to clothing changes. |
| **IoU Conflict & Collision Heuristics** | Geometric Bounding Box Intersection | Deterministic Algorithm | `backend/app/detection.py` | Computes spatial overlap between detected persons ($\text{IoU} \ge 0.18$) for fighting detection and vehicles ($\text{IoU} \ge 0.22$) for accident detection. |
| **Temporal Verification Filter** | State Machine & Frame Buffer Tracker | Deterministic Algorithm | `backend/app/detection.py` | Verifies candidate detections across $\ge 3$ consecutive sampled frames with a 10s per-camera cooldown to eliminate false alarms. |
| **Color & Texture Histogram Engine** | HSV Color Space + Sobel Gradient Magnitude | Deterministic NumPy/OpenCV | `backend/app/vehicle_service.py` | Analyzes average HSV color signatures for visual vehicle matching and plate attribute classification. |

---

## 8. Complete API Specification

### 8.1 Surveillance & Camera Management

- **`GET /api/cameras`**
  - *Description:* Returns list of all registered CCTV and video stream cameras.
  - *Response:* `200 OK` $\rightarrow$ Array of `CameraResponse` objects.
- **`POST /api/cameras`**
  - *Description:* Registers a new camera node in the surveillance grid.
  - *Payload:* `{"name": "string", "source": "string", "source_type": "video|webcam|rtsp", "lat": float, "lon": float}`
- **`PUT /api/cameras/{camera_id}`**
  - *Description:* Updates stream source URL/path or GPS coordinates for an existing camera.
- **`GET /stream/{camera_id}`**
  - *Description:* Continuous MJPEG live video stream with overlayed bounding boxes and threat HUD.
  - *Response:* `multipart/x-mixed-replace; boundary=frame`
- **`GET /stream/video/{filename}`**
  - *Description:* Streams a sample video file from `backend/samples/` as an MJPEG feed.
- **`POST /api/start_detection`**
  - *Description:* Spawns or resumes the `CameraWorker` thread for a specified camera.
  - *Payload:* `{"camera_id": int, "source": "string", "source_type": "string"}`
- **`POST /api/stop_detection`**
  - *Description:* Pauses the worker thread for a camera.
  - *Payload Query:* `camera_id=int`

### 8.2 Incidents & Event Reconstruction

- **`GET /api/events`**
  - *Description:* Retrieves paginated incident logs with filters for `event_type`, `camera_id`, `severity`, and `status`.
  - *Response:* Array of `EventResponse` objects.
- **`POST /api/reconstruction/analyze`** and **`GET /api/reconstruction/analyze`**
  - *Description:* Generates pre-incident observed path, candidate escape corridors, Likelihood Percentages, and downstream CCTV intercept checkpoints.
  - *Query / Payload:* `event_id=int`
- **`POST /api/system/reset-demo`**
  - *Description:* Resets the database incident records to the verified demonstration state.

### 8.3 Missing Person Video Re-Identification

- **`GET /api/person/videos`**
  - *Description:* Lists all indexed video evidence sources with track and sighting counts.
- **`POST /api/person/videos/upload`**
  - *Description:* Uploads MP4/AVI video evidence; runs YOLO person detection, spatial-temporal tracking, crop extraction, and OSNet 512-D embedding indexing.
- **`DELETE /api/person/videos/{source_id}`**
  - *Description:* Deletes video source record and associated tracks, sightings, and disk crops.
- **`POST /api/person/search`**
  - *Description:* Accepts uploaded reference photo, extracts 512-D OSNet embedding, and returns ranked Top-5 matches across indexed tracks.
  - *Form Data:* `file` (Image), `min_similarity` (float), `location` (optional), `limit` (int).
- **`GET /api/person/evidence/{source_id}/{track_id}`**
  - *Description:* Serves the representative track crop image (`image/jpeg`).
- **`GET /api/person/evidence/{source_id}/{track_id}/{filename}`**
  - *Description:* Serves a specific sighting frame crop image (`image/jpeg`).

### 8.4 Vehicle Finder & BOLO Watchlist

- **`GET /api/vehicles`**
  - *Description:* Retrieves paginated vehicle records with latest sightings and dossiers (`page`, `limit`).
- **`GET /api/vehicles/search`**
  - *Description:* Multi-attribute SQL search (`plate`, `vehicle_type`, `vehicle_model`, `color`, `location`, `only_stolen`).
- **`POST /api/vehicles/search/image`**
  - *Description:* Uploads vehicle crop photo, extracts HSV color signature, and matches database vehicles.
- **`GET /api/vehicles/{vehicle_id}`**
  - *Description:* Returns complete vehicle dossier including sighting history.
- **`GET /api/vehicles/{vehicle_id}/sightings`**
  - *Description:* Returns chronological sighting timeline with GPS coordinates.
  - *POST /api/vehicles/{vehicle_id}/flag`**
  - *Description:* Flags or unflags vehicle for BOLO watchlist (`is_flagged`, `reason`, `note`).

### 8.5 Multi-City GIS & System Telemetry

- **`GET /api/cities`**
  - *Description:* Returns metadata for available city meshes (Mumbai, Bengaluru).
- **`GET /api/cities/{city_name}/nodes`**
  - *Description:* Returns 200+ CCTV nodes with coordinates and operational status.
- **`GET /api/status`**
  - *Description:* Real-time hardware telemetry (`cuda` vs `cpu`, GPU name, active models, active worker threads).
- **`GET /snapshots/{filename}`** & **`GET /recordings/{filename}`**
  - *Description:* Static file endpoints for verified snapshots and 10s DVR clips.

---

## 9. Hardware Requirements & Optimization Parameters

VIGRAH AI is engineered to execute locally without external cloud dependencies:

- **Minimum GPU Spec:** NVIDIA GeForce RTX 2050 (4 GB VRAM) / GTX 1650 or Apple Silicon (M1/M2/M3 with MPS acceleration).
- **CPU Fallback:** Fully operational on modern x86_64 / ARM64 CPUs via PyTorch CPU and OpenCV multithreading.
- **Optimization Highlights:**
  - **Subsampled Neural Inference:** Video feeds are sampled at 3 FPS for deep Re-ID and 1-in-3 frames for live CCTV detection, reducing GPU load by ~65%.
  - **L2-Normalized Unit Sphere Vectors:** Cosine similarity calculation is reduced to a fast dot-product operation: $\mathbf{q} \cdot \mathbf{g}$.
  - **Memory Pooling & Connection Reuse:** SQLAlchemy connection pooling prevents database locks across concurrent camera threads.

---

## 10. Developer Onboarding & How-To Guide

### 10.1 Running the Backend

```bash
cd backend

# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch FastAPI backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend will start at `http://localhost:8000`. On first run, it initializes `vigrah.db`, downloads `yolo11n.pt` and OSNet weights, and auto-indexes default video evidence.*

### 10.2 Running the Frontend

```bash
cd frontend

# 1. Install NPM packages
npm install

# 2. Start Vite development server
npm run dev
```
*Open `http://localhost:5173` in your browser. Requests to `/api`, `/stream`, `/snapshots`, `/recordings`, and `/evidence` are automatically proxied to `http://localhost:8000` via `vite.config.js`.*

### 10.3 Key Developer Verification Commands

- **Verify Database Integrity:**
  ```bash
  python3 -c "import sqlite3; conn=sqlite3.connect('backend/vigrah.db'); print(conn.execute('SELECT count(*) FROM events').fetchone()[0], 'events in DB')"
  ```
- **Run Backend Integrity Suite:**
  ```bash
  python3 backend/test_reconstruction_and_respond.py
  python3 backend/test_vigrah_pipeline.py
  ```

---

*Authored and verified for the VIGRAH AI Engineering Team.*
