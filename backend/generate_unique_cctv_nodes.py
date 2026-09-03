import os
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)

# List of distinct CCTV nodes with unique scene styles, color palettes, and motion dynamics
CCTV_PROFILES = [
    # --- MUMBAI CCTV NODES ---
    {
        "filename": "mumbai_sealink_toll.mp4",
        "cam_id": "MUM-01",
        "location": "Bandra-Worli Sea Link Toll Plaza",
        "base_color": (35, 30, 25),      # Ocean coastal dark tone
        "scene_type": "highway_toll",
        "speed_kmh": 65
    },
    {
        "filename": "mumbai_csmt_station.mp4",
        "cam_id": "MUM-02",
        "location": "CSMT Central Transit Concourse",
        "base_color": (30, 28, 35),      # Urban heritage stone tone
        "scene_type": "crowd_transit",
        "speed_kmh": 5
    },
    {
        "filename": "mumbai_marine_drive_north.mp4",
        "cam_id": "MUM-03",
        "location": "Marine Drive Promenade North",
        "base_color": (40, 35, 20),      # Coastal amber glow
        "scene_type": "coastal_road",
        "speed_kmh": 48
    },
    {
        "filename": "mumbai_nariman_point.mp4",
        "cam_id": "MUM-04",
        "location": "Nariman Business District",
        "base_color": (25, 25, 30),      # Modern glass building tone
        "scene_type": "traffic_cross",
        "speed_kmh": 42
    },
    {
        "filename": "mumbai_dadar_tt_circle.mp4",
        "cam_id": "MUM-05",
        "location": "Dadar TT Circle Junction",
        "base_color": (35, 35, 30),      # Dense arterial junction
        "scene_type": "dense_junction",
        "speed_kmh": 35
    },
    {
        "filename": "mumbai_bkc_connector.mp4",
        "cam_id": "MUM-06",
        "location": "Bandra Kurla Complex (BKC) Connector",
        "base_color": (20, 30, 35),      # High-tech financial district
        "scene_type": "expressway",
        "speed_kmh": 55
    },
    {
        "filename": "mumbai_andheri_weh.mp4",
        "cam_id": "MUM-07",
        "location": "Andheri WEH Flyover Junction",
        "base_color": (30, 30, 28),      # Flyover elevated view
        "scene_type": "flyover_traffic",
        "speed_kmh": 60
    },
    {
        "filename": "mumbai_goregaon_hub.mp4",
        "cam_id": "MUM-08",
        "location": "Goregaon Hub Mall Junction",
        "base_color": (28, 25, 35),      # Commercial mall perimeter
        "scene_type": "commercial_hub",
        "speed_kmh": 30
    },
    {
        "filename": "mumbai_powai_hiranandani.mp4",
        "cam_id": "MUM-09",
        "location": "Powai Hiranandani Main Gate",
        "base_color": (25, 35, 30),      # Tree-lined boulevard
        "scene_type": "boulevard",
        "speed_kmh": 38
    },
    {
        "filename": "mumbai_vashi_toll.mp4",
        "cam_id": "MUM-10",
        "location": "Vashi Toll Plaza (Sion-Panvel)",
        "base_color": (35, 30, 30),      # Interstate multi-lane toll
        "scene_type": "interstate_toll",
        "speed_kmh": 70
    },
    # --- BENGALURU CCTV NODES ---
    {
        "filename": "blr_mg_road_metro.mp4",
        "cam_id": "BLR-001",
        "location": "MG Road Metro Gate 2 Concourse",
        "base_color": (25, 30, 35),      # Metro plaza
        "scene_type": "metro_concourse",
        "speed_kmh": 4
    },
    {
        "filename": "blr_indiranagar_100ft.mp4",
        "cam_id": "BLR-002",
        "location": "Indiranagar 100ft Road Signal",
        "base_color": (32, 28, 26),      # Retail food street
        "scene_type": "urban_signal",
        "speed_kmh": 36
    },
    {
        "filename": "blr_koramangala_signal.mp4",
        "cam_id": "BLR-003",
        "location": "Koramangala Sony World Signal",
        "base_color": (30, 32, 30),      # Multi-lane arterial
        "scene_type": "dense_junction",
        "speed_kmh": 40
    },
    {
        "filename": "blr_outer_ring_road.mp4",
        "cam_id": "BLR-004",
        "location": "Outer Ring Road Junction 14",
        "base_color": (26, 26, 32),      # Tech park corridor
        "scene_type": "tech_corridor",
        "speed_kmh": 58
    },
    {
        "filename": "blr_electronic_city_flyover.mp4",
        "cam_id": "BLR-005",
        "location": "Electronic City Elevated Tollway",
        "base_color": (34, 30, 28),      # High-speed elevated expressway
        "scene_type": "expressway",
        "speed_kmh": 75
    }
]

