# Dockerfile
#
# Builds the production image for Hugging Face Spaces.
# Installs production dependencies only (no Python dev group).
# Docling models download on the first extraction, not during this build.
# .dockerignore keeps .env and PDFs out of the build context.

FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-group dev --frozen

COPY . .
COPY --from=web /web/dist ./web/dist

EXPOSE 8501

CMD ["uv", "run", "python", "-m", "app"]
