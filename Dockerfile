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


# ── Stage 3: ETL (one-shot pipeline runner) ────────────────────
FROM python-base AS etl

# data/ and data_cleaned/ are mounted as volumes at runtime
CMD ["uv", "run", "python", "main.py"]


# ── Stage 4: Skillhub API server ──────────────────────────────
FROM python-base AS skillhub

# Inject the pre-built React frontend so FastAPI can serve it
COPY --from=frontend-builder /frontend/dist ./skillhub/frontend/dist

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/dashboard/stats')"

CMD ["uv", "run", "uvicorn", "skillhub.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ── Stage 5: OpenClaw agent (Telegram) ─────────────────────────
# Reuses python-base (venv + all skill dependencies already installed by uv)
# and adds Node.js + the OpenClaw CLI so the agent can run its Python skills.
FROM python-base AS agent

# Node.js 22 (NodeSource) — the OpenClaw CLI requires Node >= 22.12
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Pin the OpenClaw CLI to the version the project was built/tested against
RUN npm install -g openclaw@2026.5.7

# Put the project venv first on PATH so the skills' bare `python ...` commands
# resolve to this project's interpreter + dependencies (matches start.ps1).
ENV PATH="/app/.venv/bin:${PATH}"

# Keep OpenClaw config + state scoped to this project (mirrors start.ps1):
#   OPENCLAW_HOME        -> state in /app/.openclaw (sessions, outbound media)
#   OPENCLAW_CONFIG_PATH -> the repo-tracked config
ENV OPENCLAW_HOME="/app" \
    OPENCLAW_CONFIG_PATH="/app/openclaw/openclaw.json"

# The agent workspace is openclaw/ — skill script paths are relative to it.
WORKDIR /app/openclaw

CMD ["openclaw", "gateway", "run"]
