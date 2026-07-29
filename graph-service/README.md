# KRATOS - Graph Intelligence Service (`graph-service`)

The Graph Intelligence Service turns extracted road GeoJSON vectors into a routable, topological network graph (`NetworkX`). It performs bottleneck bridge detection, centrality analysis, criticality ranking, and disaster stress simulations (`FLOOD`, `EARTHQUAKE`, `BRIDGE_FAILURE`, `ROAD_CLOSURE`) to produce a network resilience index and travel delay metrics.

## 🚀 Features

- **Spatial Node Snapping**: Groups nearby intersection endpoints within configurable tolerance (default 5.0m) using `scipy.spatial.KDTree` on projected coordinates.
- **Topological Edge Attributes**: Computes edge length (Haversine) and travel cost based on speed.
- **Bridge Bottleneck Detection**: Uses NetworkX bridge detection (`nx.bridges`) to identify critical link bottlenecks.
- **Multi-Factor Criticality Ranking**: Calculates node criticality score using weighted centralities:
  $$\text{criticality\_score} = 0.6 \cdot \text{betweenness} + 0.25 \cdot \text{closeness} + 0.15 \cdot \text{degree}$$
- **Disaster Stress Simulation**: Simulates damage from `FLOOD`, `EARTHQUAKE`, `BRIDGE_FAILURE`, or `ROAD_CLOSURE` hazards.
- **Resilience Index & Travel Delay**: Calculates graph connectivity degradation, mean travel delay %, and geographic clustering (`DBSCAN`) of isolated sectors.

---

## 📡 API Endpoints

### 1. `GET /health`
Returns service status.
```json
{
  "status": "ok",
  "service": "graph-service",
  "version": "0.1.0"
}
```

### 2. `POST /graph/build`
Consumes GeoJSON LineStrings (directly or via `roads_geojson_path`), constructs the graph, detects bridges, and computes critical nodes.

**Request:**
```json
{
  "roads_geojson": { "type": "FeatureCollection", "features": [...] },
  "snap_tolerance_m": 5.0
}
```

**Response:**
```json
{
  "status": "success",
  "agent": "graph",
  "nodes": 1543,
  "edges": 2012,
  "graph_data": { ... },
  "critical_nodes": [
    {
      "node_id": "n_012",
      "lat": 37.7750,
      "lon": -122.4150,
      "criticality_score": 0.8421,
      "is_bridge_adjacent": true,
      "betweenness": 0.9100,
      "closeness": 0.7200,
      "degree": 0.6500
    }
  ]
}
```

### 3. `POST /simulation/run`
Simulates disaster effects on the road network graph.

**Request:**
```json
{
  "graph_data": { ... },
  "hazard_type": "FLOOD",
  "affected_node_ids": ["n_012"],
  "affected_edge_ids": ["e_101"],
  "severity": 0.8
}
```

**Response:**
```json
{
  "status": "success",
  "agent": "simulation",
  "travel_delay": 42.5,
  "resilience": 0.71,
  "affected_regions": ["Sector (37.775, -122.415)"],
  "damaged_graph_data": { ... },
  "damaged_edge_ids": ["e_101"]
}
```

---

## 🧪 Testing

Run pytest suite:
```bash
pytest tests/
```
