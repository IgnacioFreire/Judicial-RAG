"""Headings stored in Chroma come back as a list of strings."""

from pipeline.vector_store import _headings


def test_json_array_round_trips() -> None:
    assert _headings('["FALLO", "PRIMERO"]') == ["FALLO", "PRIMERO"]


def test_empty_headings() -> None:
    assert _headings("") == []
    assert _headings("[]") == []


def test_invalid_heading_payload_is_empty() -> None:
    assert _headings("not-json") == []
    assert _headings('{"heading": "FALLO"}') == []
