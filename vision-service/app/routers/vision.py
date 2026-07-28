import asyncio
import json
import logging
import os

import cv2
import numpy as np
from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect

from app.config import settings
from app.jobs.job_store import create_job, get_job, update_job
from app.logging_utils import log_event, request_id_ctx
from app.schemas import VisionProcessRequest
from app.services.dataset_loader import get_dataset_metadata
from app.services.geojson_builder import build_geojson, weighted_confidence
from app.services.segmentation import segment_scene
from app.services.skeletonize import mask_to_pruned_skeleton

router = APIRouter(prefix="/vision", tags=["vision"])
logger = logging.getLogger(__name__)


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
    out_dir = os.path.dirname(tif_path)

    def on_tile_progress(done: int, total: int) -> None:
        pct = int(5 + (done / max(total, 1)) * 65)
        update_job(job_id, stage="segmenting", pct=min(pct, 70), result=None)

    try:
        update_job(job_id, stage="preprocessing", pct=5, result=None)
        prob_map, tile_count, occluded_tile_pct = segment_scene(
            tif_path=tif_path,
            model_name=model,
            tile_size=tile_size,
            overlap=overlap,
            on_progress=on_tile_progress,
        )

        update_job(job_id, stage="skeletonizing", pct=80, result=None)
        skeleton = mask_to_pruned_skeleton(prob_map)

        update_job(job_id, stage="vectorizing", pct=90, result=None)
        feature_collection = build_geojson(skeleton=skeleton, prob_map=prob_map, tif_path=tif_path)

        roads_geojson_path = os.path.join(out_dir, "roads.geojson")
        road_mask_png_path = os.path.join(out_dir, "road_mask.png")
        centerline_png_path = os.path.join(out_dir, "centerline.png")

        with open(roads_geojson_path, "w", encoding="utf-8") as f:
            json.dump(feature_collection, f)

        binary_mask = (prob_map > settings.MASK_THRESHOLD).astype(np.uint8) * 255
        cv2.imwrite(road_mask_png_path, binary_mask)
        cv2.imwrite(centerline_png_path, skeleton.astype(np.uint8) * 255)

        result = {
            "roads_geojson": roads_geojson_path,
            "road_mask_png": road_mask_png_path,
            "centerline_png": centerline_png_path,
            "confidence": weighted_confidence(feature_collection),
            "tile_count": tile_count,
            "occluded_tile_pct": round(float(occluded_tile_pct), 2),
        }

        update_job(job_id, stage="completed", pct=100, result=result, error=None)
        log_event(
            logger,
            "vision_job_completed",
            job_id=job_id,
            dataset_id=dataset_id,
            confidence=result["confidence"],
            tile_count=tile_count,
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
async def process(req: VisionProcessRequest, background_tasks: BackgroundTasks):
    meta = get_dataset_metadata(req.dataset_id)
    if meta is None:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "agent": "vision",
                "message": f"dataset_id not found: {req.dataset_id}",
                "code": "VISION_404",
            },
        )

    job_id = create_job(initial_stage="queued")
    log_event(logger, "vision_job_queued", job_id=job_id, dataset_id=req.dataset_id)
    request_id = request_id_ctx.get()
    background_tasks.add_task(
        _run_vision_job,
        job_id,
        req.dataset_id,
        req.tile_size,
        req.overlap,
        req.model,
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
