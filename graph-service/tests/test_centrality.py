import json
import os
import pytest
from app.services.graph_builder import build_graph_from_geojson
from app.services.centrality import compute_centralities
from app.services.criticality import compute_critical_nodes


@pytest.fixture
def sample_geojson():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_roads.geojson")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_compute_centralities(sample_geojson):
    G, _ = build_graph_from_geojson(sample_geojson)
    betweenness, closeness, degree = compute_centralities(G)

    assert len(betweenness) == G.number_of_nodes()
    assert len(closeness) == G.number_of_nodes()
    assert len(degree) == G.number_of_nodes()


def test_compute_critical_nodes(sample_geojson):
    G, _ = build_graph_from_geojson(sample_geojson)
    critical_nodes = compute_critical_nodes(G, top_n=5)

    assert len(critical_nodes) > 0
    top_node = critical_nodes[0]
    assert "node_id" in top_node
    assert "criticality_score" in top_node
    assert "betweenness" in top_node
    assert "closeness" in top_node
    assert "degree" in top_node
    assert "is_bridge_adjacent" in top_node
