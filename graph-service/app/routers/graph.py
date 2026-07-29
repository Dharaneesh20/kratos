import os
from fastapi import APIRouter, HTTPException
from shared.schemas import GraphBuildRequest, GraphBuildResponse, CriticalNode
from app.services.graph_builder import build_graph_from_geojson
from app.services.criticality import compute_critical_nodes

router = APIRouter(tags=["Graph"])


@router.post("/graph/build", response_model=GraphBuildResponse)
def build_graph(req: GraphBuildRequest):
    """
    Consumes roads_geojson LineStrings (or roads_geojson_path file), builds NetworkX road graph,
    snaps coordinates, detects bridges, and computes centrality/critical nodes.
    """
    if not req.roads_geojson and not req.roads_geojson_path:
        raise HTTPException(status_code=400, detail="Either roads_geojson dict or roads_geojson_path must be provided")

    if req.roads_geojson_path and not os.path.exists(req.roads_geojson_path) and not req.roads_geojson:
        raise HTTPException(status_code=404, detail=f"GeoJSON file not found at path: {req.roads_geojson_path}")

    graph_json_path = None
    critical_nodes_path = None
    if req.roads_geojson_path:
        cache_dir = os.path.dirname(req.roads_geojson_path)
        graph_json_path = os.path.join(cache_dir, "road_graph.json")
        critical_nodes_path = os.path.join(cache_dir, "critical_nodes.json")

    G, graph_data = build_graph_from_geojson(
        geojson_data=req.roads_geojson,
        roads_geojson_path=req.roads_geojson_path,
        snap_tolerance_m=req.snap_tolerance_m,
        output_graph_path=graph_json_path,
    )

    critical_nodes_raw = compute_critical_nodes(
        G,
        top_n=20,
        output_path=critical_nodes_path,
    )

    critical_nodes = [CriticalNode(**cn) for cn in critical_nodes_raw]

    return GraphBuildResponse(
        status="success",
        agent="graph",
        nodes=G.number_of_nodes(),
        edges=G.number_of_edges(),
        graph_data=graph_data,
        graph_json_path=graph_json_path,
        critical_nodes_path=critical_nodes_path,
        critical_nodes=critical_nodes,
    )
