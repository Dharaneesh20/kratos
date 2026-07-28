import json
import time
import uuid
from typing import Any, Dict, Optional

from redis import Redis

from app.config import settings

_USE_REDIS = False
_redis_client: Optional[Redis] = None
_memory_jobs: Dict[str, Dict[str, Any]] = {}

try:
    _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    _redis_client.ping()
    _USE_REDIS = True
except Exception:
    _USE_REDIS = False
    _redis_client = None


def _job_key(job_id: str) -> str:
    return f"vision:job:{job_id}"


def create_job(initial_stage: str = "queued") -> str:
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    payload = {
        "job_id": job_id,
        "stage": initial_stage,
        "pct": 0,
        "result": None,
        "error": None,
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
    set_job(job_id, payload)
    return job_id


def set_job(job_id: str, payload: Dict[str, Any]) -> None:
    payload["updated_at"] = int(time.time())
    if _USE_REDIS and _redis_client is not None:
        _redis_client.set(_job_key(job_id), json.dumps(payload), ex=settings.JOB_TTL_SECONDS)
        return
    _memory_jobs[job_id] = payload


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    if _USE_REDIS and _redis_client is not None:
        raw = _redis_client.get(_job_key(job_id))
        return json.loads(raw) if raw else None
    return _memory_jobs.get(job_id)


def update_job(job_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    current = get_job(job_id)
    if current is None:
        return None
    current.update(fields)
    set_job(job_id, current)
    return current
