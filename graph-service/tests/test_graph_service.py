import pytest
import networkx as nx
from app.graph_builder import build_graph_from_geojson
from app.centrality import compute_critical_nodes
from app.simulation import run_disaster_simulation


@pytest.fixture
def sample_bridge_geojson():
    """
    Creates a GeoJSON road network with two clusters joined by a single bottleneck bridge edge.
    Cluster 1: (0,0) - (0,1) - (1,0)
    Bridge: (1,0) - (2,0)
    Cluster 2: (2,0) - (2,1) - (3,0)
    """
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-122.4194, 37.7749], [-122.4150, 37.7750]]
                },
                "properties": {"road_id": "r1", "speed_kmh": 40.0}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-122.4150, 37.7750], [-122.4100, 37.7752]]
                },
                "properties": {"road_id": "r2", "speed_kmh": 40.0}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-122.4100, 37.7752], [-122.4050, 37.7755]]
                },
                "properties": {"road_id": "r3", "speed_kmh": 30.0}
            }
        ]
    }


def test_graph_builder_and_bridges(sample_bridge_geojson):
    G, graph_data = build_graph_from_geojson(sample_bridge_geojson, snap_tolerance_m=10.0)
    assert G.number_of_nodes() > 0, "Graph should contain nodes"
    assert G.number_of_edges() > 0, "Graph should contain edges"
    assert "nodes" in graph_data, "graph_data must be networkx node_link format"


def test_centrality_and_critical_nodes(sample_bridge_geojson):
    G, _ = build_graph_from_geojson(sample_bridge_geojson)
    critical_nodes = compute_critical_nodes(G, top_n=5)
    assert len(critical_nodes) > 0, "Should compute critical nodes"
    assert "criticality_score" in critical_nodes[0]
    assert "betweenness" in critical_nodes[0]
    assert "closeness" in critical_nodes[0]
    assert "degree" in critical_nodes[0]


def test_disaster_simulation(sample_bridge_geojson):
    G, graph_data = build_graph_from_geojson(sample_bridge_geojson)
    sim_res = run_disaster_simulation(graph_data, hazard_type="FLOOD", severity=0.8)

    assert "travel_delay" in sim_res
    assert "resilience" in sim_res
    assert "affected_regions" in sim_res
    assert "damaged_graph_data" in sim_res
    assert 0.0 <= sim_res["resilience"] <= 1.0
