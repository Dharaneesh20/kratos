import random
from typing import Any, Dict, List, Tuple
import networkx as nx
import numpy as np

# sklearn optional — fall back to simple grid clustering if not available
try:
    from sklearn.cluster import DBSCAN
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


def run_disaster_simulation(
    graph_data: Dict[str, Any],
    hazard_type: str = "FLOOD",
    affected_node_ids: List[str] = None,
    affected_edge_ids: List[str] = None,
    severity: float = 0.8,
) -> Dict[str, Any]:
    """
    Simulates disaster effects on a road network graph.
    Returns travel_delay (%), resilience (0–1), affected_regions, and damaged_graph_data.

    Design decisions:
    - travel_delay is the % increase in average shortest-path HOPS (edge count), not raw
      travel_cost, so it is robust against any coordinate/scale system.
    - resilience = fraction of nodes still reachable in the largest connected component.
    - Sector names are generated as human-readable Zone labels (A, B, C …) rather than
      raw coordinate pairs that are meaningless to the user.
    """
    G_base = nx.node_link_graph(graph_data)
    total_nodes = G_base.number_of_nodes()
    total_edges = G_base.number_of_edges()

    if total_nodes == 0 or total_edges == 0:
        return {
            "travel_delay": 0.0,
            "resilience": 1.0,
            "affected_regions": [],
            "damaged_graph_data": graph_data,
            "damaged_edge_ids": [],
        }

    G_damaged = G_base.copy()
    affected_node_ids = set(affected_node_ids or [])
    affected_edge_ids = set(affected_edge_ids or [])

    removed_edges: set = set()
    removed_nodes: set = set()

    all_edges = list(G_base.edges(data=True))
    all_nodes = list(G_base.nodes())

    # ── Hazard-based edge removal ────────────────────────────────────────────
    if hazard_type == "BRIDGE_FAILURE":
        bridge_edges = [(u, v) for u, v, d in all_edges if d.get("is_bridge", False)]
        if not bridge_edges and all_edges:
            num_remove = max(1, int(len(all_edges) * 0.15))
            bridge_edges = [(u, v) for u, v, _ in all_edges[:num_remove]]
        for u, v in bridge_edges:
            removed_edges.add((u, v))

    elif hazard_type == "FLOOD":
        # severity 0.1 → 10% edges removed; severity 1.0 → 40% edges removed
        frac = min(0.40, max(0.05, severity * 0.40))
        num_remove = max(1, int(len(all_edges) * frac))
        rng = random.Random(42)
        for u, v, _ in rng.sample(all_edges, min(num_remove, len(all_edges))):
            removed_edges.add((u, v))

    elif hazard_type == "EARTHQUAKE":
        frac = min(0.50, max(0.10, severity * 0.50))
        num_remove = max(1, int(len(all_edges) * frac))
        rng = random.Random(99)
        for u, v, _ in rng.sample(all_edges, min(num_remove, len(all_edges))):
            removed_edges.add((u, v))

    elif hazard_type == "ROAD_CLOSURE":
        frac = min(0.25, max(0.05, severity * 0.25))
        num_remove = max(1, int(len(all_edges) * frac))
        rng = random.Random(7)
        for u, v, _ in rng.sample(all_edges, min(num_remove, len(all_edges))):
            removed_edges.add((u, v))

    # User-explicit overrides
    for u, v, d in all_edges:
        if d.get("edge_id") in affected_edge_ids:
            removed_edges.add((u, v))
    for node in all_nodes:
        if node in affected_node_ids:
            removed_nodes.add(node)

    # Apply removals
    for u, v in removed_edges:
        if G_damaged.has_edge(u, v):
            G_damaged.remove_edge(u, v)
    for node in removed_nodes:
        if G_damaged.has_node(node):
            G_damaged.remove_node(node)

    # ── Travel delay: compare mean SHORTEST-PATH HOPS (unweighted) ───────────
    # Using hop-count avoids travel_cost scale issues from pixel-space coords.
    # Sample up to 30 node pairs for speed.
    sample_nodes = all_nodes[:30]
    hop_base: List[float] = []
    hop_dam: List[float] = []
    pairs_tested = 0

    for i in range(len(sample_nodes)):
        for j in range(i + 1, min(i + 8, len(sample_nodes))):
            u, v = sample_nodes[i], sample_nodes[j]
            try:
                h_base = nx.shortest_path_length(G_base, u, v)   # hop count (unweighted)
                hop_base.append(h_base)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

            try:
                if G_damaged.has_node(u) and G_damaged.has_node(v):
                    h_dam = nx.shortest_path_length(G_damaged, u, v)
                else:
                    h_dam = h_base * 3.0
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                h_dam = h_base * 3.0

            hop_dam.append(h_dam)
            pairs_tested += 1

    if hop_base and hop_dam:
        avg_base = float(np.mean(hop_base))
        avg_dam = float(np.mean(hop_dam))
        if avg_base > 0:
            raw_delay = ((avg_dam - avg_base) / avg_base) * 100.0
        else:
            raw_delay = 0.0
        # Cap at 150% — anything higher just means "severely disrupted"
        travel_delay = round(float(np.clip(raw_delay, 0.0, 150.0)), 1)
    else:
        travel_delay = 0.0

    # ── Resilience: fraction of nodes in largest remaining component ──────────
    # This is the standard network resilience metric and is scale-independent.
    damaged_node_count = G_damaged.number_of_nodes()
    if damaged_node_count > 0:
        components_damaged = list(nx.connected_components(G_damaged))
        largest_comp_size = max(len(c) for c in components_damaged) if components_damaged else 0
        # Resilience = how much of the original network is still connected
        resilience = round(float(largest_comp_size / float(total_nodes)), 2)
    else:
        resilience = 0.0

    # Cross-check: if almost all edges were removed, push resilience lower
    edges_remaining = G_damaged.number_of_edges()
    edge_survival_ratio = edges_remaining / float(max(1, total_edges))
    # Blend: 70% connectivity ratio + 30% edge survival ratio
    resilience = round(float(resilience * 0.70 + edge_survival_ratio * 0.30), 2)
    resilience = max(0.0, min(1.0, resilience))

    # ── Damaged edge IDs ──────────────────────────────────────────────────────
    damaged_edges_ids = []
    for u, v, d in G_base.edges(data=True):
        if not G_damaged.has_edge(u, v):
            eid = d.get("edge_id")
            if eid:
                damaged_edges_ids.append(eid)

    # ── Affected regions: human-readable zone labels ──────────────────────────
    # Collect isolated / zero-degree node coordinates
    isolated_coords = []
    for node in G_base.nodes():
        if not G_damaged.has_node(node) or G_damaged.degree(node) == 0:
            lat = G_base.nodes[node].get("lat")
            lon = G_base.nodes[node].get("lon")
            if lat is not None and lon is not None:
                isolated_coords.append([float(lat), float(lon)])

    affected_regions: List[str] = []

    if isolated_coords:
        coords_arr = np.array(isolated_coords)

        if _HAS_SKLEARN and len(coords_arr) >= 2:
            # Adaptive eps: use 5% of the coordinate range so it works for any scale
            lat_range = float(coords_arr[:, 0].max() - coords_arr[:, 0].min())
            lon_range = float(coords_arr[:, 1].max() - coords_arr[:, 1].min())
            eps = max(0.001, min(lat_range, lon_range) * 0.15)
            db = DBSCAN(eps=eps, min_samples=1).fit(coords_arr)
            cluster_labels = db.labels_
        else:
            # Simple: treat each point as its own cluster
            cluster_labels = np.arange(len(coords_arr))

        unique_labels = sorted(set(int(l) for l in cluster_labels if l != -1))

        # Zone naming: compass quadrants based on centroid position relative to network center
        all_lats = np.array([G_base.nodes[n].get("lat", 0.0) for n in G_base.nodes()])
        all_lons = np.array([G_base.nodes[n].get("lon", 0.0) for n in G_base.nodes()])
        center_lat = float(np.mean(all_lats)) if len(all_lats) > 0 else 0.0
        center_lon = float(np.mean(all_lons)) if len(all_lons) > 0 else 0.0

        # Use letters for up to 26 zones, then "Sector N" for extras
        letter_names = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        for idx, lbl in enumerate(unique_labels[:20]):  # cap at 20 zones
            cluster_pts = coords_arr[cluster_labels == lbl]
            c_lat = float(np.mean(cluster_pts[:, 0]))
            c_lon = float(np.mean(cluster_pts[:, 1]))

            # Compass quadrant
            ns = "North" if c_lat >= center_lat else "South"
            ew = "East" if c_lon >= center_lon else "West"

            if idx < len(letter_names):
                zone_label = f"Zone {letter_names[idx]} ({ns}-{ew})"
            else:
                zone_label = f"Sector {idx + 1} ({ns}-{ew})"

            affected_regions.append(zone_label)

    return {
        "travel_delay": travel_delay,
        "resilience": resilience,
        "affected_regions": affected_regions,
        "damaged_graph_data": nx.node_link_data(G_damaged),
        "damaged_edge_ids": damaged_edges_ids,
    }
