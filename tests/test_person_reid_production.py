import os
import cv2
import json
import pytest
import numpy as np
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, Base, engine, IS_POSTGRES
from backend.app.models import VideoEvidence, PersonVideoTrack, PersonVideoSighting
from backend.app.person_reid.base import PersonReIDBackend
from backend.app.person_reid.transreid import TransReIDBackend, TransReIDNet
from backend.app.person_reid.factory import get_person_reid_backend
from backend.app.tracking.byte_tracker import BYTETracker, STrack
from backend.app.tracking.quality_filter import compute_person_crop_quality, QualityFilterConfig
from backend.app.video_person_engine import VideoPersonEngine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "backend", "samples")


@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown / cleanup


class TestTransReIDModel:
    def test_model_initialization_and_dimension(self):
        backend = get_person_reid_backend()
        assert backend is not None
        assert backend.embedding_dim == 768
        assert backend.model_name == "TransReID-ViT-Base"
        assert backend.device in ("cuda", "mps", "cpu")

    def test_embedding_finite_and_normalized(self):
        backend = get_person_reid_backend()
        dummy_crop = np.random.randint(50, 200, (256, 128, 3), dtype=np.uint8)
        emb = backend.extract_embedding(dummy_crop)
        
        assert emb is not None
        assert emb.shape == (768,)
        assert emb.dtype == np.float32
        assert np.all(np.isfinite(emb))
        
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 1e-4

    def test_batch_extraction(self):
        backend = get_person_reid_backend()
        crops = [
            np.random.randint(40, 220, (256, 128, 3), dtype=np.uint8)
            for _ in range(4)
        ]
        embs = backend.batch_extract_embeddings(crops, batch_size=2)
        assert len(embs) == 4
        for e in embs:
            assert e.shape == (768,)
            assert abs(np.linalg.norm(e) - 1.0) < 1e-4

    def test_cosine_similarity_computation(self):
        v1 = np.random.randn(768).astype(np.float32)
        v1 /= np.linalg.norm(v1)
        
        # Self-similarity must be exactly 1.0
        sim_self = PersonReIDBackend.compare(v1, v1)
        assert abs(sim_self - 1.0) < 1e-5
        
        # Opposite vector similarity must be -1.0
        sim_opp = PersonReIDBackend.compare(v1, -v1)
        assert abs(sim_opp - (-1.0)) < 1e-5


class TestByteTracker:
    def test_track_creation_and_continuation(self):
        tracker = BYTETracker(track_thresh=0.5, match_thresh=0.7, track_buffer=30)
        
        # Frame 1: Single detection [x1, y1, x2, y2, score, class_id]
        det_f1 = np.array([[100, 100, 200, 300, 0.90, 0]], dtype=np.float32)
        tracks_f1 = tracker.update(det_f1)
        assert len(tracks_f1) == 1
        t_id = tracks_f1[0].track_id
        
        # Frame 2: Same person moved slightly
        det_f2 = np.array([[105, 102, 205, 302, 0.88, 0]], dtype=np.float32)
        tracks_f2 = tracker.update(det_f2)
        assert len(tracks_f2) == 1
        assert tracks_f2[0].track_id == t_id  # Track ID must persist


class TestQualityFilter:
    def test_high_quality_crop(self):
        crop = np.random.randint(60, 200, (200, 100, 3), dtype=np.uint8)
        # Add high-contrast gradient pattern to simulate sharp features
        crop[::10, :] = 255
        score, is_ok, reason = compute_person_crop_quality(crop)
        assert score >= 0.25
        assert is_ok is True

    def test_tiny_crop_rejection(self):
        tiny_crop = np.zeros((15, 15, 3), dtype=np.uint8)
        score, is_ok, reason = compute_person_crop_quality(tiny_crop)
        assert is_ok is False
        assert "RESOLUTION_TOO_LOW" in reason


class TestVideoIndexingAndSearch:
    def test_real_video_indexing(self, setup_database):
        engine = VideoPersonEngine()
        sample_video = os.path.join(SAMPLES_DIR, "fight_1.mp4")
        if not os.path.exists(sample_video):
            pytest.skip(f"Sample video not found at {sample_video}")

        result = engine.process_video_evidence(
            video_path=sample_video,
            source_id="TEST-VID-01",
            source_name="CAM-01: Mumbai CSMT Concourse",
            camera_id="CAM-01",
            location="Mumbai CSMT Terminal",
            target_fps=3.0
        )

        assert result["status"] == "ready"
        assert result["track_count"] >= 1
        assert result["sighting_count"] >= 1

        db: Session = SessionLocal()
        try:
            ve = db.query(VideoEvidence).filter(VideoEvidence.source_id == "TEST-VID-01").first()
            assert ve is not None
            assert ve.status == "ready"

            tracks = db.query(PersonVideoTrack).filter(PersonVideoTrack.source_id == "TEST-VID-01").all()
            assert len(tracks) >= 1
            for trk in tracks:
                assert trk.embedding_dim == 768
                assert trk.reid_model == "TransReID-ViT-Base"
                emb = np.array(json.loads(trk.average_embedding), dtype=np.float32)
                assert emb.shape == (768,)
                assert abs(np.linalg.norm(emb) - 1.0) < 1e-3
        finally:
            db.close()

    def test_query_validation_error_codes(self):
        engine = VideoPersonEngine()
        
        # 1. Blank image -> NO_PERSON_DETECTED
        blank_img = np.zeros((400, 400, 3), dtype=np.uint8)
        res = engine.search_person_gallery(blank_img)
        assert res["status"] == "error"
        assert res["error_code"] == "NO_PERSON_DETECTED"

    def test_end_to_end_search_match(self, setup_database):
        engine = VideoPersonEngine()
        db: Session = SessionLocal()
        try:
            sighting = db.query(PersonVideoSighting).filter(PersonVideoSighting.source_id == "TEST-VID-01").first()
            if not sighting:
                pytest.skip("No indexed sighting available for search test.")

            crop_file = engine.get_evidence_crop_file_path("TEST-VID-01", sighting.track_id)
            assert crop_file is not None
            assert os.path.exists(crop_file)

            query_img = cv2.imread(crop_file)
            search_res = engine.search_person_gallery(
                query_img=query_img,
                min_similarity=0.40,
                limit=5
            )

            assert search_res["status"] == "success"
            assert search_res["returned_candidates"] >= 1
            top_match = search_res["matches"][0]
            assert top_match["similarity"] >= 0.40
            assert top_match["camera_id"] == "CAM-01"
            assert "sightings" in top_match
        finally:
            db.close()
