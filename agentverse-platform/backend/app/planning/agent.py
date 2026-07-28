import sys
from pathlib import Path
import math
from typing import Any, Dict, List
import networkx as nx

root_path = Path(__file__).resolve().parents[4]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from app.config import settings
from shared.schemas import EvacuationRoute, PlanningResponse, RepairPriorityItem


def run_planning_agent(
    graph_data: Dict[str, Any],
    critical_nodes: List[Dict[str, Any]],
    simulation_data: Dict[str, Any],
    hazard_type: str = "FLOOD",
    safe_zones: List[Dict[str, Any]] = None,
) -> PlanningResponse:
    """
    Computes evacuation routes using shortest path on the damaged graph,
    prioritizes road/node repairs based on criticality and damage state,
    and generates grounded disaster recommendations.
    """
    if not graph_data or "nodes" not in graph_data:
        return PlanningResponse(
            status="success",
            agent="planning",
            repair_priority=[],
            evacuation_routes=[],
            recommendations=["No graph data available for planning."],
        )

    # Reconstruct damaged graph from simulation data if available, else standard graph
    damaged_graph_dict = simulation_data.get("damaged_graph_data") if simulation_data else None
    if damaged_graph_dict and "nodes" in damaged_graph_dict:
        G = nx.node_link_graph(damaged_graph_dict)
    else:
        G = nx.node_link_graph(graph_data)

    nodes_list = list(G.nodes())
    if not nodes_list:
        return PlanningResponse(
            status="success",
            agent="planning",
            repair_priority=[],
            evacuation_routes=[],
            recommendations=["Graph contains no nodes."],
        )

    # Identify safe zone nodes
    safe_node_ids = []
    if safe_zones:
        safe_node_ids = [sz.get("node_id") if isinstance(sz, dict) else sz.node_id for sz in safe_zones]

    # If no safe zones provided, automatically designate highest degree connected node as safe zone
    if not safe_node_ids:
        sorted_by_degree = sorted(G.nodes(), key=lambda n: G.degree(n), reverse=True)
        if sorted_by_degree:
            safe_node_ids.append(sorted_by_degree[0])

    evacuation_routes: List[EvacuationRoute] = []

    # Calculate routes from critical nodes or affected regions to nearest safe zone
    target_nodes = [cn["node_id"] for cn in critical_nodes[:8]] if critical_nodes else nodes_list[:5]

    route_idx = 1
    for src in target_nodes:
        if not G.has_node(src):
            continue

        best_path = None
        min_cost = float("inf")
        best_target = None

        for target in safe_node_ids:
            if target == src or not G.has_node(target):
                continue
            try:
                path = nx.shortest_path(G, src, target, weight="travel_cost")
                cost = nx.shortest_path_length(G, src, target, weight="travel_cost")
                if cost < min_cost:
                    min_cost = cost
                    best_path = path
                    best_target = target
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        if best_path:
            path_coords = []
            for nid in best_path:
                lon = G.nodes[nid].get("lon", 0.0)
                lat = G.nodes[nid].get("lat", 0.0)
                path_coords.append([lon, lat])

            eta_min = round(max(1.0, min_cost / 60.0), 1)
            evacuation_routes.append(
                EvacuationRoute(
                    route_id=f"route_{route_idx}",
                    from_node=str(src),
                    to_node=str(best_target),
                    path_nodes=[str(n) for n in best_path],
                    path_coords=path_coords,
                    eta_min=eta_min,
                    vehicle="ambulance" if route_idx % 2 == 1 else "evacuation_bus",
                )
            )
            route_idx += 1

    # Repair priority ranking based on criticality and adjacent bridge state
    repair_priorities: List[RepairPriorityItem] = []
    if critical_nodes:
        for idx, cn in enumerate(critical_nodes[:5], start=1):
            is_bridge = cn.get("is_bridge_adjacent", False)
            reason = (
                f"Critical bridge-adjacent junction (Score: {cn.get('criticality_score')}) needing immediate structural stabilization."
                if is_bridge
                else f"High-centrality arterial node (Score: {cn.get('criticality_score')}) restricting sector connectivity."
            )
            repair_priorities.append(
                RepairPriorityItem(
                    node_id=cn["node_id"],
                    priority=idx,
                    reason=reason,
                )
            )

    # Generate recommendations grounded on computed simulation metrics
    resilience_val = simulation_data.get("resilience", 1.0) if simulation_data else 1.0
    delay_val = simulation_data.get("travel_delay", 0.0) if simulation_data else 0.0
    affected_regions = simulation_data.get("affected_regions", []) if simulation_data else []

    recommendations = [
        f"Deploy emergency logistics teams immediately to clear arterial routes around safe node '{safe_node_ids[0] if safe_node_ids else 'N/A'}'.",
        f"Post-disaster network resilience is measured at {int(resilience_val * 100)}% with a calculated travel delay impact of +{delay_val}%.",
        f"Prioritize repair sequence for Node {repair_priorities[0].node_id if repair_priorities else 'N/A'} to restore connectivity to isolated sectors.",
    ]

    if affected_regions:
        recommendations.append(f"Establish emergency relief posts in isolated regions: {', '.join(affected_regions[:3])}.")

    return PlanningResponse(
        status="success",
        agent="planning",
        repair_priority=repair_priorities,
        evacuation_routes=evacuation_routes,
        recommendations=recommendations,
    )
