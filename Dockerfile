# syntax=docker/dockerfile:1.10
# ---------- base ----------
ARG PYTHON_VERSION=3.12.7
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=60 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl ca-certificates build-essential libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.10 /uv /uvx /usr/local/bin/

WORKDIR /workspace

# ---------- deps stage ----------
FROM base AS deps
COPY pyproject.toml ./
RUN uv pip install --system --compile-bytecode .[dev]

# ---------- dev stage (used by docker-compose) ----------
FROM deps AS dev
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git make postgresql-client \
    && rm -rf /var/lib/apt/lists/*
COPY . .
USER 1000:1000
CMD ["bash"]

# ---------- prod build stage ----------
FROM deps AS build
COPY src ./src
COPY pyproject.toml README.md ./
RUN uv pip install --system --compile-bytecode . \
    && python -m compileall -q /usr/local/lib/python3.12/site-packages/src

# ---------- prod runtime (distroless) ----------
FROM gcr.io/distroless/python3-debian12:nonroot AS prod
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
WORKDIR /workspace
USER nonroot
EXPOSE 8000
ENTRYPOINT ["python", "-m", "src.api.main"]
