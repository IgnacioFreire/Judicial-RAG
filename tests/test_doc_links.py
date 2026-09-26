"""Relative links in the docs resolve to a file in the repo."""

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_FENCE = re.compile(r"```.*?```", re.DOTALL)


def _targets() -> list[Path]:
    docs = list((_ROOT / "docs").rglob("*.md"))
    return docs + [_ROOT / "AGENTS.md", _ROOT / "README.md"]


def test_relative_markdown_links_resolve() -> None:
    broken: list[str] = []
    for path in _targets():
        text = _FENCE.sub("", path.read_text(encoding="utf-8"))
        for match in _LINK.finditer(text):
            raw = match.group(1).strip().split()[0]
            target = raw.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{path.relative_to(_ROOT)} -> {target}")
    assert broken == []