def generate_unique_cctv_clip(profile, total_frames=90, fps=15.0):
    """
    Generates a unique, high-definition CCTV video clip with authentic perspective,
    dynamic vehicle/pedestrian trajectories, visual tone, and municipal surveillance OSD overlay.
    """
    filepath = os.path.join(SAMPLES_DIR, profile["filename"])
    w, h = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(filepath, fourcc, fps, (w, h))

    base_b, base_g, base_r = profile["base_color"]
    scene = profile["scene_type"]
    cam_tag = f"CCTV [{profile['cam_id']}] - {profile['location']}"

    # Vehicle motion simulation seeds
    num_actors = 4 if "highway" in scene or "expressway" in scene else 6
    actors = []
    for a in range(num_actors):
        actors.append({
            "x": np.random.randint(50, w - 100),
            "y": np.random.randint(160, h - 80),
            "vx": np.random.choice([-4, -3, 3, 5]),
            "vy": np.random.choice([-1, 0, 1]),
            "type": "vehicle" if "road" in scene or "toll" in scene or "junction" in scene or "expressway" in scene else "person",
            "color": (np.random.randint(50, 240), np.random.randint(50, 240), np.random.randint(50, 240))
        })

    for f_idx in range(total_frames):
        # Base scene canvas
        frame = np.full((h, w, 3), (base_b, base_g, base_r), dtype=np.uint8)

        # Perspective Road / Concourse Lines
        if "toll" in scene or "expressway" in scene or "road" in scene or "junction" in scene or "corridor" in scene:
            # Road asphalt
            cv2.fillPoly(frame, [np.array([[80, 180], [w - 80, 180], [w, h], [0, h]])], (20, 20, 22))
            # Road lane markings
            dash_offset = (f_idx * 4) % 40
            for dy in range(190 + dash_offset, h, 40):
                cv2.line(frame, (w // 2, dy), (w // 2, min(h, dy + 20)), (200, 200, 200), 2)
                cv2.line(frame, (w // 4, dy), (w // 4 - 20, min(h, dy + 20)), (160, 160, 160), 1)
                cv2.line(frame, (3 * w // 4, dy), (3 * w // 4 + 20, min(h, dy + 20)), (160, 160, 160), 1)
        else:
            # Pedestrian Concourse tiles
            for gy in range(160, h, 30):
                cv2.line(frame, (0, gy), (w, gy), (45, 45, 50), 1)
            for gx in range(0, w, 40):
                cv2.line(frame, (gx, 160), (gx, h), (45, 45, 50), 1)

        # Dynamic actors (Vehicles / Pedestrians with bounding boxes)
        for act in actors:
            act["x"] = (act["x"] + act["vx"]) % (w - 60)
            act["y"] = min(h - 50, max(180, act["y"] + act["vy"]))
            ax, ay = int(act["x"]), int(act["y"])

            if act["type"] == "vehicle":
                bw, bh = 60, 32
                cv2.rectangle(frame, (ax, ay), (ax + bw, ay + bh), act["color"], -1)
                cv2.rectangle(frame, (ax, ay), (ax + bw, ay + bh), (220, 220, 220), 1)
                # Headlights
                if act["vx"] > 0:
                    cv2.circle(frame, (ax + bw - 4, ay + 8), 3, (0, 255, 255), -1)
                    cv2.circle(frame, (ax + bw - 4, ay + bh - 8), 3, (0, 255, 255), -1)
                else:
                    cv2.circle(frame, (ax + 4, ay + 8), 3, (0, 255, 255), -1)
                    cv2.circle(frame, (ax + 4, ay + bh - 8), 3, (0, 255, 255), -1)
            else:
                pw, ph = 20, 45
                cv2.rectangle(frame, (ax, ay), (ax + pw, ay + ph), act["color"], -1)
                cv2.circle(frame, (ax + 10, ay - 6), 6, (200, 180, 160), -1)

        # Real-Time CCTV On-Screen Display (OSD HUD)
        sec = f_idx // 15
        time_str = f"2026-08-18 18:{35 + (sec // 60):02d}:{sec % 60:02d}.{int((f_idx % 15) * 66):03d}"
        
        # Header banner
        cv2.rectangle(frame, (0, 0), (w, 36), (0, 0, 0), -1)
        cv2.putText(frame, cam_tag, (12, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, time_str, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 128), 1, cv2.LINE_AA)
        
        # Bottom telemetry
        cv2.rectangle(frame, (0, h - 22), (w, h), (0, 0, 0), -1)
        telemetry = f"ZONE: {profile['location'][:24]} | SPEED: {profile['speed_kmh']} km/h | 1080p60fps"
        cv2.putText(frame, telemetry, (12, h - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1, cv2.LINE_AA)

        # REC blinking indicator
        if (f_idx // 8) % 2 == 0:
            cv2.circle(frame, (w - 20, 18), 5, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (w - 45, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 255), 1, cv2.LINE_AA)

        writer.write(frame)

    writer.release()
    print(f"  [OK] Generated unique CCTV clip: {profile['filename']} ({profile['location']})")

def main():
    print("Generating 15 Unique CCTV Surveillance Video Feeds...")
    for p in CCTV_PROFILES:
        generate_unique_cctv_clip(p)
    print("All 15 unique CCTV video feeds generated successfully!")

if __name__ == "__main__":
    main()
