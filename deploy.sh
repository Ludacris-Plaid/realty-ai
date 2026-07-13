#!/usr/bin/env bash
set -e

# RealtyAI Production Deploy Script
# Run as: bash deploy.sh

cd "$(dirname "$0")"

echo "=== Building API Docker image ==="
POSTGRES_PASSWORD=realty_local_dev docker compose -f docker-compose.prod.yml build api

echo "=== Stopping old containers ==="
docker rm -f realty-api 2>/dev/null || true

echo "=== Starting API ==="
docker run -d --name realty-api \
  --network realty-ai_default \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://realty:realty_local_dev@postgres:5432/realty_ai \
  -e LLM_API_BASE=https://api.featherless.ai/v1 \
  -e LLM_API_KEY=rc_39469c71f02a6f4d905bace1fff05adee3228beca9a0ddb85898ea20438d8435 \
  -e LLM_DEFAULT_MODEL=Qwen/Qwen3-4B-Instruct-2507 \
  -e LLM_FALLBACK_API_BASE=https://integrate.api.nvidia.com/v1 \
  -e LLM_FALLBACK_API_KEY=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 \
  -e LLM_FALLBACK_MODEL=meta/llama-3.1-8b-instruct \
  -e CORS_ORIGINS="http://localhost:3000,https://realty-ai-ten.vercel.app" \
  -e AUTH_SECRET_KEY=realty-ai-prod-secret \
  realty-ai-api:latest

echo "=== Checking health ==="
sleep 3
curl -s http://localhost:8000/health && echo ""
echo "=== Deploy complete ==="
