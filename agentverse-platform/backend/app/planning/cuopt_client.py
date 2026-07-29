import logging
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def solve_cuopt_routing(
    cost_matrix: List[List[float]],
    num_vehicles: int = 2,
) -> Optional[Dict[str, Any]]:
    """
    Calls NVIDIA cuOpt Cloud Microservice API for GPU-accelerated route optimization.
    Returns optimized route assignments if successful, else None (falling back to NetworkX).
    """
    api_key = settings.active_nvidia_key
    if not api_key:
        logger.info("CUOPT_API_KEY not configured. Falling back to NetworkX shortest path.")
        return None

    endpoint = settings.CUOPT_ENDPOINT or "https://integrate.api.nvidia.com/v1/cuopt"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "cost_matrix": cost_matrix,
        "task_locations": list(range(len(cost_matrix))),
        "fleet": {
            "num_vehicles": num_vehicles,
            "vehicle_locations": [[0, 0] for _ in range(num_vehicles)],
        },
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
            if resp.status_code == 200:
                logger.info("NVIDIA cuOpt routing solve successful.")
                return resp.json()
    except Exception as e:
        logger.warning(f"cuOpt solve call failed ({e}). Using NetworkX path solver.")
    return None
