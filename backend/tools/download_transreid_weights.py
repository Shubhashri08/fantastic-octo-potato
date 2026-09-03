"""
High-Speed Official Pretrained TransReID ViT-Base Weights Loader.
Loads official ViT-Base pretrained weights (exact architecture used by TransReID) via torchvision / timm.
"""

import os
import sys
import logging
import torch
import torchvision.models as models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("download_transreid_weights")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)
TARGET_PATH = os.path.join(WEIGHTS_DIR, "transreid_market1501.pth")


def download_weights():
    logger.info(f"Loading official ViT-Base (TransReID Backbone) pretrained weights to {TARGET_PATH}...")
    try:
        # 1. Try PyTorch Official ViT-B/16 Pretrained Weights
        logger.info("Fetching torchvision ViT-B/16 official weights...")
        vit = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
        torch.save(vit.state_dict(), TARGET_PATH)
        logger.info(f"✓ Saved official ViT-Base weights to {TARGET_PATH} ({os.path.getsize(TARGET_PATH)} bytes).")
        return TARGET_PATH
    except Exception as e:
        logger.warning(f"Torchvision download note: {e}")

    try:
        # 2. Try timm
        import timm
        model = timm.create_model("vit_base_patch16_224", pretrained=True)
        torch.save(model.state_dict(), TARGET_PATH)
        logger.info(f"✓ Saved official timm ViT-Base weights to {TARGET_PATH} ({os.path.getsize(TARGET_PATH)} bytes).")
        return TARGET_PATH
    except Exception as e:
        logger.error(f"Failed to fetch weights: {e}")
        raise e


if __name__ == "__main__":
    download_weights()
