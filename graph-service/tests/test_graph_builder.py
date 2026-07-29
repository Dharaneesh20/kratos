import json
import os
import pytest
from app.services.graph_builder import build_graph_from_geojson, shortest_path


@pytest.fixture
def sample_geojson():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_roads.geojson")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_build_graph_from_geojson(sample_geojson):
    G, graph_data = build_graph_from_geojson(sample_geojson, snap_tolerance_m=10.0)

    assert G.number_of_nodes() > 0, "Graph should contain nodes"
    assert G.number_of_edges() > 0, "Graph should contain edges"
    assert "nodes" in graph_data, "graph_data must be networkx node_link format"
    assert "links" in graph_data or "edges" in graph_data


def test_bridge_detection_in_graph(sample_geojson):
    G, _ = build_graph_from_geojson(sample_geojson, snap_tolerance_m=10.0)

    # In a simple linear chain (n0 - n1 - n2 - n3), all edges are bridges
    bridge_adjacent_nodes = [n for n, data in G.nodes(data=True) if data.get("is_bridge_adjacent")]
    assert len(bridge_adjacent_nodes) > 0, "Should detect bridge-adjacent nodes in bottleneck topology"


def test_shortest_path_helper(sample_geojson):
    G, _ = build_graph_from_geojson(sample_geojson)
    nodes = list(G.nodes())
    if len(nodes) >= 2:
        src, dst = nodes[0], nodes[-1]
        path, cost = shortest_path(G, src, dst)
        assert len(path) >= 2
        assert cost > 0.0
