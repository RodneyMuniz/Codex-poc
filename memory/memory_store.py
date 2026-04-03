from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class MemoryStore:
    def __init__(self, repo_root: str | Path | None = None, db_path: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.db_path = Path(db_path or (self.repo_root / "memory" / "memory.db")).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._encoder = self._build_encoder()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    state TEXT NOT NULL,
                    message TEXT NOT NULL,
                    embedding_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    state TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    latency_ms REAL,
                    success INTEGER NOT NULL DEFAULT 1,
                    token_usage_json TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _build_encoder(self):
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            return None
        try:
            return SentenceTransformer("paraphrase-MiniLM-L6-v2")
        except Exception:
            return None

    def _encode(self, text: str) -> list[float] | None:
        if self._encoder is None:
            return None
        vector = self._encoder.encode(text)
        return [float(value) for value in vector]

    def add_interaction(self, role: str, state: str, message: str) -> int:
        embedding = self._encode(message)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO interactions (role, state, message, embedding_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    role,
                    state,
                    message,
                    json.dumps(embedding, ensure_ascii=True) if embedding is not None else None,
                    _utc_now(),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def query_memory(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, role, state, message, embedding_json, created_at
                FROM interactions
                ORDER BY id DESC
                """
            ).fetchall()
        if not rows:
            return []
        query_embedding = self._encode(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            payload = dict(row)
            embedding = json.loads(payload["embedding_json"]) if payload.get("embedding_json") else None
            score = self._similarity(query, query_embedding, payload["message"], embedding)
            payload.pop("embedding_json", None)
            scored.append((score, payload))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [payload for score, payload in scored[:top_k] if score > 0]

    def _similarity(
        self,
        query: str,
        query_embedding: list[float] | None,
        message: str,
        message_embedding: list[float] | None,
    ) -> float:
        if query_embedding and message_embedding and len(query_embedding) == len(message_embedding):
            numerator = sum(left * right for left, right in zip(query_embedding, message_embedding))
            left_norm = math.sqrt(sum(value * value for value in query_embedding))
            right_norm = math.sqrt(sum(value * value for value in message_embedding))
            if left_norm and right_norm:
                return numerator / (left_norm * right_norm)
        query_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        message_tokens = set(re.findall(r"[a-z0-9]+", message.lower()))
        if not query_tokens or not message_tokens:
            return 0.0
        overlap = len(query_tokens & message_tokens)
        return overlap / max(len(query_tokens | message_tokens), 1)

    def record_metric(
        self,
        *,
        role: str,
        state: str,
        event_type: str,
        latency_ms: float | None,
        success: bool,
        token_usage: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO metrics (role, state, event_type, latency_ms, success, token_usage_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    role,
                    state,
                    event_type,
                    latency_ms,
                    1 if success else 0,
                    json.dumps(token_usage or {}, ensure_ascii=True),
                    json.dumps(metadata or {}, ensure_ascii=True),
                    _utc_now(),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)


_DEFAULT_STORES: dict[Path, MemoryStore] = {}


def get_default_memory_store(repo_root: str | Path | None = None) -> MemoryStore:
    root = Path(repo_root or Path.cwd()).resolve()
    store = _DEFAULT_STORES.get(root)
    if store is None:
        store = MemoryStore(root)
        _DEFAULT_STORES[root] = store
    return store


def add_interaction(role: str, state: str, message: str, repo_root: str | Path | None = None) -> int:
    return get_default_memory_store(repo_root).add_interaction(role, state, message)


def query_memory(query: str, top_k: int = 5, repo_root: str | Path | None = None) -> list[dict[str, Any]]:
    return get_default_memory_store(repo_root).query_memory(query, top_k=top_k)


def record_metric(
    *,
    role: str,
    state: str,
    event_type: str,
    latency_ms: float | None,
    success: bool,
    token_usage: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    repo_root: str | Path | None = None,
) -> int:
    return get_default_memory_store(repo_root).record_metric(
        role=role,
        state=state,
        event_type=event_type,
        latency_ms=latency_ms,
        success=success,
        token_usage=token_usage,
        metadata=metadata,
    )
