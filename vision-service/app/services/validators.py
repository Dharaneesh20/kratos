"""
GeoTIFF / CRS validation used by the Dataset Agent.
Automatically georeferences raw PNG/JPEG satellite imagery if CRS is missing,
using neutral pixel-space coordinates (NOT hardcoded to any real city).
"""

import os
import cv2
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject

from app.config import settings


class InvalidGeoTiffError(Exception):
    def __init__(self, message: str, code: str = "VISION_002"):
        self.message = message
        self.code = code
        super().__init__(message)


def ensure_georeferenced_tif(path: str, crs: str = "EPSG:4326") -> None:
    """
    Ensures that the image at path is a valid GeoTIFF with CRS and Affine Transform.
    Uses a neutral pixel-space coordinate system (near 0,0) scaled to realistic meter-per-pixel
    so roads are topologically correct without mapping to any real city.
    """
    img = cv2.imread(path)
    if img is None:
        return

    h, w = img.shape[:2]
    c = img.shape[2] if len(img.shape) == 3 else 1

    if c >= 3:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        bands = 3
    else:
        img_rgb = img
        bands = 1

    # Use a neutral pixel-space geographic extent:
    # 0.001 degrees per pixel ≈ ~111 meters per degree, so:
    # 512 px × 0.001 deg/px = 0.512 degrees across the image
    # Place it near [0.0, 0.0] to avoid any real city collision
    px_scale = 0.0001  # degrees per pixel (≈11 meters/px at equator)
    left = 0.0
    bottom = 0.0
    right = left + w * px_scale
    top = bottom + h * px_scale

    transform = from_bounds(left, bottom, right, top, w, h)

    meta = {
        "driver": "GTiff",
        "height": h,
        "width": w,
        "count": bands,
        "dtype": "uint8",
        "crs": crs,
        "transform": transform,
    }

    tmp_path = path + ".tmp.tif"
    with rasterio.open(tmp_path, "w", **meta) as dst:
        if bands >= 3:
            for i in range(3):
                dst.write(img_rgb[:, :, i], i + 1)
        else:
            dst.write(img_rgb, 1)

    os.replace(tmp_path, path)


def validate_geotiff(path: str) -> dict:
    if not os.path.exists(path):
        raise InvalidGeoTiffError(f"file not found: {path}", code="VISION_003")

    try:
        with rasterio.open(path) as src:
            # If missing CRS or pixel-grid-only bounds, apply neutral georeferencing
            bounds = list(src.bounds)
            is_pixel_space = (
                src.crs is None
                or bounds == [0.0, 0.0, float(src.width), float(src.height)]
            )

            if is_pixel_space:
                ensure_georeferenced_tif(path, crs=settings.CRS_DEFAULT)
                with rasterio.open(path) as new_src:
                    return {
                        "crs": str(new_src.crs),
                        "width": new_src.width,
                        "height": new_src.height,
                        "bounds": list(new_src.bounds),
                        "resolution_m": abs(new_src.transform.a),
                        "band_count": new_src.count,
                    }

            return {
                "crs": str(src.crs),
                "width": src.width,
                "height": src.height,
                "bounds": bounds,
                "resolution_m": abs(src.transform.a),
                "band_count": src.count,
            }
    except InvalidGeoTiffError:
        raise
    except Exception as e:
        # Fallback: try to auto-georeference raw PNG/JPEG via cv2
        try:
            ensure_georeferenced_tif(path, crs=settings.CRS_DEFAULT)
            with rasterio.open(path) as new_src:
                return {
                    "crs": str(new_src.crs),
                    "width": new_src.width,
                    "height": new_src.height,
                    "bounds": list(new_src.bounds),
                    "resolution_m": abs(new_src.transform.a),
                    "band_count": new_src.count,
                }
        except Exception:
            raise InvalidGeoTiffError(f"corrupt or unreadable image: {e}", code="VISION_002")


def reproject_to_target_crs(src_path: str, dst_path: str, target_crs: str = None) -> str:
    target_crs = target_crs or settings.CRS_DEFAULT

    with rasterio.open(src_path) as src:
        if src.crs and str(src.crs) == target_crs:
            return src_path

        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({"crs": target_crs, "transform": transform, "width": width, "height": height})

        with rasterio.open(dst_path, "w", **kwargs) as dst:
            for band in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, band),
                    destination=rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.bilinear,
                )
    return dst_path
