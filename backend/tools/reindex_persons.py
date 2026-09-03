"""
CLI Re-indexing Tool for VIGRAH AI Person Re-ID.
Re-indexes all existing video footage using the active Re-ID model backend.
Usage: python -m backend.tools.reindex_persons
"""

import sys
import logging
from backend.app.video_person_engine import video_person_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reindex_persons")


def main():
    print("=" * 80)
    print("  VIGRAH AI — RE-INDEX ALL VIDEO EVIDENCE FOOTAGE")
    print("=" * 80)
    print(f"Active Model: {video_person_engine.reid_backend.model_name}")
    print(f"Dimension:    {video_person_engine.reid_backend.embedding_dim}-D")
    print(f"Device:       {video_person_engine.reid_backend.device}")
    print("=" * 80)

    try:
        video_person_engine.reindex_all_video_evidence()
        print("\n✓ Re-indexing completed successfully.")
    except Exception as e:
        print(f"\n❌ Re-indexing encountered an error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
