"""
Non-destructive Migration and Schema Verification Tool for VIGRAH AI Person Re-ID.
Ensures all required columns, vector tables, and indexes exist without dropping existing tables.
"""

import sys
import logging
from sqlalchemy import text
from backend.app.database import engine, Base, IS_POSTGRES, SessionLocal
from backend.app.models import VideoEvidence, PersonVideoTrack, PersonVideoSighting

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_person_schema")


def migrate_schema():
    logger.info(f"Starting non-destructive schema migration. Target DB dialect: {'PostgreSQL' if IS_POSTGRES else 'SQLite'}")
    
    # 1. Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Base schema tables created / verified.")

    # 2. Check and add new columns non-destructively
    db = SessionLocal()
    try:
        if IS_POSTGRES:
            try:
                db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                db.commit()
                logger.info("✓ pgvector extension initialized.")
            except Exception as e:
                logger.warning(f"pgvector extension note: {e}")
                db.rollback()

        # Add columns to video_evidence
        video_cols = [
            ("source_hash", "VARCHAR(64)"),
            ("camera_id", "VARCHAR(50) DEFAULT 'CAM-01'"),
            ("status", "VARCHAR(20) DEFAULT 'ready'"),
            ("error_message", "TEXT")
        ]
        for col_name, col_type in video_cols:
            try:
                db.execute(text(f"ALTER TABLE video_evidence ADD COLUMN {col_name} {col_type};"))
                db.commit()
                logger.info(f"✓ Added column {col_name} to video_evidence.")
            except Exception:
                db.rollback()

        # Add columns to person_video_tracks
        track_cols = [
            ("camera_id", "VARCHAR(50) DEFAULT 'CAM-01'"),
            ("camera_name", "VARCHAR(255)"),
            ("location", "VARCHAR(255)"),
            ("first_seen_formatted", "VARCHAR(50)"),
            ("last_seen_formatted", "VARCHAR(50)"),
            ("quality_score", "FLOAT DEFAULT 1.0"),
            ("reid_model", "VARCHAR(50) DEFAULT 'transreid'"),
            ("reid_model_version", "VARCHAR(100) DEFAULT 'transreid-damo-market1501-v1'"),
            ("embedding_dim", "INTEGER DEFAULT 768"),
            ("index_version", "VARCHAR(20) DEFAULT 'v1.0'"),
            ("embedding_created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("appearance_cluster_id", "VARCHAR(100)"),
            ("cluster_confidence", "FLOAT"),
            ("linked_track_ids", "JSON")
        ]
        for col_name, col_type in track_cols:
            try:
                db.execute(text(f"ALTER TABLE person_video_tracks ADD COLUMN {col_name} {col_type};"))
                db.commit()
                logger.info(f"✓ Added column {col_name} to person_video_tracks.")
            except Exception:
                db.rollback()

        # Add columns to person_video_sightings
        sighting_cols = [
            ("camera_id", "VARCHAR(50) DEFAULT 'CAM-01'"),
            ("frame_number", "INTEGER DEFAULT 0"),
            ("quality_score", "FLOAT DEFAULT 1.0"),
            ("detection_confidence", "FLOAT DEFAULT 0.90"),
            ("reid_model", "VARCHAR(50) DEFAULT 'transreid'"),
            ("reid_model_version", "VARCHAR(100) DEFAULT 'transreid-damo-market1501-v1'"),
            ("embedding_dim", "INTEGER DEFAULT 768"),
            ("index_version", "VARCHAR(20) DEFAULT 'v1.0'"),
            ("embedding_created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        for col_name, col_type in sighting_cols:
            try:
                db.execute(text(f"ALTER TABLE person_video_sightings ADD COLUMN {col_name} {col_type};"))
                db.commit()
                logger.info(f"✓ Added column {col_name} to person_video_sightings.")
            except Exception:
                db.rollback()

        logger.info("✓ Non-destructive migration complete.")
    finally:
        db.close()


if __name__ == "__main__":
    migrate_schema()
