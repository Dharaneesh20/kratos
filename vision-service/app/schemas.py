from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    agent: str
    message: str
    code: str


class UploadResponse(BaseModel):
    status: Literal["success"] = "success"
    agent: Literal["dataset"] = "dataset"
    upload_ref: str


class DatasetLoadRequest(BaseModel):
    source: Literal["deepglobe", "spacenet", "sentinel", "osm", "upload"]
    bbox: Optional[List[float]] = Field(default=None, min_length=4, max_length=4)
    upload_ref: Optional[str] = None


class DatasetLoadResponse(BaseModel):
    status: Literal["success"] = "success"
    agent: Literal["dataset"] = "dataset"
    dataset_id: str
    tif_path: str
    crs: str
    resolution_m: float
    bbox: List[float]
    cached: bool


class VisionProcessRequest(BaseModel):
    dataset_id: str
    tile_size: int = 512
    overlap: int = 64
    model: Literal["segformer", "deeplabv3plus"] = "segformer"


class VisionResult(BaseModel):
    roads_geojson: str
    road_mask_png: str
    centerline_png: str
    confidence: float
    tile_count: int
    occluded_tile_pct: float


class VisionProcessAcceptedResponse(BaseModel):
    status: Literal["success"] = "success"
    agent: Literal["vision"] = "vision"
    job_id: str
    poll: str


class VisionStatusResponse(BaseModel):
    status: Literal["success", "error"]
    agent: Literal["vision"] = "vision"
    job_id: str
    stage: str
    pct: int
    result: Optional[VisionResult] = None
    error: Optional[Dict[str, Any]] = None
