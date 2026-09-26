"""Test defaults so importing settings does not require a local .env."""

import os

os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("HUGGINGFACE_API_KEY", "test-key")
os.environ.setdefault("LLM_PROVIDER", "deepseek")
os.environ.setdefault("EMBEDDING_PROVIDER", "huggingface")
