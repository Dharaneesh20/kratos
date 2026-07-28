import math
from typing import Any, Dict, Tuple
import networkx as nx
import numpy as np
from scipy.spatial import KDTree


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate the great circle distance between two points on the earth in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def build_graph_from_geojson(geojson_data: Dict[str, Any], snap_tolerance_m: float = 5.0) -> Tuple[nx.Graph, Dict[str, Any]]:
    """
    Parses GeoJSON LineStrings, merges endpoints within snap_tolerance_m,
    computes edge lengths and travel costs, flags bridge edges, and returns
    (NetworkX Graph, node_link_data Dict).
    """
    features = geojson_data.get("features", [])
    G = nx.Graph()

    raw_points = []
    # Collect all raw coordinates
    for f in features:
        geom = f.get("geometry", {})
        if geom.get("type") == "LineString":
            coords = geom.get("coordinates", [])
            for c in coords:
                if len(c) >= 2:
                    raw_points.append((float(c[0]), float(c[1])))

    if not raw_points:
        return G, nx.node_link_data(G)

    # Spatial snapping using KDTree on approximate projected coords (or lat/lon converted to meters)
    # Approx 1 deg lat = 111,000 meters, 1 deg lon = 111,000 * cos(lat) meters
    coords_np = np.array(raw_points)
    avg_lat = float(np.mean(coords_np[:, 1]))
    scale_x = 111000.0 * math.cos(math.radians(avg_lat))
    scale_y = 111000.0

    points_m = np.column_stack((coords_np[:, 0] * scale_x, coords_np[:, 1] * scale_y))
    tree = KDTree(points_m)

    # Group close points to unified node IDs
    visited = [False] * len(raw_points)
    coord_to_node_id = {}
    node_id_counter = 0

    for i, (lon, lat) in enumerate(raw_points):
        if visited[i]:
            continue
        idxs = tree.query_ball_point(points_m[i], r=snap_tolerance_m)
        nid = f"n_{node_id_counter}"
        node_id_counter += 1

        cluster_pts = coords_np[idxs]
        cluster_lon = float(np.mean(cluster_pts[:, 0]))
        cluster_lat = float(np.mean(cluster_pts[:, 1]))

        G.add_node(nid, lon=cluster_lon, lat=cluster_lat)

        for idx in idxs:
            visited[idx] = True
            coord_to_node_id[raw_points[idx]] = nid

    # Add edges
    edge_counter = 0
    for f in features:
        geom = f.get("geometry", {})
        props = f.get("properties", {})
        if geom.get("type") == "LineString":
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue

            for k in range(len(coords) - 1):
                p1 = (float(coords[k][0]), float(coords[k][1]))
                p2 = (float(coords[k + 1][0]), float(coords[k + 1][1]))

                u = coord_to_node_id.get(p1)
                v = coord_to_node_id.get(p2)

                if u and v and u != v:
                    dist = haversine_distance(
                        G.nodes[u]["lon"], G.nodes[u]["lat"],
                        G.nodes[v]["lon"], G.nodes[v]["lat"]
                    )
                    # If dist is zero (same snapped node), use min distance
                    length_m = max(dist, 1.0)
                    speed_kmh = props.get("speed_kmh", 30.0)
                    travel_cost = length_m / (speed_kmh * 1000.0 / 3600.0)

                    eid = f"e_{edge_counter}"
                    edge_counter += 1

                    G.add_edge(
                        u, v,
                        edge_id=eid,
                        length_m=round(length_m, 2),
                        travel_cost=round(travel_cost, 2),
                        road_id=props.get("road_id", eid),
                        confidence=props.get("confidence", 1.0),
                    )

    # Flag bridges
    try:
        bridges = list(nx.bridges(G))
        for u, v in bridges:
            G[u][v]["is_bridge"] = True
            G.nodes[u]["is_bridge_adjacent"] = True
            G.nodes[v]["is_bridge_adjacent"] = True
    except Exception:
        pass

    return G, nx.node_link_data(G)
