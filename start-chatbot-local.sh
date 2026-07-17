#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/chatbot-backend"
SITE_DIR="$ROOT_DIR/hex41434.github.io"
VENV_DIR="$BACKEND_DIR/.venv"
BACKEND_PORT="${BACKEND_PORT:-8000}"
SITE_PORT="${SITE_PORT:-8080}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed or not on PATH."
  exit 1
fi

if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama is not responding at http://127.0.0.1:11434."
  echo "Start Ollama first, then run this script again."
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"

if [ -z "${OLLAMA_MODEL:-}" ]; then
  if ollama list | awk '{print $1}' | grep -qx "qwen2.5:7b"; then
    OLLAMA_MODEL="qwen2.5:7b"
  elif ollama list | awk '{print $1}' | grep -qx "llama3.2:1b"; then
    OLLAMA_MODEL="llama3.2:1b"
  else
    OLLAMA_MODEL="$(ollama list | awk 'NR == 2 {print $1}')"
  fi
fi

if [ -z "$OLLAMA_MODEL" ]; then
  echo "No Ollama models found. Pull one first, for example:"
  echo "  ollama pull qwen2.5:7b"
  exit 1
fi

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [ -n "${SITE_PID:-}" ]; then
    kill "$SITE_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

echo "Using Ollama model: $OLLAMA_MODEL"
echo "Starting chatbot API on http://127.0.0.1:$BACKEND_PORT"
(
  cd "$BACKEND_DIR"
  OLLAMA_MODEL="$OLLAMA_MODEL" \
  ALLOWED_ORIGINS="http://localhost:$SITE_PORT,http://127.0.0.1:$SITE_PORT" \
  "$VENV_DIR/bin/uvicorn" app.main:app --host 127.0.0.1 --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

echo "Starting website on http://127.0.0.1:$SITE_PORT"
(
  cd "$SITE_DIR"
  python3 -m http.server "$SITE_PORT" --bind 127.0.0.1
) &
SITE_PID=$!

echo
echo "Open this URL in your browser:"
echo "  http://127.0.0.1:$SITE_PORT"
echo
echo "Keep this terminal open. Press Ctrl+C to stop both servers."
wait
