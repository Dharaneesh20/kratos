from typing import Any, Dict, List
import networkx as nx


def compute_critical_nodes(G: nx.Graph, top_n: int = 20) -> List[Dict[str, Any]]:
    if G.number_of_nodes() == 0:
        return []

    try:
        betweenness = nx.betweenness_centrality(G, weight="travel_cost", normalized=True)
    except Exception:
        betweenness = {n: 0.0 for n in G.nodes()}

    try:
        closeness = nx.closeness_centrality(G, distance="travel_cost")
    except Exception:
        closeness = {n: 0.0 for n in G.nodes()}

    try:
        degree = nx.degree_centrality(G)
    except Exception:
        degree = {n: 0.0 for n in G.nodes()}

    critical_nodes = []
    for node in G.nodes():
        b_val = float(betweenness.get(node, 0.0))
        c_val = float(closeness.get(node, 0.0))
        d_val = float(degree.get(node, 0.0))

        score = 0.6 * b_val + 0.25 * c_val + 0.15 * d_val
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
    return critical_nodes[:top_n]
