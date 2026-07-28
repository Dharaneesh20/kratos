# PROMPTS.md (Expanded)
# Route Resilience AI — Detailed Developer Build Specification
### AgentVerse Multi-Agent Workflow
Theme: Occlusion-Robust Road Extraction & Graph-Theoretic Criticality Analysis

This document expands the original architecture into implementation-ready specs
for each developer: exact repo layout, API contracts, algorithms, libraries,
config, testing, and day-by-day tasks. Each developer section is self-contained
and can be pasted into an AI coding assistant (Claude Code, Cursor, etc.) as a
standalone build prompt.

---

## 0. SHARED CONVENTIONS (apply to all three services)

**Language/runtime:** Python 3.11, FastAPI, Uvicorn (ASGI), Pydantic v2 for schemas.

**Repo-wide standards:**
- Every service exposes `GET /health` → `{"status":"ok","service":"<name>","version":"0.1.0"}`
- Every service exposes `GET /docs` (FastAPI auto Swagger) — keep it on for the demo.
- All inter-agent calls use JSON over HTTP, `Content-Type: application/json`.
- All responses include a top-level `"status"` (`"success"|"error"`) and `"agent"` field.
- Error shape: `{"status":"error","agent":"vision","message":"...","code":"VISION_001"}`
- All services read config from `.env` via `pydantic-settings`; never hardcode ports/URLs.
- Logging: `structlog` or Python `logging` with JSON formatter, one line per agent action, include `request_id` (a UUID passed down the pipeline by the Coordinator).
- All long-running work (segmentation, cuOpt solves) must expose progress via a `/status/{job_id}` polling endpoint AND a WebSocket event (`job_id`, `stage`, `pct`).
- Every repo has: `requirements.txt`, `Dockerfile`, `docker-compose.override.yml` (local), `.env.example`, `README.md`, `tests/`.
- Root `docker-compose.yml` (owned by Developer 3) wires all three services + Redis (for job/queue state) + Postgres (for run history) on one network.

**Shared package (`shared/`):**
- `shared/schemas/` — Pydantic models mirrored across services so the JSON contract can't drift (import these in all three repos as a git submodule or published local package).
- `shared/constants.py` — hazard types enum (`FLOOD`, `EARTHQUAKE`, `BRIDGE_FAILURE`, `ROAD_CLOSURE`), CRS default (`EPSG:4326`).

---

## 1. DEVELOPER 1 — Vision AI Service (`vision-service`)

### 1.1 Purpose
Turn a raw satellite image (or a bounding box + provider) into a validated,
georeferenced road network as GeoJSON, robust to cloud/tree/building occlusion.

### 1.2 Repo layout
```
vision-service/
  app/
    main.py                 # FastAPI app, routers mounted here
    config.py                # pydantic-settings
    routers/
      dataset.py             # /dataset/load
      vision.py               # /vision/process, /vision/status/{job_id}
    services/
      dataset_loader.py       # DeepGlobe/SpaceNet/Sentinel/OSM download+cache
      preprocess.py            # tiling, normalization, augmentation
      segmentation.py          # model load + inference
      skeletonize.py           # mask -> centerline -> graph-ready geometry
      geojson_builder.py       # centerline -> roads.geojson
      validators.py             # GeoTIFF/GeoJSON/CRS validation
    models/
      segformer_wrapper.py
      deeplabv3plus_wrapper.py
    weights/                  # .gitignored, downloaded at build time
    jobs/
      job_store.py             # Redis-backed job status
  tests/
    test_preprocess.py
    test_skeletonize.py
    test_geojson_builder.py
    fixtures/sample_tile.tif
  Dockerfile
  requirements.txt
  .env.example
  README.md
```

