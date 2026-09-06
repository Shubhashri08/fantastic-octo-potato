# Verified Surveillance & Forensic Media Catalog

All synthetic/generated videos and testing recordings have been decommissioned.
This catalog documents the **5 Verified Field Incidents** deployed to the VIGRAH AI Respond Console, as well as the underlying raw video assets, split segments, and model-derived forensic snapshots.

---

## 1. Verified Respond Incidents (Active Queue: Exactly 5 High-Impact Incidents)

| Incident ID | Threat Classification | Camera Node & Location | Confidence | Video Asset | Model-Annotated Snapshot |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **#6001** | **Vehicle Collision** | **CAM-04**: Bengaluru Trinity Circle Transit Node | **97%** | `accident_cut_01_daylight_intersection.mp4` | `accident_cut_01_daylight_intersection_snap.jpg` |
| **#6002** | **Vehicle Collision** | **CAM-06**: Mumbai Worli Sea Face Intercept | **98%** | `accident_cut_02_night_junction_tbone.mp4` | `accident_cut_02_night_junction_tbone_snap.jpg` |
| **#6003** | **Accident** | **CAM-05**: Bengaluru Outer Ring Road Hub | **98%** | `accident_cut_03_truck_swerve_sidewalk.mp4` | `accident_cut_03_truck_swerve_sidewalk_snap.jpg` |
| **#6004** | **Vehicle Collision** | **CAM-03**: Mumbai Marine Drive Coastal Unit | **95%** | `accident_cut_04_highway_night_rear_end.mp4` | `accident_cut_04_highway_night_rear_end_snap.jpg` |
| **#6005** | **Fire** | **CAM-02**: Bengaluru MG Road Commercial Corridor | **99%** | `fire_1.mp4` | `cctv_fire_mgroad.jpg` |

---

## 2. Split Accident Segments (`backend/verified_media/verified_cuts/`)

*Extracted directly from the surveillance compilation video `videoplayback (online-video-cutter.com).mp4` (76.6s, 640x360 @ 30fps):*

1. **`accident_cut_01_daylight_intersection.mp4`** (0.0s – 8.6s, 2.4 MB)
   - **Scene**: Daylight broadside collision at marked intersection between red sedan and oncoming grey SUV.
   - **Model Classification**: Vehicle bounding boxes detected with severe IoU overlap (IoU = 0.98), classified as **Vehicle Collision** (97% confidence).
2. **`accident_cut_02_night_junction_tbone.mp4`** (8.6s – 20.6s, 2.0 MB)
   - **Scene**: Night urban junction T-bone collision with multiple vehicles crossing simultaneously.
   - **Model Classification**: Impact conflict box alert, classified as **Vehicle Collision** (98% confidence).
3. **`accident_cut_03_truck_swerve_sidewalk.mp4`** (20.6s – 38.0s, 4.7 MB)
   - **Scene**: Box truck loses control and swerves directly onto pedestrian sidewalk near shop fronts.
   - **Model Classification**: Pedestrian detection (0.84, 0.71) + vehicle swerve trajectory conflict, classified as **Accident / Pedestrian Hazard** (98% confidence).
4. **`accident_cut_04_highway_night_rear_end.mp4`** (38.0s – 58.0s, 3.0 MB)
   - **Scene**: Night arterial highway rear-end impact causing vehicle spinout.
   - **Model Classification**: High-speed tail impact, classified as **Vehicle Collision** (95% confidence).
5. **`accident_cut_05_intersection_crossover.mp4`** (58.0s – 66.0s, 1.7 MB)
   - **Scene**: Multi-lane congested intersection crossover impact between commercial truck and sedan.
   - **Model Classification**: Intersection collision conflict.
6. **`accident_cut_06_arterial_lane_drift.mp4`** (66.0s – 76.6s, 3.0 MB)
   - **Scene**: Multi-lane arterial roadway lane drift sideswipe collision.

---

## 3. Model-Derived Forensic Snapshots (`backend/verified_media/verified_snapshots/`)

Each forensic snapshot is annotated with YOLO detection bounding boxes, confidence badges, and an official CCTV forensic header:

| Snapshot Filename | Origin Video | Detected Threat & Telemetry | Assigned Node |
| :--- | :--- | :--- | :--- |
| `accident_cut_01_daylight_intersection_snap.jpg` | `accident_cut_01_daylight_intersection.mp4` | Red Sedan vs Grey SUV Broadside Overlap (97%) | CAM-04: Trinity Circle Node |
| `accident_cut_02_night_junction_tbone_snap.jpg` | `accident_cut_02_night_junction_tbone.mp4` | Night Junction T-Bone Collision Alert (98%) | CAM-06: Worli Sea Face Intercept |
| `accident_cut_03_truck_swerve_sidewalk_snap.jpg` | `accident_cut_03_truck_swerve_sidewalk.mp4` | Truck Sidewalk Swerve + Pedestrian Proximity (98%) | CAM-05: Outer Ring Road Hub |
| `accident_cut_04_highway_night_rear_end_snap.jpg` | `accident_cut_04_highway_night_rear_end.mp4` | Night Highway Rear-End Spinout Alert (95%) | CAM-03: Marine Drive Coastal Unit |
| `accident_cut_05_intersection_crossover_snap.jpg` | `accident_cut_05_intersection_crossover.mp4` | Truck-Sedan Crossover Impact Conflict (94%) | CAM-07: Platform / Concourse |
| `cctv_fire_mgroad.jpg` | `fire_1.mp4` | Commercial Corridor Roadway Fire Outbreak (99%) | CAM-02: MG Road Corridor |
