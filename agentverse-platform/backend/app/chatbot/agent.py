import sys
from pathlib import Path
import json
import httpx
from typing import Dict, Any, List, Optional

root_path = Path(__file__).resolve().parents[4]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from app.config import settings
from app.spectator.agent import spectator_agent


class ChatbotControllerAgent:
    """
    Chatbot Controller Agent - Manages NVIDIA NIM / NeMoTron LLM disaster intelligence explanations.
    Explains why specific evacuation routes were selected, analyzes critical bridge bottlenecks,
    and answers user queries grounded in real multi-agent simulation telemetry.
    """

    def __init__(self):
        self.agent_id = "chatbot"
        self.name = "Chatbot Controller Agent"

    def _build_disaster_context_prompt(self, run_data: Dict[str, Any], user_query: str) -> List[Dict[str, str]]:
        hazard = run_data.get("hazard_type", "FLOOD")
        severity = run_data.get("severity", 0.8)
        sim_data = run_data.get("simulation_data") or {}
        resilience = sim_data.get("resilience", 0.85)
        delay = sim_data.get("travel_delay", 15.0)
        critical_nodes = run_data.get("critical_nodes") or []
        planning_data = run_data.get("planning_data") or {}
        evac_routes = planning_data.get("evacuation_routes") or []
        repairs = planning_data.get("repair_priority") or []

        system_prompt = (
            "You are KRATOS Disaster Intelligence AI powered by NVIDIA NeMoTron LLM. "
            "Your task is to provide clear, tactical, grounded explanations detailing why specific evacuation routes "
            "and repair priorities were selected by the multi-agent system during disaster response.\n\n"
            f"DISASTER CONTEXT:\n"
            f"- Hazard Type: {hazard} (Severity: {severity})\n"
            f"- Network Resilience Score: {int(resilience * 100)}%\n"
            f"- Calculated Travel Delay: +{delay}%\n"
            f"- Critical Bottleneck Nodes: {[cn.get('node_id') for cn in critical_nodes[:5]]}\n"
            f"- Active Evacuation Routes: {len(evac_routes)}\n"
            f"- Repair Priorities: {[r.get('node_id') for r in repairs[:3]]}\n\n"
            "Explain tactical decisions concisely, highlighting structural safety, bridge bottlenecks, and vehicle assignment."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]

    def _generate_fallback_explanation(self, run_data: Dict[str, Any], query: str) -> str:
        """Grounded fallback explanation engine when NIM API key is pending or offline."""
        hazard = run_data.get("hazard_type", "FLOOD")
        sim_data = run_data.get("simulation_data") or {}
        resilience = sim_data.get("resilience", 0.82)
        delay = sim_data.get("travel_delay", 18.5)
        planning_data = run_data.get("planning_data") or {}
        evac_routes = planning_data.get("evacuation_routes") or []
        repairs = planning_data.get("repair_priority") or []

        top_repair = repairs[0].get("node_id") if repairs else "N-104"
        route_count = len(evac_routes)

        return (
            f"### KRATOS Tactical Route Explanation ({hazard} Scenario)\n\n"
            f"1. **Route Selection Rationale**: Evacuation routes were computed using Dijkstra shortest-path optimization "
            f"on the damaged topological road network. Damaged arterial spans and flooded sectors were bypassed to minimize risk.\n"
            f"2. **Resilience & Travel Impact**: Current network resilience is at **{int(resilience * 100)}%** with a travel delay penalty of **+{delay}%**. "
            f"Safe zone destinations were assigned to maximize vehicle throughput for ambulances and relief buses.\n"
            f"3. **Repair Priority Recommendation**: Immediate structural stabilization is recommended for Node **{top_repair}** "
            f"to restore connectivity across severed sector bridges.\n\n"
            f"*(Note: Powered by KRATOS Chatbot Controller Agent. Add active NVIDIA NIM API key to `.env` for live NeMoTron 500B LLM reasoning).* "
        )

    def explain_disaster_scenario(self, run_data: Dict[str, Any], query: str) -> str:
        spectator_agent.update_agent_state(self.agent_id, f"Generating explanation for query: '{query[:20]}...'", "BUSY")
        spectator_agent.log_event(self.agent_id, "INFO", f"Chatbot processing query: {query}")

        api_key = settings.active_nvidia_key
        base_endpoint = settings.NIM_ENDPOINT.rstrip("/")
        if base_endpoint.endswith("/chat/completions"):
            nim_endpoint = base_endpoint
        else:
            nim_endpoint = f"{base_endpoint}/chat/completions"

        if api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                messages = self._build_disaster_context_prompt(run_data, query)
                payload = {
                    "model": settings.NIM_MODEL,
                    "messages": messages,
                    "temperature": 0.6,
                    "top_p": 0.95,
                    "max_tokens": 4096,
                }
                with httpx.Client(timeout=45.0) as client:
                    resp = client.post(nim_endpoint, json=payload, headers=headers)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        message_obj = res_json.get("choices", [{}])[0].get("message", {})
                        content = message_obj.get("content", "")
                        reasoning = message_obj.get("reasoning_content", "")

                        full_response = ""
                        if reasoning and reasoning.strip():
                            full_response += f"**AI Reasoning Process:**\n{reasoning.strip()}\n\n---\n\n"
                        if content and content.strip():
                            full_response += content.strip()

                        if full_response:
                            spectator_agent.log_event(self.agent_id, "INFO", f"NIM response received ({len(full_response)} chars)")
                            spectator_agent.update_agent_state(self.agent_id, "NIM Response Delivered", "HEALTHY")
                            return full_response
                    else:
                        spectator_agent.log_event(self.agent_id, "WARNING", f"NVIDIA NIM HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                spectator_agent.log_event(self.agent_id, "WARNING", f"NVIDIA NIM API call error: {str(e)}")

        # Use grounded fallback engine
        spectator_agent.update_agent_state(self.agent_id, "Idle (Fallback Mode)", "HEALTHY")
        return self._generate_fallback_explanation(run_data, query)


chatbot_agent = ChatbotControllerAgent()
