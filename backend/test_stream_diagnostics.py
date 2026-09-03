import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal
from app.models import Camera
from app.stream_manager import StreamManager

class MockDetectionEngine:
    def process_frame(self, frame, camera_id):
        return frame, []

def diagnose():
    print("==================================================")
    print("      STREAM MANAGER DIAGNOSTICS TEST")
    print("==================================================")

    db = SessionLocal()
    cams = db.query(Camera).all()
    print(f"\n1. Database Cameras ({len(cams)} found):")
    for c in cams:
        print(f"   - [CAM {c.id}] {c.name} | source: '{c.source}' | type: '{c.source_type}' | active: {c.is_active}")

    engine = MockDetectionEngine()
    sm = StreamManager(engine)

    print("\n2. Testing Camera 1 (Local Video Sample)...")
    cam1 = db.query(Camera).filter(Camera.id == 1).first()
    sm.start_camera(1, cam1.source, cam1.source_type)

    print("   Waiting 2 seconds for worker to grab frames...")
    time.sleep(2.0)

    worker1 = sm.get_worker(1)
    if worker1:
        print(f"   Worker 1 is_running: {worker1.is_running}")
        print(f"   Worker 1 raw frame present: {worker1.latest_raw_frame is not None}")
        if worker1.latest_raw_frame is not None:
            print(f"   Worker 1 frame shape: {worker1.latest_raw_frame.shape}")
        jpeg1 = worker1.get_latest_jpeg()
        print(f"   Worker 1 JPEG bytes generated: {len(jpeg1) if jpeg1 else 0} bytes")
    else:
        print("   Worker 1 NOT created!")

    print("\n3. Testing Camera 3 with user IP (http://10.49.119.32:8080/video)...")
    sm.start_camera(3, "http://10.49.119.32:8080/video", "rtsp")
    time.sleep(2.0)

    worker3 = sm.get_worker(3)
    if worker3:
        print(f"   Worker 3 is_running: {worker3.is_running}")
        print(f"   Worker 3 raw frame present: {worker3.latest_raw_frame is not None}")
        jpeg3 = worker3.get_latest_jpeg()
        print(f"   Worker 3 JPEG bytes generated: {len(jpeg3) if jpeg3 else 0} bytes")
    else:
        print("   Worker 3 NOT created!")

    sm.stop_camera(1)
    sm.stop_camera(3)
    db.close()
    print("\nDiagnostics complete.")

if __name__ == "__main__":
    diagnose()
