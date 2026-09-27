"""Memory index: ordering, isolation, and the timeout sweep."""

from datetime import UTC, datetime, timedelta

from pipeline.index_store import IndexRow


def _row(
    chunk_id: str,
    source: str = "doc.pdf",
    embedding: list[float] | None = None,
    text: str = "synthetic fragment",
    created_at: datetime | None = None,
) -> IndexRow:
    return IndexRow(
        chunk_id=chunk_id,
        source=source,
        page=1,
        chunk_index=0,
        headings=["SECTION"],
        text=text,
        embedding=embedding or [1.0, 0.0],
        created_at=created_at,
    )


def test_search_orders_by_cosine_distance(memory_index) -> None:
    memory_index.upsert(
        "session",
        [
            _row("far", embedding=[0.0, 1.0], text="far"),
            _row("near", embedding=[1.0, 0.0], text="near"),
        ],
    )
    hits = memory_index.search("session", "doc.pdf", [1.0, 0.0], 2)
    assert [hit["text"] for hit in hits] == ["near", "far"]
    assert hits[0]["distance"] == 0.0
    assert hits[1]["distance"] == 1.0


def test_search_stays_inside_one_source_and_session(memory_index) -> None:
    vector = [1.0, 0.0]
    memory_index.upsert(
        "session-a",
        [
            _row("a", source="a.pdf", text="from a"),
            _row("b", source="b.pdf", text="from b"),
        ],
    )
    memory_index.upsert(
        "session-b",
        [_row("a", source="a.pdf", text="other session")],
    )
    hits = memory_index.search("session-a", "a.pdf", vector, 5)
    assert [hit["text"] for hit in hits] == ["from a"]


def test_reupsert_keeps_the_first_created_at(memory_index) -> None:
    first = datetime.now(UTC) - timedelta(minutes=5)
    memory_index.upsert("session", [_row("id", created_at=first)])
    memory_index.upsert("session", [_row("id", text="replaced")])
    cutoff = datetime.now(UTC) - timedelta(minutes=1)
    memory_index.delete_older_than(cutoff)
    assert memory_index.text("session", "id") is None


def test_cleanup_deletes_rows_older_than_the_timeout(memory_index) -> None:
    from config.settings import settings
    from storage.cleanup import cleanup_expired_sessions

    timeout = settings.session_timeout_minutes
    old = datetime.now(UTC) - timedelta(minutes=timeout + 1)
    memory_index.upsert("orphan", [_row("old", created_at=old)])
    memory_index.upsert("live", [_row("fresh")])

    cleanup_expired_sessions()

    assert memory_index.count("orphan") == 0
    assert memory_index.text("live", "fresh") == "synthetic fragment"
