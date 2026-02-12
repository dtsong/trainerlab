#!/usr/bin/env bash
set -euo pipefail

# Benchmark /api/v1/japan/card-count-evolution latency.
#
# Required env vars:
#   BASE_URL   (default: http://localhost:8000)
#   AUTH_TOKEN (bearer token for beta-protected routes)
#
# Optional env vars:
#   ARCHETYPE  (default: Charizard ex)
#   DAYS       (default: 90)
#   TOP_CARDS  (default: 20)
#   RUNS       (default: 50)

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
ARCHETYPE="${ARCHETYPE:-Charizard ex}"
DAYS="${DAYS:-90}"
TOP_CARDS="${TOP_CARDS:-20}"
RUNS="${RUNS:-50}"

if [ -z "$AUTH_TOKEN" ]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

URL="${BASE_URL}/api/v1/japan/card-count-evolution?archetype=$(python - <<'PY'
import os
from urllib.parse import quote_plus
print(quote_plus(os.environ['ARCHETYPE']))
PY
)&days=${DAYS}&top_cards=${TOP_CARDS}"

echo "Benchmarking: $URL"
echo "Runs: $RUNS"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

for _ in $(seq 1 "$RUNS"); do
  curl -sS -o /dev/null \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -w "%{time_total}\n" \
    "$URL" >> "$tmp_file"
done

python - "$tmp_file" <<'PY'
import statistics
import sys

path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    samples = [float(line.strip()) for line in f if line.strip()]

if not samples:
    print("No samples collected")
    raise SystemExit(1)

samples_ms = sorted(x * 1000 for x in samples)
p50 = statistics.median(samples_ms)
idx = max(0, min(len(samples_ms) - 1, int(round(0.95 * len(samples_ms))) - 1))
p95 = samples_ms[idx]

print(f"p50: {p50:.1f} ms")
print(f"p95: {p95:.1f} ms")
print(f"min: {samples_ms[0]:.1f} ms")
print(f"max: {samples_ms[-1]:.1f} ms")
PY
