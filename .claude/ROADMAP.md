# ROADMAP: enso-watch

> Operational source of truth. At the top: the current work's run contract.
> Rule: "Done" = integrated, green (machine gate), reviewed.

## 🚦 Run contract, current work (V0, the observation oracle)

> The spirit (Astrolab the company, not the take home): pragmatism over pilot theatre,
> a working system that ships real data, honesty about scope. So V0 is not a demo: it is
> a live daily pipeline whose truth is provable offline, whose every number carries its
> source, and whose limits are stated out loud.

### 1. Frozen decisions

| Axis | Decision |
| --- | --- |
| Scope split | V0 = observation oracle only. V1 = forecast oracle. Impact is a separate later track, not V0 or V1 (the word "impact" is too broad to scope now). |
| V0 output | A pipeline plus a clean, versioned JSON dataset. No UI. |
| The signal | We compute the Nino 3.4 anomaly OURSELVES from OISST daily SST, area averaged over 5N to 5S and 170W to 120W. This is the load bearing piece and it owns the netCDF dependency. |
| Baseline | Climatology fixed at 1991 to 2020. Written into every record. Never changed silently. |
| The control | The CPC monthly Nino 3.4 file (ersst5.nino.mth.91-20.ascii, same 1991 to 2020 base) is the cross check, not the source. We record the gap between our value and the official one. |
| Official status | ONI phase and strength label from the CPC ONI ascii file (oni.ascii.txt, clean plain text, seasonal SEAS/YR/TOTAL/ANOM). We read the ONI value (ANOM) and derive phase and strength from documented thresholds. The fixture capture found this clean source, so the earlier HTML fragility is retired. |
| Freshness | Live daily pull. The latest days arrive as `_preliminary` files, replaced later by final ones. |
| Automation | A GitHub Actions scheduled workflow pulls, recomputes, and commits the dated JSON into the repo. Data history lives in git. |
| Precision | The anomaly is frozen to 3 decimals (0.001 C, well under the physical noise). This is what makes the deterministic test stable. |
| Leap day | The 1991 to 2020 daily climatology has 365 entries and no February 29. A February 29 observation uses the February 28 climatology. Documented and fixed, never changed silently. |
| Provenance | Every record carries: source name, dataset version, retrieval URL, pull timestamp, and preliminary/final status. No number without its block. |
| Stack | Python, minimal pinned dependency set (netCDF and geospatial reading). Adding a dependency is a decision, not a convenience. |
| Test discipline | A frozen fixture (a captured real source response) feeds the offline deterministic gate. The live pull feeds production. The two coexist: the fixture is the proof, the live data is the product. |

### 2. Finish criteria (machine verifiable, the GO threshold)

Nothing ships until these are true. Four hard gates, one live report, one mixed.

| # | Criterion | What the machine checks | Verdict |
| --- | --- | --- | --- |
| 1 | Deterministic transform | Feed the frozen fixture to the pipeline, compare the produced JSON to the expected JSON to 3 decimals, offline. | Hard gate: identical = green, any diff = red. |
| 2 | Live smoke check | Reach the real OISST and CPC sources, confirm they respond and their shape (grid, columns) is unchanged. | Reports only. Never blocks the build (network is not a test dependency). |
| 3 | Workflow end to end | The scheduled workflow runs, recomputes, and commits a dated JSON on a clean run. | Hard gate: the job exits 0. |
| 4 | Provenance complete | Every output record has a non empty provenance block (source, version, url, timestamp, preliminary/final). | Hard gate (structural): one hole = red. |
| 5 | Docs do not lie | No command quoted in the README is false; no shipped document contradicts a runnable command; Trinity (no dashes) passes. | Mixed: the deterministic half is a probe, the rest is one review pass. |

**GO threshold**: the hard gates (1, 3, 4) are green, the live smoke (2) reports without a blocking error, and the docs (5) pass the probe plus one read. A single command carries the offline hard gates (1 and 4); the workflow carries 3.

### 3. The machine gate

A single command, `run test` (concretely `./run.sh test`), runs the deterministic suite offline and exits 0 (green) or non zero (red). It never touches the network. The live smoke check is a separate command that reports, it is not part of the gate.

### 4. The output contract (the JSON)

Two products in V0, each record carrying its provenance block.

