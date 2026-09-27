"""Generation-token totals for the current UI session.

Counts come from provider usage fields. They are not a bill.
Embedding calls do not pass through here.
"""

from contextvars import ContextVar

_session_id: ContextVar[str | None] = ContextVar("jr_llm_session", default=None)
_counts: dict[str, list[int]] = {}


def bind(session_id: str) -> object:
    """Attach later model calls on this context to a session."""
    return _session_id.set(session_id)


def unbind(token: object) -> None:
    """Restore the previous session binding."""
    _session_id.reset(token)  # type: ignore[arg-type]


def add_tokens(input_tokens: int, output_tokens: int) -> None:
    """Add one model call to the bound session. No-op when nothing is bound."""
    session_id = _session_id.get()
    if not session_id:
        return
    bucket = _counts.setdefault(session_id, [0, 0])
    bucket[0] += input_tokens
    bucket[1] += output_tokens


def totals(session_id: str) -> tuple[int, int]:
    """Return input and output generation tokens for a session."""
    bucket = _counts.get(session_id, [0, 0])
    return bucket[0], bucket[1]


def clear(session_id: str) -> None:
    """Drop totals for a session. Reset uses this."""
    _counts.pop(session_id, None)
