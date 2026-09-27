"""
index_store.py

Session-scoped search index.
The app and the notebooks use Supabase pgvector.
Tests install the memory store and do not sign in.
"""

import logging
import math
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from postgrest.types import ReturnMethod

from config.settings import settings

logger = logging.getLogger(__name__)

_MISSING = (
    ("supabase_url", "SUPABASE_URL"),
    ("supabase_anon_key", "SUPABASE_ANON_KEY"),
    ("supabase_admin_email", "SUPABASE_ADMIN_EMAIL"),
    ("supabase_admin_password", "SUPABASE_ADMIN_PASSWORD"),
)


@dataclass
class IndexRow:
    """One chunk ready to store. The text has no embedding prefix."""

    chunk_id: str
    source: str
    page: int
    chunk_index: int
    headings: list[str]
    text: str
    embedding: list[float]
    created_at: datetime | None = None


class IndexStore(Protocol):
    """Reads and writes for one session id at a time."""

    def upsert(self, session_id: str, rows: list[IndexRow]) -> None:
        """Insert or replace chunks. A repeated chunk id keeps its first created_at."""

    def delete_source(self, session_id: str, source: str) -> None:
        """Delete every chunk of one PDF in one session."""

    def delete_session(self, session_id: str) -> None:
        """Delete every chunk in one session."""

    def delete_older_than(self, cutoff: datetime) -> None:
        """Delete chunks first stored at or before cutoff."""

    def search(
        self,
        session_id: str,
        source: str,
        vector: list[float],
        n_results: int,
    ) -> list[dict]:
        """Return the closest chunks for one PDF, lowest distance first."""

    def source_chunks(self, session_id: str, source: str) -> list[dict]:
        """Return every stored chunk of one PDF, without a distance."""

    def list_sources(self, session_id: str) -> list[str]:
        """Return the sorted PDF filenames indexed in one session."""

    def count(self, session_id: str) -> int:
        """Return how many chunks are stored for one session."""

    def ids(self, session_id: str) -> list[str]:
        """Return the chunk ids stored for one session, sorted."""

    def text(self, session_id: str, chunk_id: str) -> str | None:
        """Return one stored chunk's text, or None when it is absent."""


@dataclass
class _Stored:
    chunk_id: str
    source: str
    page: int
    chunk_index: int
    headings: list[str]
    text: str
    embedding: list[float]
    created_at: datetime


class MemoryIndex:
    """In-process index used by tests."""

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], _Stored] = {}
        self._lock = threading.Lock()

    def upsert(self, session_id: str, rows: list[IndexRow]) -> None:
        now = datetime.now(UTC)
        with self._lock:
            for row in rows:
                key = (session_id, row.chunk_id)
                previous = self._rows.get(key)
                created = row.created_at or (previous.created_at if previous else now)
                self._rows[key] = _Stored(
                    chunk_id=row.chunk_id,
                    source=row.source,
                    page=row.page,
                    chunk_index=row.chunk_index,
                    headings=list(row.headings),
                    text=row.text,
                    embedding=list(row.embedding),
                    created_at=created,
                )

    def delete_source(self, session_id: str, source: str) -> None:
        with self._lock:
            stale = [
                key
                for key, row in self._rows.items()
                if key[0] == session_id and row.source == source
            ]
            for key in stale:
                del self._rows[key]

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            stale = [key for key in self._rows if key[0] == session_id]
            for key in stale:
                del self._rows[key]

    def delete_older_than(self, cutoff: datetime) -> None:
        with self._lock:
            stale = [key for key, row in self._rows.items() if row.created_at <= cutoff]
            for key in stale:
                del self._rows[key]

    def search(
        self,
        session_id: str,
        source: str,
        vector: list[float],
        n_results: int,
    ) -> list[dict]:
        if n_results < 1:
            return []
        with self._lock:
            matches = [
                row
                for key, row in self._rows.items()
                if key[0] == session_id and row.source == source
            ]
        ranked = sorted(
            matches,
            key=lambda row: (
                _cosine_distance(vector, row.embedding),
                row.chunk_index,
                row.chunk_id,
            ),
        )
        return [_hit(row, _cosine_distance(vector, row.embedding)) for row in ranked][
            :n_results
        ]

    def source_chunks(self, session_id: str, source: str) -> list[dict]:
        with self._lock:
            matches = [
                row
                for key, row in self._rows.items()
                if key[0] == session_id and row.source == source
            ]
        return [_record(row) for row in matches]

    def list_sources(self, session_id: str) -> list[str]:
        with self._lock:
            names = {
                row.source for key, row in self._rows.items() if key[0] == session_id
            }
        return sorted(names)

    def count(self, session_id: str) -> int:
        with self._lock:
            return sum(1 for key in self._rows if key[0] == session_id)

    def ids(self, session_id: str) -> list[str]:
        with self._lock:
            found = [key[1] for key in self._rows if key[0] == session_id]
        return sorted(found)

    def text(self, session_id: str, chunk_id: str) -> str | None:
        with self._lock:
            row = self._rows.get((session_id, chunk_id))
        if row is None:
            return None
        return row.text