### 1.3 Dependencies (`requirements.txt`)
```
fastapi
uvicorn[standard]
pydantic-settings
torch
torchvision
segmentation-models-pytorch      # DeepLabV3+ backbone
transformers                     # SegFormer (nvidia/segformer-b2-finetuned)
albumentations
opencv-python-headless
rasterio
geopandas
shapely
scikit-image                     # skeletonize, morphology
networkx                         # centerline graph cleanup pre-handoff
numpy
redis
python-multipart                 # file uploads
pytest
httpx
```

### 1.4 Dataset Agent — endpoint spec
**`POST /dataset/load`**
Request:
```json
{
  "source": "deepglobe | spacenet | sentinel | osm | upload",
  "bbox": [lon_min, lat_min, lon_max, lat_max],
  "upload_ref": "optional file id if source=upload"
}
```
Response:
```json
{
  "status": "success",
  "agent": "dataset",
  "dataset_id": "ds_8f2a...",
  "tif_path": "/cache/ds_8f2a/scene.tif",
  "crs": "EPSG:4326",
  "resolution_m": 0.5,
  "bbox": [...],
  "cached": true
}
```
Responsibilities in detail:
- **Download**: pull from DeepGlobe/SpaceNet via their public S3/API mirrors, Sentinel via Sentinel Hub / Copernicus API (needs API key in `.env`), OSM via `osmnx` for ground-truth road overlays used in evaluation, not inference.
- **Validate**: confirm valid GeoTIFF (rasterio open succeeds, has CRS, band count ≥3), reproject to `EPSG:4326` if needed via `rasterio.warp`.
- **Cache**: content-hash the bbox+source to a `dataset_id`; store under `/cache/<dataset_id>/`; a Redis key `dataset:<id>` holds metadata with 24h TTL.
- **Failure modes to handle explicitly**: corrupt TIFF, empty bbox intersection, provider timeout (retry 3x with exponential backoff, then surface `DATASET_TIMEOUT`).

### 1.5 Vision Agent — endpoint spec
**`POST /vision/process`**
Request:
```json
{ "dataset_id": "ds_8f2a...", "tile_size": 512, "overlap": 64, "model": "segformer" }
```
Response (job accepted, async):
```json
{ "status": "success", "agent": "vision", "job_id": "job_1a2b", "poll": "/vision/status/job_1a2b" }
```
**`GET /vision/status/{job_id}`**
```json
{
  "status": "success", "agent": "vision", "job_id": "job_1a2b", "stage": "skeletonizing",
  "pct": 72,
  "result": null
}
```
On completion, `result` is populated with the final contract:
```json
{
  "roads_geojson": "/cache/ds_8f2a/roads.geojson",
  "road_mask_png": "/cache/ds_8f2a/road_mask.png",
  "centerline_png": "/cache/ds_8f2a/centerline.png",
  "confidence": 0.94,
  "tile_count": 48,
  "occluded_tile_pct": 12.5
}
```

Pipeline detail:
1. **Preprocess** — `rasterio` windowed read, normalize per-band to `[0,1]` using running dataset stats (not per-tile min/max, to avoid contrast flicker across tiles), tile into `tile_size` with `overlap` px stride so seams can be blended later.
2. **Augment (train-time only, not inference)** — `albumentations`: random occlusion (simulated cloud/shadow patches), rotation, brightness/contrast jitter. This is what makes the model "occlusion-robust" — document this augmentation policy in `README.md` since it's the theme's core claim.
3. **Segmentation** — run `SegFormer` (primary) or `DeepLabV3+` (fallback/ensemble) per tile, binary road/non-road mask, sigmoid threshold 0.5 (configurable). Stitch tiles back with overlap-averaging (feather blend) to avoid seam artifacts.
4. **Skeletonization** — `skimage.morphology.skeletonize` on the binarized full mask → 1px-wide centerlines. Prune spurious branches shorter than a configurable `min_branch_len_px` (default 15px) using a small graph pass (build a temp `networkx` graph of skeleton pixels, drop leaf edges under threshold).
5. **Vectorize → GeoJSON** — trace skeleton pixel paths into polylines (`cv2.findContours` on skeleton or `skan` library), simplify with Douglas-Peucker (`shapely.simplify`, tolerance ~1-2px in geo-units), reproject pixel coords to `EPSG:4326` using the raster's affine transform, write `LineString` features with properties `{road_id, length_m, confidence}`.
6. **Confidence score** — mean pixel-wise sigmoid probability along each extracted centerline; overall `confidence` in the response = weighted average by road length.

