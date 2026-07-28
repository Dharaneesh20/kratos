"""
Binary mask -> 1px-wide skeleton -> prune spurious short branches.
"""

import networkx as nx
import numpy as np
from skimage.morphology import skeletonize as sk_skeletonize

from app.config import settings

_NEIGHBORS_8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def binarize(prob_map: np.ndarray, threshold: float = None) -> np.ndarray:
    threshold = threshold if threshold is not None else settings.MASK_THRESHOLD
    return (prob_map > threshold).astype(np.uint8)


def to_skeleton(binary_mask: np.ndarray) -> np.ndarray:
    return sk_skeletonize(binary_mask.astype(bool))


def _pixel_graph(skeleton: np.ndarray) -> nx.Graph:
    graph = nx.Graph()
    ys, xs = np.nonzero(skeleton)
    pixel_set = set(zip(ys.tolist(), xs.tolist()))
    for y, x in pixel_set:
        graph.add_node((y, x))
        for dy, dx in _NEIGHBORS_8:
            ny, nx_ = y + dy, x + dx
            if (ny, nx_) in pixel_set:
                graph.add_edge((y, x), (ny, nx_))
    return graph


def prune_short_branches(skeleton: np.ndarray, min_branch_len_px: int = None) -> np.ndarray:
    min_branch_len_px = min_branch_len_px or settings.MIN_BRANCH_LEN_PX
    graph = _pixel_graph(skeleton)

    changed = True
    while changed:
        changed = False
        leaves = [n for n in graph.nodes if graph.degree(n) == 1]
        for leaf in leaves:
            path = [leaf]
            current, prev = leaf, None
            while True:
                neighbors = [n for n in graph.neighbors(current) if n != prev]
                if len(neighbors) != 1:
                    break
                prev, current = current, neighbors[0]
                path.append(current)
                if len(path) > min_branch_len_px:
                    break
            if len(path) <= min_branch_len_px and graph.degree(path[-1]) != 1:
                graph.remove_nodes_from(path[:-1])
                changed = True

    pruned = np.zeros_like(skeleton, dtype=bool)
    for y, x in graph.nodes:
        pruned[y, x] = True
    return pruned


def mask_to_pruned_skeleton(prob_map: np.ndarray, threshold: float = None) -> np.ndarray:
    binary = binarize(prob_map, threshold)
    skeleton = to_skeleton(binary)
    return prune_short_branches(skeleton)
