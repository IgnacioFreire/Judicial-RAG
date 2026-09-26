# Dockerfile
#
# Builds the production image for Hugging Face Spaces.
# Installs production dependencies only (no dev group).
# Docling models download on the first extraction, not during this build.
# .dockerignore keeps .env and PDFs out of the build context.

FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --no-group dev --frozen

# Copy application code
COPY . .

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
