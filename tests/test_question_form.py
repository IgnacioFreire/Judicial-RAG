"""Widget keys for the question editor stay attached to a row, not its index."""

from app.components.question_form import _ensure_id, _widget_key


def test_widget_keys_follow_the_row_id() -> None:
    first = _ensure_id({})
    second = _ensure_id({})
    assert first != second
    assert _widget_key(first, "label") == f"label_{first}"
    assert _widget_key(first, "label") != _widget_key(second, "label")


def test_existing_id_is_kept() -> None:
    assert _ensure_id({"id": "fixed"}) == "fixed"
