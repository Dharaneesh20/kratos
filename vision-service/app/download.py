"""
Fetches the DeepGlobe Road Extraction dataset via kagglehub and resolves
the actual train/ directory inside it (kagglehub caches the dataset under
its own path, e.g. ~/.cache/kagglehub/datasets/..., and the internal folder
layout can be nested one level deep depending on how Kaggle packaged it).

Usage:
    python -m app.download          # downloads + prints resolved train dir
    from app.download import get_train_dir
    train_dir = get_train_dir()     # used by dataset.py / model.py
"""

import os

import kagglehub

DATASET_SLUG = "balraj98/deepglobe-road-extraction-dataset"

_cached_train_dir = None


def download_dataset() -> str:
    """Downloads (or reuses cached copy) and returns the root path."""
    path = kagglehub.dataset_download(DATASET_SLUG)
    print(f"[download] dataset root: {path}")
    return path


def _find_train_dir(root: str) -> str:
    """
    Walk the downloaded dataset looking for a directory that contains
    *_sat.jpg / *_mask.png pairs -- this is robust to whatever nesting
    kagglehub/Kaggle uses internally.
    """
    for dirpath, _dirnames, filenames in os.walk(root):
        has_sat = any(f.endswith("_sat.jpg") for f in filenames)
        has_mask = any(f.endswith("_mask.png") for f in filenames)
        if has_sat and has_mask:
            return dirpath
    raise FileNotFoundError(
        f"Could not locate a train directory with *_sat.jpg / *_mask.png "
        f"pairs under {root}. Inspect the folder manually: "
        f"`find {root} -maxdepth 3`"
    )


def get_train_dir(force_redownload: bool = False) -> str:
    """
    Returns the resolved path to the folder containing *_sat.jpg /
    *_mask.png pairs, downloading the dataset via kagglehub if needed.
    Result is cached in-process so repeated calls don't re-walk the tree.
    """
    global _cached_train_dir
    if _cached_train_dir is not None and not force_redownload:
        return _cached_train_dir

    root = download_dataset()
    train_dir = _find_train_dir(root)
    print(f"[download] resolved train dir: {train_dir}")
    _cached_train_dir = train_dir
    return train_dir


if __name__ == "__main__":
    get_train_dir()
