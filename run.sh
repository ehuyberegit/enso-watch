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
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
cmd="${1:-test}"
case "$cmd" in
  test)  exec "$PY" tools/run_tests.py ;;
  emit)  exec "$PY" -m enso_watch.cli ;;
  pull)  exec "$PY" -m enso_watch.pull ;;
  smoke) exec "$PY" -m enso_watch.smoke ;;
  serve) exec "$PY" -m enso_watch.dashboard ;;
  baselines) exec "$PY" tools/run_baselines.py ;;
  forecast) exec "$PY" tools/ingest_cpc_forecast.py ;;
  *) echo "usage: ./run.sh [test|emit|pull|smoke|serve|baselines|forecast]" >&2; exit 2 ;;
esac
