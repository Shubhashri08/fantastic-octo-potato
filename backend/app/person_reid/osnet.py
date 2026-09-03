import os
import cv2
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import List, Optional

from .base import PersonReIDBackend

logger = logging.getLogger("osnet_backend")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
OSNET_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, "osnet_x1_0_market1501.pth")


class OSNetBackend(PersonReIDBackend):
    """
    Legacy OSNet x1.0 Person Re-ID Backend.
    Maintained for backward compatibility, reference benchmarking, and test rollbacks.
    """
    def __init__(self, weights_path: Optional[str] = None, device: Optional[str] = None):
        self.weights_path = weights_path or OSNET_WEIGHTS_PATH
        if device:
            self._device = device
        elif torch.cuda.is_available():
            self._device = "cuda"
        elif torch.backends.mps.is_available():
            self._device = "mps"
        else:
            self._device = "cpu"

        self.model: Optional[nn.Module] = None
        self._embedding_dim = 512
        self._model_name = "OSNet-x1.0"
        self._model_version = "osnet-market1501-legacy"
        self.input_size = (256, 128)
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        self.load()

    def load(self) -> None:
        from ..person_reid_model import OSNet, download_osnet_weights_if_missing
        logger.info(f"Loading Legacy OSNet Backend on device: {self._device}...")
        download_osnet_weights_if_missing()
        model = OSNet(num_classes=751, blocks=[2, 2, 2], channels=[64, 256, 384, 512], feature_dim=512)
        
        if os.path.exists(self.weights_path):
            state_dict = torch.load(self.weights_path, map_location="cpu")
            model_dict = model.state_dict()
            matched_dict = {k: v for k, v in state_dict.items() if k in model_dict and model_dict[k].shape == v.shape}
            model_dict.update(matched_dict)
            model.load_state_dict(model_dict)
            logger.info(f"✓ OSNet weights loaded ({len(matched_dict)} tensors).")

        model.eval()
        model.to(self._device)
        self.model = model

    def preprocess(self, img: np.ndarray) -> Optional[torch.Tensor]:
        if img is None or img.size == 0:
            return None
        h, w = img.shape[:2]
        if h < 10 or w < 10:
            return None
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.input_size[1], self.input_size[0]), interpolation=cv2.INTER_LINEAR)
        normalized = (resized.astype(np.float32) / 255.0 - self.mean) / self.std
        transposed = np.transpose(normalized, (2, 0, 1))
        return torch.from_numpy(transposed).float().unsqueeze(0)

    @torch.no_grad()
    def extract_embedding(self, image: np.ndarray) -> np.ndarray:
        if image is None or image.size == 0 or self.model is None:
            return np.zeros(self._embedding_dim, dtype=np.float32)

        tensor = self.preprocess(image)
        if tensor is None:
            return np.zeros(self._embedding_dim, dtype=np.float32)

        tensor = tensor.to(self._device)
        feat = self.model(tensor).cpu().numpy().flatten().astype(np.float32)
        norm = np.linalg.norm(feat)
        return (feat / norm).astype(np.float32) if norm > 1e-6 else np.zeros(self._embedding_dim, dtype=np.float32)

    @torch.no_grad()
    def batch_extract_embeddings(
        self, images: List[np.ndarray], batch_size: int = 16
    ) -> List[np.ndarray]:
        if not images or self.model is None:
            return []

        valid_tensors = []
        valid_indices = []
        for idx, img in enumerate(images):
            t = self.preprocess(img)
            if t is not None:
                valid_tensors.append(t)
                valid_indices.append(idx)

        res = [np.zeros(self._embedding_dim, dtype=np.float32) for _ in images]
        if not valid_tensors:
            return res

        for i in range(0, len(valid_tensors), batch_size):
            batch_t = torch.cat(valid_tensors[i:i + batch_size], dim=0).to(self._device)
            batch_feats = self.model(batch_t).cpu().numpy()
            for j, feat in enumerate(batch_feats):
                norm = np.linalg.norm(feat)
                feat_norm = feat / norm if norm > 1e-6 else np.zeros(self._embedding_dim, dtype=np.float32)
                orig_idx = valid_indices[i + j]
                res[orig_idx] = feat_norm.astype(np.float32)

        return res

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def device(self) -> str:
        return self._device
