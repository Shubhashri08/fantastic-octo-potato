from fastapi import FastAPI, HTTPException

from app.correlate import find_candidates
from app.event_output import get_event_output
from app.mapping import save_mapping
from app.reconstruction import reconstruct_event

app = FastAPI(
    title="VIGRAH Reconstruction API",
    version="1.0.0",
)


@app.post("/events/{event_id}/correlate")
def correlate_event(event_id: str):
    try:
        candidates = find_candidates(event_id)

        saved_count = save_mapping(
            event_id,
            candidates,
        )

        return {
            "event_id": event_id,
            "candidate_count": len(candidates),
            "saved_count": saved_count,
            "candidates": candidates,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.post("/events/{event_id}/reconstruct")
def reconstruct_event_timeline(event_id: str):
    try:
        return reconstruct_event(event_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.get("/events/{event_id}/output")
def read_event_output(event_id: str):
    try:
        return get_event_output(event_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
