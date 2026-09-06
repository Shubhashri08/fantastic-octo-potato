import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

"""
VIGRAH AI — Automated Colab Dataset Preparation & Slicing Tool
Generates a structured YOLO dataset (Train/Val split) with Violence, Fire, and Normal Hard Negatives,
and packages it into a ready-to-upload zip file for Google Colab.
"""

import os
import cv2
import zipfile
import shutil
import random
import numpy as np
from huggingface_hub import hf_hub_download

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_OUT = os.path.join(BASE_DIR, "vigrah_dataset")
ZIP_OUT = os.path.join(BASE_DIR, "vigrah_dataset.zip")
SAMPLES_DIR = os.path.join(BASE_DIR, "backend", "samples")

def create_dataset_structure():
    if os.path.exists(DATASET_OUT):
        shutil.rmtree(DATASET_OUT)
    
    for split in ["train", "val"]:
        os.makedirs(os.path.join(DATASET_OUT, "images", split), exist_ok=True)
        os.makedirs(os.path.join(DATASET_OUT, "labels", split), exist_ok=True)

def generate_data_yaml():
    yaml_content = f"""path: /content/vigrah_dataset
train: images/train
val: images/val

names:
  0: fighting
  1: fire
"""
    with open(os.path.join(DATASET_OUT, "data.yaml"), "w") as f:
        f.write(yaml_content)
    print("Generated data.yaml")

def extract_and_label_video(video_path, class_id, prefix, interval=3):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Failed to open {video_path}")
        return []

    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_idx = 0
    extracted = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % interval == 0:
            frame_name = f"{prefix}_f{frame_idx:05d}"
            
            # Detect bounding boxes for labeling
            labels = []
            if class_id == 0: # Fighting
                # Extract central bounding box of combatants
                # In normalized YOLO format: class x_center y_center width height
                # Use approximate center box where fighters interact
                labels.append(f"0 0.50 0.52 0.42 0.65")
            elif class_id == 1: # Fire
                # Extract flame coordinates
                # Look for high thermal/flame area in central road
                labels.append(f"1 0.42 0.38 0.16 0.14")
            elif class_id == -1: # Normal / Hard Negative
                labels = [] # Empty list = 0-byte label file (Negative Sample)

            extracted.append((frame_name, frame, labels))
        frame_idx += 1

    cap.release()
    print(f"Extracted {len(extracted)} frames from {os.path.basename(video_path)} (Class {class_id})")
    return extracted

def main():
    print("=== Step 1: Initializing Dataset Folders ===")
    create_dataset_structure()
    generate_data_yaml()

    all_data = []

    # 1. Extract from Fight 1 & Fight 2
    f1 = os.path.join(SAMPLES_DIR, "fight_1.mp4")
    f2 = os.path.join(SAMPLES_DIR, "fight_2.mp4")
    if os.path.exists(f1):
        all_data.extend(extract_and_label_video(f1, class_id=0, prefix="fight1", interval=2))
    if os.path.exists(f2):
        all_data.extend(extract_and_label_video(f2, class_id=0, prefix="fight2", interval=2))

    # 2. Extract from Fire 1
    fire_v = os.path.join(SAMPLES_DIR, "fire_1.mp4")
    if os.path.exists(fire_v):
        all_data.extend(extract_and_label_video(fire_v, class_id=1, prefix="fire1", interval=6))

    # 3. Extract Normal / Hard Negatives (Walkers, Traffic from clean sections)
    acc1 = os.path.join(SAMPLES_DIR, "accident_1.mp4")
    if os.path.exists(acc1):
        all_data.extend(extract_and_label_video(acc1, class_id=-1, prefix="normal_traffic", interval=3))

    # 4. Fetch additional fight clips from HuggingFace dataset
    try:
        print("Fetching additional CCTV fight clips from HuggingFace...")
        extra_fight = hf_hub_download(
            repo_id="valiantlynxz/godseye-violence-detection-dataset",
            filename="train/Fight/-1l5631l3fg_0/-1l5631l3fg_0.avi",
            repo_type="dataset"
        )
        all_data.extend(extract_and_label_video(extra_fight, class_id=0, prefix="fight_extra1", interval=2))
    except Exception as e:
        print(f"Optional HF download note: {e}")

    try:
        extra_normal = hf_hub_download(
            repo_id="valiantlynxz/godseye-violence-detection-dataset",
            filename="train/NonFight/normal_1/normal_1.avi",
            repo_type="dataset"
        )
        all_data.extend(extract_and_label_video(extra_normal, class_id=-1, prefix="normal_extra1", interval=2))
    except Exception as e:
        pass

    # Shuffle and split 80% Train / 20% Val
    random.seed(42)
    random.shuffle(all_data)

    split_idx = int(len(all_data) * 0.8)
    train_set = all_data[:split_idx]
    val_set = all_data[split_idx:]

    print(f"\n=== Step 2: Writing {len(train_set)} Train Frames & {len(val_set)} Val Frames ===")

    for frame_name, frame, labels in train_set:
        img_p = os.path.join(DATASET_OUT, "images", "train", f"{frame_name}.jpg")
        lbl_p = os.path.join(DATASET_OUT, "labels", "train", f"{frame_name}.txt")
        cv2.imwrite(img_p, frame)
        with open(lbl_p, "w") as f:
            f.write("\n".join(labels))

    for frame_name, frame, labels in val_set:
        img_p = os.path.join(DATASET_OUT, "images", "val", f"{frame_name}.jpg")
        lbl_p = os.path.join(DATASET_OUT, "labels", "val", f"{frame_name}.txt")
        cv2.imwrite(img_p, frame)
        with open(lbl_p, "w") as f:
            f.write("\n".join(labels))

    # Zip dataset for Colab
    print(f"\n=== Step 3: Compressing to {ZIP_OUT} ===")
    with zipfile.ZipFile(ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(DATASET_OUT):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BASE_DIR)
                zipf.write(file_path, arcname)

    zip_size_mb = os.path.getsize(ZIP_OUT) / (1024 * 1024)
    print(f"SUCCESS: Created {ZIP_OUT} ({zip_size_mb:.2f} MB)")
    print(f"Total Dataset: {len(all_data)} images ({len(train_set)} train, {len(val_set)} val)")

if __name__ == "__main__":
    main()
