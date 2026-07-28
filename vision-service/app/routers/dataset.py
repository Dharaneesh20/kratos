import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.logging_utils import log_event
from app.schemas import DatasetLoadRequest, UploadResponse
from app.services.dataset_loader import DatasetLoadError, load_dataset, save_upload
from app.services.validators import InvalidGeoTiffError

router = APIRouter(prefix="/dataset", tags=["dataset"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "agent": "dataset",
                "message": "missing filename",
                "code": "DATASET_BAD_UPLOAD",
            },
        )
    file_bytes = await file.read()
    suffix = ".tif"
    if "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    upload_ref = save_upload(file_bytes=file_bytes, extension=suffix)
    log_event(logger, "dataset_upload_saved", upload_ref=upload_ref, filename=file.filename)
    return {"status": "success", "agent": "dataset", "upload_ref": upload_ref}


@router.post("/load")
async def dataset_load(req: DatasetLoadRequest):
    try:
        payload = load_dataset(req.source, req.bbox, req.upload_ref)
    except InvalidGeoTiffError as e:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "agent": "dataset", "message": e.message, "code": e.code},
        )
    except DatasetLoadError as e:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "agent": "dataset", "message": e.message, "code": e.code},
        )

    log_event(
        logger,
        "dataset_loaded",
        source=req.source,
        dataset_id=payload["dataset_id"],
        cached=payload["cached"],
    )
    return {"status": "success", "agent": "dataset", **payload}
