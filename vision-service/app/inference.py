"""
Ties trained model + postprocess pipeline together for the /vision/process
endpoint. Loads the model once at import time (not per-request).
"""

import base64
import io

import cv2
import numpy as np
import torch
from PIL import Image

from app.config import settings
from app.model import load_model
from app.postprocess import mask_to_geojson

_device = "cuda" if torch.cuda.is_available() else "cpu"
_model = None


def get_model():
    global _model
    if _model is None:
        _model = load_model(device=_device)
    return _model


def _preprocess_image_bytes(image_bytes: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((settings.IMG_SIZE, settings.IMG_SIZE))
    return np.array(image)


def _mask_to_png_b64(mask: np.ndarray) -> str:
    mask_img = (mask * 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", mask_img)
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def run_inference(image_bytes: bytes) -> dict:
    model = get_model()
    image = _preprocess_image_bytes(image_bytes)

    image_norm = image.astype(np.float32) / 255.0
    tensor = torch.from_numpy(image_norm).permute(2, 0, 1).unsqueeze(0).float().to(_device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits)[0, 0].cpu().numpy()

    binary_mask = (probs > 0.5).astype(np.uint8)

    roads_geojson = mask_to_geojson(binary_mask)
    mask_png_b64 = _mask_to_png_b64(binary_mask)

    return {
        "road_mask_png_base64": mask_png_b64,
        "roads_geojson": roads_geojson,
        "image_size": settings.IMG_SIZE,
    }
