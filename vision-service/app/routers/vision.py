import asyncio
import base64
import json
import logging
import os
from typing import Optional

import cv2
import numpy as np
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect

from app.config import settings
from app.jobs.job_store import create_job, get_job, update_job
from app.logging_utils import log_event, request_id_ctx
from app.schemas import VisionProcessRequest
from app.services.dataset_loader import get_dataset_metadata, load_dataset, save_upload
from app.services.geojson_builder import build_geojson, weighted_confidence
from app.services.segmentation import segment_scene
from app.services.skeletonize import mask_to_pruned_skeleton

router = APIRouter(prefix="/vision", tags=["vision"])
logger = logging.getLogger(__name__)


def process_scene_pipeline(tif_path: str, model_name: str = "segformer", tile_size: int = 512, overlap: int = 64, on_progress=None):
    out_dir = os.path.dirname(tif_path)
    prob_map, tile_count, occluded_tile_pct = segment_scene(
        tif_path=tif_path,
        model_name=model_name,
        tile_size=tile_size,
        overlap=overlap,
        on_progress=on_progress,
    )
    skeleton = mask_to_pruned_skeleton(prob_map)
    feature_collection = build_geojson(skeleton=skeleton, prob_map=prob_map, tif_path=tif_path)

    roads_geojson_path = os.path.join(out_dir, "roads.geojson")
    road_mask_png_path = os.path.join(out_dir, "road_mask.png")
    centerline_png_path = os.path.join(out_dir, "centerline.png")

    with open(roads_geojson_path, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f)

    binary_mask = (prob_map > settings.MASK_THRESHOLD).astype(np.uint8) * 255
    cv2.imwrite(road_mask_png_path, binary_mask)
    cv2.imwrite(centerline_png_path, skeleton.astype(np.uint8) * 255)

    _, encoded_img = cv2.imencode(".png", binary_mask)
    road_mask_base64 = base64.b64encode(encoded_img).decode("utf-8")

    return {
        "roads_geojson": feature_collection,
        "roads_geojson_path": roads_geojson_path,
        "road_mask_png": road_mask_png_path,
        "road_mask_png_base64": road_mask_base64,
        "centerline_png": centerline_png_path,
        "confidence": weighted_confidence(feature_collection),
        "tile_count": tile_count,
        "occluded_tile_pct": round(float(occluded_tile_pct), 2),
    }


def _run_vision_job(
    job_id: str, dataset_id: str, tile_size: int, overlap: int, model: str, request_id: str
) -> None:
    token = request_id_ctx.set(request_id)
    log_event(logger, "vision_job_started", job_id=job_id, dataset_id=dataset_id, model=model)
    meta = get_dataset_metadata(dataset_id)
    if meta is None:
        update_job(
            job_id,
            stage="failed",
            error={
                "status": "error",
                "agent": "vision",
                "message": f"dataset not found: {dataset_id}",
                "code": "VISION_404",
            },
        )
        request_id_ctx.reset(token)
        return

    tif_path = meta["tif_path"]

    def on_tile_progress(done: int, total: int) -> None:
        pct = int(5 + (done / max(total, 1)) * 65)
        update_job(job_id, stage="segmenting", pct=min(pct, 70), result=None)

    try:
        update_job(job_id, stage="preprocessing", pct=5, result=None)
        result = process_scene_pipeline(
            tif_path=tif_path,
            model_name=model,
            tile_size=tile_size,
            overlap=overlap,
            on_progress=on_tile_progress,
        )

        update_job(job_id, stage="completed", pct=100, result=result, error=None)
        log_event(
            logger,
            "vision_job_completed",
            job_id=job_id,
            dataset_id=dataset_id,
            confidence=result["confidence"],
            tile_count=result["tile_count"],
        )
    except Exception as e:
        update_job(
            job_id,
            stage="failed",
            error={
                "status": "error",
                "agent": "vision",
                "message": str(e),
                "code": "VISION_001",
            },
        )
        log_event(logger, "vision_job_failed", job_id=job_id, dataset_id=dataset_id, error=str(e))
    finally:
        request_id_ctx.reset(token)


@router.post("/process")
async def process(
    request: Request,
    background_tasks: BackgroundTasks,
):
    content_type = request.headers.get("content-type", "")
    dataset_id = None
    tile_size = 512
    overlap = 64
    model = "segformer"

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
            file_bytes = await uploaded_file.read()
            suffix = ".tif"
            if "." in uploaded_file.filename:
                suffix = "." + uploaded_file.filename.rsplit(".", 1)[-1].lower()
            upload_ref = save_upload(file_bytes=file_bytes, extension=suffix)
            meta = load_dataset(source="upload", upload_ref=upload_ref)
            result = process_scene_pipeline(
                meta["tif_path"],
                model_name=str(form.get("model", "segformer")),
                tile_size=int(form.get("tile_size", 512)),
                overlap=int(form.get("overlap", 64)),
            )
            return {
                "status": "success",
                "agent": "vision",
                "dataset_id": meta["dataset_id"],
                **result,
            }
        dataset_id = str(form.get("dataset_id")) if form.get("dataset_id") else None
        tile_size = int(form.get("tile_size", 512))
        overlap = int(form.get("overlap", 64))
        model = str(form.get("model", "segformer"))
    else:
        body = await request.json()
        req = VisionProcessRequest(**body)
        dataset_id = req.dataset_id
        tile_size = req.tile_size
        overlap = req.overlap
        model = req.model

    if not dataset_id:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "agent": "vision",
                "message": "Either image file upload or dataset_id must be provided",
                "code": "VISION_400",
            },
        )

    meta = get_dataset_metadata(dataset_id)
    if meta is None:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "agent": "vision",
                "message": f"dataset_id not found: {dataset_id}",
                "code": "VISION_404",
            },
        )

    job_id = create_job(initial_stage="queued")
    log_event(logger, "vision_job_queued", job_id=job_id, dataset_id=dataset_id)
    request_id = request_id_ctx.get()

    background_tasks.add_task(
        _run_vision_job,
        job_id,
        dataset_id,
        tile_size,
        overlap,
        model,
        request_id,
    )
    return {
        "status": "success",
        "agent": "vision",
        "job_id": job_id,
        "poll": f"/vision/status/{job_id}",
    }


@router.get("/status/{job_id}")
async def status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "agent": "vision",
                "message": f"job not found: {job_id}",
                "code": "VISION_404",
            },
        )

    if job.get("stage") == "failed":
        return {
            "status": "error",
            "agent": "vision",
            "job_id": job_id,
            "stage": job.get("stage"),
            "pct": job.get("pct", 0),
            "result": None,
            "error": job.get("error"),
        }

    return {
        "status": "success",
        "agent": "vision",
        "job_id": job_id,
        "stage": job.get("stage"),
        "pct": job.get("pct", 0),
        "result": job.get("result"),
    }


@router.websocket("/ws/status/{job_id}")
async def status_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            job = get_job(job_id)
            if job is None:
                await websocket.send_json(
                    {
                        "status": "error",
                        "agent": "vision",
                        "job_id": job_id,
                        "message": "job not found",
                        "code": "VISION_404",
                    }
                )
                break

            await websocket.send_json(
                {
                    "job_id": job_id,
                    "stage": job.get("stage"),
                    "pct": job.get("pct", 0),
                }
            )

            if job.get("stage") in {"completed", "failed"}:
                break
            await asyncio.sleep(settings.WS_POLL_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        return
