#!/usr/bin/env bash
set -euo pipefail

# Get script directory and go to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
cd "${PROJECT_ROOT}"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Default port if not set
PORT="${PORT:-8787}"

# Check for --reload flag (either via command line arg or ENABLE_RELOAD env var)
RELOAD_FLAG=""
if [[ "$*" == *"--reload"* ]] || [[ "${ENABLE_RELOAD}" == "true" ]]; then
    RELOAD_FLAG="--reload"
fi

# Run FastAPI server with uvicorn via uv
uv run python -m uvicorn src.main:app ${RELOAD_FLAG} --host 127.0.0.1 --port "${PORT}"
