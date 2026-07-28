"""
Dataset Agent core logic: download/locate/validate/cache a scene as a GeoTIFF.
"""

import hashlib
import json
import os
import shutil
import time
import uuid
from typing import Optional

import httpx
import rasterio
from rasterio.transform import from_bounds

from app.config import settings
from app.jobs.job_store import _USE_REDIS, _redis_client
from app.services.validators import InvalidGeoTiffError, reproject_to_target_crs, validate_geotiff

_memory_dataset_cache = {}


class DatasetLoadError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


class ProviderTimeoutError(DatasetLoadError):
    def __init__(self, message: str):
        super().__init__(message, code="DATASET_TIMEOUT")


def _dataset_id(source: str, bbox: Optional[list], upload_ref: Optional[str]) -> str:
    key = f"{source}:{bbox}:{upload_ref}"
    return "ds_" + hashlib.sha256(key.encode()).hexdigest()[:12]


def _cache_get(dataset_id: str) -> Optional[dict]:
    if _USE_REDIS and _redis_client is not None:
        raw = _redis_client.get(f"dataset:{dataset_id}")
        return json.loads(raw) if raw else None
    entry = _memory_dataset_cache.get(dataset_id)
    if entry and time.time() - entry["_cached_at"] > settings.DATASET_CACHE_TTL_SECONDS:
        return None
    return entry


def _cache_set(dataset_id: str, meta: dict) -> None:
    if _USE_REDIS and _redis_client is not None:
        _redis_client.set(
            f"dataset:{dataset_id}", json.dumps(meta), ex=settings.DATASET_CACHE_TTL_SECONDS
        )
    else:
        _memory_dataset_cache[dataset_id] = {**meta, "_cached_at": time.time()}


def get_dataset_metadata(dataset_id: str) -> Optional[dict]:
    data = _cache_get(dataset_id)
    if data is None:
        return None
    return {**data, "dataset_id": dataset_id}


