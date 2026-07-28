"""
DeepLabV3+ wrapper -- fallback model.
"""

import os

import numpy as np
import segmentation_models_pytorch as smp
import torch

from app.config import settings

_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def build() -> torch.nn.Module:
    return smp.DeepLabV3Plus(
        encoder_name=settings.ENCODER_NAME,
        encoder_weights="imagenet",
        in_channels=3,
        classes=1,
        activation=None,
    )


def load(checkpoint_path: str = None) -> torch.nn.Module:
    global _model
    if _model is not None:
        return _model

    checkpoint_path = checkpoint_path or settings.DEEPLABV3PLUS_CHECKPOINT
    model = build()
    if os.path.exists(checkpoint_path):
        state = torch.load(checkpoint_path, map_location=_device)
        model.load_state_dict(state)
    model.to(_device)
    model.eval()
    _model = model
    return model


def predict_tile(tile_array: np.ndarray) -> np.ndarray:
    model = load()
    tensor = torch.from_numpy(tile_array).permute(2, 0, 1).unsqueeze(0).float().to(_device)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits)[0, 0].cpu().numpy()
    return probs
