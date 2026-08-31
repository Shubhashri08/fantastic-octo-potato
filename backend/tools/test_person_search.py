"""
CLI Real Query Search Verification Tool for VIGRAH AI Person Re-ID.
Usage: python -m backend.tools.test_person_search --query path/to/image.jpg [--similarity 0.50] [--limit 10]
"""

import os
import sys
import cv2
import argparse
import logging
from backend.app.video_person_engine import video_person_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_person_search")


def main():
    parser = argparse.ArgumentParser(description="Test CCTV Person Search with real query image.")
    parser.add_argument("--query", "-q", type=str, required=True, help="Path to missing person query image file")
    parser.add_argument("--similarity", "-s", type=float, default=0.50, help="Minimum similarity threshold (0.0 - 1.0)")
    parser.add_argument("--camera", "-c", type=str, default=None, help="Optional camera ID / source ID filter")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Top-K candidates limit")

    args = parser.parse_args()

    if not os.path.exists(args.query):
        print(f"Error: Query image not found at '{args.query}'")
        sys.exit(1)

    query_img = cv2.imread(args.query)
    if query_img is None:
        print(f"Error: Could not read image at '{args.query}'")
        sys.exit(1)

    print("=" * 80)
    print("  VIGRAH AI — CCTV PERSON SEARCH QUERY EXECUTION")
    print("=" * 80)
    print(f"Query Image:       {args.query} ({query_img.shape[1]}x{query_img.shape[0]}px)")
    print(f"Min Similarity:    {args.similarity:.2f}")
    print(f"Camera Filter:     {args.camera or 'All Cameras'}")
    print(f"Limit (Top-K):     {args.limit}")

    result = video_person_engine.search_person_gallery(
        query_img=query_img,
        min_similarity=args.similarity,
        camera_id=args.camera,
        limit=args.limit
    )

    if result.get("status") == "error":
        print(f"\n❌ Query Validation Failed: [{result.get('error_code')}]")
        print(f"   Message: {result.get('message')}")
        sys.exit(1)

    matches = result.get("matches", [])
    total = result.get("total_candidates", 0)
    query_info = result.get("query", {})

    print(f"\nModel:             {query_info.get('model')} ({query_info.get('embedding_dimension')}-D)")
    print(f"Query Quality:     {query_info.get('quality', 1.0):.2f}")
    print(f"Total Candidates:  {total} matching threshold")
    print(f"Returned Matches:  {len(matches)}")
    print("-" * 80)

    if not matches:
        print("No candidate person tracks matched the similarity criteria in indexed video footage.")
    else:
        for idx, m in enumerate(matches):
            best_mark = " ★ BEST MATCH" if m.get("is_best_match") else ""
            print(f"\n[RANK #{m['rank']}{best_mark}] Track ID: {m['track_id']} (Source: {m['source_id']})")
            print(f"  • Visual Similarity:    {m['similarity']:.4f} ({m['similarity_percent']}%)")
            print(f"  • Camera / Sensor:      {m['camera_id']} ({m['camera_name']})")
            print(f"  • Location:             {m['location']}")
            print(f"  • Time Window:          {m['first_seen']} -> {m['last_seen']}")
            print(f"  • Sighting Count:       {m['sighting_count']} confirmed observations")
            print(f"  • Representative Crop:  {m['representative_crop_url']}")
            if m.get("sightings"):
                s_times = [s["formatted_time"] for s in m["sightings"]]
                print(f"  • Sighting Timeline:    {', '.join(s_times[:6])}{'...' if len(s_times) > 6 else ''}")

    print("=" * 80)


if __name__ == "__main__":
    main()
