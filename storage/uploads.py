"""Write the current upload set into a session directory."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_MB = 20
MAX_BYTES = MAX_MB * 1024 * 1024


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
        safe_name = file_name(name)
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


def file_name(name: str) -> str:
    """Return the last path segment, on either separator.

    ``Path.name`` treats ``\\`` as a separator only on Windows. A name such
    as ``..\\nested\\secret.pdf`` would otherwise be stored verbatim on Linux.
    """
    return Path(name.replace("\\", "/")).name


def list_accepted(pdf_dir: Path) -> list[str]:
    """Return stored PDF names in directory order."""
    if not pdf_dir.is_dir():
        return []
    return sorted(path.name for path in pdf_dir.iterdir() if path.is_file())
