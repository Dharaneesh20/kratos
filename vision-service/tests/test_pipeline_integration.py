import time

import numpy as np
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin

from app.config import settings
from app.main import app


def _create_fixture_tif(path: str, width: int = 64, height: int = 64) -> None:
    data = np.zeros((3, height, width), dtype=np.uint8)
    yy, xx = np.indices((height, width))
    data[0] = ((xx / max(width - 1, 1)) * 255).astype(np.uint8)
    data[1] = ((yy / max(height - 1, 1)) * 255).astype(np.uint8)
    data[2] = 90

    transform = from_origin(-122.0, 37.0, 0.0001, 0.0001)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=3,
        dtype="uint8",
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data)


def test_upload_load_process_status_e2e(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "CACHE_DIR", str(tmp_path / "cache"))

    def fake_segment_scene(tif_path, model_name=None, tile_size=None, overlap=None, on_progress=None):
        prob_map = np.zeros((64, 64), dtype=np.float32)
        prob_map[32, 8:56] = 0.9
        if on_progress:
            on_progress(1, 1)
        return prob_map, 1, 0.0

    def fake_mask_to_pruned_skeleton(prob_map, threshold=None):
        sk = np.zeros_like(prob_map, dtype=bool)
        sk[32, 8:56] = True
        return sk

    def fake_build_geojson(skeleton, prob_map, tif_path, simplify_tolerance_px=None):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-122.0, 37.0], [-121.995, 37.0]],
                    },
                    "properties": {
                        "road_id": "r_001",
                        "length_m": 400.0,
                        "confidence": 0.9,
                        "road_class": "unknown",
                    },
                }
            ],
        }

    monkeypatch.setattr("app.routers.vision.segment_scene", fake_segment_scene)
    monkeypatch.setattr("app.routers.vision.mask_to_pruned_skeleton", fake_mask_to_pruned_skeleton)
    monkeypatch.setattr("app.routers.vision.build_geojson", fake_build_geojson)
    monkeypatch.setattr("app.routers.vision.weighted_confidence", lambda _: 0.9)

    tif_path = tmp_path / "scene.tif"
    _create_fixture_tif(str(tif_path))

    client = TestClient(app)

    with open(tif_path, "rb") as f:
        upload_resp = client.post("/dataset/upload", files={"file": ("scene.tif", f, "image/tiff")})
    assert upload_resp.status_code == 200
    upload_payload = upload_resp.json()
    assert upload_payload["status"] == "success"
    upload_ref = upload_payload["upload_ref"]

    load_resp = client.post(
        "/dataset/load",
        json={
            "source": "upload",
            "upload_ref": upload_ref,
        },
    )
    assert load_resp.status_code == 200
    load_payload = load_resp.json()
    assert load_payload["status"] == "success"
    assert load_payload["agent"] == "dataset"
    dataset_id = load_payload["dataset_id"]

    process_resp = client.post(
        "/vision/process",
        json={
            "dataset_id": dataset_id,
            "tile_size": 64,
            "overlap": 0,
            "model": "segformer",
        },
    )
    assert process_resp.status_code == 200
    process_payload = process_resp.json()
    assert process_payload["status"] == "success"
    job_id = process_payload["job_id"]

    final = None
    for _ in range(30):
        status_resp = client.get(f"/vision/status/{job_id}")
        assert status_resp.status_code == 200
        body = status_resp.json()
        if body.get("stage") in {"completed", "failed"}:
            final = body
            break
        time.sleep(0.05)

    assert final is not None
    assert final["status"] == "success"
    assert final["stage"] == "completed"
    assert final["result"] is not None

    result = final["result"]
    assert result["confidence"] == 0.9
    assert result["tile_count"] == 1
    assert "roads_geojson" in result
