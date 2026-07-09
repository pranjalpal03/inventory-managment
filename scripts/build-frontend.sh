#!/usr/bin/env bash
# Render / CI build script for frontend static deploy
set -euo pipefail
cd "$(dirname "$0")/../frontend"

npm ci

if [ -n "${VITE_API_BASE:-}" ]; then
  export VITE_API_BASE
elif [ -n "${API_HOST:-}" ]; then
  export VITE_API_BASE="https://${API_HOST}/api"
fi

echo "Building with VITE_API_BASE=${VITE_API_BASE:-/api}"
npm run build