def _with_retries(fn, *args, **kwargs):
    last_exc = None
    for attempt in range(settings.PROVIDER_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except DatasetLoadError as e:
            last_exc = e
            transient_codes = {"DATASET_TIMEOUT", "DATASET_PROVIDER_ERROR"}
            if e.code not in transient_codes or attempt >= settings.PROVIDER_MAX_RETRIES - 1:
                raise
            time.sleep(settings.PROVIDER_BACKOFF_BASE_SECONDS * (2**attempt))
        except Exception as e:
            last_exc = e
            if attempt < settings.PROVIDER_MAX_RETRIES - 1:
                time.sleep(settings.PROVIDER_BACKOFF_BASE_SECONDS * (2**attempt))
    raise ProviderTimeoutError(
        f"provider call failed after {settings.PROVIDER_MAX_RETRIES} attempts: {last_exc}"
    )


def _write_rgb_geotiff_from_image(image_path: str, tif_path: str, bbox: Optional[list]) -> str:
    import cv2

    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise DatasetLoadError(f"could not read image: {image_path}", code="DATASET_PROVIDER_ERROR")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width = image.shape[:2]
    bounds = bbox or [0.0, 0.0, float(width), float(height)]
    transform = from_bounds(*bounds, width=width, height=height)
    with rasterio.open(
        tif_path,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=3,
        dtype=image.dtype,
        crs=settings.CRS_DEFAULT,
        transform=transform,
    ) as dst:
        dst.write(image[:, :, 0], 1)
        dst.write(image[:, :, 1], 2)
        dst.write(image[:, :, 2], 3)
    return tif_path


def _fetch_deepglobe(bbox: Optional[list], cache_dir: str) -> str:
    from app.dataset import list_pairs, resolve_train_dir

    train_dir = resolve_train_dir(os.path.join(settings.DATA_DIR, "train"))
    pairs = list_pairs(train_dir)
    if not pairs:
        raise DatasetLoadError("DeepGlobe dataset has no *_sat.jpg files", code="DATASET_EMPTY")
    tif_path = os.path.join(cache_dir, "scene.tif")
    return _write_rgb_geotiff_from_image(pairs[0][0], tif_path, bbox)


def _fetch_spacenet(bbox: list, cache_dir: str) -> str:
    if not settings.SPACENET_SAMPLE_TIF_URL:
        raise DatasetLoadError(
            "SPACENET_SAMPLE_TIF_URL must point to a GeoTIFF scene for source=spacenet",
            code="DATASET_PROVIDER_CONFIG_MISSING",
        )
    tif_path = os.path.join(cache_dir, "scene.tif")
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(settings.SPACENET_SAMPLE_TIF_URL)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise DatasetLoadError(f"spacenet request failed: {e}", code="DATASET_TIMEOUT")
    with open(tif_path, "wb") as f:
        f.write(resp.content)
    return tif_path


def _fetch_sentinel(bbox: list, cache_dir: str) -> str:
    if not bbox or len(bbox) != 4:
        raise DatasetLoadError(
            "bbox with [lon_min, lat_min, lon_max, lat_max] is required for source=sentinel",
            code="DATASET_BAD_BBOX",
        )

    lon_min, lat_min, lon_max, lat_max = bbox
    if lon_min >= lon_max or lat_min >= lat_max:
        raise DatasetLoadError(
            "invalid bbox ordering; must satisfy lon_min < lon_max and lat_min < lat_max",
            code="DATASET_BAD_BBOX",
        )

    if not settings.SENTINEL_HUB_CLIENT_ID or not settings.SENTINEL_HUB_CLIENT_SECRET:
        raise DatasetLoadError(
            "SENTINEL_HUB_CLIENT_ID / SENTINEL_HUB_CLIENT_SECRET not set in .env",
            code="DATASET_AUTH_MISSING",
        )

    token_payload = {
        "grant_type": "client_credentials",
        "client_id": settings.SENTINEL_HUB_CLIENT_ID,
        "client_secret": settings.SENTINEL_HUB_CLIENT_SECRET,
    }
    try:
        with httpx.Client(timeout=45.0) as client:
            token_resp = client.post(settings.SENTINEL_TOKEN_URL, data=token_payload)
            token_resp.raise_for_status()
            token = token_resp.json().get("access_token")
            if not token:
                raise DatasetLoadError(
                    "sentinel auth response missing access_token",
                    code="DATASET_AUTH_FAILED",
                )

            process_payload = {
                "input": {
                    "bounds": {
                        "bbox": [lon_min, lat_min, lon_max, lat_max],
                        "properties": {
                            "crs": "http://www.opengis.net/def/crs/EPSG/0/4326",
                        },
                    },
                    "data": [
                        {
                            "type": settings.SENTINEL_COLLECTION,
                            "dataFilter": {
                                "maxCloudCoverage": 35,
                            },
                        }
                    ],
                },
                "output": {
                    "width": settings.SENTINEL_OUTPUT_SIZE,
                    "height": settings.SENTINEL_OUTPUT_SIZE,
                    "responses": [
                        {
                            "identifier": "default",
                            "format": {"type": "image/tiff"},
                        }
                    ],
                },
                "evalscript": (
                    "//VERSION=3\n"
                    "function setup(){return {input:['B04','B03','B02'],output:{bands:3,sampleType:'UINT16'}};}\n"
                    "function evaluatePixel(s){return [s.B04,s.B03,s.B02];}"
                ),
            }

            img_resp = client.post(
                settings.SENTINEL_PROCESS_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=process_payload,
            )
            img_resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = e.response.text[:300] if e.response is not None else str(e)
        raise DatasetLoadError(
            f"sentinel request failed ({status}): {body}",
            code="DATASET_PROVIDER_ERROR",
        )
    except httpx.HTTPError as e:
        raise DatasetLoadError(
            f"sentinel network error: {e}",
            code="DATASET_TIMEOUT",
        )

    tif_path = os.path.join(cache_dir, "scene.tif")
    with open(tif_path, "wb") as f:
        f.write(img_resp.content)
    return tif_path


def _fetch_osm(bbox: list, cache_dir: str) -> str:
    raise DatasetLoadError(
        "source=osm has no raster scene; use it for vector overlays only.",
        code="DATASET_UNSUPPORTED_SOURCE",
    )


def fetch_osm_ground_truth(bbox: list):
    import osmnx as ox

    west, south, east, north = bbox
    return ox.graph_from_bbox(north, south, east, west, network_type="drive")


def _fetch_upload(upload_ref: str, cache_dir: str) -> str:
    src_path = os.path.join(settings.CACHE_DIR, "uploads", upload_ref)
    if not os.path.exists(src_path):
        raise DatasetLoadError(f"upload_ref not found on disk: {src_path}", code="VISION_003")

    dst_path = os.path.join(cache_dir, "scene.tif")
    shutil.copyfile(src_path, dst_path)
    return dst_path


def save_upload(file_bytes: bytes, extension: str = ".tif") -> str:
    os.makedirs(os.path.join(settings.CACHE_DIR, "uploads"), exist_ok=True)
    upload_ref = f"file_{uuid.uuid4().hex[:10]}{extension}"
    path = os.path.join(settings.CACHE_DIR, "uploads", upload_ref)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return upload_ref


def load_dataset(source: str, bbox: Optional[list] = None, upload_ref: Optional[str] = None) -> dict:
    dataset_id = _dataset_id(source, bbox, upload_ref)

    cached = _cache_get(dataset_id)
    if cached is not None:
        return {**cached, "dataset_id": dataset_id, "cached": True}

    cache_dir = os.path.join(settings.CACHE_DIR, dataset_id)
    os.makedirs(cache_dir, exist_ok=True)

    if source == "deepglobe":
        tif_path = _with_retries(_fetch_deepglobe, bbox, cache_dir)
    elif source == "spacenet":
        tif_path = _with_retries(_fetch_spacenet, bbox, cache_dir)
    elif source == "sentinel":
        tif_path = _with_retries(_fetch_sentinel, bbox, cache_dir)
    elif source == "osm":
        tif_path = _fetch_osm(bbox, cache_dir)
    elif source == "upload":
        if not upload_ref:
            raise DatasetLoadError("upload_ref required when source=upload", code="VISION_003")
        tif_path = _fetch_upload(upload_ref, cache_dir)
    else:
        raise DatasetLoadError(f"unknown source: {source}", code="DATASET_UNKNOWN_SOURCE")

    try:
        meta = validate_geotiff(tif_path)
    except InvalidGeoTiffError:
        raise

    if meta["crs"] != settings.CRS_DEFAULT:
        reprojected_path = os.path.join(cache_dir, "scene_reprojected.tif")
        tif_path = reproject_to_target_crs(tif_path, reprojected_path, settings.CRS_DEFAULT)
        meta = validate_geotiff(tif_path)

    result = {
        "tif_path": tif_path,
        "crs": meta["crs"],
        "resolution_m": meta["resolution_m"],
        "bbox": bbox or meta["bounds"],
        "cached": False,
    }
    _cache_set(dataset_id, result)
    return {**result, "dataset_id": dataset_id}
