"""
Deterministic Person Crop Quality Assessment Filter.
Evaluates resolution, aspect ratio, Laplacian blur variance, contrast, and frame clipping.
Produces a deterministic quality score in [0.0, 1.0].
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class QualityFilterConfig:
    min_width: int = 24
    min_height: int = 48
    min_area: int = 1500
    ideal_aspect_ratio: float = 0.5  # width / height ~ 1:2
    min_laplacian_var: float = 30.0
    min_brightness: float = 25.0
    max_brightness: float = 235.0
    min_contrast_std: float = 18.0


def compute_person_crop_quality(
    crop: np.ndarray,
    bbox: Optional[Tuple[int, int, int, int]] = None,
    frame_shape: Optional[Tuple[int, int]] = None,
    config: Optional[QualityFilterConfig] = None
) -> Tuple[float, bool, str]:
    """
    Computes a deterministic quality score for a person crop.
    
    Returns:
        quality_score: float in [0.0, 1.0]
        is_acceptable: bool (True if acceptable for Re-ID)
        reason: str (Diagnostic reason if rejected or scored low)
    """
    if config is None:
        config = QualityFilterConfig()

    if crop is None or crop.size == 0:
        return 0.0, False, "EMPTY_IMAGE"

    h, w = crop.shape[:2]
    area = w * h

    # 1. Extreme Minimum Dimension Check
    if w < config.min_width or h < config.min_height or area < config.min_area:
        return 0.05, False, f"RESOLUTION_TOO_LOW: {w}x{h}px (min: {config.min_width}x{config.min_height})"

    # 2. Aspect Ratio Evaluation (width / height)
    aspect_ratio = float(w) / float(max(1, h))
    if aspect_ratio > 1.2:  # Significantly wider than tall -> likely a crowd group, truncated top, or false positive
        aspect_score = 0.1
    elif aspect_ratio > 0.8:
        aspect_score = 0.4
    elif aspect_ratio < 0.2:  # Overly skinny sliver
        aspect_score = 0.3
    else:
        # Ideal human body profile is aspect ratio ~ 0.35 - 0.60
        diff = abs(aspect_ratio - config.ideal_aspect_ratio)
        aspect_score = float(np.clip(1.0 - (diff / 0.4), 0.3, 1.0))

    # 3. Blur Assessment via Laplacian Variance
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < config.min_laplacian_var:
        blur_score = float(np.clip(laplacian_var / config.min_laplacian_var, 0.1, 0.8))
    else:
        blur_score = float(np.clip(0.8 + (laplacian_var - config.min_laplacian_var) / 300.0, 0.8, 1.0))

    # 4. Illumination & Contrast Assessment
    mean_brightness = float(np.mean(gray))
    std_contrast = float(np.std(gray))

    if mean_brightness < config.min_brightness:
        illum_score = 0.2  # Severe underexposure / silhouette
    elif mean_brightness > config.max_brightness:
        illum_score = 0.2  # Severe overexposure / washout
    else:
        illum_score = 1.0

    if std_contrast < config.min_contrast_std:
        contrast_score = float(np.clip(std_contrast / config.min_contrast_std, 0.2, 1.0))
    else:
        contrast_score = 1.0

    # 5. Frame Boundary Clipping Check
    boundary_score = 1.0
    if bbox is not None and frame_shape is not None:
        x1, y1, x2, y2 = bbox
        fh, fw = frame_shape[:2]
        # Check if box touches edges of camera frame
        clipped_edges = 0
        if x1 <= 2: clipped_edges += 1
        if y1 <= 2: clipped_edges += 1
        if x2 >= fw - 3: clipped_edges += 1
        if y2 >= fh - 3: clipped_edges += 1
        if clipped_edges >= 2:
            boundary_score = 0.5
        elif clipped_edges == 1:
            boundary_score = 0.85

    # 6. Resolution Factor
    # Scale from 1500 to 20000 px^2
    res_score = float(np.clip((area - config.min_area) / 15000.0, 0.3, 1.0))

    # Composite Deterministic Quality Formula
    composite_quality = (
        0.30 * blur_score +
        0.25 * res_score +
        0.20 * aspect_score +
        0.15 * contrast_score * illum_score +
        0.10 * boundary_score
    )
    quality_score = float(np.clip(composite_quality, 0.0, 1.0))

    is_acceptable = quality_score >= 0.25
    reason = "OK" if is_acceptable else "QUALITY_INSUFFICIENT"

    return round(quality_score, 4), is_acceptable, reason
