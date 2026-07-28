import time
import os
import sys
import json
import urllib.request

def get_json(url: str, timeout: float = 2.0):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KratosMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("Initializing KRATOS Master Agent Telemetry Sentinel...")
    time.sleep(1)

    while True:
        clear_screen()
        print("=" * 80)
        print(" KRATOS MULTI-AGENT SENTINEL & SYSTEM HEALTH MONITOR")
        print("=" * 80)
        print(f" Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)

        # 1. Check Microservices Health
        backend_health = get_json("http://localhost:8000/health")
        vision_health = get_json("http://localhost:8001/health")
        graph_health = get_json("http://localhost:8002/health")

        print(" MICROSERVICES STATUS:")
        print(f"  [Backend Service]  Port 8000 : {'[ ONLINE  ]' if backend_health else '[ OFF-LINE ]'}")
        print(f"  [Vision Service]   Port 8001 : {'[ ONLINE  ]' if vision_health else '[ OFF-LINE ]'}")
        print(f"  [Graph Service]    Port 8002 : {'[ ONLINE  ]' if graph_health else '[ OFF-LINE ]'}")
        print("-" * 80)

        # 2. Check Agents Telemetry
        agents_data = get_json("http://localhost:8000/api/spectator/agents")

        print(" AGENTVERSE OPERATIONAL MATRIX:")
        if agents_data and isinstance(agents_data, list):
            for agent in agents_data:
                agent_id = agent.get('agent_id', 'unknown').upper().ljust(12)
                name = agent.get('name', '').ljust(24)
                status = agent.get('status', 'OFFLINE').ljust(10)
                task = agent.get('current_task', 'Idle')
                print(f"  > {agent_id} | {name} | Status: [{status}] | Task: {task}")
        else:
            default_agents = ["COORDINATOR", "DATASET", "VISION", "GRAPH", "SIMULATION", "PLANNING", "REPORT", "SPECTATOR"]
            for ag in default_agents:
                status_str = "[ HEALTHY ]" if backend_health else "[ INITIALIZING ]"
                print(f"  > {ag.ljust(12)} | Status: {status_str} | Monitoring active...")

        print("-" * 80)
        print(" [Ctrl+C] to exit sentinel | Refreshing every 3 seconds...")
        print("=" * 80)

        time.sleep(3)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSentinel monitor stopped.")
        sys.exit(0)
