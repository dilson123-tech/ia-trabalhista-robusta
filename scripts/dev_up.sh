#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Checa .env
if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "ERROR: .env não encontrado em $ROOT_DIR/.env" >&2
  echo "Copie o exemplo: cp -n .env.example .env" >&2
  exit 1
fi

# Checa venv
if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "ERROR: .venv não encontrado em $ROOT_DIR/.venv" >&2
  echo "Crie o ambiente virtual, por exemplo:" >&2
  echo "  cd \"$ROOT_DIR/backend\"" >&2
  echo "  python -m venv ../.venv" >&2
  echo "  source ../.venv/bin/activate" >&2
  echo "  pip install -r requirements.txt" >&2
  exit 1
fi

cd "$ROOT_DIR/backend"
source "$ROOT_DIR/.venv/bin/activate"

uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8099 \
  --env-file "$ROOT_DIR/.env" \
  --reload
