import random
from typing import Any, Dict, List, Tuple
import networkx as nx
import numpy as np
from sklearn.cluster import DBSCAN


def run_disaster_simulation(
    graph_data: Dict[str, Any],
    hazard_type: str = "FLOOD",
    affected_node_ids: List[str] = None,
    affected_edge_ids: List[str] = None,
    severity: float = 0.8,
) -> Dict[str, Any]:
    """
    Simulates disaster effects on a road network graph.
    Returns travel_delay, resilience, affected_regions, and damaged_graph_data.
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

    removed_edges = set()
    removed_nodes = set()

    # Pre-select edges/nodes depending on hazard_type & severity if not explicitly passed
    all_edges = list(G_base.edges(data=True))
    all_nodes = list(G_base.nodes())

    if hazard_type == "BRIDGE_FAILURE":
        bridge_edges = [(u, v) for u, v, d in all_edges if d.get("is_bridge", False)]
        if not bridge_edges and all_edges:
            # Pick a subset of edges as bridge candidates
            num_remove = max(1, int(len(all_edges) * 0.15))
            bridge_edges = [(u, v) for u, v, d in all_edges[:num_remove]]
        for u, v in bridge_edges:
            removed_edges.add((u, v))

    elif hazard_type == "FLOOD":
        # Remove fraction of edges determined by severity
        num_remove = max(1, int(len(all_edges) * min(0.6, max(0.1, severity * 0.4))))
        # Deterministic sampling based on node index to be reproducible
        rng = random.Random(42)
        sampled = rng.sample(all_edges, num_remove)
        for u, v, _ in sampled:
            removed_edges.add((u, v))

    elif hazard_type == "EARTHQUAKE":
        num_remove = max(1, int(len(all_edges) * min(0.7, max(0.1, severity * 0.5))))
        rng = random.Random(99)
        sampled = rng.sample(all_edges, num_remove)
        for u, v, _ in sampled:
            removed_edges.add((u, v))

    # Also remove user-explicit node/edge IDs
    for u, v, d in all_edges:
        eid = d.get("edge_id")
        if eid in affected_edge_ids:
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

    # Measure connectivity & baseline travel cost
    nodes_sample = list(G_base.nodes())[:40]
    baseline_costs = []
    damaged_costs = []

    reachable_before = 0
    reachable_after = 0

    for i in range(len(nodes_sample)):
        for j in range(i + 1, len(nodes_sample)):
            u, v = nodes_sample[i], nodes_sample[j]

            # Baseline path cost
            try:
                c_base = nx.shortest_path_length(G_base, u, v, weight="travel_cost")
                reachable_before += 1
                baseline_costs.append(c_base)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

            # Damaged path cost
            try:
                if G_damaged.has_node(u) and G_damaged.has_node(v):
                    c_dam = nx.shortest_path_length(G_damaged, u, v, weight="travel_cost")
                    reachable_after += 1
                    damaged_costs.append(c_dam)
                else:
                    damaged_costs.append(c_base * 5.0)  # Penalty
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                damaged_costs.append(c_base * 5.0)

    # Travel delay calculation
    if baseline_costs and damaged_costs:
        avg_base = np.mean(baseline_costs)
        avg_dam = np.mean(damaged_costs)
        travel_delay = round(float(max(0.0, ((avg_dam - avg_base) / max(avg_base, 1e-5)) * 100.0)), 1)
    else:
        travel_delay = 0.0

    # Resilience score calculation
    if G_damaged.number_of_nodes() > 0:
        components_damaged = list(nx.connected_components(G_damaged))
        largest_comp_size = max(len(c) for c in components_damaged) if components_damaged else 0
        comp_ratio = largest_comp_size / float(total_nodes)
        reach_ratio = (reachable_after / float(max(1, reachable_before)))
        resilience = round(float(np.clip(comp_ratio * reach_ratio, 0.0, 1.0)), 2)
    else:
        resilience = 0.0

    # Affected regions clustering via DBSCAN
    damaged_edges_ids = []
    for u, v, d in G_base.edges(data=True):
        if not G_damaged.has_edge(u, v):
            eid = d.get("edge_id")
            if eid:
                damaged_edges_ids.append(eid)

    isolated_coords = []
    for node in G_base.nodes():
        if not G_damaged.has_node(node) or G_damaged.degree(node) == 0:
            lat = G_base.nodes[node].get("lat")
            lon = G_base.nodes[node].get("lon")
            if lat is not None and lon is not None:
                isolated_coords.append([lat, lon])

    affected_regions = []
    if isolated_coords:
        coords_arr = np.array(isolated_coords)
        # Cluster within ~500m (approx 0.005 degrees)
        db = DBSCAN(eps=0.005, min_samples=1).fit(coords_arr)
        labels = set(db.labels_)
        for lbl in labels:
            if lbl != -1:
                cluster_pts = coords_arr[db.labels_ == lbl]
                avg_lat = round(float(np.mean(cluster_pts[:, 0])), 4)
                avg_lon = round(float(np.mean(cluster_pts[:, 1])), 4)
                affected_regions.append(f"Sector ({avg_lat}, {avg_lon})")

    return {
        "travel_delay": travel_delay,
        "resilience": resilience,
        "affected_regions": affected_regions,
        "damaged_graph_data": nx.node_link_data(G_damaged),
        "damaged_edge_ids": damaged_edges_ids,
    }
