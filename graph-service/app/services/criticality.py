import json
import os
from typing import Any, Dict, List, Optional
import networkx as nx
from app.config import settings
from app.services.centrality import compute_centralities


def compute_critical_nodes(
    G: nx.Graph,
    top_n: int = 20,
    output_path: Optional[str] = None,
    weight_betweenness: float = settings.WEIGHT_BETWEENNESS,
    weight_closeness: float = settings.WEIGHT_CLOSENESS,
    weight_degree: float = settings.WEIGHT_DEGREE,
) -> List[Dict[str, Any]]:
    """
    Computes top critical nodes based on combined criticality formula:
    criticality_score = weight_betweenness * betweenness + weight_closeness * closeness + weight_degree * degree
    """
    if G.number_of_nodes() == 0:
        return []

    betweenness, closeness, degree = compute_centralities(G)

    critical_nodes = []
    for node in G.nodes():
        b_val = float(betweenness.get(node, 0.0))
        c_val = float(closeness.get(node, 0.0))
        d_val = float(degree.get(node, 0.0))

        score = weight_betweenness * b_val + weight_closeness * c_val + weight_degree * d_val
        is_bridge_adj = bool(G.nodes[node].get("is_bridge_adjacent", False))

        critical_nodes.append({
            "node_id": str(node),
            "lat": float(G.nodes[node].get("lat", 0.0)),
            "lon": float(G.nodes[node].get("lon", 0.0)),
            "criticality_score": round(score, 4),
            "is_bridge_adjacent": is_bridge_adj,
            "betweenness": round(b_val, 4),
            "closeness": round(c_val, 4),
            "degree": round(d_val, 4),
        })

    # Sort descending by criticality score
    critical_nodes.sort(key=lambda x: x["criticality_score"], reverse=True)
    result = critical_nodes[:top_n]

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    return result
