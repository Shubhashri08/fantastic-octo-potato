import os
import cv2
import time
import asyncio
from datetime import datetime
import threading
import numpy as np
import logging
from typing import Dict, Optional

logger = logging.getLogger("stream_manager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class CameraStreamWorker:
    """
    Zero-Lag Real-Time Motion Projected Camera Stream Worker.
    Separates the high-frequency 30 FPS video render pipeline from background AI neural inference.
    Features:
      1. Real-time velocity motion projection: Bounding boxes are dynamically projected forward
         to match the current frame position, eliminating the 1-second lag!
      2. Clock-synchronized 30 FPS playback: Delivers fluid, continuous motion with zero frame skipping.
    """
    def __init__(self, camera_id: int, source: str, source_type: str, detection_engine):
        self.camera_id = camera_id
        self.source = source
        self.source_type = source_type
        self.detection_engine = detection_engine
        self.is_running = False

        # Dual Threads
        self.render_thread = None
        self.ai_thread = None
        self.grab_thread = None

        # Thread-safe frame buffers
        self.lock = threading.Lock()
        self.latest_jpeg = None
        self.frame_count = 0
        self.fps = 30.0

        # Raw frame buffer for AI worker
        self.frame_lock = threading.Lock()
        self.latest_raw_frame = None

        # Active neural annotations buffer
        self.anno_lock = threading.Lock()
        self.latest_annotations = {
            "detections": [],
            "vehicles": [],
            "timestamp": 0.0
        }
        self.last_accessed = time.time()

    def _normalize_stream_url(self, url: str) -> str:
        """Auto-corrects common phone IP camera endpoint patterns and resolves local file paths."""
        if not isinstance(url, str):
            return url
        url = url.strip()

        # 1. Local video files or webcam index
        if url.isdigit():
            return url

        # Direct existing file path (absolute or relative)
        if os.path.exists(url):
            return os.path.abspath(url)

        # Check candidate locations for video files
        clean_url = url.lstrip("/")
        base_name = os.path.basename(url)
        candidates = [
            os.path.join(BASE_DIR, clean_url),
            os.path.join(BASE_DIR, "samples", clean_url),
            os.path.join(BASE_DIR, "samples", base_name),
            os.path.join(BASE_DIR, "evidence", clean_url),
            os.path.join(BASE_DIR, "evidence", base_name),
            os.path.join(BASE_DIR, "verified_media", "videos", clean_url),
            os.path.join(BASE_DIR, "verified_media", "videos", base_name),
            os.path.join(BASE_DIR, "uploads", clean_url),
            os.path.join(BASE_DIR, "uploads", "videos", clean_url),
            os.path.join(BASE_DIR, "uploads", "videos", base_name),
            os.path.join(os.path.expanduser("~"), "Downloads", base_name),
            os.path.join(os.path.dirname(BASE_DIR), clean_url),
            os.path.join(os.path.dirname(BASE_DIR), "samples", base_name),
        ]
        
        # Test candidate paths directly and with common extensions if needed
        exts = ["", ".MOV", ".mov", ".mp4", ".MP4", ".avi", ".mkv", ".webm"]
        for ext in exts:
            for cand in list(candidates):
                test_path = cand + ext if ext and not cand.lower().endswith(ext.lower()) else cand
                if os.path.exists(test_path):
                    return os.path.abspath(test_path)

        # Case-insensitive search within samples directory
        samples_dir = os.path.join(BASE_DIR, "samples")
        if os.path.exists(samples_dir):
            try:
                for fname in os.listdir(samples_dir):
                    if fname.lower() == base_name.lower():
                        return os.path.join(samples_dir, fname)
                    if os.path.splitext(fname)[0].lower() == os.path.splitext(base_name)[0].lower():
                        return os.path.join(samples_dir, fname)
            except Exception:
                pass

        # 2. Phone IP Camera or Network stream
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("rtsp://")):
            if any(char.isdigit() for char in url) and (":" in url or "." in url):
                url = "http://" + url

        # Fix /videos -> /video (Android IP Webcam)
        if url.endswith("/videos"):
            url = url[:-7] + "/video"
        elif url.endswith("/videos/"):
            url = url[:-8] + "/video"
        elif url.endswith("/") and url.count("/") == 3:
            url = url + "video"
        elif url.count("/") == 2 and (url.startswith("http://") or url.startswith("https://")):
            url = url + "/video"
        return url

    def _grab_http_mjpeg(self, url: str):
        """Ultra-resilient direct HTTP MJPEG frame grabber for phone IP cameras."""
        import urllib.request
        normalized_url = self._normalize_stream_url(url)
        logger.info(f"Connecting to phone IP camera at: {normalized_url}")
        
        req = urllib.request.Request(
            normalized_url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (VigrahAI Surveillance Engine)',
                'Accept': 'multipart/x-mixed-replace, image/jpeg, */*'
            }
        )
        stream = urllib.request.urlopen(req, timeout=5.0)
        bytes_buffer = b""

        while self.is_running:
            chunk = stream.read(4096)
            if not chunk:
                break
            bytes_buffer += chunk

            # Find Start of JPEG (0xFF 0xD8)
            a = bytes_buffer.find(b'\xff\xd8')
            if a != -1:
                b = bytes_buffer.find(b'\xff\xd9', a + 2)
                if b != -1:
                    jpg = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    try:
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                            with self.frame_lock:
                                self.latest_raw_frame = frame
                    except Exception:
                        pass
            elif len(bytes_buffer) > 65536:
                bytes_buffer = bytes_buffer[-2048:]

    def _grab_network_loop(self):
        """Continuously drains phone IP camera or RTSP buffer in background."""
        norm_source = self._normalize_stream_url(self.source) if isinstance(self.source, str) else self.source
        while self.is_running:
            if isinstance(norm_source, str) and (norm_source.startswith("http://") or norm_source.startswith("https://")):
                try:
                    self._grab_http_mjpeg(norm_source)
                except Exception as e:
                    logger.warning(f"HTTP MJPEG grab error for {norm_source}: {e}. Retrying in 1s...")
                    time.sleep(1.0)
            else:
                time.sleep(0.5)

    def _create_synthetic_frame(self, text="CONNECTING FEED..."):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f"VIGRAH AI - CAM #{self.camera_id}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 128), 2)
        cv2.putText(frame, text, (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        return frame

    def start(self):
        if self.is_running:
            return
        self.is_running = True

        norm_source = self._normalize_stream_url(self.source) if isinstance(self.source, str) else self.source
        is_network = isinstance(norm_source, str) and (
            norm_source.startswith("http://") or norm_source.startswith("https://") or norm_source.startswith("rtsp://")
        )

        # Network stream grabber
        if is_network:
            self.grab_thread = threading.Thread(target=self._grab_network_loop, daemon=True)
            self.grab_thread.start()

        # Dedicated background AI worker thread
        self.ai_thread = threading.Thread(target=self._ai_worker_loop, daemon=True)
        self.ai_thread.start()

        # Dedicated 30 FPS render loop
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()

        logger.info(f"Zero-lag motion-projected stream worker started for Camera {self.camera_id} (Source: {self.source})")

    def stop(self):
        self.is_running = False
        for th in [self.render_thread, self.ai_thread, self.grab_thread]:
            if th and th.is_alive():
                th.join(timeout=0.5)
        logger.info(f"Stream worker stopped for Camera {self.camera_id}")

    def _ai_worker_loop(self):
        """Asynchronous background AI inference worker: extracts authentic detections without stalling video playback."""
        while self.is_running:
            # Idle sleep if camera stream has no active viewers for > 6 seconds
            if time.time() - self.last_accessed > 6.0:
                time.sleep(0.4)
                continue

            frame_snapshot = None
            with self.frame_lock:
                if self.latest_raw_frame is not None:
                    frame_snapshot = self.latest_raw_frame.copy()

            if frame_snapshot is None:
                time.sleep(0.02)
                continue

            try:
                if self.detection_engine:
                    if hasattr(self.detection_engine, "extract_detections"):
                        dets, vehs, _ = self.detection_engine.extract_detections(
                            frame_snapshot, self.camera_id, source=self.source
                        )
                    else:
                        _, _ = self.detection_engine.process_frame(frame_snapshot, self.camera_id)
                        dets, vehs = [], []

                    now = time.time()
                    with self.anno_lock:
                        self.latest_annotations = {
                            "detections": dets,
                            "vehicles": vehs,
                            "timestamp": now
                        }
            except Exception as e:
                logger.error(f"AI worker error for Camera {self.camera_id}: {e}")

            time.sleep(0.06)

    def _render_loop(self):
        """Clock-synchronized, 30 FPS video compositor with Real-Time Motion Projection."""
        norm_source = self._normalize_stream_url(self.source) if isinstance(self.source, str) else self.source
        cap = None

        is_network = isinstance(norm_source, str) and (
            norm_source.startswith("http://") or norm_source.startswith("https://") or norm_source.startswith("rtsp://")
        )
        is_video_file = (
            self.source_type == "video" or
            (isinstance(norm_source, str) and (
                norm_source.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.ts')) or
                os.path.isfile(norm_source)
            ))
        )

        fps_target = 30.0
        frame_interval = 1.0 / fps_target
        last_fps_time = time.perf_counter()
        frames_in_second = 0

        while self.is_running:
            # Idle sleep if camera stream has no active viewers for > 6 seconds
            if time.time() - self.last_accessed > 6.0:
                time.sleep(0.2)
                continue

            loop_start = time.perf_counter()
            frame = None

            if is_network:
                with self.frame_lock:
                    if self.latest_raw_frame is not None:
                        frame = self.latest_raw_frame.copy()
            else:
                if cap is None or not cap.isOpened():
                    if self.source_type == "webcam" or (isinstance(norm_source, str) and norm_source.isdigit()):
                        idx = int(norm_source)
                        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
                    else:
                        cap = cv2.VideoCapture(norm_source)
                        try:
                            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        except Exception:
                            pass

                    if not cap or not cap.isOpened():
                        synthetic = self._create_synthetic_frame(f"Connecting to: {self.source}")
                        ret, buffer = cv2.imencode('.jpg', synthetic, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                        if ret:
                            with self.lock:
                                self.latest_jpeg = buffer.tobytes()
                        time.sleep(0.3)
                        continue

                ret, frame = cap.read()
                if not ret or frame is None:
                    if is_video_file:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                    if not ret or frame is None:
                        time.sleep(0.033)
                        continue

                # Normalize high-res video to 960px for instant 30 FPS encoding
                fh, fw = frame.shape[:2]
                if fw > 960:
                    scale = 960.0 / fw
                    frame = cv2.resize(frame, (960, int(fh * scale)), interpolation=cv2.INTER_AREA)

                # Publish latest frame for AI worker
                with self.frame_lock:
                    self.latest_raw_frame = frame

            if frame is None:
                time.sleep(0.02)
                continue

            display_frame = frame.copy()

            # Retrieve latest neural annotations with timestamp
            with self.anno_lock:
                cur_dets = list(self.latest_annotations.get("detections", []))
                cur_vehs = list(self.latest_annotations.get("vehicles", []))
                anno_ts = self.latest_annotations.get("timestamp", time.time())

            # Render annotations with real-time motion projection (<0.5ms)
            if self.detection_engine and hasattr(self.detection_engine, "render_annotations"):
                display_frame = self.detection_engine.render_annotations(
                    display_frame, cur_dets, cur_vehs, self.camera_id, current_time=time.time()
                )

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

            # Encode to JPEG (<10ms)
            ret, buffer = cv2.imencode('.jpg', display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret:
                with self.lock:
                    self.latest_jpeg = buffer.tobytes()
                    self.frame_count += 1

            # FPS calculation
            frames_in_second += 1
            now = time.perf_counter()
            if now - last_fps_time >= 1.0:
                self.fps = frames_in_second / (now - last_fps_time)
                frames_in_second = 0
                last_fps_time = now

            # Clock-locked frame pacing (30 FPS)
            elapsed = time.perf_counter() - loop_start
            sleep_time = max(0.001, frame_interval - elapsed)
            time.sleep(sleep_time)

        if cap:
            cap.release()

    def get_latest_jpeg(self) -> Optional[bytes]:
        self.last_accessed = time.time()
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

    def get_frame(self, camera_id: int) -> Optional[bytes]:
        worker = self.get_worker(camera_id)
        return worker.get_latest_jpeg() if worker else None

    def get_latest_frame(self, camera_id: int) -> Optional[bytes]:
        return self.get_frame(camera_id)

    async def generate_mjpeg_frames(self, camera_id: int):
        """Asynchronously streams newly rendered frames at ~30 FPS with zero latency."""
        last_id = -1
        while True:
            worker = self.get_worker(camera_id)
            if worker and worker.is_running:
                frame_bytes = worker.get_latest_jpeg()
                frame_id = worker.frame_count
                if frame_bytes and frame_id != last_id:
                    last_id = frame_id
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                await asyncio.sleep(0.008)
            else:
                await asyncio.sleep(0.05)
