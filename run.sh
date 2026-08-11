#!/usr/bin/env bash
# enso-watch entry point. Today it carries the offline machine gate.
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "no venv found. create it with:" >&2
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 2
fi
cmd="${1:-test}"
case "$cmd" in
  test) exec "$PY" tools/run_tests.py ;;
  *) echo "usage: ./run.sh test" >&2; exit 2 ;;
esac
