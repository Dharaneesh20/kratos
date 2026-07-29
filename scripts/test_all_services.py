import sys
import importlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]

# 1. Test Graph Service
graph_dir = root / "graph-service"
sys.path.insert(0, str(graph_dir))
import app.main as g_main
print("[OK] Graph Service loaded:", g_main.app.title)

# 2. Test Vision Service
sys.path.pop(0)
vision_dir = root / "vision-service"
sys.path.insert(0, str(vision_dir))
import app.main as v_main
print("[OK] Vision Service loaded:", v_main.app.title)

# 3. Test Backend Coordinator
sys.path.pop(0)
backend_dir = root / "agentverse-platform" / "backend"
sys.path.insert(0, str(backend_dir))
import app.main as b_main
print("[OK] Backend Coordinator loaded:", b_main.app.title)

print("\nSUCCESS: All 3 services load cleanly without errors!")
