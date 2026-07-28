"""
DeepGlobe Road Extraction dataset loader.

Expects the Kaggle DeepGlobe layout inside DATA_DIR:
    data/train/1_sat.jpg   data/train/1_mask.png
    data/train/2_sat.jpg   data/train/2_mask.png
    ...

Masks are grayscale, road pixels ~255. We binarize at MASK_THRESHOLD.
"""

import glob
import os

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

from app.config import settings


def list_pairs(split_dir: str):
    """Return list of (sat_path, mask_path) tuples found in split_dir."""
    sat_paths = sorted(glob.glob(os.path.join(split_dir, f"*{settings.TRAIN_SAT_SUFFIX}")))
    pairs = []
    for sat_path in sat_paths:
        mask_path = sat_path.replace(settings.TRAIN_SAT_SUFFIX, settings.TRAIN_MASK_SUFFIX)
        if os.path.exists(mask_path):
            pairs.append((sat_path, mask_path))
    return pairs


def resolve_train_dir(preferred_dir: str) -> str:
    """
    Use preferred_dir (e.g. data/train) if it already has sat/mask pairs
    (manual download path). Otherwise fall back to kagglehub, which
    downloads/caches the dataset and returns the resolved internal path.
    """
    if os.path.isdir(preferred_dir) and list_pairs(preferred_dir):
        return preferred_dir

    from app.download import get_train_dir

    return get_train_dir()


class RoadDataset(Dataset):
    def __init__(self, split_dir: str, transform=None, img_size: int = None):
        split_dir = resolve_train_dir(split_dir)
        self.pairs = list_pairs(split_dir)
        if not self.pairs:
            raise FileNotFoundError(
                f"No sat/mask pairs found in {split_dir}. "
                f"Check that the DeepGlobe zip was extracted here and filenames "
                f"match *{settings.TRAIN_SAT_SUFFIX} / *{settings.TRAIN_MASK_SUFFIX}."
            )
        self.transform = transform
        self.img_size = img_size or settings.IMG_SIZE

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        sat_path, mask_path = self.pairs[idx]

        image = cv2.imread(sat_path, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        image = cv2.resize(image, (self.img_size, self.img_size))
        mask = cv2.resize(mask, (self.img_size, self.img_size), interpolation=cv2.INTER_NEAREST)
        mask = (mask > settings.MASK_THRESHOLD).astype(np.float32)

        if self.transform is not None:
            augmented = self.transform(image=image, mask=mask)
            image, mask = augmented["image"], augmented["mask"]

        image = image.astype(np.float32) / 255.0
        image_t = torch.from_numpy(image).permute(2, 0, 1).float()
        mask_t = torch.from_numpy(mask).unsqueeze(0).float()

        return image_t, mask_t


def train_val_split(split_dir: str, val_fraction: float = 0.1, seed: int = 42):
    """
    DeepGlobe's own valid/ folder ships without masks (it's for the original
    competition leaderboard), so split train/ ourselves.

    split_dir is resolved via resolve_train_dir first: if a local manual
    download exists at that path it's used as-is, otherwise the dataset is
    fetched (or read from cache) via kagglehub.
    """
    split_dir = resolve_train_dir(split_dir)
    pairs = list_pairs(split_dir)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(pairs))
    n_val = int(len(pairs) * val_fraction)
    val_idx, train_idx = set(idx[:n_val]), set(idx[n_val:])
    train_pairs = [pairs[i] for i in train_idx]
    val_pairs = [pairs[i] for i in val_idx]
    return train_pairs, val_pairs
