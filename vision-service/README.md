# vision-service

Extracts road networks from satellite imagery, robust to partial occlusion
(cloud cover / tree canopy). First service in the KRATOS pipeline --
its GeoJSON output feeds graph-service.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Dataset

Dataset fetching is automatic via `kagglehub` -- no manual download or
`~/.kaggle/kaggle.json` setup required for the dataset itself (kagglehub
handles auth on first call, prompting for a Kaggle token if needed).

```python
import kagglehub
path = kagglehub.dataset_download("balraj98/deepglobe-road-extraction-dataset")
```

`app/dataset.py` and `app/model.py` call this automatically the first time
they need data: they first check `vision-service/data/train/` for a manual
copy, and if that's empty they fall back to `app/download.py`, which
downloads (or reuses the kagglehub cache) and auto-locates the folder
containing `*_sat.jpg` / `*_mask.png` pairs -- so it works whether Kaggle's
zip nests the `train/` folder or not.

To pre-warm the cache / see the resolved path without training:

```bash
python -m app.download
```

If you'd rather use a manual copy, drop it at:

```
vision-service/data/train/1_sat.jpg
vision-service/data/train/1_mask.png
...
```

and it'll be preferred over the kagglehub download automatically.

## Train

```bash
python -m app.model
```

Saves the best checkpoint to `weights/roadnet.pt`.

## Run the service

```bash
uvicorn app.main:app --reload --port 8001
```

## Test

```bash
curl -X POST -F "file=@data/train/1_sat.jpg" http://localhost:8001/vision/process
curl http://localhost:8001/health
```

## Output contract

`POST /vision/process` returns:

```json
{
  "road_mask_png_base64": "...",
  "roads_geojson": { "type": "FeatureCollection", "features": [...] },
  "image_size": 512
}
```

`roads_geojson` is what graph-service consumes.
