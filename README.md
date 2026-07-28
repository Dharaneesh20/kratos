# KRATOS - Knowledge-driven Road Analysis for Terrain Occlusion & Security

AgentVerse multi-agent workflow for occlusion-robust road extraction and
graph-theoretic route criticality analysis.

## Current Build Status

Short answer: the implemented work is concentrated in `vision-service`.
`graph-service`, the coordinator/backend, the frontend, and root orchestration
are still scaffolds.

| Area | Status | Notes |
| --- | --- | --- |
| `vision-service` | Mostly complete | Main FastAPI service, dataset upload/load, Sentinel load path, async vision jobs, status polling, WebSocket status, request-id JSON logging, tiled segmentation, skeleton pruning, GeoJSON output, Dockerfile, local compose override, env example, and tests are present. |
| `graph-service` | Scaffold only | `app/main.py` only creates a FastAPI app. Graph ingestion, criticality analysis, hazard modeling, endpoints, tests, and Docker integration still need implementation. |
| `agentverse-platform/backend` | Scaffold only | `app/main.py` only creates a FastAPI app. Coordinator pipeline, request ID propagation, run history, service orchestration, and API contracts still need implementation. |
| `agentverse-platform/frontend` | Scaffold only | Vite project files exist, but the demo UI/workflow is not implemented. |
| `shared` | Minimal | `constants.py` defines hazard types and default CRS. Shared Pydantic schemas are not implemented yet. |
| Root Docker Compose | Not complete | `agentverse-platform/docker-compose.yml` only contains `version: "3.9"` and does not wire services, Redis, or Postgres yet. |

## Vision Service Coverage

Implemented:

- `GET /health`
- `POST /dataset/upload`
- `POST /dataset/load`
- `POST /vision/process`
- `GET /vision/status/{job_id}`
- `WS /vision/ws/status/{job_id}`
- `.env`-driven config via `pydantic-settings`
- Upload-backed dataset loading with GeoTIFF validation and CRS reprojection
- DeepGlobe sample-to-GeoTIFF and configured SpaceNet GeoTIFF loading paths
- Sentinel Hub Process API loading path
- Redis-backed job/dataset cache with in-memory fallback
- Request-id middleware and one-line JSON action logs
- Top-level API error response bodies for HTTP and validation errors
- Tiled raster preprocessing with dataset-level normalization
- Train-time augmentation policy for occlusion robustness
- SegFormer primary model wrapper and DeepLabV3+ fallback wrapper
- Overlap-averaged tile stitching
- Skeletonization and short-branch pruning
- Skeleton-to-GeoJSON vectorization with `road_id`, `length_m`, `confidence`, and `road_class`
- Unit/integration tests for preprocessing, skeletonization, GeoJSON building, pipeline behavior, and mocked Sentinel loading

Known Vision-specific boundaries against the expanded `PROMPTS.md` spec:

- DeepGlobe is represented as a training-data source converted to GeoTIFF rather than a true bbox-addressable imagery API; OSM is vector ground truth support rather than raster inference input.
- Model weights are not provided in the repo. The wrappers load configured local checkpoints when present, otherwise they rely on upstream pretrained defaults where applicable.
- The exact requested service layout is approximated, but some legacy files remain directly under `vision-service/app/`.

## Local Service Layout

```text
vision-service/
  app/
    main.py
    config.py
    routers/
    services/
    models/
    jobs/
  tests/
  Dockerfile
  requirements.txt
  .env.example
  README.md

graph-service/
  app/main.py

agentverse-platform/
  backend/app/main.py
  frontend/
  docker-compose.yml

shared/
  constants.py
```

## Next Build Priorities

1. Add shared Pydantic schemas under `shared/schemas/` and import them across services.
2. Build `graph-service` ingestion and graph criticality endpoints.
3. Build the coordinator backend pipeline and root Docker Compose with Redis and Postgres.
