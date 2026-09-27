"""Small helpers shared by the manual notebooks."""

import os
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

from models.query import AnswerConfidence
from supabase import create_client

_MAX_PDF_BYTES = 20 * 1024 * 1024


def accepted_pdfs(directory: Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Return PDFs of at most 20 MB, plus a reason for every other file."""
    accepted: list[Path] = []
    rejected: list[tuple[Path, str]] = []
    files = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )
    for path in files:
        if not path.name.strip():
            rejected.append((path, "empty name"))
        elif path.suffix.lower() != ".pdf":
            rejected.append((path, "not a PDF"))
        elif path.stat().st_size > _MAX_PDF_BYTES:
            rejected.append((path, "over 20 MB"))
        else:
            accepted.append(path)
    return accepted, rejected


def classify_uploads(
    files: list[tuple[str, int]],
) -> tuple[list[tuple[str, int]], list[tuple[str, int, str]]]:
    """Apply the 20 MB PDF rule to storage objects already listed."""
    accepted: list[tuple[str, int]] = []
    rejected: list[tuple[str, int, str]] = []
    for name, size in files:
        if name == ".gitkeep":
            continue
        if not name.strip():
            rejected.append((name, size, "empty name"))
        elif not name.lower().endswith(".pdf"):
            rejected.append((name, size, "not a PDF"))
        elif size > _MAX_PDF_BYTES:
            rejected.append((name, size, "over 20 MB"))
        else:
            accepted.append((name, size))
    return accepted, rejected


def download_supabase_pdfs(
    directory: Path,
) -> tuple[str, list[Path], list[tuple[str, int, str]]]:
    """Sign in and save accepted bucket PDFs into directory."""
    required = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_ADMIN_EMAIL",
        "SUPABASE_ADMIN_PASSWORD",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing Supabase settings: " + ", ".join(missing))

    bucket = os.environ.get("SUPABASE_PDF_BUCKET", "pdfs")
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    client.auth.sign_in_with_password(
        {
            "email": os.environ["SUPABASE_ADMIN_EMAIL"],
            "password": os.environ["SUPABASE_ADMIN_PASSWORD"],
        }
    )
    accepted, rejected = classify_uploads(_list_bucket(client, bucket))
    paths: list[Path] = []
    for name, size in accepted:
        if name != Path(name).name:
            rejected.append((name, size, "nested path"))
            continue
        target = directory / name
        target.write_bytes(client.storage.from_(bucket).download(name))
        paths.append(target)
    return bucket, paths, rejected


def _list_bucket(client, bucket: str) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    offset = 0
    while True:
        page = client.storage.from_(bucket).list(
            "",
            {"limit": 100, "offset": offset},
        )
        for item in page:
            metadata = item.get("metadata") or None
            if not metadata:
                continue
            size = metadata.get("size", metadata.get("contentLength", 0)) or 0
            rows.append((item.get("name") or "", int(size)))
        if len(page) < 100:
            return rows
        offset += 100


def new_session_id() -> str:
    """Return a session id that belongs only to this notebook run."""
    return f"nb-{uuid.uuid4()}"


@contextmanager
def timed(name: str):
    """Record the wall-clock seconds spent inside the block."""
    record = {"name": name, "seconds": 0.0}
    started = time.perf_counter()
    try:
        yield record
    finally:
        record["seconds"] = time.perf_counter() - started


def preview(text: str | None, enabled: bool) -> str | int:
    """Return the text only when the notebook opted in."""
    body = text or ""
    return body if enabled else len(body)


def result_rows(results) -> list[dict]:
    """Map answers to counts and labels, leaving answer text out."""
    rows = []
    for document in results:
        for answer in document.answers:
            citation = answer.citation
            source = answer.answer_source
            rows.append(
                {
                    "document": document.document,
                    "label": answer.question.label,
                    "question_type": answer.question.question_type.value,
                    "confidence": answer.confidence.value,
                    "answer_source": source.value if source else None,
                    "citation_page": citation.page if citation else None,
                    "citation_score": citation.score if citation else None,
                    "citation_source": citation.source if citation else None,
                    "citation_chars": len(citation.text) if citation else 0,
                }
            )
    return rows


def answered_counts(results) -> list[dict]:
    """Count answers that are not not_found, matching the results viewer."""
    counts = []
    for document in results:
        answered = sum(
            1
            for answer in document.answers
            if answer.confidence != AnswerConfidence.NOT_FOUND
        )
        counts.append(
            {
                "document": document.document,
                "answered": answered,
                "total": len(document.answers),
            }
        )
    return counts


def _stage(event) -> str:
    stage = event.stage
    return stage.value if hasattr(stage, "value") else str(stage)


def phase_durations(events) -> dict:
    """Split one stamped run into phase 1, phase 2, and per-question gaps."""
    staged = [(_stage(event), event.stamp) for event in events]
    started: dict[str, float] = {}
    for stage, stamp in staged:
        started.setdefault(stage, stamp)

    questions = [
        staged[index + 1][1] - stamp
        for index, (stage, stamp) in enumerate(staged)
        if stage == "answering" and index + 1 < len(staged)
    ]
    return {
        "phase_1": started["answering"] - started["extracting"],
        "phase_2": started["complete"] - started["answering"],
        "questions": questions,
    }


def kpi_summary(results, failures, durations) -> dict:
    """Count indexed PDFs, answers, confidence, and citations for one run."""
    rows = result_rows(results)
    confidence = Counter(row["confidence"] for row in rows)
    answers = len(rows)
    not_found = confidence.get("not_found", 0)
    return {
        "pdfs_indexed": len(results),
        "pdfs_failed": len(failures),
        "questions": len(results[0].answers) if results else 0,
        "answers": answers,
        "confidence": dict(confidence),
        "direct": sum(row["answer_source"] == "direct" for row in rows),
        "inferred": sum(row["answer_source"] == "inferred" for row in rows),
        "with_citation": sum(row["citation_page"] is not None for row in rows),
        "not_found_rate": (not_found / answers) if answers else 0.0,
        "durations": durations,
    }
