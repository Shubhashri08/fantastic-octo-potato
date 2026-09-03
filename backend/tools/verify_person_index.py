"""
Verification Command for VIGRAH AI Person Re-ID Index.
Usage: python -m backend.tools.verify_person_index
"""

import os
import json
import logging
import numpy as np
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, IS_POSTGRES
from backend.app.models import VideoEvidence, PersonVideoTrack, PersonVideoSighting
from backend.app.person_reid.factory import get_person_reid_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_person_index")


def verify_index() -> bool:
    print("=" * 80)
    print("  VIGRAH AI — PERSON RE-ID INDEX VERIFICATION REPORT")
    print("=" * 80)

    reid_backend = get_person_reid_backend()
    expected_dim = reid_backend.embedding_dim
    model_name = reid_backend.model_name
    device = reid_backend.device

    print(f"\n[1] Active Re-ID Backend: {model_name}")
    print(f"    - Target Embedding Dimension: {expected_dim}-D")
    print(f"    - Inference Device: {device}")
    print(f"    - Database Backend: {'PostgreSQL + pgvector' if IS_POSTGRES else 'SQLite (NumPy Cosine Engine)'}")

    db: Session = SessionLocal()
    all_passed = True
    try:
        videos = db.query(VideoEvidence).all()
        tracks = db.query(PersonVideoTrack).all()
        sightings = db.query(PersonVideoSighting).all()

        print(f"\n[2] Index Summary Statistics:")
        print(f"    - Total Registered Video Sources: {len(videos)}")
        print(f"    - Total Indexed Person Tracks:    {len(tracks)}")
        print(f"    - Total Indexed Person Sightings: {len(sightings)}")

        if not videos:
            print("    ⚠️  Warning: No video evidence sources found in database.")
            all_passed = False

        if not tracks:
            print("    ⚠️  Warning: No person tracks found in database.")
            all_passed = False

        print("\n[3] Video Evidence Verification:")
        for v in videos:
            exists = os.path.exists(v.file_path)
            print(f"    • [{v.source_id}] {v.source_name} (Camera: {v.camera_id}): Status={v.status}, Tracks={v.track_count}, FileExists={exists}")
            if not exists:
                print(f"      ❌ File missing on disk: {v.file_path}")
                all_passed = False

        print("\n[4] Track & Embedding Integrity Verification:")
        dim_mismatches = 0
        non_normalized = 0
        missing_crops = 0

        for trk in tracks:
            if not trk.average_embedding:
                print(f"    ❌ Track {trk.track_id} has no average_embedding stored!")
                all_passed = False
                continue

            try:
                emb = np.array(json.loads(trk.average_embedding), dtype=np.float32)
            except Exception as e:
                print(f"    ❌ Track {trk.track_id} failed to parse JSON embedding: {e}")
                all_passed = False
                continue

            if emb.shape[0] != expected_dim:
                dim_mismatches += 1
                all_passed = False

            norm = np.linalg.norm(emb)
            if abs(norm - 1.0) > 1e-3 and norm > 1e-6:
                non_normalized += 1
                all_passed = False

        print(f"    - Dimension Check ({expected_dim}-D): {'✓ All Match' if dim_mismatches == 0 else f'❌ {dim_mismatches} Mismatches'}")
        print(f"    - L2 Normalization (||v|| = 1.0):   {'✓ All Normalized' if non_normalized == 0 else f'❌ {non_normalized} Unnormalized'}")

        print("\n[5] Sighting Evidence Crop Verification:")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for s in sightings[:30]:  # Sample first 30 sightings
            rel_path = s.crop_path.lstrip("/")
            disk_path = os.path.join(base_dir, rel_path)
            if not os.path.exists(disk_path):
                # Also check direct evidence directory
                alt_path = os.path.join(base_dir, "evidence", "persons", s.source_id, s.track_id, os.path.basename(s.crop_path))
                if not os.path.exists(alt_path):
                    missing_crops += 1

        print(f"    - Evidence Crop Inspection: {'✓ All verified on disk' if missing_crops == 0 else f'⚠️ {missing_crops} sampled crops missing'}")

    finally:
        db.close()

    print("\n" + "=" * 80)
    print(f"  VERIFICATION STATUS: {'PASSED (READY FOR INVESTIGATION)' if all_passed else 'ATTENTION REQUIRED'}")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    import sys
    success = verify_index()
    sys.exit(0 if success else 1)
