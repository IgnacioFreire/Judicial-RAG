"""The advanced-settings control defaults to the medium parser tier."""

from streamlit.testing.v1 import AppTest


def test_parser_defaults_to_medium() -> None:
    app = AppTest.from_file("app/main.py", default_timeout=30)
    app.run()
    parsers = [box for box in app.selectbox if box.label == "Parser"]
    assert len(parsers) == 1
    assert parsers[0].value == "medium"
    shown = parsers[0].options
    assert "pymupdf4llm" in shown[0]
    assert "docling" in shown[1]
    assert "marker" in shown[2]
    chunking = [box for box in app.selectbox if box.label == "Chunking"]
    assert len(chunking) == 1
    assert chunking[0].value == "medium"
    chunk_shown = chunking[0].options
    assert "window" in chunk_shown[0]
    assert "hybrid" in chunk_shown[1]
    assert "context" in chunk_shown[2]
    retrieval = [box for box in app.selectbox if box.label == "Retrieval"]
    assert len(retrieval) == 1
    assert retrieval[0].value == "fast"
    retrieval_shown = retrieval[0].options
    assert "dense" in retrieval_shown[0]
    assert "hybrid" in retrieval_shown[1]
    assert "rerank" in retrieval_shown[2]
