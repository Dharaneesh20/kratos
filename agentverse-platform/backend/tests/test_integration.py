import os
import sys
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
backend_path = root_path / "agentverse-platform" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
graph_path = root_path / "graph-service"
if str(graph_path) not in sys.path:
    sys.path.insert(0, str(graph_path))

from app.db.session import init_db
from app.planning.agent import run_planning_agent
from app.report.pdf_builder import generate_report_files

import importlib.util

def load_graph_module(name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(name, graph_path / "app" / file_name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

graph_builder_mod = load_graph_module("graph_builder_mod", "graph_builder.py")
centrality_mod = load_graph_module("centrality_mod", "centrality.py")
simulation_mod = load_graph_module("simulation_mod", "simulation.py")

build_graph_from_geojson = graph_builder_mod.build_graph_from_geojson
compute_critical_nodes = centrality_mod.compute_critical_nodes
run_disaster_simulation = simulation_mod.run_disaster_simulation


def test_full_pipeline_without_mock_data():
    init_db()

    # 1. Sample real GeoJSON extracted from satellite road lines
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-122.4194, 37.7749], [-122.4150, 37.7750], [-122.4100, 37.7752]]
                },
                "properties": {"road_id": "r_1", "speed_kmh": 40.0}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-122.4150, 37.7750], [-122.4152, 37.7790], [-122.4155, 37.7830]]
                },
                "properties": {"road_id": "r_2", "speed_kmh": 35.0}
            }
        ]
    }

    # 2. Test Graph Service building & centrality
    G, graph_data = build_graph_from_geojson(sample_geojson)
    assert G.number_of_nodes() > 0, "Graph should contain nodes"
    critical_nodes = compute_critical_nodes(G)
    assert len(critical_nodes) > 0, "Critical nodes should be computed"

    # 3. Test Disaster Simulation
    sim_data = run_disaster_simulation(graph_data, hazard_type="FLOOD", severity=0.8)
    assert "resilience" in sim_data
    assert "travel_delay" in sim_data

    # 4. Test Planning Agent
    plan_res = run_planning_agent(graph_data, critical_nodes, sim_data, hazard_type="FLOOD")
    assert len(plan_res.evacuation_routes) > 0 or len(plan_res.recommendations) > 0

    # 5. Test Report Generator
    report_res = generate_report_files("wf_test123", {
        "hazard_type": "FLOOD",
        "simulation_data": sim_data,
        "critical_nodes": critical_nodes,
        "planning_data": plan_res.model_dump(),
    })
    assert os.path.exists(report_res["pdf_path"]), "PDF report should exist"
    assert os.path.exists(report_res["csv_path"]), "CSV export should exist"

    print("[SUCCESS] Full integration pipeline test passed cleanly with zero mock data!")


if __name__ == "__main__":
    test_full_pipeline_without_mock_data()