class SupabaseIndex:
    """pgvector index in the maintainer's Supabase project."""

    def __init__(self) -> None:
        missing = [env for attr, env in _MISSING if not getattr(settings, attr)]
        if missing:
            raise RuntimeError("Missing Supabase settings: " + ", ".join(missing))

        from supabase import create_client

        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        auth = client.auth.sign_in_with_password(
            {
                "email": settings.supabase_admin_email,
                "password": settings.supabase_admin_password,
            }
        )
        user = auth.user
        if user is None or not user.id:
            raise RuntimeError("Supabase sign-in did not return a user")
        self._client = client
        self._user_id = user.id
        self._lock = threading.Lock()
        logger.debug("Supabase index client signed in")

    def upsert(self, session_id: str, rows: list[IndexRow]) -> None:
        if not rows:
            return
        payload = [
            {
                "session_id": session_id,
                "chunk_id": row.chunk_id,
                "user_id": self._user_id,
                "source": row.source,
                "page": row.page,
                "chunk_index": row.chunk_index,
                "headings": list(row.headings),
                "content": row.text,
                "embedding": _vector_literal(row.embedding),
            }
            for row in rows
        ]
        with self._lock:
            self._client.table("chunks").upsert(
                payload,
                on_conflict="session_id,chunk_id",
                default_to_null=False,
                returning=ReturnMethod.minimal,
            ).execute()
        logger.debug("Upserted %d chunks (session=%s)", len(rows), session_id)

    def delete_source(self, session_id: str, source: str) -> None:
        with self._lock:
            (
                self._client.table("chunks")
                .delete(returning=ReturnMethod.minimal)
                .eq("session_id", session_id)
                .eq("source", source)
                .execute()
            )

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            (
                self._client.table("chunks")
                .delete(returning=ReturnMethod.minimal)
                .eq("session_id", session_id)
                .execute()
            )

    def delete_older_than(self, cutoff: datetime) -> None:
        with self._lock:
            (
                self._client.table("chunks")
                .delete(returning=ReturnMethod.minimal)
                .lte("created_at", cutoff.isoformat())
                .execute()
            )

    def search(
        self,
        session_id: str,
        source: str,
        vector: list[float],
        n_results: int,
    ) -> list[dict]:
        if n_results < 1:
            return []
        with self._lock:
            response = self._client.rpc(
                "match_session_chunks",
                {
                    "query_embedding": _vector_literal(vector),
                    "match_session_id": session_id,
                    "match_source": source,
                    "match_count": n_results,
                },
            ).execute()
        hits = []
        for row in response.data or []:
            hits.append(
                {
                    "chunk_id": row.get("chunk_id", ""),
                    "text": row.get("content", ""),
                    "source": row.get("source", ""),
                    "page": row.get("page", 1),
                    "headings": row.get("headings") or [],
                    "chunk_index": row.get("chunk_index", 0),
                    "distance": float(row.get("distance", 1.0)),
                }
            )
        return hits

    def source_chunks(self, session_id: str, source: str) -> list[dict]:
        columns = "chunk_id,content,source,page,chunk_index,headings"
        rows = self._select_session(session_id, columns, source)
        return [
            {
                "chunk_id": row.get("chunk_id", ""),
                "text": row.get("content", ""),
                "source": row.get("source", ""),
                "page": row.get("page", 1),
                "headings": row.get("headings") or [],
                "chunk_index": row.get("chunk_index", 0),
            }
            for row in rows
        ]

    def list_sources(self, session_id: str) -> list[str]:
        rows = self._select_session(session_id, "source")
        return sorted({row["source"] for row in rows if row.get("source")})

    def count(self, session_id: str) -> int:
        return len(self.ids(session_id))

    def ids(self, session_id: str) -> list[str]:
        rows = self._select_session(session_id, "chunk_id")
        return sorted(row["chunk_id"] for row in rows if row.get("chunk_id"))

    def text(self, session_id: str, chunk_id: str) -> str | None:
        with self._lock:
            response = (
                self._client.table("chunks")
                .select("content")
                .eq("session_id", session_id)
                .eq("chunk_id", chunk_id)
                .limit(1)
                .execute()
            )
        rows = response.data or []
        if not rows:
            return None
        return rows[0].get("content")

    def _select_session(
        self,
        session_id: str,
        columns: str,
        source: str | None = None,
    ) -> list[dict]:
        page_size = 1000
        start = 0
        rows: list[dict] = []
        while True:
            with self._lock:
                query = (
                    self._client.table("chunks")
                    .select(columns)
                    .eq("session_id", session_id)
                )
                if source is not None:
                    query = query.eq("source", source)
                response = query.range(start, start + page_size - 1).execute()
            batch = response.data or []
            rows.extend(batch)
            if len(batch) < page_size:
                return rows
            start += page_size


_store: IndexStore | None = None
_guard = threading.Lock()


def use_memory_index() -> MemoryIndex:
    """Install a fresh memory store. Tests call this so nothing is signed in."""
    global _store
    store = MemoryIndex()
    with _guard:
        _store = store
    return store


def get_index() -> IndexStore:
    """Return the process store, creating the Supabase client on first use."""
    global _store
    if _store is not None:
        return _store
    with _guard:
        if _store is None:
            _store = SupabaseIndex()
        return _store


def _record(row: _Stored) -> dict:
    return {
        "chunk_id": row.chunk_id,
        "text": row.text,
        "source": row.source,
        "page": row.page,
        "headings": list(row.headings),
        "chunk_index": row.chunk_index,
    }


def _hit(row: _Stored, distance: float) -> dict:
    return {**_record(row), "distance": distance}


def _cosine_distance(left: list[float], right: list[float]) -> float:
    """Cosine distance in the same direction as pgvector `<=>`. Lower is closer."""
    if len(left) != len(right) or not left:
        return 1.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right, strict=True):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm == 0.0 or right_norm == 0.0:
        return 1.0
    similarity = dot / (math.sqrt(left_norm) * math.sqrt(right_norm))
    return 1.0 - similarity


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(format(value, ".8g") for value in values) + "]"
