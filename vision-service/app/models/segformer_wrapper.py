"""
SegFormer wrapper -- primary model per spec.
"""

import os

import numpy as np
import torch
from transformers import SegformerConfig, SegformerForSemanticSegmentation

from app.config import settings

_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"
BASE_CHECKPOINT = "nvidia/segformer-b2-finetuned-ade-512-512"


def build() -> torch.nn.Module:
    config = SegformerConfig.from_pretrained(BASE_CHECKPOINT, num_labels=1)
    model = SegformerForSemanticSegmentation.from_pretrained(
        BASE_CHECKPOINT,
        config=config,
        ignore_mismatched_sizes=True,
    )
    return model


def load(checkpoint_dir: str = None) -> torch.nn.Module:
    global _model
    if _model is not None:
        return _model

    checkpoint_dir = checkpoint_dir or settings.SEGFORMER_CHECKPOINT
    if os.path.isdir(checkpoint_dir):
        model = SegformerForSemanticSegmentation.from_pretrained(checkpoint_dir)
    else:
        model = build()
    model.to(_device)
    model.eval()
    _model = model
    return model


def predict_tile(tile_array: np.ndarray) -> np.ndarray:
    model = load()
    h, w = tile_array.shape[:2]
    tensor = torch.from_numpy(tile_array).permute(2, 0, 1).unsqueeze(0).float().to(_device)
    with torch.no_grad():
        outputs = model(pixel_values=tensor)
        logits = outputs.logits
        logits = torch.nn.functional.interpolate(
            logits,
            size=(h, w),
            mode="bilinear",
            align_corners=False,
        )
        probs = torch.sigmoid(logits)[0, 0].cpu().numpy()
    return probs
