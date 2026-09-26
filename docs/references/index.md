# Local references

Notes on how this repo uses a library. They are not the upstream manual. If the code and a note diverge, the code wins and the note is corrected.

| Note | Library | Used in |
|---|---|---|
| [`docling.md`](docling.md) | Docling, HybridChunker | `pipeline/extractor.py` |
| [`embeddings.md`](embeddings.md) | Hugging Face Inference, Chroma, e5 | `pipeline/embedder.py`, `pipeline/vector_store.py` |

Other pieces, without their own note, because the code is the short reference:

- Streamlit in `app/`. One page, no multipage app.
- Pydantic v2 and pydantic-settings in `models/` and `config/settings.py`.
- LangGraph is in `pyproject.toml` and no module imports it (TD-13).
- LLM providers in `services/llm_client.py`: Anthropic via its SDK; OpenAI via its SDK; DeepSeek (`https://api.deepseek.com/v1`) and Gemini (`https://generativelanguage.googleapis.com/v1beta/openai`) via the OpenAI-compatible client. Call `max_tokens`: 1024.
