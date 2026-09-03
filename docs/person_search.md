# VIGRAH AI — Person Identification & CCTV Person Search Subsystem

## 1. System Architecture Overview

The VIGRAH AI Person Identification and CCTV Person Search subsystem provides end-to-end, multi-camera neural video indexing, tracking, quality assessment, and appearance similarity retrieval.

```
[ CCTV VIDEO STREAM / MP4 ]
           │
           ▼
[ Frame Ingestion (~3 FPS configurable via PERSON_INDEX_FPS) ]
           │
           ▼
[ YOLO11 Person Detection (Class = 0) ]
           │
           ▼
[ ByteTrack Multi-Object Association & Kalman Filtering ]
           │
           ▼
[ Deterministic Person Crop Quality Assessment ]
           │
           ▼
[ TransReID Vision Transformer Feature Extractor ]
           │
           ▼
[ L2-Normalized 768-D Feature Embedding ]
           │
           ▼
[ Track-Level Quality-Weighted Mean Embedding Aggregation ]
           │
           ▼
[ Vector Database (PostgreSQL + pgvector / SQLite Development Engine) ]
```

---

## 2. Neural Models & Tracking Infrastructure

### A. Person Detection
- **Model**: YOLO11n (`yolo11n.pt`)
- **Class**: Class 0 (Person / Pedestrian)
- **Output**: Bounding Box `[x1, y1, x2, y2]`, Detection Confidence, Class ID

