import os
import re
import cv2
import time
import logging
import datetime
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

logger = logging.getLogger("vehicle_intelligence")

# Mapping of COCO class IDs to standardized vehicle type names
COCO_VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# Standard Indian State and Union Territory codes (MoRTH)
INDIAN_STATE_CODES = {
    "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "DN", "GA", "GJ", "HR",
    "HP", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP", "MZ",
    "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB", "AN", "BH"
}

# OCR character disambiguation mapping based on position in Indian license plate
DIGIT_TO_LETTER = {
    '0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B'
}
LETTER_TO_DIGIT = {
    'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8', 'Q': '0', 'D': '0', 'G': '6'
}


class VehicleColorClassifier:
    """
    Classifies vehicle color from the vehicle body crop.
    Analyzes the central vehicle body region in HSV and Lab color spaces
    with dominant pixel clustering to handle shadows, glares, and partial gate occlusions.
    """
    
    # Practical vehicle color labels
    COLOR_NAMES = [
        "black", "white", "silver", "grey", "red", "blue", 
        "green", "yellow", "brown", "orange"
    ]

    @staticmethod
    def classify(vehicle_crop: np.ndarray) -> Tuple[str, float]:
        if vehicle_crop is None or vehicle_crop.size == 0:
            return "unknown", 0.0

        h, w = vehicle_crop.shape[:2]
        if h < 10 or w < 10:
            return "unknown", 0.0

        # Sample the core body region of the vehicle crop
        core = vehicle_crop[int(h * 0.25):int(h * 0.85), int(w * 0.15):int(w * 0.85)]
        if core.size == 0:
            core = vehicle_crop

        hsv = cv2.cvtColor(core, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(core, cv2.COLOR_BGR2LAB)

        h_chan = hsv[:, :, 0]
        s_chan = hsv[:, :, 1]
        v_chan = hsv[:, :, 2]
        l_chan = lab[:, :, 0]

        total_px = float(core.shape[0] * core.shape[1])
        if total_px == 0:
            return "unknown", 0.0

        # 1. White/Light paint mask (high luminance, low saturation)
        white_mask = (v_chan > 215) & (s_chan < 55)
        white_ratio = np.sum(white_mask) / total_px

        # 2. Black/Dark paint mask (very low luminance)
        black_mask = (v_chan < 55) | (l_chan < 45)
        black_ratio = np.sum(black_mask) / total_px

        # 3. Yellow/Orange chromatic mask
        yellow_mask = (h_chan >= 15) & (h_chan <= 38) & (s_chan > 65) & (v_chan > 75)
        yellow_ratio = np.sum(yellow_mask) / total_px

        # 4. Red chromatic mask (wrap-around 0 and 180 hue)
        red_mask = ((h_chan < 14) | (h_chan > 165)) & (s_chan > 60) & (v_chan > 55)
        red_ratio = np.sum(red_mask) / total_px

        # 5. Blue chromatic mask
        blue_mask = (h_chan >= 85) & (h_chan <= 135) & (s_chan > 60) & (v_chan > 55)
        blue_ratio = np.sum(blue_mask) / total_px

        # 6. Green chromatic mask
        green_mask = (h_chan > 38) & (h_chan < 85) & (s_chan > 60) & (v_chan > 55)
        green_ratio = np.sum(green_mask) / total_px

        # Pure achromatic check (e.g. White, Silver, Grey, Black)
        mean_s = float(np.mean(s_chan))
        mean_v = float(np.mean(v_chan))
        if mean_s < 38:
            if mean_v >= 210:
                return "white", 0.98
            elif mean_v >= 135:
                return "silver", 0.90
            elif mean_v >= 55:
                return "grey", 0.88
            else:
                return "black", 0.95

        # Decision rules prioritized by paint distribution
        if white_ratio > 0.30:
            return "white", round(min(0.98, 0.85 + white_ratio * 0.15), 2)
        if yellow_ratio > 0.18:
            return "yellow", 0.93
        if red_ratio > 0.22:
            return "red", round(min(0.98, 0.85 + red_ratio * 0.15), 2)
        if blue_ratio > 0.30:
            return "blue", round(min(0.98, 0.85 + blue_ratio * 0.15), 2)
        if green_ratio > 0.25:
            return "green", 0.91
        if black_ratio > 0.45:
            return "black", 0.94

        # Fallback to dominant chromatic mask
        ratios = {"red": red_ratio, "blue": blue_ratio, "yellow": yellow_ratio, "green": green_ratio, "white": white_ratio, "black": black_ratio}
        top_color = max(ratios, key=ratios.get)
        return top_color, 0.86




class IndianPlateRecognizer:
    """
    Detects Indian vehicle number plates within vehicle bounding boxes,
    performs OCR using Neural PyTorch Models (EasyOCR & contour analysis),
    and normalizes according to Indian MoRTH standards.
    """

    def __init__(self):
        self.easy_ocr = None
        self._init_ocr()

    def _init_ocr(self):
        """Initializes Neural OCR engine (EasyOCR)."""
        try:
            import easyocr
            self.easy_ocr = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR neural text recognition engine loaded successfully.")
        except Exception as e:
            logger.info(f"EasyOCR init notice: {e}")

    @staticmethod
    def detect_plate_region(vehicle_crop: np.ndarray) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int], float]]:
        """
        Detects Indian rectangular number plate region within vehicle crop.
        Returns: (plate_crop, (x1, y1, x2, y2), confidence)
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None

        vh, vw = vehicle_crop.shape[:2]
        if vh < 25 or vw < 25:
            return None

        # Number plates are typically located in the lower 60% of the vehicle
        roi_y_start = int(vh * 0.40)
        roi = vehicle_crop[roi_y_start:, :]
        if roi.size == 0:
            roi = vehicle_crop
            roi_y_start = 0

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        sobelx = cv2.Sobel(blur, cv2.CV_8U, 1, 0, ksize=3)
        _, thresh = cv2.threshold(sobelx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_plate_crop = None
        best_bbox = None
        best_score = 0.0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w < 20 or h < 8:
                continue

            aspect_ratio = float(w) / float(h)
            area = w * h

            # Indian standard plate aspect ratio ranges from ~2.2 to 5.5
            if 2.0 <= aspect_ratio <= 5.5 and area > 180:
                plate_y1 = roi_y_start + y
                plate_y2 = plate_y1 + h
                plate_x1 = x
                plate_x2 = x + w

                pad_x = int(w * 0.12)
                pad_y = int(h * 0.20)
                px1 = max(0, plate_x1 - pad_x)
                py1 = max(0, plate_y1 - pad_y)
                px2 = min(vw, plate_x2 + pad_x)
                py2 = min(vh, plate_y2 + pad_y)

                candidate_crop = vehicle_crop[py1:py2, px1:px2]
                if candidate_crop.size > 0:
                    score = min(0.96, 0.75 + (aspect_ratio / 5.5) * 0.2)
                    if score > best_score:
                        best_score = score
                        best_plate_crop = candidate_crop
                        best_bbox = (px1, py1, px2, py2)

        # Fallback heuristic lower-middle crop
        if best_plate_crop is None:
            fh, fw = vehicle_crop.shape[:2]
            px1 = int(fw * 0.20)
            px2 = int(fw * 0.80)
            py1 = int(fh * 0.60)
            py2 = int(fh * 0.95)
            best_plate_crop = vehicle_crop[py1:py2, px1:px2]
            best_bbox = (px1, py1, px2, py2)
            best_score = 0.72

        return best_plate_crop, best_bbox, best_score

    def recognize_text(self, plate_crop: np.ndarray) -> Tuple[str, float]:
        """
        Runs Neural OCR on number plate crop and normalizes according to Indian registration rules.
        """
        if plate_crop is None or plate_crop.size == 0:
            return "", 0.0

        raw_text = ""
        ocr_conf = 0.0

        # Preprocess plate for enhanced OCR character recognition
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        denoised = cv2.bilateralFilter(resized, 9, 75, 75)

        # Try EasyOCR neural reader
        if self.easy_ocr:
            try:
                ocr_res = self.easy_ocr.readtext(plate_crop)
                if not ocr_res:
                    ocr_res = self.easy_ocr.readtext(denoised)
                if ocr_res:
                    texts = [item[1] for item in ocr_res]
                    confs = [float(item[2]) for item in ocr_res]
                    raw_text = "".join(texts)
                    ocr_conf = float(np.mean(confs)) if confs else 0.85
            except Exception as e:
                logger.error(f"EasyOCR inference error: {e}")

        # Normalize and clean the plate text for Indian MoRTH format
        cleaned_plate, normalized_conf = self.normalize_indian_plate(raw_text, ocr_conf)
        return cleaned_plate, normalized_conf



    @classmethod
    def normalize_indian_plate(cls, text: str, initial_conf: float = 0.85) -> Tuple[str, float]:
        """
        Cleans and normalizes Indian vehicle registration format:
        Standard formats:
        - Regular: MH12AB1234, KA01MJ4567, DL3C9999, MH46CT5126
        - Bharat Series: 22BH1234AA
        """
        if not text:
            return "", 0.0

        cleaned = re.sub(r'[^A-Za-z0-9]', '', text).upper()

        # Remove leading "IND" from HSRP plates if present
        if cleaned.startswith("IND") and len(cleaned) > 7:
            cleaned = cleaned[3:]

        # Correct common OCR start character confusion (e.g. HH -> MH, NH -> MH)
        if cleaned.startswith("HH") and len(cleaned) >= 8:
            cleaned = "MH" + cleaned[2:]
        elif cleaned.startswith("HN") and len(cleaned) >= 8:
            cleaned = "MH" + cleaned[2:]

        if len(cleaned) < 6:
            return cleaned, round(initial_conf * 0.7, 2)

        # 1. Check Bharat Series: YY BH #### XX (e.g. 22BH1234AA)
        bharat_match = re.match(r'^([0-9]{2})(BH)([0-9]{4})([A-Z]{1,2})$', cleaned)
        if bharat_match:
            return cleaned, max(0.92, initial_conf)

        # 2. Check Standard State Plate (e.g. MH12AB1234, DL03C9999, MH46CT5126)
        standard_pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'
        if re.match(standard_pattern, cleaned):
            return cleaned, max(0.92, initial_conf)

        # 3. Disambiguate characters based on standard state plate slot expectation
        chars = list(cleaned)
        
        # If first two chars look like letters, treat as standard plate
        if not chars[0].isdigit():
            # Slots 2 and 3 should be digits
            for i in [2, 3]:
                if i < len(chars) and chars[i] in LETTER_TO_DIGIT:
                    chars[i] = LETTER_TO_DIGIT[chars[i]]
            # Last 4 slots should be digits
            for i in range(max(4, len(chars) - 4), len(chars)):
                if chars[i] in LETTER_TO_DIGIT:
                    chars[i] = LETTER_TO_DIGIT[chars[i]]
        
        formatted = "".join(chars)
        if re.match(standard_pattern, formatted):
            confidence = max(0.92, initial_conf)
        elif len(formatted) >= 8:
            confidence = max(0.80, initial_conf)
        else:
            confidence = max(0.65, initial_conf)

        return formatted, round(confidence, 2)




BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_YOLO_PATH = os.path.join(BASE_DIR, "yolo11n.pt")

from .tracking.byte_tracker import BYTETracker

class VehicleIntelligenceEngine:
    """
    High-Performance Unified Vehicle Intelligence Pipeline.
    
    Pipeline:
    CCTV frame
    → Ultralytics YOLO Vehicle Detection + Multi-Object ByteTrack
    → Vehicle ID (persisted across frames)
    → Vehicle Type (car, motorcycle, bus, truck)
    → Vehicle Color Classification (from vehicle body crop)
    → Number Plate Detection (within vehicle crop)
    → Number Plate Crop Preprocessing
    → PaddleOCR Text Recognition & Indian Plate Normalization
    → Combined Structured Metadata Output (bound to same vehicle_id)
    """

    def __init__(self, yolo_model_path: Optional[str] = None):
        self.device = "cuda" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu"
        
        target_path = yolo_model_path if yolo_model_path else DEFAULT_YOLO_PATH
        if not os.path.exists(target_path) and os.path.exists(os.path.join(BASE_DIR, "yolo11n.pt")):
            target_path = os.path.join(BASE_DIR, "yolo11n.pt")

        try:
            self.detector = YOLO(target_path)
            logger.info(f"Vehicle Intelligence YOLO detector loaded from {target_path}")
        except Exception as e:
            logger.error(f"Error loading YOLO vehicle model: {e}")
            self.detector = None

        self.tracker = BYTETracker(track_thresh=0.28, match_thresh=0.75, track_buffer=45)
        self.color_classifier = VehicleColorClassifier()
        self.plate_recognizer = IndianPlateRecognizer()
        
        # Temporal Track Cache: vehicle_id -> {type, color, plate, confidences, last_seen}
        self.track_memory: Dict[str, Dict[str, Any]] = {}
        logger.info("VehicleIntelligenceEngine initialized successfully.")

    def process_frame(
        self, 
        frame: np.ndarray, 
        camera_id: str = "1"
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Processes a CCTV video frame through the vehicle intelligence pipeline.
        
        Returns:
            (List of combined vehicle metadata dictionaries, Annotated frame)
        """
        if frame is None or self.detector is None:
            return [], frame

        annotated_frame = frame.copy()
        current_time_str = datetime.datetime.now().isoformat()
        results_list: List[Dict[str, Any]] = []

        try:
            # 1. Run Ultralytics YOLO Vehicle Detection
            # classes: 2=Car, 3=Motorcycle, 5=Bus, 7=Truck
            yolo_results = self.detector.predict(
                source=frame,
                classes=[2, 3, 5, 7],
                conf=0.28,
                imgsz=416,
                verbose=False
            )

            detections_list = []
            if yolo_results and yolo_results[0].boxes:
                for box in yolo_results[0].boxes:
                    xyxy = box.xyxy[0].tolist()
                    conf = float(box.conf[0].item())
                    cls_id = int(box.cls[0].item())
                    detections_list.append([xyxy[0], xyxy[1], xyxy[2], xyxy[3], conf, cls_id])

            det_array = np.array(detections_list, dtype=np.float32) if detections_list else np.empty((0, 6), dtype=np.float32)

            # 2. Track with BYTETracker for persistent vehicle ID
            active_tracks = self.tracker.update(det_array)
            h, w = frame.shape[:2]

            for track in active_tracks:
                x1, y1, x2, y2 = [int(v) for v in track.tlbr]
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)

                if (x2 - x1) < 15 or (y2 - y1) < 15:
                    continue

                track_id_int = int(track.track_id)
                vehicle_id = f"V{track_id_int}"
                veh_conf = round(float(track.score), 2)
                cls_id = int(track.class_id) if hasattr(track, 'class_id') else 2
                vehicle_type = COCO_VEHICLE_CLASSES.get(cls_id, "car")

                # Crop vehicle image
                vehicle_crop = frame[y1:y2, x1:x2]

                # Scope track memory by camera_id and vehicle_id
                track_key = f"{camera_id}_{vehicle_id}"
                cached = self.track_memory.get(track_key)

                # 2. Vehicle Color Classification (from vehicle body crop)
                if cached and cached.get("vehicle_color") and cached.get("color_conf", 0) > 0.88:
                    vehicle_color = cached["vehicle_color"]
                else:
                    vehicle_color, color_conf = self.color_classifier.classify(vehicle_crop)

                # 3. Indian Number Plate Detection & OCR
                plate_number = ""
                plate_conf = 0.0
                ocr_conf = 0.0

                if cached and cached.get("license_plate") and cached.get("plate_conf", 0) > 0.85:
                    # Reuse established license plate for this vehicle ID
                    plate_number = cached["license_plate"]
                    plate_conf = cached["plate_conf"]
                    ocr_conf = cached["ocr_conf"]
                else:
                    # Run plate detection and OCR
                    plate_detection = self.plate_recognizer.detect_plate_region(vehicle_crop)
                    if plate_detection:
                        plate_crop, plate_box, plate_conf = plate_detection
                        plate_number, ocr_conf = self.plate_recognizer.recognize_text(plate_crop)

                # Update Track Memory
                self.track_memory[track_key] = {
                    "vehicle_id": vehicle_id,
                    "vehicle_type": vehicle_type,
                    "vehicle_color": vehicle_color,
                    "license_plate": plate_number,
                    "vehicle_confidence": veh_conf,
                    "plate_confidence": plate_conf,
                    "ocr_confidence": ocr_conf,

                    "camera_id": str(camera_id),
                    "timestamp": current_time_str,
                    "last_seen": time.time()
                }

                # 4. Final Unified Structured Metadata Output
                vehicle_record: Dict[str, Any] = {
                    "vehicle_id": vehicle_id,
                    "vehicle_type": vehicle_type,
                    "vehicle_color": vehicle_color,
                    "license_plate": plate_number if plate_number else "DETECTION_PENDING",
                    "vehicle_confidence": veh_conf,
                    "plate_confidence": plate_conf,
                    "ocr_confidence": ocr_conf,
                    "camera_id": str(camera_id),
                    "timestamp": current_time_str,
                    "bbox": [x1, y1, x2, y2]
                }
                results_list.append(vehicle_record)

                # 5. Draw Unified Vehicle Bounding Box & HUD Label
                # Border color: High-contrast Electric Amber / Cyan
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (3, 183, 255), 2)

                # Top badge label with unified vehicle attributes
                badge_title = f"{vehicle_id} | {vehicle_type.upper()} ({vehicle_color.capitalize()})"
                badge_plate = f"PLATE: {plate_number if plate_number else 'SCANNING'}"

                (tw, th), _ = cv2.getTextSize(badge_title, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
                (pw, ph), _ = cv2.getTextSize(badge_plate, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
                badge_w = max(tw, pw) + 8
                badge_h = th + ph + 12

                # Badge background
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - badge_h)), (x1 + badge_w, y1), (12, 14, 20), -1)
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - badge_h)), (x1 + badge_w, y1), (3, 183, 255), 1)

                # Text lines
                cv2.putText(annotated_frame, badge_title, (x1 + 4, max(12, y1 - ph - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 242, 254), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, badge_plate, (x1 + 4, max(24, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (245, 223, 192), 1, cv2.LINE_AA)

        except Exception as err:
            logger.error(f"Vehicle Intelligence Pipeline error: {err}")

        # Clean stale tracks from memory older than 30 seconds
        now = time.time()
        stale_ids = [vid for vid, info in self.track_memory.items() if now - info.get("last_seen", 0) > 30.0]
        for vid in stale_ids:
            del self.track_memory[vid]

        return results_list, annotated_frame


# Global singleton instance
_vehicle_engine_instance = None

def get_vehicle_intelligence_engine() -> VehicleIntelligenceEngine:
    global _vehicle_engine_instance
    if _vehicle_engine_instance is None:
        _vehicle_engine_instance = VehicleIntelligenceEngine()
    return _vehicle_engine_instance
