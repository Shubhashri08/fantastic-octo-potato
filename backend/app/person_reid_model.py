import os
import cv2
import math
import logging
import numpy as np
import torch
import torch.nn as nn
from torch.nn import functional as F
from typing import List, Union, Optional, Tuple

logger = logging.getLogger("person_reid_model")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)
OSNET_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, "osnet_x1_0_market1501.pth")


# =========================================================================
# 1. OSNet (Omni-Scale Network for Person Re-Identification) Architecture
# Reference: Zhou et al., "Omni-Scale Feature Learning for Person Re-Identification", ICCV 2019
# =========================================================================

class ConvLayer(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, groups=1):
        super(ConvLayer, self).__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, kernel_size,
            stride=stride, padding=padding, groups=groups, bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))


class Conv1x1(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1, groups=1):
        super(Conv1x1, self).__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, 1,
            stride=stride, padding=0, groups=groups, bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))


class LightConv3x3(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(LightConv3x3, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 1, bias=False)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, padding=1, groups=out_channels, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.conv2(self.conv1(x))))


class ChannelGate(nn.Module):
    def __init__(self, in_channels, num_gates=None, return_gates=False, gate_activation='sigmoid', reduction=16):
        super(ChannelGate, self).__init__()
        if num_gates is None:
            num_gates = in_channels
        self.return_gates = return_gates
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc1 = nn.Conv2d(in_channels, in_channels // reduction, 1, bias=True)
        self.relu = nn.ReLU(inplace=True)
        self.fc2 = nn.Conv2d(in_channels // reduction, num_gates, 1, bias=True)
        if gate_activation == 'sigmoid':
            self.gate_activation = nn.Sigmoid()
        elif gate_activation == 'relu':
            self.gate_activation = nn.ReLU(inplace=True)
        elif gate_activation == 'linear':
            self.gate_activation = None
        else:
            raise RuntimeError(f"Unknown gate activation: {gate_activation}")

    def forward(self, x):
        input = x
        x = self.global_avgpool(x)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        if self.gate_activation is not None:
            x = self.gate_activation(x)
        if self.return_gates:
            return x
        return input * x


class OSBlock(nn.Module):
    def __init__(self, in_channels, out_channels, IN=False, bottleneck_reduction=4):
        super(OSBlock, self).__init__()
        mid_channels = out_channels // bottleneck_reduction
        self.conv1 = Conv1x1(in_channels, mid_channels)
        self.conv2a = LightConv3x3(mid_channels, mid_channels)
        self.conv2b = nn.Sequential(
            LightConv3x3(mid_channels, mid_channels),
            LightConv3x3(mid_channels, mid_channels)
        )
        self.conv2c = nn.Sequential(
            LightConv3x3(mid_channels, mid_channels),
            LightConv3x3(mid_channels, mid_channels),
            LightConv3x3(mid_channels, mid_channels)
        )
        self.conv2d = nn.Sequential(
            LightConv3x3(mid_channels, mid_channels),
            LightConv3x3(mid_channels, mid_channels),
            LightConv3x3(mid_channels, mid_channels),
            LightConv3x3(mid_channels, mid_channels)
        )
        self.gate = ChannelGate(mid_channels)
        self.conv3 = Conv1x1(mid_channels, out_channels)
        self.downsample = None
        if in_channels != out_channels:
            self.downsample = Conv1x1(in_channels, out_channels)

    def forward(self, x):
        residual = x
        x1 = self.conv1(x)
        x2a = self.conv2a(x1)
        x2b = self.conv2b(x1)
        x2c = self.conv2c(x1)
        x2d = self.conv2d(x1)
        x2 = self.gate(x2a + x2b + x2c + x2d)
        x3 = self.conv3(x2)
        if self.downsample is not None:
            residual = self.downsample(residual)
        return F.relu(x3 + residual, inplace=True)


class OSNet(nn.Module):
    def __init__(self, num_classes=1000, blocks=[2, 2, 2], channels=[64, 256, 384, 512], feature_dim=512, IN=False):
        super(OSNet, self).__init__()
        self.feature_dim = feature_dim
        self.conv1 = ConvLayer(3, channels[0], 7, stride=2, padding=3)
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)

        self.conv2 = self._make_layer(channels[0], channels[1], blocks[0], IN=IN)
        self.conv3 = self._make_layer(channels[1], channels[2], blocks[1], IN=IN)
        self.conv4 = self._make_layer(channels[2], channels[3], blocks[2], IN=IN)

        self.conv5 = Conv1x1(channels[3], channels[3])
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(feature_dim, channels[3], dropout_p=None)
        self.classifier = nn.Linear(self.feature_dim, num_classes) if num_classes > 0 else None

    def _make_layer(self, in_channels, out_channels, num_blocks, IN=False):
        layers = [OSBlock(in_channels, out_channels, IN=IN)]
        for _ in range(1, num_blocks):
            layers.append(OSBlock(out_channels, out_channels, IN=IN))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        if fc_dims is None or fc_dims < 0:
            self.feature_dim = input_dim
            return None
        layers = [
            nn.Linear(input_dim, fc_dims),
            nn.BatchNorm1d(fc_dims),
            nn.ReLU(inplace=True)
        ]
        if dropout_p is not None:
            layers.append(nn.Dropout(p=dropout_p))
        self.feature_dim = fc_dims
        return nn.Sequential(*layers)

    def forward(self, x, return_featuremaps=False):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        if return_featuremaps:
            return x
        v = self.global_avgpool(x)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        return v


def download_osnet_weights_if_missing():
    """Downloads official OSNet x1_0 pretrained weights trained on Market-1501."""
    if os.path.exists(OSNET_WEIGHTS_PATH) and os.path.getsize(OSNET_WEIGHTS_PATH) > 5000000:
        return OSNET_WEIGHTS_PATH

    import requests
    url = "https://drive.google.com/uc?id=1LaG1EJpHrxdAxKnSCJ_i0u-nbxSAeiFY"
    logger.info("Downloading pretrained OSNet x1.0 weights from official repository...")
    session = requests.Session()
    response = session.get(url, stream=True)
    token = None
    for k, v in response.cookies.items():
        if k.startswith('download_warning'):
            token = v
    if token:
        response = session.get(f"{url}&confirm={token}", stream=True)

    with open(OSNET_WEIGHTS_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    logger.info(f"Downloaded OSNet weights ({os.path.getsize(OSNET_WEIGHTS_PATH)} bytes) to {OSNET_WEIGHTS_PATH}")
    return OSNET_WEIGHTS_PATH


# =========================================================================
# 2. PersonReIDModel Wrapper (Singleton, Device-Optimized, Batched)
# =========================================================================

class PersonReIDModel:
    """
    Standardized Pretrained Person Re-Identification Model Abstraction.
    - Model: OSNet x1.0 (512-dimensional output embedding)
    - Image Input: (256, 128) RGB Tensor, ImageNet normalized
    - Embeddings: L2-Normalized (unit sphere), comparison via Cosine Similarity
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PersonReIDModel, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, weights_path: Optional[str] = None, device: Optional[str] = None):
        if self._initialized:
            return

        self.weights_path = weights_path or OSNET_WEIGHTS_PATH
        if device:
            self.device = device
        elif torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        self.model = None
        self.embedding_dim = 512
        self.model_name = "OSNet-x1.0-Market1501"
        self.input_size = (256, 128)  # height=256, width=128
        
        # ImageNet normalization parameters
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        self.load_model()
        self._initialized = True

    def load_model(self):
        """Loads and initializes OSNet with pretrained Market-1501 weights."""
        logger.info(f"Loading Person Re-ID Model [{self.model_name}] on device: {self.device}...")
        try:
            download_osnet_weights_if_missing()
            model = OSNet(num_classes=751, blocks=[2, 2, 2], channels=[64, 256, 384, 512], feature_dim=512)
            
            state_dict = torch.load(self.weights_path, map_location="cpu")
            # Strip potential classifier weights if shape mismatch
            model_dict = model.state_dict()
            matched_dict = {}
            for k, v in state_dict.items():
                if k in model_dict and model_dict[k].shape == v.shape:
                    matched_dict[k] = v
            model_dict.update(matched_dict)
            model.load_state_dict(model_dict)

            model.eval()
            model.to(self.device)
            self.model = model
            logger.info(f"✓ Person Re-ID Model [{self.model_name}] successfully loaded ({len(matched_dict)} tensors).")
        except Exception as e:
            logger.error(f"Failed to load OSNet weights: {e}. Falling back to initialized model.")
            model = OSNet(num_classes=751, blocks=[2, 2, 2], channels=[64, 256, 384, 512], feature_dim=512)
            model.eval()
            model.to(self.device)
            self.model = model

    def preprocess(self, img: np.ndarray) -> Optional[torch.Tensor]:
        """Preprocesses a BGR OpenCV image crop into a normalized PyTorch tensor [1, 3, 256, 128]."""
        if img is None or img.size == 0:
            return None

        h, w = img.shape[:2]
        if h < 10 or w < 10:
            return None

        # Convert BGR to RGB
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Resize to standard Re-ID dimensions (height=256, width=128)
        resized = cv2.resize(rgb, (self.input_size[1], self.input_size[0]), interpolation=cv2.INTER_LINEAR)
        
        # Normalize (img / 255.0 - mean) / std
        normalized = (resized.astype(np.float32) / 255.0 - self.mean) / self.std
        # HWC to CHW
        transposed = np.transpose(normalized, (2, 0, 1))
        tensor = torch.from_numpy(transposed).float().unsqueeze(0)
        return tensor

    @torch.no_grad()
    def extract_embedding(self, image: np.ndarray) -> np.ndarray:
        """
        Extracts 512-D L2-normalized deep appearance feature embedding vector.
        Input: BGR numpy image array.
        Output: 512-D float32 numpy array with unit L2 norm.
        """
        if image is None or image.size == 0:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        tensor = self.preprocess(image)
        if tensor is None:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        tensor = tensor.to(self.device)
        features = self.model(tensor)
        feat_np = features.cpu().numpy().flatten().astype(np.float32)
        
        # L2-Normalize
        norm = np.linalg.norm(feat_np)
        if norm > 1e-6:
            feat_np = feat_np / norm
        else:
            feat_np = np.zeros(self.embedding_dim, dtype=np.float32)
            
        return feat_np

    @torch.no_grad()
    def extract_embeddings_batch(self, images: List[np.ndarray], batch_size: int = 16) -> List[np.ndarray]:
        """
        Batch-extracts 512-D L2-normalized embeddings for a list of images.
        """
        if not images:
            return []

        embeddings = []
        valid_tensors = []
        valid_indices = []

        for idx, img in enumerate(images):
            t = self.preprocess(img)
            if t is not None:
                valid_tensors.append(t)
                valid_indices.append(idx)

        if not valid_tensors:
            return [np.zeros(self.embedding_dim, dtype=np.float32) for _ in images]

        # Allocate placeholder list
        result_embeddings = [np.zeros(self.embedding_dim, dtype=np.float32) for _ in images]

        for i in range(0, len(valid_tensors), batch_size):
            batch_t = torch.cat(valid_tensors[i:i + batch_size], dim=0).to(self.device)
            batch_feats = self.model(batch_t).cpu().numpy()
            
            for j, feat in enumerate(batch_feats):
                norm = np.linalg.norm(feat)
                feat_norm = feat / norm if norm > 1e-6 else np.zeros(self.embedding_dim, dtype=np.float32)
                orig_idx = valid_indices[i + j]
                result_embeddings[orig_idx] = feat_norm.astype(np.float32)

        return result_embeddings

    @staticmethod
    def compare(query_emb: np.ndarray, gallery_emb: np.ndarray) -> float:
        """
        Computes Cosine Similarity between two L2-normalized feature vectors.
        Returns float strictly in [-1.0, 1.0].
        """
        if query_emb is None or gallery_emb is None:
            return 0.0
        q_norm = np.linalg.norm(query_emb)
        g_norm = np.linalg.norm(gallery_emb)
        if q_norm < 1e-6 or g_norm < 1e-6:
            return 0.0
        # Dot product of normalized vectors
        cos_sim = float(np.dot(query_emb / q_norm, gallery_emb / g_norm))
        return float(np.clip(cos_sim, -1.0, 1.0))


# Global Singleton Instance
reid_model_instance = PersonReIDModel()

def get_person_reid_model() -> PersonReIDModel:
    global reid_model_instance
    if reid_model_instance is None or reid_model_instance.model is None:
        reid_model_instance = PersonReIDModel()
    return reid_model_instance
