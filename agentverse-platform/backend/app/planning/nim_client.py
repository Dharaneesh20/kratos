import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def call_nim_explanation(
    hazard_type: str,
    resilience_score: float,
    travel_delay: float,
    critical_nodes: List[Dict[str, Any]],
    affected_regions: List[str],
) -> Optional[Dict[str, Any]]:
    """
    Calls NVIDIA NIM LLM endpoint to generate reasoning/explanations grounded on actual computed numbers.
    Enforces strict JSON output format.
    """
    api_key = settings.active_nvidia_key
    if not api_key:
        logger.info("NVIDIA_API_KEY not set. Using templated reasoning.")
        return None

    endpoint = f"{settings.NIM_ENDPOINT.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""You are an expert AI Disaster Logistics Advisor. Explain the analysis and rank repair priorities based STRICTLY on the following computed data:
Hazard Type: {hazard_type}
Network Resilience Score: {resilience_score} (0.0 to 1.0)
Travel Delay Increase: +{travel_delay}%
Top Critical Nodes: {json.dumps(critical_nodes[:5])}
Affected Regions: {json.dumps(affected_regions)}

Respond ONLY with a valid JSON object matching this schema:
{{
  "repair_priority_justifications": [
    {{"node_id": "string", "priority": 1, "reason": "string"}}
  ],
  "recommendations": [
    "string"
  ]
}}
"""

    payload = {
        "model": settings.NIM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a disaster response AI that responds ONLY in JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 512,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                # Clean up markdown code blocks if model wraps in ```json
                if "```" in content:
                    content = content.split("```json")[-1].split("```")[0].strip()
                return json.loads(content)
    except Exception as e:
        logger.warning(f"NVIDIA NIM API call failed ({e}). Falling back to grounded template.")
    return None
