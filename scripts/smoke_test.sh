#!/usr/bin/env bash
# Smoke test for the BrightWave stack — runs locally (no Docker).
# Starts the pdf renderer and backend, hits a few endpoints, then cleans up.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --- cleanup any prior runs ---
pkill -f "flask --app app" 2>/dev/null || true
pkill -f "node server.js" 2>/dev/null || true
sleep 1

LOGDIR=/tmp/bw_smoke
mkdir -p "$LOGDIR"
rm -f "$LOGDIR"/*.log

# --- start PDF renderer ---
cd "$ROOT/pdf_renderer"
STATEMENTS_DIR="$ROOT/statements" \
  nohup python3 -m flask --app app run -p 8001 \
  > "$LOGDIR/pdf.log" 2>&1 &
PDF_PID=$!
echo "Started PDF renderer (pid $PDF_PID)"

# --- start backend ---
cd "$ROOT/backend"
PORT=8000 RENDERER_URL=http://localhost:8001 ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-dummy} \
  nohup node server.js \
  > "$LOGDIR/backend.log" 2>&1 &
BE_PID=$!
echo "Started backend (pid $BE_PID)"

cleanup() { kill "$PDF_PID" "$BE_PID" 2>/dev/null || true; }
trap cleanup EXIT

# --- wait for both ---
for i in $(seq 1 20); do
  curl -fsS --max-time 1 http://localhost:8001/health >/dev/null 2>&1 && \
    curl -fsS --max-time 1 http://localhost:8000/api/health >/dev/null 2>&1 && break
  sleep 0.5
done

echo
echo "=== Renderer /health ==="
curl -sS http://localhost:8001/health; echo
echo
echo "=== Backend /api/health ==="
curl -sS http://localhost:8000/api/health; echo
echo
echo "=== Backend /api/statements ==="
curl -sS http://localhost:8000/api/statements | python3 -m json.tool
echo
echo "=== PDF passthrough (statement 3) ==="
curl -sS -o "$LOGDIR/s3.pdf" -w "HTTP %{http_code}  bytes=%{size_download}  type=%{content_type}\n" \
  http://localhost:8000/api/statements/3/pdf
echo
echo "=== System prompt size (sanity check) ==="
cd "$ROOT/backend"
node -e "
import('./lib/systemPrompt.js').then(async m => {
  const p = await m.buildSystemPrompt();
  console.log('System prompt characters:', p.length);
  console.log('First 240 chars:', p.slice(0, 240).replace(/\n/g,' \\\\n '));
});
"
