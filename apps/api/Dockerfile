FROM python:3.12-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install monorepo packages first
COPY packages/database /packages/database
COPY packages/ai /packages/ai
COPY packages/integrations /packages/integrations
COPY packages/hermes /packages/hermes
COPY packages/bots /packages/bots
RUN pip install --no-cache-dir -e /packages/database && \
    pip install --no-cache-dir -e /packages/ai && \
    pip install --no-cache-dir -e /packages/integrations && \
    pip install --no-cache-dir -e /packages/hermes && \
    pip install --no-cache-dir -e /packages/bots

# Install API package
COPY apps/api/pyproject.toml /app/apps/api/
RUN pip install --no-cache-dir -e /app/apps/api[dev]

# Copy API source
COPY apps/api/src /app/apps/api/src

WORKDIR /app/apps/api
EXPOSE 8000
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
