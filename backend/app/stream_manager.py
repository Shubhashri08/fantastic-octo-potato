import os
import cv2
import time
from datetime import datetime
import threading
import numpy as np
import logging
from typing import Dict, Optional

logger = logging.getLogger("stream_manager")

class CameraStreamWorker:
    """
    High-Performance Zero-Latency Camera Stream Worker.
    Drains frames in background and serves smooth, real-time MJPEG streams
    with integrated neural vehicle & threat detection.
    """
    def __init__(self, camera_id: int, source: str, source_type: str, detection_engine):
        self.camera_id = camera_id
        self.source = source
        self.source_type = source_type
        self.detection_engine = detection_engine
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        self.latest_jpeg = None
        self.fps = 0.0
        self.frame_count = 0
        self.last_annotated_frame = None

        # Zero-Latency Frame Grabber
        self.latest_raw_frame = None
        self.frame_lock = threading.Lock()
        self.grab_thread = None

    def _grab_loop(self):
        """Continuously drains OpenCV network buffer in background to guarantee real-time (<50ms) frames."""
        cap = None
        while self.is_running:
            if cap is None or not cap.isOpened():
                if self.source_type == "webcam" or (isinstance(self.source, str) and self.source.isdigit()):
                    idx = int(self.source)
                    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
                else:
                    cap = cv2.VideoCapture(self.source)
                    try:
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    except Exception:
                        pass

                if not cap or not cap.isOpened():
                    time.sleep(0.5)
                    continue

            ret, frame = cap.read()
            if ret and frame is not None:
                with self.frame_lock:
                    self.latest_raw_frame = frame
            else:
                if self.source_type == "video":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    try:
                        cap.release()
                    except Exception:
                        pass
                    cap = None
                    time.sleep(0.2)
        if cap:
            cap.release()

    def _create_synthetic_frame(self, text="CONNECTING FEED..."):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f"VIGRAH AI - CAM #{self.camera_id}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 128), 2)
        cv2.putText(frame, text, (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        return frame

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.grab_thread = threading.Thread(target=self._grab_loop, daemon=True)
        self.grab_thread.start()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Stream worker started for Camera {self.camera_id} (Source: {self.source})")

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.grab_thread and self.grab_thread.is_alive():
            self.grab_thread.join(timeout=1.0)
        logger.info(f"Stream worker stopped for Camera {self.camera_id}")

    def _run_loop(self):
        frame_idx = 0
        last_time = time.time()
        
        while self.is_running:
            loop_start = time.time()
            raw_frame = None

            with self.frame_lock:
                if self.latest_raw_frame is not None:
                    raw_frame = self.latest_raw_frame.copy()

            if raw_frame is None:
                raw_frame = self._create_synthetic_frame(f"Connecting to: {self.source}")
                time.sleep(0.04)

            # Process frame through detection engine
            frame_idx += 1
            if frame_idx % 2 == 0 or self.last_annotated_frame is None:
                if self.detection_engine:
                    annotated, _ = self.detection_engine.process_frame(raw_frame, self.camera_id)
                    self.last_annotated_frame = annotated
                else:
                    self.last_annotated_frame = raw_frame
            
            display_frame = self.last_annotated_frame if self.last_annotated_frame is not None else raw_frame
            display_frame = display_frame.copy()

            # Official CCTV Forensic OSD Overlay
            dh, dw = display_frame.shape[:2]
            ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.rectangle(display_frame, (0, 0), (dw, 22), (12, 14, 20), -1)
            cam_labels = {
                1: "MUMBAI SAFE CITY // CAM-01 CSMT CONCOURSE",
                2: "BENGALURU TECH GRID // CAM-02 MG ROAD CORRIDOR",
                3: "LIVE FIELD PATROL // CAM-03 MOBILE SENSOR"
            }
            label = cam_labels.get(self.camera_id, f"SURVEILLANCE NODE // CAM-0{self.camera_id}")
            cv2.putText(display_frame, f"● REC [LIVE] {label}", (8, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 242, 254), 1)
            cv2.putText(display_frame, f"{ts_str} IST", (max(10, dw - 170), 15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (245, 223, 192), 1)

            ret, buffer = cv2.imencode('.jpg', display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret:
                with self.lock:
                    self.latest_jpeg = buffer.tobytes()

            self.frame_count += 1
            now = time.time()
            if now - last_time >= 1.0:
                self.fps = self.frame_count / (now - last_time)
                self.frame_count = 0
                last_time = now

            elapsed = time.time() - loop_start
            sleep_time = max(0.010, 0.035 - elapsed)
            time.sleep(sleep_time)

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self.lock:
            return self.latest_jpeg


class StreamManager:
    def __init__(self, detection_engine):
        self.detection_engine = detection_engine
        self.workers: Dict[int, CameraStreamWorker] = {}
        self.lock = threading.Lock()

    def start_camera(self, camera_id: int, source: str, source_type: str = "webcam"):
        with self.lock:
            if camera_id in self.workers:
                worker = self.workers[camera_id]
                if worker.source == source and worker.is_running:
                    return
                worker.stop()

            worker = CameraStreamWorker(camera_id, source, source_type, self.detection_engine)
            worker.start()
            self.workers[camera_id] = worker

    def stop_camera(self, camera_id: int):
        with self.lock:
            if camera_id in self.workers:
                self.workers[camera_id].stop()
                del self.workers[camera_id]

    def get_worker(self, camera_id: int) -> Optional[CameraStreamWorker]:
        with self.lock:
            return self.workers.get(camera_id)

    def generate_mjpeg_frames(self, camera_id: int):
        while True:
            worker = self.get_worker(camera_id)
            if worker and worker.is_running:
                frame_bytes = worker.get_latest_jpeg()
                if frame_bytes:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.035)
            else:
                time.sleep(0.1)