### B. Multi-Object Tracking
- **Algorithm**: ByteTrack ([FoundationVision/ByteTrack](https://github.com/FoundationVision/ByteTrack))
- **Mechanism**: Kalman state estimation (`[x_center, y_center, aspect_ratio, height, vx, vy, va, vh]`), two-stage bipartite Hungarian matching using IoU distance.
- **Configurable Parameters**:
  - `BYTE_TRACK_THRESH`: Minimum confidence for primary detection association (default: `0.50`).
  - `BYTE_MATCH_THRESH`: Maximum IoU distance threshold for Hungarian association (default: `0.70`).
  - `BYTE_TRACK_BUFFER`: Maximum frame retention for lost tracks before removal (default: `30` frames).

### C. Person Re-Identification Model
- **Model**: TransReID Vision Transformer ([damo-cv/TransReID](https://github.com/damo-cv/TransReID), ICCV 2021)
- **Backbone**: ViT-Base with 16x16 patch embeddings
- **Pretrained Checkpoint**: Market-1501 / MSMT17 weights (`backend/weights/transreid_market1501.pth`)
- **Runtime Dimension**: 768-D (dynamically validated on startup)
- **Preprocessing**:
  - Resolution: 256x128 px (Height: 256, Width: 128)
  - Color space: RGB
  - Normalization: ImageNet standard (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`)
- **Output**: Unit L2-normalized float32 embedding vector (`||v|| = 1.0`)

---

## 3. Crop Quality Filter

Crops are evaluated deterministically with a quality score in `[0.0, 1.0]`:
1. **Resolution Factor**: Minimum 24x48px (penalizes extreme low-resolution sightings).
2. **Aspect Ratio Factor**: Evaluates body proportion (penalizes wide boxes or thin slivers).
3. **Laplacian Blur Variance**: Detects motion blur and defocus.
4. **Illumination & Contrast**: Detects severe underexposure / silhouette or overexposure.
5. **Frame Clipping**: Penalizes bounding boxes intersecting the camera edge.

---

## 4. Database Architecture & Vector Search

### Supported Backends
1. **Production**: PostgreSQL with `pgvector` extension (`<=>` cosine distance index).
2. **Development Fallback**: Local SQLite database with optimized NumPy vectorized cosine similarity.

### Table Schema

#### `video_evidence`
- `source_id`: Unique video identifier (e.g., `VIDEO-01`)
- `source_hash`: SHA-256 idempotency checksum
- `filename`, `file_path`, `source_name`
- `camera_id`: Camera identifier (e.g., `CAM-01`)
- `location`, `latitude`, `longitude`
- `duration_sec`, `fps`, `total_frames`
- `status`: `queued` | `processing` | `ready` | `failed`
- `error_message`, `track_count`, `sighting_count`

#### `person_video_tracks`
- `track_id`: Unique track identifier (e.g., `TRK-001`)
- `source_id`, `camera_id`, `camera_name`, `location`
- `start_time_sec`, `end_time_sec`, `first_seen_formatted`, `last_seen_formatted`
- `detection_count`, `quality_score`, `representative_crop_path`
- `average_embedding`: Quality-weighted mean L2-normalized vector
- **Model Provenance**: `reid_model`, `reid_model_version`, `embedding_dim`, `index_version`, `embedding_created_at`
- **Cross-Camera Association**: `appearance_cluster_id`, `cluster_confidence`, `linked_track_ids`

#### `person_video_sightings`
- `sighting_id`, `track_id`, `source_id`, `camera_id`
- `timestamp_sec`, `frame_number`, `formatted_time`
- `crop_path`, `bbox`, `confidence`, `quality_score`, `detection_confidence`
- `embedding`, `reid_model`, `reid_model_version`, `embedding_dim`, `index_version`

---

## 5. API Reference

### 1. Upload Video Evidence (Asynchronous)
- **Endpoint**: `POST /api/person/videos/upload`
- **Parameters**: `file` (MP4/AVI), `source_name`, `camera_id`, `location`
- **Response**:
  ```json
  {
    "status": "queued",
    "message": "Video evidence [VIDEO-01] accepted and queued for background indexing.",
    "video": {
      "source_id": "VIDEO-01",
      "status": "queued"
    }
  }
  ```

### 2. Search Person (Query Photo)
- **Endpoint**: `POST /api/person/search`
- **Parameters**: `file` (Image), `min_similarity` (default 0.50), `camera_id`, `limit` (default 10)
- **Response (Success)**:
  ```json
  {
    "status": "success",
    "query": {
      "model": "TransReID-ViT-Base",
      "embedding_dimension": 768,
      "quality": 0.92
    },
    "total_candidates": 3,
    "returned_candidates": 3,
    "matches": [
      {
        "rank": 1,
        "is_best_match": true,
        "track_id": "TRK-001",
        "source_id": "VIDEO-01",
        "camera_id": "CAM-01",
        "camera_name": "CAM-01: Mumbai CSMT Concourse",
        "location": "Mumbai CSMT Terminal",
        "first_seen": "00:04",
        "last_seen": "00:18",
        "similarity": 0.8942,
        "similarity_percent": 89,
        "quality_score": 0.88,
        "sighting_count": 8,
        "representative_crop_url": "/api/person/evidence/VIDEO-01/TRK-001",
        "sightings": [...]
      }
    ]
  }
  ```
- **Error Codes**:
  - `NO_PERSON_DETECTED`: No person found in uploaded image.
  - `MULTIPLE_PERSONS_DETECTED`: Multiple individuals found in uploaded image.
  - `QUERY_QUALITY_TOO_LOW`: Uploaded photograph resolution/contrast/blur unviable for reliable Re-ID.

### 3. System Status
- **Endpoint**: `GET /api/status`
- **Response**:
  ```json
  {
    "status": "online",
    "device": "mps",
    "person_reid": {
      "enabled": true,
      "model": "TransReID-ViT-Base",
      "model_version": "transreid-damo-market1501-v1",
      "checkpoint_loaded": true,
      "embedding_dimension": 768,
      "device": "mps",
      "vector_database": "sqlite_numpy_fallback",
      "indexed_videos": 4,
      "indexed_tracks": 28
    }
  }
  ```

---

## 6. CLI Tools & Verification

1. **Verify Person Re-ID Index**:
   ```bash
   python -m backend.tools.verify_person_index
   ```
2. **Execute Real Image Query Search**:
   ```bash
   python -m backend.tools.test_person_search --query path/to/person.jpg --similarity 0.50 --limit 10
   ```
3. **Re-index Video Gallery**:
   ```bash
   python -m backend.tools.reindex_persons
   ```
4. **Database Schema Migration**:
   ```bash
   python -m backend.tools.migrate_person_schema
   ```
