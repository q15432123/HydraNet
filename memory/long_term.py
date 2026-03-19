"""
Long-Term Memory — persistent knowledge base using vector embeddings.

Uses ChromaDB for semantic search over agent observations,
wallet patterns, and learned knowledge.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import chromadb
from chromadb.config import Settings

from config import CHROMADB_PATH

logger = logging.getLogger("hydranet.memory")


class LongTermMemory:
    """Vector-based persistent knowledge store."""

    def __init__(self, collection_name: str = "hydranet_knowledge"):
        self._client = chromadb.Client(Settings(
            persist_directory=CHROMADB_PATH,
            anonymized_telemetry=False,
        ))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"LongTermMemory initialized: {collection_name}")

    def store(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ):
        meta = metadata or {}
        meta["stored_at"] = time.time()
        self._collection.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[meta],
        )

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        kwargs: dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        entries = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                entries.append({
                    "id": results["ids"][0][i],
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        return entries

    def get(self, doc_id: str) -> dict | None:
        result = self._collection.get(ids=[doc_id])
        if result and result["documents"] and result["documents"][0]:
            return {
                "id": doc_id,
                "content": result["documents"][0],
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
            }
        return None

    def delete(self, doc_id: str):
        self._collection.delete(ids=[doc_id])

    def count(self) -> int:
        return self._collection.count()
