import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

"""
VIGRAH AI — CCTV Video Downloader & Frame Slicing Tool
Uses yt-dlp to download footage and OpenCV to extract training frames.
"""

import os
import cv2
import yt_dlp
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

def download_cctv_video(url: str, output_filename: str):
    """Downloads a video clip using yt-dlp in 720p MP4 format."""
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    out_path = os.path.join(SAMPLES_DIR, output_filename)
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': out_path,
        'quiet': False,
        'overwrites': True
    }
    
    print(f"Downloading video from {url} -> {out_path}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"Downloaded successfully: {out_path}")
    return out_path

def extract_frames_for_dataset(video_path: str, output_dir: str, class_label: str, sample_interval: int = 15):
    """
    Slices a video into training frames and creates placeholder YOLO label files.
    sample_interval=15 extracts ~2 frames per second from a 30fps clip.
    """
    images_dir = os.path.join(output_dir, "images", "train")
    labels_dir = os.path.join(output_dir, "labels", "train")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    frame_count = 0
    saved_count = 0

    print(f"Extracting frames from {video_path} into {images_dir}...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % sample_interval == 0:
            img_name = f"{base_name}_frame{frame_count:05d}.jpg"
            img_path = os.path.join(images_dir, img_name)
            cv2.imwrite(img_path, frame)

            # If class_label is 'normal', create empty label file (Hard Negative Sample)
            lbl_name = f"{base_name}_frame{frame_count:05d}.txt"
            lbl_path = os.path.join(labels_dir, lbl_name)
            with open(lbl_path, "w") as f:
                if class_label == "normal":
                    pass  # Empty file = background negative
                else:
                    # Placeholder annotation prompt
                    pass

            saved_count += 1
        frame_count += 1

    cap.release()
    print(f"Extracted {saved_count} frames from {video_path}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download CCTV Video & Slice to Training Frames")
    parser.add_argument("--url", type=str, help="Video URL (YouTube/Direct link)")
    parser.add_argument("--name", type=str, default="cctv_sample.mp4", help="Output filename")
    parser.add_argument("--slice", action="store_true", help="Extract frames to dataset/")
    parser.add_argument("--label", type=str, default="fighting", choices=["fighting", "fire", "normal"], help="Class label")
    args = parser.parse_args()

    if args.url:
        video_file = download_cctv_video(args.url, args.name)
        if args.slice:
            extract_frames_for_dataset(video_file, DATASET_DIR, args.label)
    else:
        print("Usage: python dataset_downloader.py --url <URL> --name sample.mp4 --slice --label fighting")
