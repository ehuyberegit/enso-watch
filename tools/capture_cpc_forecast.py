"""Freeze the current CPC ENSO probability forecast page as a fixture.

One time fixture builder for the official-forecast parser test. Downloads the
live CPC probabilities page and freezes it, so the parser is proven offline
against a real, dated response. Records the fixture in fixtures/MANIFEST.json.

Run from the repo root with the project venv:
    .venv/bin/python tools/capture_cpc_forecast.py
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import manifest
from enso_watch import sources

OUT = "fixtures/cpc/roni_probabilities.html"


def main():
    tmp = sources.download(sources.CPC_FORECAST_URL, "data/_incoming/roni_probabilities.html")
    with open(tmp, encoding="utf-8") as fh:
        html = fh.read()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as out:
        out.write(html)
    retrieved_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest.record("cpc_enso_probabilities", OUT, sources.CPC_FORECAST_URL, retrieved_at,
                    note="The official CPC ENSO phase probability forecast page, fixture for "
                         "the official_forecast parser, built by tools/capture_cpc_forecast.py.")
    print("wrote", OUT, f"({len(html)} bytes)")


if __name__ == "__main__":
    main()
