from typing import Any, Dict, List, Tuple
import networkx as nx
import numpy as np
from sklearn.cluster import DBSCAN


def compute_resilience_and_delay(
    G_base: nx.Graph,
    G_damaged: nx.Graph,
    sample_size: int = 50,
) -> Tuple[float, float, List[str]]:
    """
    Computes resilience score, travel delay %, and affected geographic regions.
    Resilience formula:
      resilience = (largest_connected_component_size_after / total_nodes) * (reachable_pairs_after / max(1, reachable_pairs_before))
      clamped to [0.0, 1.0].
    Travel delay formula:
      travel_delay = mean percentage increase in travel cost across sampled OD pairs.
    """
    total_nodes = G_base.number_of_nodes()
    if total_nodes == 0:
        return 1.0, 0.0, []

    # Sample origin-destination pairs
    nodes_list = list(G_base.nodes())
    if len(nodes_list) <= sample_size:
        sample_nodes = nodes_list
    else:
        # Deterministic sampling for consistency
        sample_indices = np.linspace(0, len(nodes_list) - 1, sample_size, dtype=int)
        sample_nodes = [nodes_list[idx] for idx in sample_indices]

    baseline_costs = []
    damaged_costs = []

    reachable_before = 0
    reachable_after = 0

    for i in range(len(sample_nodes)):
        for j in range(i + 1, len(sample_nodes)):
            u, v = sample_nodes[i], sample_nodes[j]

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
                    damaged_costs.append(c_base * 5.0)  # Unreachable penalty
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                damaged_costs.append(c_base * 5.0)

    # Travel delay calculation
    if baseline_costs and damaged_costs:
        avg_base = float(np.mean(baseline_costs))
        avg_dam = float(np.mean(damaged_costs))
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

    # Cluster isolated/disconnected nodes geographically via DBSCAN
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
        for lbl in sorted(labels):
            if lbl != -1:
                cluster_pts = coords_arr[db.labels_ == lbl]
                avg_lat = round(float(np.mean(cluster_pts[:, 0])), 4)
                avg_lon = round(float(np.mean(cluster_pts[:, 1])), 4)
                affected_regions.append(f"Sector ({avg_lat}, {avg_lon})")

    return resilience, travel_delay, affected_regions
