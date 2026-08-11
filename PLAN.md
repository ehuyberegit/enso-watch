# enso-watch, production plan (V0 and V1)

> Staging document. This folder holds only this plan for now. The first act of the
> build session is to scaffold the project (which lays the chef and pins the crews),
> then formalize the run contract from this plan, then build. Written in English
> (estate rule), no dashes (Trinity constitution).

## What enso-watch is

A truth first pipeline that tracks the live super El Nino day by day from
authoritative public data. It is an **open world** project: its truth is not a frozen
corpus (that was Astrolab) but a **living external feed** that moves every day. So it
carries the data discipline at project scale, provenance on every number, false by
default, uncertainty kept explicit.

V0 tracks the **observation oracle** only (where ENSO is, right now). V1 overlays the
**forecast oracle** (where it is heading) and the **impact oracle** (who it hits, and
when), by aggregating what official bodies already publish, without inventing a
prediction of our own.

## The frozen decisions (the run contract seed)

| Axis | Decision |
| --- | --- |
| V0 output form | Pipeline plus data only (clean versioned JSON, no UI yet) |
| V0 sources | Observation only: OISST daily SST, plus NOAA CPC ONI status |
| V0 freshness | Live daily pull |
| V0 automation | GitHub Actions scheduled workflow, commits the JSON into the repo |
| V0 test gate | Frozen fixture snapshot for deterministic tests, alongside the live pull |
| Stack | Python plus a minimal pinned dependency set (netCDF and geospatial) |
| V1 ambition | Aggregate the official (IRI plume plus FEWS NET), no own prediction |
| Tooling | Build ingestion inside the project first, extract a data crew on proof |

## The truth architecture (why this project differs from Astrolab)

Astrolab was a closed world: a frozen corpus, a fully offline test gate, correctness
scored against known outcomes. enso-watch is the open world twin. The reconciliation
that makes it still verifiable:

- The **live pull** feeds production (the daily commit of fresh data).
- A **frozen fixture** (a captured snapshot of a real source response) feeds the test
  gate, so the pipeline transform is proven deterministic and offline, exactly like
  Astrolab. The two coexist: live data is the product, the fixture is the proof.

This keeps a machine verifiable "done" even though the world moves under us.

## V0, scope and machine verifiable done

**Deliverable.** A clean, versioned JSON dataset plus the pipeline that produces it,
refreshed daily and committed to the repo by an automated workflow.

**Sources (observation oracle).**
- **OISST v2.1** daily sea surface temperature (quarter degree grid, 1981 to present,
  updated daily). The pipeline computes the **Nino 3.4 anomaly** itself by area
  averaging the region (5N to 5S, 170W to 120W) against a documented climatology
  baseline. This is the load bearing piece, and it is what justifies the netCDF
  dependency.
- **NOAA CPC ONI** table (monthly), for the official ENSO status and strength label.

**Output contract (the JSON).** Two products:
- A **daily series**: date, Nino 3.4 SST anomaly, computed by us.
- A **status record**: latest ONI value, ENSO phase (El Nino, neutral, La Nina),
  strength band, official alert status.
- Every record carries a **provenance block**: source name, dataset version, retrieval
  URL, and the pull timestamp. No number without its source.

**Automation.** A GitHub Actions scheduled workflow runs daily, pulls, recomputes,
and commits the updated JSON. The data history therefore lives in git (native
provenance, and the-map could read it later).

**Definition of done (all machine checkable).**
1. `run test` is green: the pipeline turns the frozen fixture into the exact expected
   JSON, offline, deterministically.
2. A separate live smoke check confirms the real source is reachable and its shape is
   unchanged. It reports, it never gates the build (network is not a test dependency).
3. The scheduled workflow runs end to end and commits a dated JSON on a clean run.
4. Every output record has a complete, non empty provenance block (a structural test).
5. The README states how to run it, and no shipped document contradicts a command a
   reader can run.

## V1, scope and done

**Add the forecast oracle.** Ingest the **IRI/CPC ENSO plume** (probabilistic Nino 3.4
forecast, the multi model spread). Uncertainty is first class: outputs carry the
distribution (the spread), never a single naked number.

**Add the impact oracle.** Ingest the **FEWS NET** outlooks for the current episode
(free account, key in a gitignored .env). Overlay their country level food security
projections. We aggregate and make legible what they publish, we do not model impact
ourselves.

**Definition of done.**
1. The forecast product carries the full plume spread, not a point value, proven by a
   structural test on the fixture.
2. The impact product traces each country entry to a FEWS NET source and date.
3. The provenance and false by default discipline holds across all three oracles.
4. The daily workflow now refreshes observation, forecast, and impact together.

## Build sequence

**V0**
1. Scaffold enso-watch in laboratory (chef plus pinned crews), freeze the run contract
   from this plan.
2. Capture one real OISST response and one ONI response as frozen fixtures.
3. Write the Nino 3.4 computation (area average against the baseline) against the
   fixture, test it to the exact expected value.
4. Write the JSON output contract and its provenance block, with a structural test.
5. Wire the live pull (network) behind the same transform, plus the live smoke check.
6. Add the GitHub Actions daily workflow that pulls, recomputes, and commits.
7. README and decision log. Ship V0.

**V1**
8. Add the IRI plume ingestion, uncertainty carried through, fixture and test.
9. Add the FEWS NET ingestion (key in .env), country overlay, fixture and test.
10. Extend the daily workflow to the three oracles. README update. Ship V1.

## The harness side (what feeds back to the-workspace)

The five ideas from the framing map onto this project cleanly, and honestly:

- Ideas **1 (data ingestion), 2 (data provenance), 5 (uncertainty first class)** are
  exercised by V0 and V1. Once their shape is proven in enso-watch, extract them into a
  reusable **data crew** in the-workspace (single sourced tooling, add on proof). Not
  before: we build in the project first, harden into a crew once it recurs.
- Ideas **3 (the backtest gate) and 4 (Trinity on physical invariants)** are **not
  needed** for V0 or V1, because V1 only aggregates official products and makes no
  prediction of its own. They become relevant only if a later V2 builds our own impact
  or forecast model. Flagged here so nobody builds them prematurely.

## Known risks and honest limits

- **Impact prediction is the research frontier.** V1 deliberately only aggregates
  official outlooks (FEWS NET). Claiming to out forecast them would be fanfaronnade.
- **Latency.** OISST daily has a short lag (a day or two). "Day by day" means data day,
  not real time.
- **Baseline choice.** The Nino 3.4 anomaly depends on the climatology baseline
  (for example 1991 to 2020). Pick one, document it, keep it fixed. Changing it later
  silently would rewrite history.
- **FEWS NET needs a free account and key.** It lives in a gitignored .env, never
  committed (estate security rule).
- **Source shape drift.** A public source can change its format. The live smoke check
  is there to catch it early and loudly.

## Sources (verified)

- NOAA CPC ONI: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/
- NOAA OISST (NCEI): https://www.ncei.noaa.gov/products/optimum-interpolation-sst
- NOAA PSL climate indices: https://psl.noaa.gov/data/climateindices/list/
- IRI ENSO forecast: https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/
- Copernicus Climate Data Store: https://cds.climate.copernicus.eu/
- FEWS NET, current El Nino: https://fews.net/topics/el-nino-2026-2027
- FEWS NET API: https://help.fews.net/fdw/fews-net-api
- NOAA and FEWS NET historic ENSO impacts: https://psl.noaa.gov/enso/fewsnet/
