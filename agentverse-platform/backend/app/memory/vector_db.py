"""
Vector DB & Feature Store Module for KRATOS Multi-Agent Platform.
Provides persistent, portable vector embeddings and feature caching stored in vector.db.
Allows transferring pre-computed road segment embeddings and disaster scenario memory
between Cloud/Rig training environments and offline laptop runtimes.
"""

import os
import sqlite3
import json
import math
from typing import List, Dict, Any, Optional, Tuple


class VectorDB:
    def __init__(self, db_path: str = "vector.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,
                    collection TEXT NOT NULL,
                    vector JSON NOT NULL,
                    metadata JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_collection ON embeddings(collection);")
            conn.commit()

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def store_embedding(self, entity_id: str, collection: str, vector: List[float], metadata: Dict[str, Any]):
        """Stores a vector embedding and metadata in vector.db."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO embeddings (id, collection, vector, metadata)
                VALUES (?, ?, ?, ?);
            """, (entity_id, collection, json.dumps(vector), json.dumps(metadata)))
            conn.commit()

    def search_similar(self, query_vector: List[float], collection: str = "road_features", top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs cosine similarity search against stored vector embeddings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, vector, metadata FROM embeddings WHERE collection = ?;", (collection,))
            rows = cursor.fetchall()

        results: List[Tuple[float, str, Dict[str, Any]]] = []
        for entity_id, vec_json, meta_json in rows:
            vec = json.loads(vec_json)
            meta = json.loads(meta_json)
            sim = self._cosine_similarity(query_vector, vec)
            results.append((sim, entity_id, meta))

        results.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": r[1],
                "similarity": round(r[0], 4),
                "metadata": r[2],
            }
            for r in results[:top_k]
        ]

    def export_vector_db(self, export_path: str = "exported_vector.db"):
        """Exports a copy of the portable vector.db for laptop deployment."""
        with self._get_connection() as src, sqlite3.connect(export_path) as dst:
            src.backup(dst)
        print(f"[VectorDB] Exported portable database to {export_path}")


# Global Singleton Vector Database instance
vector_db = VectorDB()
