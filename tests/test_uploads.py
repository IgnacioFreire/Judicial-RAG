"""Tests for storing the current upload set on disk."""

from pathlib import Path

import pytest

from app.components.uploader import store_uploads


def test_same_name_replaces_bytes(tmp_path: Path) -> None:
    store_uploads(tmp_path, [("a.pdf", b"first")])
    store_uploads(tmp_path, [("a.pdf", b"second")])
    assert (tmp_path / "a.pdf").read_bytes() == b"second"


def test_removed_name_is_deleted(tmp_path: Path) -> None:
    store_uploads(tmp_path, [("a.pdf", b"a"), ("b.pdf", b"b")])
    kept = store_uploads(tmp_path, [("a.pdf", b"a")])
    assert [path.name for path in kept] == ["a.pdf"]
    assert not (tmp_path / "b.pdf").exists()


def test_empty_batch_clears_the_directory(tmp_path: Path) -> None:
    store_uploads(tmp_path, [("a.pdf", b"a")])
    assert store_uploads(tmp_path, []) == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "raw_name",
    ["..\\nested\\secret.pdf", "../nested/secret.pdf"],
)
def test_path_is_reduced_to_the_file_name(tmp_path: Path, raw_name: str) -> None:
    stored = store_uploads(tmp_path, [(raw_name, b"x")])
    assert stored[0] == tmp_path / "secret.pdf"
    assert stored[0].read_bytes() == b"x"
    assert list(tmp_path.iterdir()) == [tmp_path / "secret.pdf"]
