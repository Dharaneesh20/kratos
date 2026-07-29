import json
import os
import pytest
from app.services.graph_builder import build_graph_from_geojson
from app.services.simulation import run_disaster_simulation


@pytest.fixture
def sample_geojson():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_roads.geojson")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_disaster_simulation_flood(sample_geojson):
    _, graph_data = build_graph_from_geojson(sample_geojson)
    sim_res = run_disaster_simulation(graph_data, hazard_type="FLOOD", severity=0.8)

    assert sim_res["status"] == "success"
    assert "travel_delay" in sim_res
    assert "resilience" in sim_res
    assert 0.0 <= sim_res["resilience"] <= 1.0
    assert "affected_regions" in sim_res
    assert "damaged_graph_data" in sim_res


def test_disaster_simulation_all_hazards(sample_geojson):
    _, graph_data = build_graph_from_geojson(sample_geojson)

    for hazard in ["FLOOD", "EARTHQUAKE", "BRIDGE_FAILURE", "ROAD_CLOSURE"]:
        res = run_disaster_simulation(graph_data, hazard_type=hazard, severity=0.5)
        assert res["status"] == "success"
        assert 0.0 <= res["resilience"] <= 1.0