### 1.6 Output contract (what Graph Agent expects)
`roads.geojson` — `FeatureCollection` of `LineString`s, each with:
```json
{
  "type": "Feature",
  "geometry": {"type": "LineString", "coordinates": [[lon,lat], ...]},
  "properties": {"road_id": "r_001", "length_m": 342.1, "confidence": 0.91, "road_class": "unknown"}
}
```

### 1.7 Testing
- Unit test skeletonization on a synthetic mask (draw known lines with `cv2`, assert extracted length within 5% of ground truth).
- Unit test GeoJSON builder coordinate reprojection against a known affine transform.
- Integration test: feed `fixtures/sample_tile.tif` through the full `/vision/process` pipeline, assert `roads.geojson` is valid via `geopandas.read_file` and has ≥1 feature.

### 1.8 Day-by-day
**Day 1:** dataset loader (upload + one real provider working end-to-end), FastAPI skeleton, model wrapper loading pretrained weights, tiling+normalize pipeline, basic inference on one tile.
**Day 2:** full-image stitching, skeletonization + pruning, GeoJSON vectorization, confidence scoring, async job/status endpoints, write tests, Dockerize.
**Day 3:** integration with Coordinator, latency optimization (batch tile inference on GPU), bug fixes from Developer 2's ingestion, demo dry-run with real occluded imagery.

---

## 2. DEVELOPER 2 — Graph Intelligence Service (`graph-service`)

### 2.1 Purpose
Turn `roads.geojson` into a routable, analyzable network graph; compute
criticality/centrality; run disaster stress simulations; produce a resilience score.

### 2.2 Repo layout
```
graph-service/
  app/
    main.py
    config.py
    routers/
      graph.py                # /graph/build
      simulation.py            # /simulation/run
    services/
      graph_builder.py          # geojson -> networkx graph
      centrality.py              # betweenness/closeness/degree, bridge nodes
      criticality.py              # critical_nodes.json logic
      simulation.py                # hazard removal + resilience recompute
      resilience_score.py
    jobs/job_store.py
  tests/
    test_graph_builder.py
    test_centrality.py
    test_simulation.py
    fixtures/sample_roads.geojson
  Dockerfile
  requirements.txt
  .env.example
  README.md
```

### 2.3 Dependencies
```
fastapi
uvicorn[standard]
pydantic-settings
networkx
geopandas
shapely
pyproj
numpy
scipy
redis
pytest
httpx
```

### 2.4 Graph Agent — endpoint spec
**`POST /graph/build`**
Request:
```json
{ "roads_geojson_path": "/cache/ds_8f2a/roads.geojson", "snap_tolerance_m": 5.0 }
```
Response:
```json
{
  "status": "success", "agent": "graph",
  "nodes": 1543, "edges": 2012,
  "graph_json_path": "/cache/ds_8f2a/road_graph.json",
  "critical_nodes_path": "/cache/ds_8f2a/critical_nodes.json"
}
```

