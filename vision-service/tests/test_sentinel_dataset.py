import numpy as np
from fastapi.testclient import TestClient
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from app.config import settings
from app.main import app


def _tif_bytes() -> bytes:
    data = np.zeros((3, 16, 16), dtype=np.uint8)
    data[0] = 100
    data[1] = 120
    data[2] = 140
    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            width=16,
            height=16,
            count=3,
            dtype="uint8",
            crs="EPSG:4326",
            transform=from_origin(77.55, 13.05, 0.0001, 0.0001),
        ) as dst:
            dst.write(data)
        return memfile.read()


class _FakeResponse:
    def __init__(self, *, json_body=None, content=b"", status_code=200):
        self._json_body = json_body or {}
        self.content = content
        self.status_code = status_code
        self.text = content[:200].decode("utf-8", errors="ignore") if content else ""

    def json(self):
        return self._json_body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected fake HTTP status {self.status_code}")


class _FakeHttpClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url == settings.SENTINEL_TOKEN_URL:
            return _FakeResponse(json_body={"access_token": "fake-token"})
        if url == settings.SENTINEL_PROCESS_URL:
            assert kwargs["headers"]["Authorization"] == "Bearer fake-token"
            assert kwargs["json"]["input"]["bounds"]["bbox"] == [77.55, 12.9, 77.7, 13.05]
            return _FakeResponse(content=_tif_bytes())
        raise AssertionError(f"unexpected URL {url}")


def test_sentinel_load_is_cached_and_validated(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(settings, "SENTINEL_HUB_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "SENTINEL_HUB_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr("app.services.dataset_loader.httpx.Client", _FakeHttpClient)

    client = TestClient(app)
    payload = {"source": "sentinel", "bbox": [77.55, 12.9, 77.7, 13.05]}

    first = client.post("/dataset/load", json=payload)
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["status"] == "success"
    assert first_body["agent"] == "dataset"
    assert first_body["cached"] is False
    assert first_body["crs"] == "EPSG:4326"

    second = client.post("/dataset/load", json=payload)
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["dataset_id"] == first_body["dataset_id"]
    assert second_body["cached"] is True
