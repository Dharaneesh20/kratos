from typing import Dict, Tuple
import networkx as nx


def compute_centralities(G: nx.Graph) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """
    Computes betweenness centrality (weighted by travel_cost), closeness centrality (distance=travel_cost),
    and degree centrality for all nodes in graph G.
    """
    if G.number_of_nodes() == 0:
        return {}, {}, {}

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

    return betweenness, closeness, degree
