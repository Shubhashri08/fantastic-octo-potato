from pathlib import Path

from sqlalchemy import text

from app.config import CORRELATION_WINDOWS
from app.db import SessionLocal

SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "find_candidates.sql"


def load_candidate_query() -> str:
    return SQL_FILE.read_text(encoding="utf-8")


def find_candidates(event_id: str):
    db = SessionLocal()

    try:
        event = db.execute(
            text(
                """
                SELECT event_type
                FROM public.events
                WHERE event_id = :event_id
                """
            ),
            {"event_id": event_id},
        ).fetchone()

        if event is None:
            raise ValueError(f"Event not found: {event_id}")

        event_type = event[0]

        config = CORRELATION_WINDOWS.get(
            event_type,
            CORRELATION_WINDOWS["DEFAULT"],
        )

        query = text(load_candidate_query())

        result = db.execute(
            query,
            {
                "event_id": event_id,
                "time_window_minutes": config["time_minutes"],
                "radius_meters": config["radius_meters"],
            },
        )

        return [dict(row._mapping) for row in result]

    finally:
        db.close()
