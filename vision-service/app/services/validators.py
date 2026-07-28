"""
GeoTIFF / CRS validation used by the Dataset Agent.
"""

import os

import rasterio
from rasterio.warp import Resampling, calculate_default_transform, reproject

from app.config import settings


class InvalidGeoTiffError(Exception):
    def __init__(self, message: str, code: str = "VISION_002"):
        self.message = message
        self.code = code
        super().__init__(message)


def validate_geotiff(path: str) -> dict:
    if not os.path.exists(path):
        raise InvalidGeoTiffError(f"file not found: {path}", code="VISION_003")

    try:
        with rasterio.open(path) as src:
            if src.crs is None:
                raise InvalidGeoTiffError(f"{path} has no CRS", code="VISION_002")
            if src.count < 3:
                raise InvalidGeoTiffError(
                    f"{path} has {src.count} bands, need >=3 (RGB)", code="VISION_002"
                )
            return {
                "crs": str(src.crs),
                "width": src.width,
                "height": src.height,
                "bounds": list(src.bounds),
                "resolution_m": abs(src.transform.a),
                "band_count": src.count,
            }
    except rasterio.errors.RasterioIOError as e:
        raise InvalidGeoTiffError(f"corrupt or unreadable GeoTIFF: {e}", code="VISION_002")


def reproject_to_target_crs(src_path: str, dst_path: str, target_crs: str = None) -> str:
    target_crs = target_crs or settings.CRS_DEFAULT

    with rasterio.open(src_path) as src:
        if str(src.crs) == target_crs:
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
