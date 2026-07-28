import sys
import types

import cv2
import numpy as np
from fastapi.testclient import TestClient
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from app.config import settings
from app.main import app


def _provider_tif_bytes() -> bytes:
    data = np.full((3, 8, 8), 180, dtype=np.uint8)
    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            width=8,
            height=8,
            count=3,
            dtype="uint8",
            crs="EPSG:4326",
            transform=from_origin(0.0, 1.0, 0.01, 0.01),
        ) as dst:
            dst.write(data)
        return memfile.read()


class _FakeResponse:
    content = _provider_tif_bytes()
    status_code = 200

    def raise_for_status(self):
        return None


class _FakeHttpClient:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url):
        assert url == settings.SPACENET_SAMPLE_TIF_URL
        return _FakeResponse()


def test_spacenet_loads_configured_geotiff_url(monkeypatch, tmp_path):
    import app.services.dataset_loader as dataset_loader

    dataset_loader._memory_dataset_cache.clear()
    monkeypatch.setattr(settings, "CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(settings, "SPACENET_SAMPLE_TIF_URL", "https://example.test/scene.tif")
    monkeypatch.setattr("app.services.dataset_loader.httpx.Client", _FakeHttpClient)

    resp = TestClient(app).post("/dataset/load", json={"source": "spacenet"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["agent"] == "dataset"
    assert body["crs"] == "EPSG:4326"


def test_deepglobe_converts_training_tile_to_geotiff(monkeypatch, tmp_path):
    import app.services.dataset_loader as dataset_loader

    dataset_loader._memory_dataset_cache.clear()
    monkeypatch.setattr(settings, "CACHE_DIR", str(tmp_path / "cache"))

    sat_path = tmp_path / "1_sat.jpg"
    mask_path = tmp_path / "1_mask.png"
    cv2.imwrite(str(sat_path), np.full((10, 12, 3), 120, dtype=np.uint8))
    cv2.imwrite(str(mask_path), np.full((10, 12), 255, dtype=np.uint8))

    fake_dataset_module = types.SimpleNamespace(
        resolve_train_dir=lambda preferred_dir: str(tmp_path),
        list_pairs=lambda train_dir: [(str(sat_path), str(mask_path))],
    )
    monkeypatch.setitem(sys.modules, "app.dataset", fake_dataset_module)

    resp = TestClient(app).post(
        "/dataset/load",
        json={"source": "deepglobe", "bbox": [77.55, 12.9, 77.7, 13.05]},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["agent"] == "dataset"
    assert body["crs"] == "EPSG:4326"
    assert body["bbox"] == [77.55, 12.9, 77.7, 13.05]