Pipeline detail:
1. **Node/edge extraction** — for each `LineString`, endpoints become candidate nodes; snap nearby endpoints within `snap_tolerance_m` (using a KD-tree via `scipy.spatial.cKDTree` on projected coords, e.g. `EPSG:3857`) into a single node to merge near-duplicate intersections from noisy vision output.
2. **Edge weights** — `length_m` (haversine or projected length), `travel_cost` = `length_m / assumed_speed_kmh` where `assumed_speed_kmh` defaults by inferred road class (fallback: flat 30 km/h if unknown).
3. **Graph object** — build as `networkx.Graph` (undirected, since satellite extraction doesn't reliably give direction) with node attrs `{lat, lon}` and edge attrs `{length_m, travel_cost, road_id, confidence}`. Serialize to `road_graph.json` via `networkx.node_link_data`.
4. **Bridge detection** — `networkx.bridges(G)` → edges whose removal disconnects the graph; flag their endpoint nodes as `is_bridge_adjacent: true`.
5. **Connectivity** — `networkx.number_connected_components(G)`, largest component size, isolated-node count.
6. **Shortest path utility** — expose an internal helper `shortest_path(G, src, dst, weight="travel_cost")` used by both simulation and later by Planning Agent for pre-checks.
7. **Centrality**:
   - Betweenness: `networkx.betweenness_centrality(G, weight="travel_cost", normalized=True)` — this is the primary "criticality" signal (nodes/edges many shortest paths pass through).
   - Closeness: `networkx.closeness_centrality(G, distance="travel_cost")`.
   - Degree: `networkx.degree_centrality(G)`.
   - Combine into a single `criticality_score = 0.6*betweenness + 0.25*closeness + 0.15*degree` (weights configurable in `.env`) — document this formula clearly since judges will ask "why is this node critical."
8. **`critical_nodes.json`** — top-N nodes (default N=20 or top 5%) sorted by `criticality_score`, each with `{node_id, lat, lon, criticality_score, is_bridge_adjacent, betweenness, closeness, degree}`.

### 2.5 Simulation Agent — endpoint spec
**`POST /simulation/run`**
Request:
```json
{
  "graph_json_path": "/cache/ds_8f2a/road_graph.json",
  "hazard_type": "FLOOD | EARTHQUAKE | BRIDGE_FAILURE | ROAD_CLOSURE",
  "affected_node_ids": ["n_012","n_045"],
  "affected_edge_ids": ["e_101"],
  "severity": 0.8
}
```
Response:
```json
{
  "status": "success", "agent": "simulation",
  "simulation_json_path": "/cache/ds_8f2a/simulation.json",
  "travel_delay": 42,
  "resilience": 0.71,
  "affected_regions": ["region_a"]
}
```
Pipeline detail:
1. **Apply hazard** — remove `affected_node_ids`/`affected_edge_ids` from a *copy* of the graph (never mutate the base graph; keep `G_baseline` intact for comparisons).
2. **Recalculate network** — recompute connected components on `G_damaged`.
3. **Connectivity impact** — for a sample of origin-destination node pairs (default: 50 random pairs, or all pairs if graph < 200 nodes), compute shortest path travel cost on `G_baseline` vs `G_damaged`; unreachable pairs get a penalty cost (e.g. 5x the graph's max finite path cost).
4. **`travel_delay`** — mean percentage increase in travel cost across all previously-reachable OD pairs that remain reachable.
5. **`resilience` score** — `(largest_connected_component_size_after / total_nodes) * (reachable_pairs_after / reachable_pairs_before)`, clamped to `[0,1]`. Document formula in README.
6. **`affected_regions`** — cluster newly-disconnected nodes geographically (simple DBSCAN via `sklearn.cluster.DBSCAN` on lat/lon, or connected-component grouping) and label by centroid.
7. Support **hazard presets**: `FLOOD` = remove all edges/nodes within a supplied polygon or below an elevation threshold if DEM available; `EARTHQUAKE` = randomly remove edges weighted by a fragility curve tied to `severity`; `BRIDGE_FAILURE` = remove specific bridge-flagged edges; `ROAD_CLOSURE` = direct user-specified edge removal.

### 2.6 Testing
- Build a small synthetic road network (grid graph) as fixture, assert bridge detection finds the single connecting edge when the grid is split into two halves joined by one edge.
- Assert `resilience` returns `1.0` when hazard removes nothing, and drops when a bridge is removed.
- Assert `critical_nodes.json` output count matches configured top-N.

### 2.7 Day-by-day
**Day 1:** GeoJSON → NetworkX graph builder with node snapping, `road_graph.json` serialization, FastAPI skeleton, basic connectivity checks.
**Day 2:** full centrality suite, `critical_nodes.json`, simulation engine (all 4 hazard types), resilience formula, region clustering, tests.
**Day 3:** integration with Vision Agent output (handle real noisy geometry, not just fixtures), performance tuning for 1500+ node graphs (cache centrality results, avoid recompute on every simulation call), bug fixes, demo dry-run.

---

## 3. DEVELOPER 3 — AgentVerse Platform + NVIDIA NIM + cuOpt + Dashboard (`agentverse-platform`)

### 3.1 Scope
This is the largest surface area: Coordinator, Memory, Planning (NIM+cuOpt),
Report (NIM), auth, agent monitor, and the React dashboard.

### 3.2 Repo layout
```
agentverse-platform/
  backend/
    app/
      main.py
      config.py
      auth/
        routes.py               # login/signup, JWT issuance
        deps.py                  # get_current_user dependency
      coordinator/
        agent.py                  # orchestration state machine
        routes.py                  # POST /workflow/run, GET /workflow/{id}
        retry.py                    # retry/backoff policy
      memory/
        agent.py                    # run history, embeddings for past runs
        routes.py
      planning/
        nim_client.py                 # NVIDIA NIM chat/explanation calls
        cuopt_client.py                # NVIDIA cuOpt routing calls
        routes.py                      # POST /planning/generate
      report/
        nim_client.py
        pdf_builder.py                  # ReportLab
        routes.py                        # POST /report/create
      websocket/
        manager.py                        # connection registry, broadcast
      db/
        models.py                          # SQLAlchemy: runs, agent_logs, users
        session.py
    tests/
    Dockerfile
    requirements.txt
    .env.example
  frontend/
    src/
      pages/
        Dashboard.tsx
        RunDetail.tsx
        Login.tsx
      components/
        MapView.tsx                # Leaflet map: roads, critical nodes, heatmap
        AgentMonitor.tsx             # live agent status via WebSocket
        ResilienceGauge.tsx
        RoutePanel.tsx                # evacuation/repair route list
        ReportViewer.tsx
        UploadPanel.tsx
      hooks/
        useWebSocket.ts
        useWorkflow.ts
      api/client.ts
    package.json
    vite.config.ts
  docker-compose.yml               # root-level, wires all 3 services + redis + postgres
  .env.example
  README.md
```

### 3.3 Dependencies (backend)
```
fastapi
uvicorn[standard]
pydantic-settings
sqlalchemy
psycopg2-binary
redis
python-jose[cryptography]        # JWT
passlib[bcrypt]
httpx
reportlab
websockets
pytest
```
Dependencies (frontend): `react`, `react-router-dom`, `leaflet`, `react-leaflet`, `recharts` or `chart.js`, `axios`, `zustand` (lightweight state for workflow/job status), `tailwindcss`.

### 3.4 Coordinator Agent
**Purpose:** project manager — no LLM, pure orchestration logic.

**`POST /workflow/run`**
Request:
```json
{ "dataset_source": "upload", "upload_ref": "file_123", "hazard_type": "FLOOD", "severity": 0.8 }
```
Response: `{"status":"success","agent":"coordinator","workflow_id":"wf_9c1d","poll":"/workflow/wf_9c1d"}`

Responsibilities in detail:
- Implement as an explicit **state machine** (`DATASET → VISION → GRAPH → SIMULATION → PLANNING → REPORT → DONE`, plus `FAILED`), persisted in Postgres (`runs` table: `id, state, current_stage, created_at, updated_at, error`).
- Each stage transition: call the relevant agent's REST endpoint via `httpx.AsyncClient`, poll its `/status/{job_id}` if async, on success write to `agent_logs` table and broadcast a WebSocket event `{workflow_id, stage, status, pct}` to the frontend.
- **Retry policy**: up to 3 retries per stage with exponential backoff (1s, 4s, 16s); on final failure, mark workflow `FAILED`, store the error, broadcast a failure event — do not silently hang.
- **Timeouts**: per-stage timeout configurable in `.env` (default Vision=300s, Graph=60s, Simulation=60s, Planning=120s, Report=60s).
- **Idempotency**: re-running `/workflow/run` with the same `upload_ref`+`hazard_type` should reuse cached intermediate artifacts (dataset_id, roads_geojson) rather than recomputing from scratch — check Redis cache before calling Vision/Graph again.

### 3.5 Memory Agent
**Purpose:** stores run history so the dashboard can show past runs and the Planning Agent can reference prior similar scenarios.
**`GET /memory/runs`** — paginated list of past `workflow_id`s with summary stats (resilience score, hazard type, timestamp).
**`GET /memory/runs/{workflow_id}`** — full artifact bundle for one run.
Implementation: Postgres table `runs` (already used by Coordinator) is the source of truth; Memory Agent is a thin read layer + optional simple similarity lookup (e.g., match by `hazard_type` + nearest resilience score) to let Planning Agent say "this is similar to a prior scenario."

### 3.6 Planning Agent — the intelligent core
**`POST /planning/generate`**
Request:
```json
{
  "road_graph_path": "...", "critical_nodes_path": "...", "simulation_json_path": "...",
  "hazard_type": "FLOOD", "safe_zones": [{"node_id":"n_200","label":"Hospital A"}]
}
```
Response:
```json
{
  "status": "success", "agent": "planning",
  "repair_priority": [{"node_id":"n_012","reason":"...","priority":1}],
  "evacuation_routes": [{"from":"n_034","to":"n_200","path":["n_034","n_050","n_200"],"eta_min":14,"vehicle":"ambulance"}],
  "recommendations": ["..."]
}
```
**NVIDIA cuOpt usage (routing/optimization):**
- Build a cuOpt request from the *damaged* graph: cost matrix from edge `travel_cost`, vehicle set (ambulances/emergency vehicles with capacity/count from config), pickup points (affected regions' centroid nodes) and drop points (`safe_zones`).
- Call cuOpt's routing solve endpoint (self-hosted NIM microservice or NVIDIA-hosted API per `.env` `CUOPT_ENDPOINT`), parse the optimized route assignment, map solved node sequences back to lat/lon via the graph's node attributes for the dashboard to draw.
- Fallback: if cuOpt is unreachable during dev/demo, fall back to `networkx` weighted shortest-path multi-route computation so the demo never blocks on external service availability — log clearly that fallback mode is active.

**NVIDIA NIM usage (explanation/reasoning):**
- `nim_client.py` wraps calls to a hosted LLM NIM endpoint (`.env`: `NIM_ENDPOINT`, `NIM_MODEL`).
- Prompt template (system + structured input) that feeds: critical node stats, simulation resilience delta, bridge status → asks the model to (a) explain in plain language *why* each top critical node/bridge matters, (b) rank repair priority with a one-line justification each, (c) draft 3-5 government-facing recommendations.
- **Important:** always pass the actual computed numbers (centrality, resilience, delay) into the prompt as grounding data — the LLM explains and prioritizes reasoning, it does not invent numbers. Response must be requested as strict JSON (see `structured_outputs` pattern) and validated against a Pydantic schema before use; on schema-validation failure, retry once with a stricter "return ONLY JSON" reminder, then fall back to a templated (non-LLM) explanation so the pipeline never breaks the demo.

### 3.7 Report Agent
**`POST /report/create`**
Request: `{"workflow_id":"wf_9c1d"}` (pulls everything else from Memory/DB)
Response: `{"status":"success","agent":"report","summary":"...","pdf":"/reports/wf_9c1d.pdf","csv":"/reports/wf_9c1d.csv"}`
Detail:
- Use NIM to draft: Executive Summary, Risk Analysis narrative, Repair Priority narrative, Travel Delay narrative, Critical Roads narrative — same grounding-data pattern as Planning Agent (numbers in, prose out).
- **PDF** via `ReportLab`: title page, map screenshot placeholder (frontend can post a captured PNG of the Leaflet map to embed), tables for critical nodes/repair priority/evacuation routes, resilience score gauge as a simple drawn chart.
- **CSV**: flat export of critical nodes + repair priority for judges/analysts to open in Excel.
- **JSON**: full machine-readable bundle (`summary.json`) — same data as PDF, for the dashboard/API consumers.

### 3.8 Dashboard (React + Leaflet)
- `UploadPanel.tsx` — image/bbox upload, hazard type + severity selector, "Run Analysis" button → calls `/workflow/run`.
- `AgentMonitor.tsx` — subscribes to WebSocket, renders a 7-stage pipeline strip (Coordinator→Dataset→Vision→Graph→Simulation→Planning→Report) with live status per stage (pending/running/done/failed) and % progress bars.
- `MapView.tsx` (Leaflet) — layers: base roads (from `roads.geojson`), critical nodes (sized/colored by `criticality_score`), heatmap of `betweenness_centrality`, hazard-affected region overlay, evacuation/repair route polylines (distinct color per route, animated dash for "recommended").
- `ResilienceGauge.tsx` — before/after resilience score as a radial gauge + travel delay % as a stat card.
- `RoutePanel.tsx` — list of evacuation routes with ETA and vehicle type, clicking one highlights it on the map.
- `ReportViewer.tsx` — embed/preview the generated PDF, download buttons for PDF/CSV/JSON.
- Auth: simple JWT login screen gating the dashboard (`Login.tsx`), token stored in memory/zustand store (not localStorage per artifact rules if this were rendered as an artifact — but this is a real deployed app, so normal browser storage is fine here since it's outside the Claude artifact sandbox).

### 3.9 Testing
- Backend: test the Coordinator state machine transitions with mocked httpx responses for each downstream agent (success path + one forced failure to verify retry logic).
- Test Planning Agent's JSON-schema validation fallback path by mocking a malformed NIM response.
- Frontend: component test that `AgentMonitor` reflects WebSocket events correctly (React Testing Library + mocked socket).

### 3.10 Day-by-day
**Day 1:** Coordinator skeleton + Postgres models, mock downstream responses so frontend isn't blocked, Auth (login/JWT), Dashboard shell + routing, `UploadPanel`.
**Day 2:** wire real NVIDIA NIM + cuOpt clients (with fallback paths), Report Agent (PDF/CSV/JSON), `MapView` with Leaflet layers, `AgentMonitor` live via WebSocket, `ResilienceGauge`, `RoutePanel`.
**Day 3:** full integration against real Vision/Graph services, error-state UI polish, PDF report visual polish, root `docker-compose.yml` finalized, end-to-end rehearsal of the Demo Flow below.

---

## 4. INTEGRATION CHECKLIST (Day 3, all developers)

1. Bring up `docker-compose.yml` from repo root — all 3 services + Redis + Postgres healthy on `/health`.
2. Run the full demo flow against one real occluded satellite tile end-to-end, timing each stage.
3. Verify JSON contract fields match exactly what the next agent expects (use the `shared/schemas/` Pydantic models to validate at each hop in a quick integration test script).
4. Confirm WebSocket events reach the dashboard for every stage, including a forced-failure test (kill Vision Agent mid-run) to confirm Coordinator retry/failure UI works.
5. Generate one full PDF report and sanity-check numbers match what's shown on the dashboard.

---

## 5. DEMO FLOW (unchanged, for reference)

Judge uploads satellite image → Vision Agent extracts roads → Graph Agent builds
network → Simulation Agent simulates flood → Planning Agent uses NVIDIA cuOpt to
generate the optimal evacuation route → Planning Agent uses NVIDIA NIM to explain
why → Report Agent generates a Government Disaster Report → Dashboard visualizes
roads, critical nodes, heatmaps, alternative routes, travel delays, resilience
index, and the PDF report.
