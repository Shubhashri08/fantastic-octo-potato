import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

"""
VIGRAH AI — Model Training & Fine-Tuning Pipeline
Optimized for NVIDIA RTX 2050 (4GB VRAM) & CPU Fallback

Supported Datasets:
1. Violence / Fighting: RWF-2000 / SPHAR / UCF-Crime (Bounding boxes for fighting/altercation)
2. Fire & Smoke: D-Fire / Roboflow Fire Dataset (Bounding boxes for fire/flame)
"""

import os
import argparse
import torch
from ultralytics import YOLO

def train_custom_model(
    data_yaml: str,
    base_model: str = "yolo11n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch_size: int = 8,
    project_name: str = "vigrah_models",
    experiment_name: str = "violence_fire_finetune"
):
    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"=== Starting VIGRAH AI Fine-Tuning on {device} ===")
    print(f"Base Weights: {base_model} | Epochs: {epochs} | Batch Size: {batch_size} (Optimized for 4GB VRAM)")

    # Load base nano model (lightweight 2.6M params)
    model = YOLO(base_model)

    # Train with FP16 half precision to maximize RTX 2050 throughput
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        half=(device == 0),  # Enable FP16 on CUDA
        project=project_name,
        name=experiment_name,
        save=True,
        workers=2,
        optimizer="AdamW",
        lr0=0.001,
        patience=10
    )

    print(f"=== Training Complete! Best weights saved at: {project_name}/{experiment_name}/weights/best.pt ===")
    return results

def export_for_inference(weights_path: str, format_type: str = "onnx"):
    """Exports fine-tuned model to ONNX or TensorRT for ultra-low latency inference."""
    print(f"Exporting {weights_path} to {format_type.upper()} format...")
    model = YOLO(weights_path)
    exported_path = model.export(format=format_type, half=True)
    print(f"Exported model: {exported_path}")
    return exported_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VIGRAH AI Model Fine-Tuning CLI")
    parser.add_argument("--data", type=str, default="data.yaml", help="Path to dataset YAML file")
    parser.add_argument("--base", type=str, default="yolo11n.pt", help="Base model weights")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=8, help="Batch size for 4GB VRAM")
    parser.add_argument("--export", action="store_true", help="Export to ONNX after training")
    args = parser.parse_args()

    if os.path.exists(args.data):
        train_custom_model(data_yaml=args.data, base_model=args.base, epochs=args.epochs, batch_size=args.batch)
        if args.export:
            export_for_inference(f"vigrah_models/violence_fire_finetune/weights/best.pt", format_type="onnx")
    else:
        print(f"Data config '{args.data}' not found. To train, prepare a dataset with images/ and labels/ and point data.yaml to it.")
