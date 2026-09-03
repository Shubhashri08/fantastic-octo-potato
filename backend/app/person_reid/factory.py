import os
import logging
from typing import Optional
from .base import PersonReIDBackend

logger = logging.getLogger("person_reid_factory")

_active_reid_backend: Optional[PersonReIDBackend] = None


def get_person_reid_backend(force_reload: bool = False) -> PersonReIDBackend:
    """
    Singleton factory returning the active Person Re-ID Backend.
    Configured via environment variable: PERSON_REID_MODEL (default: 'transreid').
    """
    global _active_reid_backend

    if _active_reid_backend is not None and not force_reload:
        return _active_reid_backend

    model_type = os.getenv("PERSON_REID_MODEL", "transreid").strip().lower()
    checkpoint_path = os.getenv("PERSON_REID_CHECKPOINT", None)
    device_override = os.getenv("PERSON_REID_DEVICE", None)

    logger.info(f"Initializing Person Re-ID Backend: model='{model_type}', checkpoint='{checkpoint_path}'")

    if model_type == "transreid":
        from .transreid import TransReIDBackend
        try:
            _active_reid_backend = TransReIDBackend(
                checkpoint_path=checkpoint_path,
                device=device_override
            )
        except Exception as e:
            logger.warning(f"TransReIDBackend initialization failed ({e}), falling back to OSNetBackend.")
            from .osnet import OSNetBackend
            _active_reid_backend = OSNetBackend(
                weights_path=checkpoint_path,
                device=device_override
            )
    elif model_type == "osnet":
        from .osnet import OSNetBackend
        _active_reid_backend = OSNetBackend(
            weights_path=checkpoint_path,
            device=device_override
        )
    else:
        raise ValueError(
            f"Unsupported PERSON_REID_MODEL '{model_type}'. Supported backends: 'transreid', 'osnet'."
        )

    return _active_reid_backend
