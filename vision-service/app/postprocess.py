"""
Binary road mask -> skeleton -> graph -> GeoJSON LineStrings.

This is the contract boundary with graph-service: it consumes the
"roads_geojson" this module produces.
"""

import geojson
import networkx as nx
import numpy as np
import sknw
from skimage.morphology import skeletonize


def mask_to_skeleton(mask: np.ndarray) -> np.ndarray:
    """mask: 2D binary array (0/1 or bool). Returns 1px-wide skeleton."""
    binary = mask.astype(bool)
    return skeletonize(binary)


def skeleton_to_graph(skeleton: np.ndarray) -> nx.Graph:
    """
    Uses sknw to convert a skeleton image directly into a networkx graph
    with node pixel-coordinates and edge pixel-paths -- avoids hand-rolling
    8-connectivity graph extraction.
    """
    return sknw.build_sknw(skeleton)


def graph_to_geojson(graph: nx.Graph, pixel_to_geo=None) -> dict:
    """
    Convert graph edges (pixel-coordinate paths) into GeoJSON LineString
    features. If pixel_to_geo is provided (a callable taking (row, col) and
    returning (lon, lat)), coordinates are geo-referenced; otherwise raw
    pixel coordinates are used (fine for a demo without tile geo-metadata).
    """
    features = []
    for (s, e) in graph.edges():
        edge = graph[s][e]
        pts = edge.get("pts")
        if pts is None or len(pts) < 2:
            continue
        if pixel_to_geo is not None:
            coords = [list(pixel_to_geo(r, c)) for r, c in pts]
        else:
            coords = [[float(c), float(r)] for r, c in pts]
        features.append(
            geojson.Feature(
                geometry=geojson.LineString(coords),
                properties={"source_node": int(s), "target_node": int(e)},
            )
        )
    return geojson.FeatureCollection(features)


def mask_to_geojson(mask: np.ndarray, pixel_to_geo=None) -> dict:
    """Convenience wrapper chaining the full postprocess pipeline."""
    skeleton = mask_to_skeleton(mask)
    graph = skeleton_to_graph(skeleton)
    return graph_to_geojson(graph, pixel_to_geo=pixel_to_geo)
