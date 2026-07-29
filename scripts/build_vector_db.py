"""
KRATOS Script Runner for Vector DB Generation.
Usage: python scripts/build_vector_db.py
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
backend_app = root / "agentverse-platform" / "backend"
sys.path.insert(0, str(backend_app))
sys.path.insert(0, str(root))

from app.memory.build_vector_db import build_vector_db_from_dataset

if __name__ == "__main__":
    build_vector_db_from_dataset()
