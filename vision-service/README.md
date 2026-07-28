# vision-service

Vision agent for occlusion-robust road extraction. It loads a dataset scene,
runs tiled segmentation, skeletonizes and prunes centerlines, and outputs
GeoJSON for the graph service.

## Endpoints

- `GET /health`
- `POST /dataset/upload`
- `POST /dataset/load`
- `POST /vision/process`
- `GET /vision/status/{job_id}`
- `WS /vision/ws/status/{job_id}`

All API responses include top-level `status` and `agent` fields. Errors use:

```json
{"status":"error","agent":"vision","message":"...","code":"VISION_001"}
```

Dataset errors use the same shape with `agent: "dataset"`.

## Local Run

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

For Docker-based local development:

```bash
docker compose -f docker-compose.override.yml up --build
```

## Typical Flow

1. Upload a GeoTIFF:

```bash
curl -X POST "http://localhost:8001/dataset/upload" -F "file=@scene.tif"
```

2. Load dataset metadata:

```bash
curl -X POST "http://localhost:8001/dataset/load" \
  -H "Content-Type: application/json" \
  -d '{"source":"upload","upload_ref":"file_xxx.tif"}'
```

3. Start async processing:

```bash
curl -X POST "http://localhost:8001/vision/process" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"ds_xxx","tile_size":512,"overlap":64,"model":"segformer"}'
```

4. Poll status:

```bash
curl "http://localhost:8001/vision/status/job_xxx"
```

## Sentinel BBox Load

Minimal real Sentinel Hub integration is wired for `source=sentinel`.

Required env vars:

- `SENTINEL_HUB_CLIENT_ID`
- `SENTINEL_HUB_CLIENT_SECRET`

Example request:

```bash
curl -X POST "http://localhost:8001/dataset/load" \
  -H "Content-Type: application/json" \
  -d '{
    "source":"sentinel",
    "bbox":[77.55,12.90,77.70,13.05]
  }'
```

The service requests a GeoTIFF from Sentinel Process API and stores it under
`cache/<dataset_id>/scene.tif`.

## Occlusion-Robust Augmentation Policy

The inference path never mutates imagery. Train-time augmentation is defined in
`app/services/preprocess.py` and applies random rotations, flips,
brightness/contrast jitter, and coarse dropout blocks that simulate cloud,
shadow, tree, or building occlusion. This is the intended training policy behind
the service's occlusion-robust road extraction claim.

## Logging and Request IDs

The FastAPI app installs middleware that reads `x-request-id` from incoming
requests, or creates a UUID-backed request id when it is missing. Service actions
emit one-line JSON logs with the request id, route, status code, timing, job id,
dataset id, and relevant stage metadata.

## Output Contract

Completed status includes:

```json
{
  "roads_geojson": "cache/ds_xxx/roads.geojson",
  "road_mask_png": "cache/ds_xxx/road_mask.png",
  "centerline_png": "cache/ds_xxx/centerline.png",
  "confidence": 0.94,
  "tile_count": 48,
  "occluded_tile_pct": 12.5
}
```

`roads.geojson` features include `road_id`, `length_m`, `confidence`, and `road_class`.

## Tests

The test suite covers:

- tiled preprocessing and dataset-level normalization
- skeletonization and short-branch pruning
- GeoJSON coordinate reprojection and road properties
- upload/load/process/status integration
- mocked Sentinel Hub `source=sentinel` loading without external network access
- mocked DeepGlobe and SpaceNet provider loading paths

Run with:

```bash
pytest
```

## Provider Notes

`source=upload` and `source=sentinel` are the primary end-to-end dataset loading
paths. `source=deepglobe` resolves the local or Kaggle-cached DeepGlobe training
set and converts one satellite tile into an EPSG:4326 GeoTIFF scene, using the
provided bbox when present. `source=spacenet` downloads a configured GeoTIFF from
`SPACENET_SAMPLE_TIF_URL`. OSM is used for ground-truth vector overlays through
`fetch_osm_ground_truth`; it is not a raster inference source.
