import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.preprocess import compute_band_stats, iter_tiles


def _write_test_tif(path: str, width: int = 16, height: int = 16):
    data = np.zeros((3, height, width), dtype=np.uint8)
    data[0] = 10
    data[1] = 20
    data[2] = 30
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


def test_iter_tiles_and_stats(tmp_path):
    tif_path = tmp_path / "sample.tif"
    _write_test_tif(str(tif_path))

    mins, maxs = compute_band_stats(str(tif_path))
    assert mins.shape == (3,)
    assert maxs.shape == (3,)

    tiles = list(iter_tiles(str(tif_path), tile_size=8, overlap=0, band_stats=(mins, maxs)))
    assert len(tiles) == 4
    assert tiles[0].array.shape == (8, 8, 3)
