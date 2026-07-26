#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
exec python3 -m uvicorn src.web.app:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
