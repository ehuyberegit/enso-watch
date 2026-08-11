# enso-watch

A truth first pipeline that tracks the live ENSO signal (El Nino, neutral, La Nina) day by day from authoritative public data. V0 ships the **observation oracle**: a clean, versioned JSON dataset of the Nino 3.4 sea surface temperature anomaly, computed from NOAA OISST, plus the official ONI status. Refreshed daily by an automated workflow and committed to the repo.

## Quick start

### Prerequisites
- Python 3.9+
- curl (for network I/O)
- netCDF4, numpy (see `requirements.txt`)

### Setup
```bash
# Create the virtual environment and install dependencies
git clone <repo-url>
cd enso-watch
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Commands
All commands are run from the project root via `./run.sh`:

| Command | Description |
|---------|-------------|
| `./run.sh test` | Run the deterministic test suite offline (frozen fixtures). Machine gate. |
| `./run.sh emit` | Emit the V0 JSON product to stdout from frozen fixtures. |
| `./run.sh pull` | Perform the live daily pull: download real sources, compute, write dated JSON to `data/`. |
| `./run.sh smoke` | Live smoke check: confirm real sources are reachable and unchanged. Reports only, never gates. |

Example:
```bash
# Run the test gate (offline, deterministic)
./run.sh test

# See the current V0 product (from frozen fixtures)
./run.sh emit

# Pull today's live data
./run.sh pull
```

## Output contract (V0)

The pipeline produces a dated JSON file in `data/enso-watch-{date}.json` with:

```json
{
  "daily_series": [
    {
      "date": "2026-08-10",
      "nino34_anomaly_c": 2.754,
      "region_mean_sst_c": 29.625,
      "climatology_mean_c": 26.871,
      "baseline": "1991-2020",
      "provenance": {
        "source": "NOAA OISST",
        "dataset_version": "v2.1",
        "retrieval_url": "https://www.ncei.noaa.gov/...",
        "pull_timestamp": "2026-08-11T22:29:02Z",
        "status": "preliminary"
      }
    }
  ],
  "status": {
    "oni_latest": 1.39,
    "oni_season": "MJJ 2026",
    "phase": "el_nino",
    "strength": "moderate",
    "our_nino34_vs_official": 1.314,
    "control_period": "2026-06",
    "provenance": {
      "source": "NOAA CPC ONI",
      "dataset_version": "ascii v6",
      "retrieval_url": "https://www.cpc.ncep.noaa.gov/...",
      "pull_timestamp": "2026-08-11T22:29:02Z",
      "status": "published"
    }
  }
}
```

### Provenance
Every record carries a **complete provenance block** with:
- `source`: data provider (e.g., NOAA OISST, NOAA CPC ONI)
- `dataset_version`: version of the dataset
- `retrieval_url`: direct URL to the source file
- `pull_timestamp`: UTC timestamp when the data was retrieved
- `status`: `final`, `preliminary`, or `published`

No number ships without a complete, non-empty provenance block.

## Data sources (V0)

| Source | Purpose | URL |
|--------|---------|-----|
| NOAA OISST v2.1 | Daily sea surface temperature (0.25 degree grid) | [NCEI](https://www.ncei.noaa.gov/products/optimum-interpolation-sst) |
| NOAA CPC ONI | Official Oceanic Nino Index (monthly) | [CPC](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/) |
| NOAA CPC Control | Monthly Nino 3.4 SST for cross-check | [CPC](https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii) |

## Automation

A GitHub Actions scheduled workflow runs daily at 12:00 UTC:
- Pulls the latest OISST and ONI data
- Computes the Nino 3.4 anomaly
- Commits the dated JSON to the `data/` directory
- Pushes to the repository

Workflow file: `.github/workflows/daily_pull.yml`

## Baseline and precision

- **Baseline**: 1991-2020 climatology (fixed, never changed silently)
- **Precision**: 3 decimal places for all numeric values
- **Anomaly computation**: cosine of latitude weighted area average over Nino 3.4 box (5N-5S, 170W-120W)

## Project layout

```
enso-watch/
├── src/enso_watch/          # Pipeline code
│   ├── nino34.py           # Nino 3.4 anomaly computation
│   ├── output.py           # JSON output assembly
│   ├── pull.py             # Live daily pull
│   ├── sources.py          # Source URLs and downloads
│   ├── provenance.py       # Provenance block validation
│   ├── smoke.py            # Live smoke check
│   ├── cli.py              # Offline emit command
│   └── ...
├── tests/                  # Deterministic test suite
├── fixtures/               # Frozen test fixtures + MANIFEST.json
├── data/                   # Output JSON products (committed)
├── data/_incoming/         # Raw downloads (gitignored)
├── tools/                  # One-off utilities
├── run.sh                  # Entry point
├── requirements.txt         # Python dependencies
└── README.md
```

## Testing

The test suite is **fully offline** and deterministic:
- Runs against frozen fixtures (captured real source responses)
- Validates the transform to 3 decimal places
- Checks provenance completeness on every record
- Confirms output shape and structure

```bash
# Run all tests
./run.sh test

# Run a single test module
PYTHONPATH="$PWD/src" .venv/bin/python -m unittest tests.test_nino34 -v
```

## V1 roadmap

V1 will add:
- **Forecast oracle**: IRI/CPC ENSO plume (probabilistic Nino 3.4 forecast)
- **Impact oracle**: FEWS NET country-level outlooks
- Extended daily workflow to refresh all three oracles

See `PLAN.md` for full details.

## License

This project is part of the Atlas estate. See the repository license for details.
