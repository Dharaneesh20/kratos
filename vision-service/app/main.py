from fastapi import FastAPI, HTTPException, UploadFile

from app.config import settings
from app.schemas import HealthResponse, VisionResponse

app = FastAPI(title="vision-service")


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.post("/vision/process", response_model=VisionResponse)
async def process(file: UploadFile):
    """
    Accepts a satellite image tile, returns:
      - road_mask_png_base64: predicted binary road mask (PNG, base64)
      - roads_geojson: extracted road centerlines as GeoJSON LineStrings

    This is the output contract consumed by graph-service.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="file must be an image")

    # Imported lazily so the API boots even before a model checkpoint exists
    # or torch/segmentation deps are installed in a lightweight dev shell.
    from app.inference import run_inference

    image_bytes = await file.read()
    try:
        result = run_inference(image_bytes)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return result
