# enso-watch Progress Tracker

> Last updated: 2026-08-11
> Session: Mistral Vibe (closed)

---

## Current Status (2026-08-11)

### V0 - Observation Oracle: 98% COMPLETE

| Task | Status | Evidence |
|------|--------|----------|
| Scaffold + run contract | ✅ | Code in `src/`, `run.sh` |
| OISST/ONI fixtures captured | ✅ | `fixtures/oisst/`, `fixtures/cpc/` |
| Nino 3.4 transform + tests | ✅ | `nino34.py`, 29 tests OK |
| JSON contract + provenance | ✅ | `output.py`, `provenance.py` |
| Live pull (curl) | ✅ | `pull.py`, `sources.py` |
| Smoke check | ✅ | `smoke.py` |
| GitHub Actions workflow | ✅ | `.github/workflows/daily_pull.yml` |
| README.md | ✅ | Complete documentation |
| First data file | ✅ | `data/enso-watch-2026-08-10.json` (+2.754°C) |
| GitHub repo created | ✅ | https://github.com/ehuyberegit/enso-watch |
| First push to main | ✅ | Commit `ec05971` |

**Latest data**: 2026-08-10 → Nino 3.4 anomaly = **+2.754°C** (El Niño moderate)
**Latest commit**: `ec05971` - "Close V0: add README, GitHub Actions workflow, and first live pull output"

---

## Remaining for V0 (2 minor tasks)

| Task | Effort | Priority |
|------|--------|----------|
| Verify CI runs tomorrow (12:00 UTC) | 0h (automatic) | ⭐⭐⭐ |
| Add CI badge to README | 10 min | ⭐ |

**V0 will be 100% complete after the first automated CI run (2026-08-12 ~12:00 UTC).**

---

## V1 - Forecast + Impact Oracle Roadmap

### Overview
V1 adds two new oracles to the pipeline:
1. **Forecast Oracle**: IRI/CPC ENSO plume (probabilistic Nino 3.4 forecast)
2. **Impact Oracle**: FEWS NET country-level outlooks

### Detailed Steps

| Step | Task | Estimated Effort | Dependencies |
|------|------|------------------|--------------|
| 1 | Capture IRI plume + FEWS NET fixtures | 2h | FEWS NET account (free) |
| 2 | Write `src/enso_watch/forecast.py` | 3h | IRI fixtures |
| 3 | Write `src/enso_watch/impact.py` | 3h | FEWS NET API key |
| 4 | Extend JSON contract (add `forecast`, `impact`) | 1h | Design validation |
| 5 | Add unit tests | 2h | Fixtures ready |
| 6 | Update CI (pull forecast + impact) | 1h | V1 code ready |
| 7 | Update README | 1h | V1 functional |

**Total estimated effort**: ~13 hours (spread over 1-2 weeks)

### Technical Details

#### 1. Forecast Oracle (IRI Plume)
- **Source**: [IRI Columbia](https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/)
- **Data**: Quarterly probabilities (e.g., 60% El Niño in Q4 2026)
- **Format**: CSV or JSON to parse
- **Constraint**: Uncertainty first class → store full distribution, not averages

Example output:
```json
"forecast": {
  "plume": [
    {"period": "2026-Q4", "prob_el_nino": 0.60, "prob_la_nina": 0.05, "prob_neutral": 0.35},
    {"period": "2027-Q1", "prob_el_nino": 0.45, "prob_la_nina": 0.10, "prob_neutral": 0.45}
  ],
  "provenance": { ... }
}
```

#### 2. Impact Oracle (FEWS NET)
- **Source**: [FEWS NET API](https://help.fews.net/fdw/fews-net-api)
- **Data**: Country-level alerts (e.g., Ethiopia = "warning")
- **Prerequisite**: API key (free account)
- **Storage**: `.env` (gitignored) for the key

Example output:
```json
"impact": {
  "countries": [
    {"code": "ET", "name": "Ethiopia", "alert": "warning", "source_url": "..."},
    {"code": "KE", "name": "Kenya", "alert": "watch", "source_url": "..."}
  ],
  "provenance": { ... }
}
```

---

## Global Roadmap

| Version | Deliverable | Status | Target Date |
|---------|-------------|--------|-------------|
| V0 | Observation Oracle (Nino 3.4 + ONI) | 98% | Today |
| V1 | + Forecast Oracle (IRI) + Impact Oracle (FEWS NET) | 0% | Q4 2026 |
| V2 | (Optional) Custom impact model | TBD | 2027 |

---

## Known Data (2026-08-11)
- **Current ENSO**: Moderate El Niño
- **ONI value**: 1.39 (MJJ 2026)
- **Our Nino 3.4 anomaly**: +2.754°C (2026-08-10, preliminary)
- **Next data**: CI will generate `enso-watch-2026-08-11.json` tomorrow ~12:00 UTC

---

## Session Summary (2026-08-11)

### Actions Completed
1. **C**: Tested `./run.sh pull` locally → Success (anomaly +2.754°C)
2. **B**: Created `README.md` → Full documentation
3. **A**: Created `.github/workflows/daily_pull.yml` → Scheduled CI at 12:00 UTC
4. Created GitHub repo: https://github.com/ehuyberegit/enso-watch
5. Pushed all changes to `main` (commit `ec05971`)

### Files Changed
- `README.md` (new)
- `.github/workflows/daily_pull.yml` (new)
- `data/enso-watch-2026-08-10.json` (new)

### Next Immediate Step
- Verify CI runs automatically tomorrow (12:00 UTC)

---

## How to Interact with the Project

### Local Commands
```bash
# Run tests (29 tests, offline)
./run.sh test

# Pull latest data manually
./run.sh pull

# View data
cat data/enso-watch-*.json
cat data/enso-watch-*.json | jq .  # pretty-print

# View README
cat README.md

# View CI workflow
cat .github/workflows/daily_pull.yml
```

### GitHub
- **Repo**: https://github.com/ehuyberegit/enso-watch
- **CI Actions**: https://github.com/ehuyberegit/enso-watch/actions
- **Data files**: https://github.com/ehuyberegit/enso-watch/tree/main/data

---

*Generated by Mistral Vibe. Session closed 2026-08-11.*
