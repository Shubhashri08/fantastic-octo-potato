import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

#!/usr/bin/env python3
"""
VIGRAH AI - Backend Video Storage & Abnormality / Violence Inspector
Classifies videos as Violent (Fighting / Altercation / Threat) vs Non-Violent (Normal People Walking),
checks for behavioral abnormalities, and stores videos into backend/video_storage/(violent / non_violent).

Usage:
  python store_and_check_videos.py --path sample_media/whatsapp_test_video.mp4
  python store_and_check_videos.py --all-samples
  python store_and_check_videos.py --list
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure backend package import
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ["YOLO_CONFIG_DIR"] = os.path.join(BASE_DIR, "Ultralytics")

from app.video_storage_manager import backend_video_storage, VIOLENT_DIR, NON_VIOLENT_DIR, STORAGE_DIR


def print_header():
    print("=" * 78)
    print(" VIGRAH AI | Backend Video Storage & Abnormality Inspector")
    print(" Violent vs Non-Violent Video Classification & Storage Engine")
    print("=" * 78)


def process_single_video(video_path: str, custom_name: str = None):
    print(f"\n[*] Inspecting & Storing Video: {video_path}")
    if not os.path.exists(video_path):
        print(f"[!] Error: File does not exist: {video_path}")
        return None

    try:
        report = backend_video_storage.inspect_and_store_video(video_path, custom_name=custom_name)
    except Exception as e:
        print(f"[!] Inspection failed: {e}")
        return None

    category = report["category"].upper()
    is_violent = report["is_violent"]
    metrics = report["metrics"]

    print("\n" + "-" * 78)
    if is_violent:
        print(f"🚨 CLASSIFICATION VERDICT: [{category}] (VIOLENT ALTERCATION DETECTED)")
    else:
        print(f"✅ CLASSIFICATION VERDICT: [{category}] (NORMAL PEOPLE WALKING)")
    print("-" * 78)
    print(f"  • Video File:         {report['filename']}")
    print(f"  • Duration / Frames:  {metrics['duration_sec']}s ({metrics['total_frames']} total frames, {metrics['inspected_frames']} sampled)")
    print(f"  • Resolution / FPS:   {metrics['resolution']} @ {metrics['fps']} FPS")
    print(f"  • Violence Score:     {metrics['violence_score'] * 100:.1f}%")
    print(f"  • Max Threat Conf:    {metrics['max_threat_confidence'] * 100:.1f}%")
    print(f"  • Avg People / Frame: {metrics['avg_pedestrians']}")
    print(f"  • Fighting Frames:    {metrics['fighting_frames']}")
    print(f"  • Walking Frames:     {metrics['walking_frames']}")
    print(f"  • Behavioral Status:  {report['abnormality_summary']}")
    print(f"  • Stored Location:    {report['stored_location']}")
    print(f"  • Evidence Snapshots: {len(report['evidence_snapshots'])} saved in backend/video_storage/reports/snapshots/")
    print("-" * 78)
    return report


def list_storage_catalog():
    index = backend_video_storage.get_index()
    print("\n" + "=" * 78)
    print(f" BACKEND VIDEO STORAGE CATALOG (Total: {index.get('total_videos', 0)})")
    print(f" • Violent Altercations:     {index.get('violent_count', 0)} files in {VIOLENT_DIR}")
    print(f" • Non-Violent Walkers:      {index.get('non_violent_count', 0)} files in {NON_VIOLENT_DIR}")
    print("=" * 78)

    videos = index.get("videos", [])
    if not videos:
        print("  (Storage is currently empty. Run with --path or --all-samples to ingest videos)")
        return

    print(f"{'CATEGORY':<14} | {'FILENAME':<35} | {'DURATION':<8} | {'VERDICT'}")
    print("-" * 78)
    for v in videos:
        cat = v.get("category", "").upper()
        fn = v.get("filename", "")[:34]
        dur = f"{v.get('duration_sec', 0)}s"
        verdict = v.get("verdict", "")
        print(f"{cat:<14} | {fn:<35} | {dur:<8} | {verdict}")
    print("-" * 78)


def main():
    print_header()
    parser = argparse.ArgumentParser(description="VIGRAH AI Backend Video Storage & Classifier")
    parser.add_argument("--path", type=str, help="Path to video file to inspect and store")
    parser.add_argument("--name", type=str, help="Optional custom name for stored video")
    parser.add_argument("--all-samples", action="store_true", help="Process all baseline sample videos and WhatsApp video")
    parser.add_argument("--list", action="store_true", help="List all videos in backend storage")

    args = parser.parse_args()

    if args.list:
        list_storage_catalog()
        return

    if args.all_samples:
        test_videos = [
            os.path.join(BASE_DIR, "sample_media", "whatsapp_test_video.mp4"),
            os.path.join(BASE_DIR, "samples", "fight_1.mp4"),
            os.path.join(BASE_DIR, "samples", "fight_2.mp4"),
            os.path.join(BASE_DIR, "samples", "mumbai_csmt_station.mp4"),
            os.path.join(BASE_DIR, "samples", "blr_mg_road_metro.mp4")
        ]
        for vid in test_videos:
            if os.path.exists(vid):
                process_single_video(vid)
        list_storage_catalog()
        return

    if args.path:
        process_single_video(args.path, custom_name=args.name)
        list_storage_catalog()
        return

    # Default if no arguments: process the WhatsApp video directly!
    default_whatsapp = os.path.join(BASE_DIR, "sample_media", "whatsapp_test_video.mp4")
    if os.path.exists(default_whatsapp):
        print("\n[*] No arguments provided. Processing default WhatsApp test video...")
        process_single_video(default_whatsapp)
        list_storage_catalog()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
