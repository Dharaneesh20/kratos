import json
import os
import random
from typing import Any, Dict, List, Optional
import networkx as nx
from app.services.resilience_score import compute_resilience_and_delay


def run_disaster_simulation(
    graph_data: Optional[Dict[str, Any]] = None,
    graph_json_path: Optional[str] = None,
    hazard_type: str = "FLOOD",
    affected_node_ids: List[str] = None,
    affected_edge_ids: List[str] = None,
    severity: float = 0.8,
    output_simulation_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Simulates disaster effects on a road network graph.
    Supports hazard types: FLOOD, EARTHQUAKE, BRIDGE_FAILURE, ROAD_CLOSURE.
    Returns dict with status, agent, simulation_json_path, travel_delay, resilience, affected_regions, damaged_graph_data, damaged_edge_ids.
    """
    if not graph_data and graph_json_path and os.path.exists(graph_json_path):
        with open(graph_json_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

    if not graph_data:
        graph_data = {"nodes": [], "links": []}

    G_base = nx.node_link_graph(graph_data)
    total_nodes = G_base.number_of_nodes()
    total_edges = G_base.number_of_edges()

    if total_nodes == 0 or total_edges == 0:
        result = {
            "status": "success",
            "agent": "simulation",
            "simulation_json_path": output_simulation_path,
            "travel_delay": 0.0,
            "resilience": 1.0,
            "affected_regions": [],
            "damaged_graph_data": graph_data,
            "damaged_edge_ids": [],
        }
        if output_simulation_path:
            os.makedirs(os.path.dirname(output_simulation_path), exist_ok=True)
            with open(output_simulation_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        return result

    G_damaged = G_base.copy()
    affected_node_ids = set(affected_node_ids or [])
    affected_edge_ids = set(affected_edge_ids or [])

    removed_edges = set()
    removed_nodes = set()

    all_edges = list(G_base.edges(data=True))
    all_nodes = list(G_base.nodes())

    # Apply hazard logic by preset
    if hazard_type == "BRIDGE_FAILURE":
        bridge_edges = [(u, v) for u, v, d in all_edges if d.get("is_bridge", False)]
        if not bridge_edges and all_edges:
            num_remove = max(1, int(len(all_edges) * 0.15))
            bridge_edges = [(u, v) for u, v, d in all_edges[:num_remove]]
        for u, v in bridge_edges:
            removed_edges.add((u, v))

    elif hazard_type == "FLOOD":
        num_remove = max(1, int(len(all_edges) * min(0.6, max(0.1, severity * 0.4))))
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

    # Also remove explicit user-selected edges/nodes
    for u, v, d in all_edges:
        eid = d.get("edge_id")
        if eid in affected_edge_ids:
            removed_edges.add((u, v))

    for node in all_nodes:
        if node in affected_node_ids:
            removed_nodes.add(node)

    # Execute removals
    for u, v in removed_edges:
        if G_damaged.has_edge(u, v):
            G_damaged.remove_edge(u, v)

    for node in removed_nodes:
        if G_damaged.has_node(node):
            G_damaged.remove_node(node)

    # Compute resilience, delay, and affected regions
    resilience, travel_delay, affected_regions = compute_resilience_and_delay(G_base, G_damaged)

    # List damaged edge IDs
    damaged_edge_ids_list = []
    for u, v, d in G_base.edges(data=True):
        if not G_damaged.has_edge(u, v):
            eid = d.get("edge_id")
            if eid:
                damaged_edge_ids_list.append(eid)

    damaged_graph_data = nx.node_link_data(G_damaged)

    result = {
        "status": "success",
        "agent": "simulation",
        "simulation_json_path": output_simulation_path,
        "travel_delay": travel_delay,
        "resilience": resilience,
        "affected_regions": affected_regions,
        "damaged_graph_data": damaged_graph_data,
        "damaged_edge_ids": damaged_edge_ids_list,
    }

    if output_simulation_path:
        os.makedirs(os.path.dirname(output_simulation_path), exist_ok=True)
        with open(output_simulation_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    return result
