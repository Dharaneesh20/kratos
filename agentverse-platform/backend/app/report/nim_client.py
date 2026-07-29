import json
import logging
from typing import Any, Dict, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def generate_report_narrative_nim(
    hazard_type: str,
    resilience_score: float,
    travel_delay: float,
    critical_nodes: list,
) -> Optional[Dict[str, str]]:
    """
    Calls NVIDIA NIM endpoint to draft Executive Summary, Risk Analysis, and Repair Narrative.
    """
    api_key = settings.active_nvidia_key
    if not api_key:
        return None

    endpoint = f"{settings.NIM_ENDPOINT.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""Draft a formal government-level disaster intelligence summary based on the following:
Hazard: {hazard_type}
Post-Disaster Resilience: {resilience_score}
Travel Delay Increase: +{travel_delay}%
Top Critical Nodes: {json.dumps(critical_nodes[:3])}

Return ONLY a JSON object with fields:
"executive_summary", "risk_analysis", "repair_narrative"
"""

    payload = {
        "model": settings.NIM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a government disaster report generator. Output ONLY JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                if "```" in content:
                    content = content.split("```json")[-1].split("```")[0].strip()
                return json.loads(content)
    except Exception as e:
        logger.warning(f"NIM narrative generation failed ({e}). Falling back to template.")
    return None
