#!/bin/bash
set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
URL="http://127.0.0.1:43127/"

if command -v node >/dev/null 2>&1; then
  node "$APP_DIR/server.mjs" &
  SERVER_PID=$!
  trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM
  sleep 1
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    open "$URL"
    wait "$SERVER_PID"
  else
    echo "The local server did not start. Opening portable mode instead. Portable mode has separate browser storage."
    open "$APP_DIR/index.html"
  fi
else
  echo "Node.js was not found. Opening portable mode; it has separate browser storage. Export a reviewed backup before changing launch modes."
  open "$APP_DIR/index.html"
fi
