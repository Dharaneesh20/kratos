"""
Tiling, normalization, and (train-time only) augmentation.

Normalization uses running dataset-level per-band stats rather than
per-tile min/max, to avoid contrast flicker across tile seams when we
stitch the segmentation mask back together in services/segmentation.py.
"""

from dataclasses import dataclass
from typing import Iterator, List, Tuple

import albumentations as A
import numpy as np
import rasterio
from rasterio.windows import Window

from app.config import settings


@dataclass
class Tile:
    array: np.ndarray
    row_off: int
    col_off: int
    height: int
    width: int


def compute_band_stats(path: str, sample_windows: int = 8) -> Tuple[np.ndarray, np.ndarray]:
    with rasterio.open(path) as src:
        band_count = min(src.count, 3)
        mins = np.full(band_count, np.inf)
        maxs = np.full(band_count, -np.inf)

        rows = max(1, src.height // sample_windows)
        cols = max(1, src.width // sample_windows)
        for r in range(0, src.height, rows):
            for c in range(0, src.width, cols):
                window = Window(c, r, min(cols, src.width - c), min(rows, src.height - r))
                data = src.read(list(range(1, band_count + 1)), window=window)
                mins = np.minimum(mins, data.reshape(band_count, -1).min(axis=1))
                maxs = np.maximum(maxs, data.reshape(band_count, -1).max(axis=1))
    return mins, maxs


def iter_tiles(
    path: str,
    tile_size: int = None,
    overlap: int = None,
    band_stats: Tuple[np.ndarray, np.ndarray] = None,
) -> Iterator[Tile]:
    tile_size = settings.TILE_SIZE if tile_size is None else tile_size
    overlap = settings.TILE_OVERLAP if overlap is None else overlap
    stride = tile_size - overlap
    if stride <= 0:
        raise ValueError("overlap must be smaller than tile_size")

    with rasterio.open(path) as src:
        band_count = min(src.count, 3)
        if band_stats is None:
            mins, maxs = compute_band_stats(path)
        else:
            mins, maxs = band_stats
        ranges = np.where((maxs - mins) == 0, 1, maxs - mins)

        for row_off in range(0, src.height, stride):
            for col_off in range(0, src.width, stride):
                h = min(tile_size, src.height - row_off)
                w = min(tile_size, src.width - col_off)
                window = Window(col_off, row_off, w, h)
                data = src.read(list(range(1, band_count + 1)), window=window).astype(np.float32)

                data = (data - mins[:, None, None]) / ranges[:, None, None]
                data = np.clip(data, 0.0, 1.0)
                array = np.transpose(data, (1, 2, 0))

                yield Tile(array=array, row_off=row_off, col_off=col_off, height=h, width=w)


def list_tile_grid(path: str, tile_size: int = None, overlap: int = None) -> List[Tuple[int, int]]:
    tile_size = settings.TILE_SIZE if tile_size is None else tile_size
    overlap = settings.TILE_OVERLAP if overlap is None else overlap
    stride = tile_size - overlap
    with rasterio.open(path) as src:
        height, width = src.height, src.width
    offsets = []
    for row_off in range(0, height, stride):
        for col_off in range(0, width, stride):
            offsets.append((row_off, col_off))
    return offsets


def train_augmentation(img_size: int = None):
    img_size = img_size or settings.TILE_SIZE
    return A.Compose(
        [
            A.RandomRotate90(p=0.5),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            A.CoarseDropout(
                max_holes=6,
                max_height=img_size // 6,
                max_width=img_size // 6,
                min_holes=1,
                fill_value=0,
                mask_fill_value=None,
                p=0.5,
            ),
        ]
    )
