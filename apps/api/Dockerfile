FROM python:3.12-slim AS base
WORKDIR /app

# System deps: build tools + Playwright dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl ca-certificates \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# ─── Step 1: Copy pyproject.toml files to extract dependencies ──────────
COPY packages/ai/pyproject.toml /packages/ai/pyproject.toml
COPY packages/database/pyproject.toml /packages/database/pyproject.toml
COPY packages/hermes/pyproject.toml /packages/hermes/pyproject.toml
COPY packages/integrations/pyproject.toml /packages/integrations/pyproject.toml
COPY packages/bots/pyproject.toml /packages/bots/pyproject.toml
COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml

# ─── Step 2: Extract & install all dependencies ─────────────────────────
COPY apps/api/extract_deps.py /tmp/extract_deps.py
RUN python3 /tmp/extract_deps.py && pip install --no-cache-dir -r /tmp/requirements.txt

# ─── Step 3: Copy package source code ───────────────────────────────────
COPY packages/ai /packages/ai
COPY packages/database /packages/database
COPY packages/hermes /packages/hermes
COPY packages/integrations /packages/integrations
COPY packages/bots /packages/bots

# ─── Step 4: Install optional ML packages (graceful fallback if they fail) ──
RUN pip install --no-cache-dir mem0ai 2>/dev/null || echo "mem0ai skipped (optional)"
RUN pip install --no-cache-dir sentence-transformers 2>/dev/null || echo "sentence-transformers skipped (optional)"

# ─── Step 5: Install scraping tools (browser automation, web reading) ────
# Obscura — lightweight Rust headless browser (80MB, fast, stealth)
RUN curl -sL https://github.com/h4ckf0r0day/obscura/releases/download/v0.1.10/obscura-x86_64-linux.tar.gz \
    -o /tmp/obscura.tar.gz \
    && tar -xzf /tmp/obscura.tar.gz -C /tmp/ \
    && mv /tmp/obscura /usr/local/bin/obscura \
    && chmod +x /usr/local/bin/obscura \
    && rm /tmp/obscura.tar.gz /tmp/obscura-worker 2>/dev/null; echo "obscura installed"

# Agent-Reach — platform connectivity (web reading, search, YouTube, GitHub, etc.)
RUN pip install --no-cache-dir git+https://github.com/Panniantong/Agent-Reach.git 2>/dev/null \
    || echo "agent-reach skipped (optional)"

# Browser-Use — full browser automation with Playwright
RUN pip install --no-cache-dir browser-use 2>/dev/null \
    && python3 -m playwright install chromium 2>/dev/null \
    || echo "browser-use skipped (optional)"

# ─── Step 6: Add monorepo source dirs to Python path ────────────────────
# Each package's import root is wherever __init__.py lives (src/ or root/)
ENV PYTHONPATH=\
/packages/ai:\
/packages/database/src:\
/packages/hermes/src:\
/packages/bots/src

# ─── Step 7: Copy API and run ──────────────────────────────────────────
COPY apps/api/src /app/apps/api/src

WORKDIR /app/apps/api
EXPOSE 8000
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]