- **Daily series** (the trajectory): `date`, `nino34_anomaly_c` (computed by us, 3 decimals), `region_mean_sst_c`, `baseline` ("1991-2020"), `provenance`.
- **Status record** (the official snapshot): `oni_latest`, `oni_season`, `phase` (el_nino / neutral / la_nina), `strength` (none / weak / moderate / strong / very_strong), `our_nino34_vs_official` (the gap to the CPC control) with `control_period` (the month that control came from), `provenance`.

### 5. Build sequence (V0)

1. Fill the chef (CLAUDE.md): product, glossary, stack, the machine gate, domain rules. Confirm the repo (enso-watch is now its own git repo, Atlas ignores the folder).
2. Capture one real OISST response and one CPC response as frozen fixtures.
3. Write the Nino 3.4 computation (area average against the 1991 to 2020 baseline) against the fixture, tested to the exact expected value at 3 decimals.
4. Write the JSON output contract and its provenance block, with a structural test.
5. Wire the live pull behind the same transform, plus the live smoke check.
6. Add the GitHub Actions daily workflow (pull, recompute, commit the dated JSON).
7. README and decision log, in the Astrolab spirit (what it does, what it costs, what is still wrong, honest limits). Ship V0.

## 🔥 In progress

_(V0. Build sequence steps 1 to 5 done. Next action: step 6, the GitHub Actions daily workflow that pulls, recomputes, and commits the dated JSON.)_

## ✅ Done

- Scaffold laid (chef, pinned crews, roadmap, signatures, design).
- Sources verified live: OISST daily netCDF path and file naming, CPC Nino 3.4 control file, official ONI ascii, IRI plume.
- enso-watch made its own git repo (estate invariant: one repo per project). Initial commit sealed.
- Run contract frozen (this document).
- V0 fixtures captured and frozen (build step 2): OISST daily netCDF (2026-07-01, full global grid), CPC Nino 3.4 monthly control, official ONI seasonal ascii, plus the 1991 to 2020 daily climatology subset to the Nino 3.4 box (via OPeNDAP), each recorded in fixtures/MANIFEST.json with source url, retrieval timestamp, byte size, and sha256.
- Nino 3.4 computation built and gated (build step 3): area averaged box anomaly from OISST against the 1991 to 2020 box climatology, tested to the exact golden value at 3 decimals, offline, with a proven offline guard. Our raw region SST (29.215 C) matches the CPC control within 0.05 C. First hard gate green (./run.sh test, 9 tests). Passed adversarial review after fixing three robustness gaps (leap day policy, masked cell coverage, honest offline guard).
- JSON output contract built and gated (build step 4): the daily series and the status record, each carrying a complete provenance block, plus the ENSO phase and strength derived from the ONI thresholds and the gap to the CPC control (with its period). Structural gate (criterion 4) refuses any provenance hole, including a null field. `./run.sh emit` prints the product. 15 tests green. Passed adversarial review after fixing the null provenance hole and adding threshold and lag coverage.
- Live pull and smoke check built (build step 5): `./run.sh pull` downloads the real sources (via curl) and runs the same transform to write a dated JSON with honest live provenance; `./run.sh smoke` (criterion 2) reaches the real sources and confirms their shape, reporting without ever gating. Proven live against NOAA (resolved 2026-08-10 preliminary, all sources reachable and shape unchanged). The offline gate stays offline (network never a test dependency). 29 tests green. Passed adversarial review after switching network I/O from stdlib urllib to curl and fixing an HTTP status classification bug (a transient block must raise, only a real 404 means absent).

## 🧊 Later

**V1, the forecast oracle.** Ingest the IRI/CPC ENSO plume (probabilistic Nino 3.4, 26 models, 9 months ahead). Uncertainty is first class: the output carries the full spread (min, median, max) and the per phase probabilities, never a single naked number. Known blocker to solve first: the IRI plume has no clean downloadable file (visualization only), so V1 must find the machine readable door (for example the CPC probability table) before building.

**Impact, a separate track.** Deferred by decision. "Impact" is scoped on its own, after observation and forecast are alive, never bolted onto V0 or V1.

**Harness feedback.** Once the ingestion and provenance shapes prove out here, extract a reusable data crew into the-workspace (single sourced tooling, add on proof, not before).
