# judicial-rag

Extracts, classifies, and answers variables over judicial PDFs. The user uploads the PDFs, defines the questions, and the agent returns each answer together with the exact fragment it came from.

Agent map: [`AGENTS.md`](AGENTS.md). Current behavior: [`docs/product-specs/`](docs/product-specs/index.md).

## Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| PDF extraction | Docling |
| Embeddings | Hugging Face Inference API |
| Vector store | ChromaDB (in memory, per session) |
| LLM | DeepSeek, Anthropic, OpenAI, or Gemini |
| Orchestration | `pipeline/orchestrator.py` |
| Validation | Pydantic v2 |
| Deployment | Hugging Face Spaces + Docker |

## Project layout

```
judicial-rag/
│
├── app/
│   ├── main.py
│   ├── components/
│   │   ├── uploader.py
│   │   ├── question_form.py
│   │   └── results_viewer.py
│   └── session_state.py
│
├── pipeline/
│   ├── orchestrator.py
│   ├── extractor.py
│   ├── embedder.py
│   ├── vector_store.py
│   └── rag_agent.py
│
├── models/
│   ├── document.py
│   └── query.py
│
├── services/
│   └── llm_client.py
│
├── storage/
│   ├── session_manager.py
│   └── cleanup.py
│
├── config/
│   └── settings.py
│
├── tests/
│   ├── test_document.py
│   ├── test_embedder.py
│   ├── test_extractor.py
│   ├── test_query.py
│   ├── test_rag_agent.py
│   └── fixtures/
│
├── docs/
├── AGENTS.md
├── .huggingface/
│   └── README.md
│
├── Dockerfile
├── CHANGELOG.md
├── pyproject.toml
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- An API key for the active LLM provider (DeepSeek by default) and a Hugging Face token for embeddings

## Installation

```bash
# Clone the repository
git clone https://github.com/IgnacioFreire/Judicial-RAG.git
cd judicial-rag

# Create the virtualenv and install dependencies
uv sync

# Copy and fill in environment variables
cp .env.example .env
```

Edit `.env`. The defaults in `.env.example` are DeepSeek plus Hugging Face:

```env
DEEPSEEK_API_KEY=sk-...
LLM_PROVIDER=deepseek
HUGGINGFACE_API_KEY=hf_...
```

## Usage

```bash
# Start the application
uv run streamlit run app/main.py
```

The interface is at `http://localhost:8501`. What the screen does is specified in [`docs/product-specs/`](docs/product-specs/index.md).

## Development

```bash
# Install development dependencies
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=pipeline --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format .
```

### Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/). Use `commitizen` for guided commit messages:

```bash
uv run cz commit
```

### Versioning

The project follows [Semantic Versioning](https://semver.org/). To bump the version:

```bash
uv run bump-my-version bump patch   # 0.1.0 → 0.1.1
uv run bump-my-version bump minor   # 0.1.0 → 0.2.0
uv run bump-my-version bump major   # 0.1.0 → 1.0.0
```

After a bump, update the changelog:

```bash
uv run cz changelog
```

## Deploying to Hugging Face Spaces

The project deploys to Hugging Face Spaces via Docker on every push to `main`.

Set the active LLM provider key and `HUGGINGFACE_API_KEY` as secrets on the Space. The default provider is DeepSeek, so that is `DEEPSEEK_API_KEY` unless `LLM_PROVIDER` is changed.

## Privacy and sensitive data

Session isolation and lifetime are specified in [`docs/product-specs/session.md`](docs/product-specs/session.md). Keys and logs are in [`docs/SECURITY.md`](docs/SECURITY.md).

## Version

`0.1.0`
