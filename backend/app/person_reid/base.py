from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np


class PersonReIDBackend(ABC):
    """
    Abstract Base Class for Person Re-Identification Backends.
    Ensures modularity and allows seamless swapping between Re-ID models (TransReID, OSNet, fine-tuned checkpoints).
    """

    @abstractmethod
    def load(self) -> None:
        """Loads neural network weights onto the configured inference device."""
        pass

    @abstractmethod
    def extract_embedding(self, image: np.ndarray) -> np.ndarray:
        """
        Extracts an L2-normalized 1D feature embedding vector from a BGR person image crop.
        Returns: 1D float32 numpy array with unit L2 norm.
        """
        pass

    @abstractmethod
    def batch_extract_embeddings(
        self, images: List[np.ndarray], batch_size: int = 16
    ) -> List[np.ndarray]:
        """
        Extracts L2-normalized 1D feature embeddings for a batch of BGR person image crops.
        Returns: List of 1D float32 numpy arrays.
        """
        pass

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Embedding vector dimension (e.g., 768 for ViT-Base)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Canonical model architecture identifier."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Model version or checkpoint identifier."""
        pass

    @property
    @abstractmethod
    def device(self) -> str:
        """Current inference device ('cuda', 'mps', or 'cpu')."""
        pass

    @staticmethod
    def compare(query_emb: np.ndarray, gallery_emb: np.ndarray) -> float:
        """
        Computes cosine visual similarity between two L2-normalized feature vectors.
        Returns: float strictly in range [-1.0, 1.0].
        """
        if query_emb is None or gallery_emb is None:
            return 0.0
        q_norm = np.linalg.norm(query_emb)
        g_norm = np.linalg.norm(gallery_emb)
        if q_norm < 1e-6 or g_norm < 1e-6:
            return 0.0
        cos_sim = float(np.dot(query_emb / q_norm, gallery_emb / g_norm))
        return float(np.clip(cos_sim, -1.0, 1.0))
