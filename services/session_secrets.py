"""Optional per-session API key overrides for the UI cookie session.

Overrides live in UiState and are bound during pipeline runs. They are never
returned from HTTP responses.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from config.settings import settings

_bound: ContextVar[KeyOverrides | None] = ContextVar("jr_session_secrets", default=None)


@dataclass
class KeyOverrides:
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    deepseek_api_key: str | None = None
    huggingface_api_key: str | None = None

    def merge(self, patch: KeyOverrides) -> None:
        for name in (
            "anthropic_api_key",
            "openai_api_key",
            "gemini_api_key",
            "deepseek_api_key",
            "huggingface_api_key",
        ):
            value = getattr(patch, name)
            if value is not None:
                setattr(self, name, value or None)


def bind(overrides: KeyOverrides | None) -> object:
    return _bound.set(overrides)


def unbind(token: object) -> None:
    _bound.reset(token)  # type: ignore[arg-type]


def _effective(field: str) -> str:
    active = _bound.get()
    if active is not None:
        override = getattr(active, field, None)
        if override:
            return override
    return getattr(settings, field)


def active_llm_key_configured(overrides: KeyOverrides | None) -> bool:
    provider = settings.llm_provider
    field = {
        "anthropic": "anthropic_api_key",
        "openai": "openai_api_key",
        "gemini": "gemini_api_key",
        "deepseek": "deepseek_api_key",
    }[provider]
    if overrides is not None and getattr(overrides, field):
        return True
    return bool(getattr(settings, field))


def huggingface_key_configured(overrides: KeyOverrides | None) -> bool:
    if overrides is not None and overrides.huggingface_api_key:
        return True
    return bool(settings.huggingface_api_key)


def anthropic_api_key() -> str:
    return _effective("anthropic_api_key")


def openai_api_key() -> str:
    return _effective("openai_api_key")


def gemini_api_key() -> str:
    return _effective("gemini_api_key")


def deepseek_api_key() -> str:
    return _effective("deepseek_api_key")


def huggingface_api_key() -> str:
    return _effective("huggingface_api_key")
