"""
Pruned skeleton -> vectorized LineStrings -> GeoJSON matching Vision->Graph contract.
"""

import geojson
import numpy as np
import rasterio
import sknw
from pyproj import Geod
from shapely.geometry import LineString

from app.config import settings

_geod = Geod(ellps="WGS84")


def skeleton_to_graph(skeleton: np.ndarray):
    return sknw.build_sknw(skeleton)


def _pixel_to_lonlat_fn(affine):
    def _fn(col, row):
        lon, lat = affine * (col, row)
        return lon, lat

    return _fn


def _line_length_m(coords) -> float:
    if len(coords) < 2:
        return 0.0
    total = 0.0
    for (lon1, lat1), (lon2, lat2) in zip(coords[:-1], coords[1:]):
        _, _, dist = _geod.inv(lon1, lat1, lon2, lat2)
        total += dist
    return total


def _mean_confidence_along_path(prob_map: np.ndarray, pts) -> float:
    vals = [
        prob_map[int(r), int(c)]
        for r, c in pts
        if 0 <= int(r) < prob_map.shape[0] and 0 <= int(c) < prob_map.shape[1]
    ]
    return float(np.mean(vals)) if vals else 0.0


def build_geojson(
    skeleton: np.ndarray,
    prob_map: np.ndarray,
    tif_path: str,
    simplify_tolerance_px: float = None,
) -> dict:
    simplify_tolerance_px = simplify_tolerance_px or settings.SIMPLIFY_TOLERANCE_PX

    graph = skeleton_to_graph(skeleton)

    with rasterio.open(tif_path) as src:
        affine = src.transform
        tolerance_geo = simplify_tolerance_px * abs(affine.a)

    to_lonlat = _pixel_to_lonlat_fn(affine)

    features = []
    road_idx = 1
    for s, e in graph.edges():
        edge = graph[s][e]
        pts = edge.get("pts")
        if pts is None or len(pts) < 2:
            continue

        lonlat_coords = [to_lonlat(c, r) for r, c in pts]

        line = LineString(lonlat_coords)
        simplified = line.simplify(tolerance_geo, preserve_topology=True)
        coords = list(simplified.coords)
        if len(coords) < 2:
            continue

        length_m = _line_length_m(coords)
        confidence = _mean_confidence_along_path(prob_map, pts)

        road_id = f"r_{road_idx:03d}"
        road_idx += 1

        features.append(
            geojson.Feature(
                geometry=geojson.LineString([[float(x), float(y)] for x, y in coords]),
                properties={
                    "road_id": road_id,
                    "length_m": round(length_m, 1),
                    "confidence": round(confidence, 3),
                    "road_class": "unknown",
                },
            )
        )

    return geojson.FeatureCollection(features)


def weighted_confidence(feature_collection: dict) -> float:
    total_len = 0.0
    weighted = 0.0
    for f in feature_collection["features"]:
        length = f["properties"]["length_m"]
        conf = f["properties"]["confidence"]
        total_len += length
        weighted += length * conf
    return round(weighted / total_len, 3) if total_len > 0 else 0.0
