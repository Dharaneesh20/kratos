import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.geojson_builder import build_geojson, weighted_confidence


def _write_test_tif(path: str, width: int = 64, height: int = 64):
    data = np.zeros((3, height, width), dtype=np.uint8)
    data[:] = 120
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


def test_build_geojson_contains_features(tmp_path):
    tif_path = tmp_path / "sample.tif"
    _write_test_tif(str(tif_path))

    skeleton = np.zeros((64, 64), dtype=np.uint8)
    skeleton[32, 10:54] = 1
    prob_map = np.zeros((64, 64), dtype=np.float32)
    prob_map[32, 10:54] = 0.9

    fc = build_geojson(skeleton=skeleton, prob_map=prob_map, tif_path=str(tif_path))
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) >= 1

    p = fc["features"][0]["properties"]
    assert "road_id" in p
    assert "length_m" in p
    assert "confidence" in p

    score = weighted_confidence(fc)
    assert 0.0 <= score <= 1.0
