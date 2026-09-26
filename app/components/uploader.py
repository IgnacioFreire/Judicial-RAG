"""
uploader.py

Streamlit component for PDF upload.
Validates uploaded files, saves accepted ones to the session temporary
directory and returns their absolute paths for the pipeline.
"""

import logging
from pathlib import Path

import streamlit as st

from app import session_state as state
from storage.session_manager import get_or_create_session

logger = logging.getLogger(__name__)

# PDFs larger than this are rejected before extraction to avoid memory
# exhaustion in Docling and the HF Inference API.
_MAX_MB = 20
_MAX_BYTES = _MAX_MB * 1024 * 1024


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def store_uploads(pdf_dir: Path, files: list[tuple[str, bytes]]) -> list[Path]:
    """Write accepted uploads into the session directory.

    A file whose name is already stored is replaced when its bytes differ.
    Files left in the directory from an earlier selection are removed, so
    a PDF dropped from the uploader is not kept for a later run.

    Args:
        pdf_dir: Session directory that holds uploaded PDFs.
        files: Pairs of original filename and file bytes, already size-checked.

    Returns:
        Absolute paths of the files kept, in upload order.
    """
    pdf_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    keep: set[str] = set()

    for name, data in files:
        safe_name = _file_name(name)
        if not safe_name or safe_name in {".", ".."}:
            logger.warning("Rejected upload with an unsafe name: %r", name)
            continue
        dest = pdf_dir / safe_name
        if not dest.exists() or dest.read_bytes() != data:
            dest.write_bytes(data)
            logger.debug("Saved: %s", dest)
        keep.add(safe_name)
        paths.append(dest)

    for existing in pdf_dir.iterdir():
        if existing.is_file() and existing.name not in keep:
            existing.unlink()
            logger.info("Removed upload no longer in the batch: %s", existing.name)

    return paths


def _file_name(name: str) -> str:
    """Return the last path segment, on either separator.

    ``Path.name`` treats ``\\`` as a separator only on Windows. A name such
    as ``..\\nested\\secret.pdf`` would otherwise be stored verbatim on Linux.
    """
    return Path(name.replace("\\", "/")).name


def render() -> list[Path]:
    """Render the PDF upload widget and return paths to accepted files.

    Validates each file for type (enforced by Streamlit) and size.
    Accepted files are written to the session temporary directory. A later
    upload with the same name replaces the stored bytes. A file removed
    from the uploader is deleted from that directory.

    Returns:
        Absolute paths to the saved PDFs, ready for the pipeline.
        Empty list if no valid files have been uploaded yet.
    """
    st.subheader("Upload documents")

    uploaded = st.file_uploader(
        label="Upload one or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        disabled=state.is_processing(),
        help=f"Maximum {_MAX_MB} MB per file.",
    )

    session = get_or_create_session(state.session_id())

    if not uploaded:
        store_uploads(session.pdf_dir, [])
        state.set_uploaded_files([])
        st.info("Upload at least one PDF to get started.")
        return []

    paths: list[Path] = []
    rejected: list[str] = []
    accepted: list[tuple[str, bytes]] = []

    for file in uploaded:
        if file.size > _MAX_BYTES:
            rejected.append(
                f"{file.name} ({file.size / 1024 / 1024:.1f} MB — limit {_MAX_MB} MB)"
            )
            logger.warning(
                "Rejected oversized file: %s (%d bytes)", file.name, file.size
            )
            continue
        accepted.append((file.name, file.getvalue()))

    paths = store_uploads(session.pdf_dir, accepted)

    if rejected:
        st.error(
            "Files rejected (size limit exceeded):\n"
            + "\n".join(f"- {r}" for r in rejected)
        )

    if paths:
        st.success(f"{len(paths)} file(s) ready: " + ", ".join(p.name for p in paths))

    state.set_uploaded_files(uploaded)
    return paths
