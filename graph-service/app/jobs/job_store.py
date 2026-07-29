import json
import logging
from typing import Any, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory job store
_in_memory_jobs: Dict[str, Dict[str, Any]] = {}


class JobStore:
    def __init__(self):
        self.redis_client = None
        if settings.REDIS_URL:
            try:
                import redis
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.redis_client.ping()
                logger.info("Connected to Redis job store.")
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}). Falling back to in-memory job store.")
                self.redis_client = None

    def set_job(self, job_id: str, data: Dict[str, Any], ttl_seconds: int = 86400):
        if self.redis_client:
            try:
                self.redis_client.setex(f"graph_job:{job_id}", ttl_seconds, json.dumps(data))
                return
            except Exception as e:
                logger.error(f"Redis set failed: {e}")
        _in_memory_jobs[job_id] = data

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        if self.redis_client:
            try:
                val = self.redis_client.get(f"graph_job:{job_id}")
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
        return _in_memory_jobs.get(job_id)


job_store = JobStore()
