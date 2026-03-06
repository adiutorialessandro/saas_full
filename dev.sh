#!/usr/bin/env bash
set -e

PORT="${1:-5000}"

echo ">>> Using venv: $(which python)"
echo ">>> Trying port: $PORT"

# if port busy, show who uses it and switch port
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo ">>> Port $PORT is busy. Processes:"
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || true
  PORT=5050
  echo ">>> Switching to port: $PORT"
fi

export FLASK_ENV=development
python run.py --port "$PORT"
