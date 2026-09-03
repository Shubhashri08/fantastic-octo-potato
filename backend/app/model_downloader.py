import os
import logging
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model_downloader")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)

def load_models():
    """Loads fine-tuned ONNX/PyTorch model weights for real-time violence and fire detection."""
    models = {}
    
    # Priority 1: Fine-tuned ONNX Model (best.onnx)
    custom_onnx = os.path.join(WEIGHTS_DIR, "best.onnx")
    root_onnx = os.path.join(os.path.dirname(BASE_DIR), "best.onnx")
    custom_pt = os.path.join(WEIGHTS_DIR, "best.pt")

    if os.path.exists(custom_onnx):
        try:
            models["base"] = YOLO(custom_onnx, task="detect")
            logger.info(f"Loaded Fine-Tuned Custom ONNX Model: {custom_onnx} (Classes: {models['base'].names})")
            return models
        except Exception as e:
            logger.warning(f"Error loading {custom_onnx}: {e}")

    if os.path.exists(root_onnx):
        try:
            models["base"] = YOLO(root_onnx, task="detect")
            logger.info(f"Loaded Fine-Tuned Custom ONNX Model from Root: {root_onnx}")
            return models
        except Exception as e:
            logger.warning(f"Error loading {root_onnx}: {e}")

    if os.path.exists(custom_pt):
        try:
            models["base"] = YOLO(custom_pt)
            logger.info(f"Loaded Fine-Tuned PyTorch Model: {custom_pt}")
            return models
        except Exception as e:
            logger.warning(f"Error loading {custom_pt}: {e}")

    # Fallback to YOLO11 Nano Base
    base_target = os.path.join(WEIGHTS_DIR, "yolo11n.pt")
    if os.path.exists(base_target):
        models["base"] = YOLO(base_target)
    else:
        models["base"] = YOLO("yolo11n.pt")
    logger.info("Loaded Default YOLO11n Base Model.")

    return models
