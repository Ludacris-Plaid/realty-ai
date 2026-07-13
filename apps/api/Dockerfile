FROM python:3.12-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# ─── Step 1: Copy pyproject.toml files to extract dependencies ──────────
COPY packages/ai/pyproject.toml /packages/ai/pyproject.toml
COPY packages/database/pyproject.toml /packages/database/pyproject.toml
COPY packages/hermes/pyproject.toml /packages/hermes/pyproject.toml
COPY packages/integrations/pyproject.toml /packages/integrations/pyproject.toml
COPY packages/bots/pyproject.toml /packages/bots/pyproject.toml
COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml

# ─── Step 2: Extract & install all dependencies ─────────────────────────
RUN echo "Collecting dependencies..." && python3 -c "
import tomllib, os

deps = set()
for path, extra in [
    ('/packages/ai/pyproject.toml', []),
    ('/packages/database/pyproject.toml', []),
    ('/packages/hermes/pyproject.toml', []),
    ('/packages/integrations/pyproject.toml', []),
    ('/packages/bots/pyproject.toml', []),
    ('/app/apps/api/pyproject.toml', ['dev']),
]:
    if not os.path.exists(path):
        continue
    with open(path) as f:
        data = tomllib.load(f)
    for dep in data.get('project', {}).get('dependencies', []):
        clean = dep.strip().strip('\"').strip(\"'\")
        if clean:
            deps.add(clean)
    # Also add optional dev deps
    for opt in extra:
        for dep in data.get('project', {}).get('optional-dependencies', {}).get(opt, []):
            clean = dep.strip().strip('\"').strip(\"'\")
            if clean:
                deps.add(clean)

with open('/tmp/requirements.txt', 'w') as f:
    f.write('\n'.join(sorted(deps)))

print(f'{len(deps)} dependencies extracted')
" && pip install --no-cache-dir -r /tmp/requirements.txt

# ─── Step 3: Copy package source code ───────────────────────────────────
COPY packages/ai /packages/ai
COPY packages/database /packages/database
COPY packages/hermes /packages/hermes
COPY packages/integrations /packages/integrations
COPY packages/bots /packages/bots

# ─── Step 4: Install mem0ai (optional, graceful fallback) ───────────────
RUN pip install --no-cache-dir mem0ai 2>/dev/null || echo "mem0ai skipped (optional)"

# ─── Step 5: Add monorepo source dirs to Python path ────────────────────
# Each package's import root is wherever __init__.py lives (src/ or root/)
ENV PYTHONPATH=\
/packages/ai:\
/packages/database/src:\
/packages/hermes/src:\
/packages/integrations:\
/packages/bots/src

# ─── Step 6: Copy API and run ──────────────────────────────────────────
COPY apps/api/src /app/apps/api/src

WORKDIR /app/apps/api
EXPOSE 8000
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]