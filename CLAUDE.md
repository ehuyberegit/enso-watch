# enso-watch: director

> This file is the project's CLAUDE.md: the SPECIFICS of this work.
> The doctrine (who I am, how I work: the tiers, the self harness loop, the security
> rules) lives in `~/.claude/CLAUDE.md` and holds for every project.
> The roles and procedures (reviewer, worker, run contract, the loop) come from the
> `engine` crew plugin, available everywhere.
> The frozen run contract and the roadmap live in `.claude/ROADMAP.md`.

## The product
enso-watch is a truth first pipeline that tracks the live ENSO signal (El Nino, neutral, La Nina) day by day from authoritative public data. V0 ships the observation oracle: a clean, versioned JSON dataset of the Nino 3.4 sea surface temperature anomaly, computed by us from NOAA OISST, plus the official ONI status, refreshed daily by an automated workflow and committed to the repo. It is an open world project: the truth is a living external feed that moves every day, so provenance rides every number and nothing is asserted without its source.

## Glossary
- **ENSO**: the El Nino Southern Oscillation, the Pacific warm and cold cycle.
- **Nino 3.4**: the ocean region (5N to 5S, 170W to 120W) whose SST anomaly is the headline ENSO signal.
- **Anomaly**: how far the SST sits above or below the fixed 1991 to 2020 climatology baseline.
- **OISST**: NOAA daily quarter degree sea surface temperature (netCDF), the raw source we compute from.
- **ONI**: the official Oceanic Nino Index (NOAA CPC), the ENSO phase and strength label. Used as status and as the control on our own number.
- **Oracle**: one question the project answers. Observation (where ENSO is now, V0), forecast (where it heads, V1), impact (who it hits, a separate later track).
- **Provenance block**: source name, dataset version, retrieval url, pull timestamp, preliminary or final status. Attached to every record.
- **Fixture**: a captured real source response, frozen, that feeds the offline deterministic test.

## Stack & machine gate
Python, with a minimal pinned dependency set (numpy and netCDF4, in requirements.txt). Adding a dependency is a decision, not a convenience. The V0 product is the JSON dataset, not a UI; a private local dashboard (`./run.sh serve`, stdlib only, no new dependency) is a read only lens over that JSON, not a shipped surface. Automation is a GitHub Actions scheduled daily workflow that pulls, recomputes, and commits the dated JSON into the repo.

Layout: the pipeline code lives under `src/enso_watch/`, the tests under `tests/`, one time capture tools under `tools/`, the frozen fixtures under `fixtures/` (with a provenance MANIFEST.json), the static dashboard page under `ui/`.

THE MACHINE GATE: `./run.sh test` runs the deterministic suite offline (the frozen fixture in, the expected value out, compared to 3 decimals) and exits 0 (green) or non zero (red). It runs behind a proven socket guard and never touches the network. It needs the project venv: create it once with `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

Other commands: `./run.sh emit` prints the V0 JSON product from the frozen fixtures. `./run.sh pull` performs the live daily pull (download the real sources, run the same transform, write a dated JSON to data/). `./run.sh smoke` is the live smoke check: it reaches the real sources and confirms their shape, reporting without ever gating. `./run.sh serve` opens the private local dashboard (see below). Live network I/O uses curl (robust and ubiquitous, present on CI runners), not stdlib urllib, which hangs against some NOAA hosts on the stock macOS Python. The pull and smoke are outside the gate: the network is never a test dependency.

The dashboard (a private local lens, not a shipped surface): `./run.sh serve` derives one time series from the committed dated JSON files, then serves a static tabbed page on localhost (`ui/index.html`) and opens the browser. It is read only and private (localhost, no host, no account). It renders the JSON and its provenance, it invents nothing, and it is NOT a second source of truth: the truth stays the JSON in git. Three tabs mirror the three oracles: Observation (V0, live), Forecast (V1, empty state), Impact (later track, empty state). The derived `ui/series.json` is gitignored (rebuilt on every serve). The aggregation logic lives in `src/enso_watch/dashboard.py` and is tested offline by the gate.

## Domain & security rules specific to this project
- **False by default**: no number ships without a complete, non empty provenance block.
- **The baseline is fixed at 1991 to 2020**, written into every record, never changed silently. Changing it would silently rewrite history.
- **We compute the Nino 3.4 anomaly ourselves** from OISST. The CPC monthly file is the control, not the source. We record the gap between our value and the official one.
- **Uncertainty is first class** (V1): a forecast carries its full spread, never a single naked number.
- **The network is never a test dependency**: the gate is offline on a fixture, the live pull is production.
- **Secrets** (for example the future FEWS NET key) live in a gitignored `.env`, never committed.
