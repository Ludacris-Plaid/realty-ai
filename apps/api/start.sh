#!/bin/bash
set -e

# Lazy-install agent-reach at runtime (avoids slow GitHub clone during Docker build)
if ! command -v agent-reach &> /dev/null; then
    echo "Installing agent-reach (optional, background)..."
    pip install git+https://github.com/Panniantong/Agent-Reach.git --quiet 2>/dev/null &
fi

# Start the API server
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
