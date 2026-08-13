"""Ingest the current official CPC ENSO probability forecast.

Downloads the CPC probabilities page, parses the per season phase probabilities
with official_forecast.parse_cpc_probabilities (the same parser the gate proves
offline on a fixture), and writes data/forecast/cpc_official.json plus a
provenance sidecar. Network at the edges only; never imported by the offline gate.

Run from the repo root with the project venv:
    .venv/bin/python tools/ingest_cpc_forecast.py
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from enso_watch import sources
from enso_watch.official_forecast import parse_cpc_probabilities

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "forecast")
OUT = os.path.join(OUT_DIR, "cpc_official.json")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"pulling {sources.CPC_FORECAST_URL} ...", flush=True)
    raw = sources.download(sources.CPC_FORECAST_URL, os.path.join(ROOT, "data", "_incoming", "roni_probabilities.html"))
    with open(raw, encoding="utf-8") as fh:
        parsed = parse_cpc_probabilities(fh.read())

    pulled_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "issued": parsed["issued"],
        "seasons": parsed["seasons"],
        "provenance": {
            "source": "NOAA CPC official ENSO probabilities",
            "retrieval_url": sources.CPC_FORECAST_URL,
            "pull_timestamp": pulled_at,
            "phase_definition": "El Nino > +0.5 C, La Nina < -0.5 C, Nino 3.4, 1991-2020 base (RONI)",
            "note": "Phase probabilities per overlapping 3 month season. IRI stopped "
                    "publishing the numeric plume, so this is the machine readable official forecast.",
        },
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, OUT)
    print(f"done. issued {parsed['issued']}, {len(parsed['seasons'])} seasons. "
          f"first {parsed['seasons'][0]['season']} "
          f"(EN {parsed['seasons'][0]['p_el_nino']}%)", flush=True)


if __name__ == "__main__":
    main()
