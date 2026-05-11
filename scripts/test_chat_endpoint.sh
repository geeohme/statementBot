#!/usr/bin/env bash
# Test that the chat endpoint reaches the Anthropic SDK (not just errors locally).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

pkill -f "flask --app app" 2>/dev/null || true
pkill -f "node server.js" 2>/dev/null || true
sleep 1

cd "$ROOT/pdf_renderer"
STATEMENTS_DIR="$ROOT/statements" nohup python3 -m flask --app app run -p 8001 > /tmp/pdf.log 2>&1 &
PDF_PID=$!
cd "$ROOT/backend"
PORT=8000 RENDERER_URL=http://localhost:8001 ANTHROPIC_API_KEY=dummy nohup node server.js > /tmp/backend.log 2>&1 &
BE_PID=$!
trap "kill $PDF_PID $BE_PID 2>/dev/null || true" EXIT

# Wait for backend
for i in $(seq 1 20); do
  curl -fsS --max-time 1 http://localhost:8000/api/health >/dev/null 2>&1 && break
  sleep 0.5
done

echo "=== Chat with dummy key (expecting 401 from Anthropic, not 500) ==="
curl -sS -w "\nHTTP %{http_code}\n" -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

echo
echo "=== Bad payload (empty messages — expecting 400) ==="
curl -sS -w "\nHTTP %{http_code}\n" -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[]}'

echo
echo "=== Last 10 lines of backend log ==="
tail -10 /tmp/backend.log
