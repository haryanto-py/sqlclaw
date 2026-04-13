# =============================================================
# Multi-stage Dockerfile
#
# Stages:
#   frontend-builder  — builds the React app with Vite
#   python-base       — installs all Python deps via uv
#   etl               — runs the ETL pipeline (used by docker compose run etl)
#   skillhub          — serves the FastAPI backend + built React frontend
# =============================================================

# ── Stage 1: Build React frontend ─────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend

COPY skillhub/frontend/package*.json ./
RUN npm ci

COPY skillhub/frontend/ .
RUN npm run build


# ── Stage 2: Python base ──────────────────────────────────────
FROM python:3.12-slim AS python-base

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (Docker layer cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application source
COPY . .

# Inject the pre-built React frontend so FastAPI can serve it
COPY --from=frontend-builder /frontend/dist ./skillhub/frontend/dist


# ── Stage 3: ETL (one-shot pipeline runner) ────────────────────
FROM python-base AS etl

# data/ and data_cleaned/ are mounted as volumes at runtime
CMD ["uv", "run", "python", "main.py"]


# ── Stage 4: Skillhub API server ──────────────────────────────
FROM python-base AS skillhub

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/dashboard/stats')"

CMD ["uv", "run", "uvicorn", "skillhub.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
