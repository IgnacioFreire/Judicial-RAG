"""Test defaults so importing settings does not require a local .env."""

import os

import pytest

os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("HUGGINGFACE_API_KEY", "test-key")
os.environ.setdefault("LLM_PROVIDER", "deepseek")
os.environ.setdefault("EMBEDDING_PROVIDER", "huggingface")


@pytest.fixture(autouse=True)
def memory_index():
    """Keep every test off Supabase. Each test gets an empty index."""
    from pipeline.index_store import use_memory_index

    return use_memory_index()
