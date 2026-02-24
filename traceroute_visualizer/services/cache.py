from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class SQLiteTTLCache:
    def __init__(self, db_path: str, ttl_seconds: int) -> None:
        self.db_path = Path(db_path)
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    namespace TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    PRIMARY KEY(namespace, cache_key)
                )
                """
            )
            conn.commit()

    def get(self, namespace: str, key: str) -> dict[str, Any] | None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache_entries WHERE namespace=? AND cache_key=?",
                (namespace, key),
            ).fetchone()
            if not row:
                return None
            value, expires_at = row
            if expires_at < int(time.time()):
                conn.execute(
                    "DELETE FROM cache_entries WHERE namespace=? AND cache_key=?",
                    (namespace, key),
                )
                conn.commit()
                return None
            return json.loads(value)

    def set(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        expires_at = int(time.time()) + self.ttl_seconds
        payload = json.dumps(value)
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache_entries(namespace, cache_key, value, expires_at)
                VALUES(?,?,?,?)
                ON CONFLICT(namespace, cache_key)
                DO UPDATE SET value=excluded.value, expires_at=excluded.expires_at
                """,
                (namespace, key, payload, expires_at),
            )
            conn.commit()


class SimpleRateLimiter:
    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = interval_seconds
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self.interval_seconds:
                time.sleep(self.interval_seconds - elapsed)
            self._last_call = time.monotonic()
