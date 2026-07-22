#!/bin/sh
set -u

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
URL="http://127.0.0.1:43127/"

if command -v node >/dev/null 2>&1; then
  node "$APP_DIR/server.mjs" &
  SERVER_PID=$!
  trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM
  sleep 1
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true; fi
    wait "$SERVER_PID"
  else
    echo "The local server did not start. Open $APP_DIR/index.html in your browser. Portable mode uses a different browser-storage origin from local-server mode."
  fi
else
  echo "Node.js was not found. Open $APP_DIR/index.html in your browser. Portable mode uses a different browser-storage origin from local-server mode."
fi
