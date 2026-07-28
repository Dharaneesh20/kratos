from typing import Any, Dict

from pydantic import BaseModel


class VisionResponse(BaseModel):
    road_mask_png_base64: str
    roads_geojson: Dict[str, Any]
    image_size: int


class HealthResponse(BaseModel):
    status: str
    service: str
