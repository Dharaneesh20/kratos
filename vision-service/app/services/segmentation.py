"""
Runs the chosen model over every tile and stitches results back into one
full-scene probability map using overlap-averaging, so tile seams are smooth.
"""

from typing import Callable, Tuple

import numpy as np
import rasterio

from app.config import settings
from app.services.preprocess import compute_band_stats, iter_tiles


def _get_predict_fn(model_name: str) -> Callable[[np.ndarray], np.ndarray]:
    if model_name == "segformer":
        from app.models.segformer_wrapper import predict_tile

        return predict_tile
    if model_name == "deeplabv3plus":
        from app.models.deeplabv3plus_wrapper import predict_tile

        return predict_tile
    raise ValueError(f"unknown model: {model_name}")


def _feather_weight(h: int, w: int, overlap: int) -> np.ndarray:
    ramp_h = np.ones(h, dtype=np.float32)
    ramp_w = np.ones(w, dtype=np.float32)
    if overlap > 0:
        edge = min(overlap, h // 2, w // 2)
        if edge > 0:
            ramp_h[:edge] = np.linspace(0.1, 1.0, edge)
            ramp_h[-edge:] = np.linspace(1.0, 0.1, edge)
            ramp_w[:edge] = np.linspace(0.1, 1.0, edge)
            ramp_w[-edge:] = np.linspace(1.0, 0.1, edge)
    return np.outer(ramp_h, ramp_w)


def segment_scene(
    tif_path: str,
    model_name: str = None,
    tile_size: int = None,
    overlap: int = None,
    on_progress: Callable[[int, int], None] = None,
) -> Tuple[np.ndarray, int, float]:
    model_name = settings.DEFAULT_MODEL if model_name is None else model_name
    tile_size = settings.TILE_SIZE if tile_size is None else tile_size
    overlap = settings.TILE_OVERLAP if overlap is None else overlap
    predict_fn = _get_predict_fn(model_name)

    with rasterio.open(tif_path) as src:
        height, width = src.height, src.width

    prob_sum = np.zeros((height, width), dtype=np.float32)
    weight_sum = np.zeros((height, width), dtype=np.float32)

    band_stats = compute_band_stats(tif_path)

    tile_count = 0
    occluded_count = 0
    tiles = list(iter_tiles(tif_path, tile_size, overlap, band_stats=band_stats))
    total = len(tiles)

    for i, tile in enumerate(tiles):
        probs = predict_fn(tile.array)
        weight = _feather_weight(tile.height, tile.width, overlap)

        r0, c0 = tile.row_off, tile.col_off
        prob_sum[r0 : r0 + tile.height, c0 : c0 + tile.width] += probs * weight
        weight_sum[r0 : r0 + tile.height, c0 : c0 + tile.width] += weight

        mean_val = tile.array.mean()
        if mean_val < 0.08 or mean_val > 0.92:
            occluded_count += 1

        tile_count += 1
        if on_progress:
            on_progress(i + 1, total)

    weight_sum = np.where(weight_sum == 0, 1, weight_sum)
    full_prob_map = prob_sum / weight_sum
    occluded_pct = 100.0 * occluded_count / max(tile_count, 1)

    return full_prob_map, tile_count, occluded_pct
