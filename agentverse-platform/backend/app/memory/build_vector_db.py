"""
KRATOS Vector Database Builder & Feature Store Indexer.
Extracts spatial road feature embeddings from DeepGlobe satellite image/mask pairs
and stores portable vector embeddings in vector.db.
"""

import os
import sys
import glob
import json
import sqlite3
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple

import cv2
import numpy as np

# Ensure root paths are on sys.path
root_dir = Path(__file__).resolve().parents[4]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

backend_dir = root_dir / "agentverse-platform" / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.memory.vector_db import VectorDB


def extract_road_feature_vector(sat_path: str, mask_path: str) -> Tuple[List[float], Dict[str, Any]]:
    """
    Extracts a 128-dimensional normalized feature vector and metadata from a 
    satellite image and ground-truth road mask pair.
    """
    sat_img = cv2.imread(sat_path, cv2.IMREAD_COLOR)
    mask_img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    if sat_img is None or mask_img is None:
        raise ValueError(f"Could not read image files: {sat_path}, {mask_path}")

    # Resize to standard feature extraction dimensions
    sat_res = cv2.resize(sat_img, (256, 256))
    mask_res = cv2.resize(mask_img, (256, 256))

    # Binarize mask
    binary_mask = (mask_res > 127).astype(np.uint8)
    road_pixels = np.sum(binary_mask)
    total_pixels = 256 * 256
    road_ratio = float(road_pixels / total_pixels)

    # 1. Color Histogram Features (RGB 16 bins per channel = 48 dimensions)
    chans = cv2.split(sat_res)
    color_features = []
    for chan in chans:
        hist = cv2.calcHist([chan], [0], binary_mask if road_pixels > 0 else None, [16], [0, 256])
        cv2.normalize(hist, hist)
        color_features.extend(hist.flatten().tolist())

    # 2. Road Topology & Contour Features
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    num_contours = len(contours)
    max_contour_area = 0.0
    aspect_ratios = []

    for c in contours:
        area = cv2.contourArea(c)
        if area > max_contour_area:
            max_contour_area = float(area)
        x, y, w, h = cv2.boundingRect(c)
        if min(w, h) > 0:
            aspect_ratios.append(max(w, h) / min(w, h))

    avg_aspect_ratio = float(np.mean(aspect_ratios)) if aspect_ratios else 1.0

    # 3. Spatial Edge & Orientation Features (Sobel edges on road regions)
    gray_sat = cv2.cvtColor(sat_res, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray_sat, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray_sat, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx**2 + sobely**2)
    cv2.normalize(magnitude, magnitude)

    if road_pixels > 0:
        edge_hist, _ = np.histogram(magnitude[binary_mask > 0], bins=32, range=(0, 1.0))
    else:
        edge_hist, _ = np.histogram(magnitude, bins=32, range=(0, 1.0))
    edge_features = (edge_hist / (np.sum(edge_hist) + 1e-6)).tolist()

    # 4. Spatial Grid Density (4x4 grid = 16 dimensions)
    grid_features = []
    cell_h, cell_w = 64, 64
    for r in range(4):
        for c in range(4):
            cell = binary_mask[r*cell_h:(r+1)*cell_h, c*cell_w:(c+1)*cell_w]
            grid_features.append(float(np.mean(cell)))

    # Combine into 128-dimensional vector
    raw_vector = color_features + edge_features + grid_features + [
        road_ratio,
        float(num_contours / 100.0),
        float(max_contour_area / total_pixels),
        float(avg_aspect_ratio / 10.0),
    ]

    # Pad or truncate to exactly 128 dimensions
    if len(raw_vector) < 128:
        raw_vector += [0.0] * (128 - len(raw_vector))
    else:
        raw_vector = raw_vector[:128]

    # L2 Normalize
    norm = math.sqrt(sum(x*x for x in raw_vector))
    norm_vector = [x / norm if norm > 0 else 0.0 for x in raw_vector]

    img_id = Path(sat_path).stem.replace("_sat", "")
    metadata = {
        "image_id": img_id,
        "sat_file": os.path.basename(sat_path),
        "mask_file": os.path.basename(mask_path),
        "road_coverage_pct": round(road_ratio * 100, 2),
        "num_road_segments": num_contours,
        "sample_type": "deepglobe_satellite",
        "resolution": "256x256_normalized",
    }

    return norm_vector, metadata


def build_vector_db_from_dataset(
    dataset_dir: str = None,
    target_db_paths: List[str] = None,
    max_samples: int = 500
):
    """Populates vector.db databases with satellite road feature embeddings."""
    root = Path(__file__).resolve().parents[4]

    if dataset_dir is None:
        candidate_paths = [
            root / "vision-service" / "dataset_unprocessed" / "train",
            root / "vision-service" / "data" / "train",
        ]
        for cp in candidate_paths:
            if cp.exists() and list(cp.glob("*_sat.jpg")):
                dataset_dir = str(cp)
                break

    if not dataset_dir or not os.path.exists(dataset_dir):
        print(f"[VectorDB Builder] Error: Dataset directory not found at {dataset_dir}")
        return

    if target_db_paths is None:
        target_db_paths = [
            str(root / "agentverse-platform" / "backend" / "vector.db"),
            str(root / "vector.db"),
        ]

    sat_files = sorted(glob.glob(os.path.join(dataset_dir, "*_sat.jpg")))
    print(f"\n===============================================================================")
    print(f"      KRATOS VECTOR DATABASE INDEXER (DeepGlobe Road Embeddings)")
    print(f"===============================================================================")
    print(f"Source Dataset: {dataset_dir}")
    print(f"Target Vector DB Files: {target_db_paths}")
    print(f"Found Satellite Images: {len(sat_files)}")
    print(f"Indexing Up To: {max_samples} samples\n")

    indexed_count = 0

    for db_path in target_db_paths:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        vdb = VectorDB(db_path=db_path)

        for i, sat_path in enumerate(sat_files[:max_samples]):
            mask_path = sat_path.replace("_sat.jpg", "_mask.png")
            if not os.path.exists(mask_path):
                continue

            try:
                vec, meta = extract_road_feature_vector(sat_path, mask_path)
                entity_id = f"deepglobe_{meta['image_id']}"
                
                # Store under both collections for retrieval
                vdb.store_embedding(entity_id, "deepglobe_features", vec, meta)
                vdb.store_embedding(entity_id, "road_features", vec, meta)
                indexed_count += 1

                if (i + 1) % 50 == 0 or (i + 1) == min(len(sat_files), max_samples):
                    print(f"  [+] Indexed {i + 1}/{min(len(sat_files), max_samples)} image pairs into {os.path.basename(db_path)}...")
            except Exception as e:
                print(f"  [!] Error processing {sat_path}: {e}")

    print(f"\n===============================================================================")
    print(f"  SUCCESS! VECTOR DB GENERATION COMPLETE")
    print(f"  Total Indexed Embeddings: {indexed_count}")
    print(f"===============================================================================\n")


if __name__ == "__main__":
    build_vector_db_from_dataset()
