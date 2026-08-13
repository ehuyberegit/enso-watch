# ROADMAP: enso-watch

> Operational source of truth. At the top: the current work's run contract.
> Rule: "Done" = integrated, green (machine gate), reviewed.

## 🚦 Run contract, current work (V1, the forecast oracle, Projet A)

> Decision 2026-08-13, frozen: V1 builds OUR OWN simple statistical forecast of the
> Nino 3.4 ocean signal at a 1 to 3 month lead, whose target is to resemble the official
> IRI plume. The earlier "aggregate the official, make no prediction of our own" framing
> is retired. Projet B (land impact) stays a separate, harder, later track: ENSO shifts
> regional probabilities, it does not decide local weather. The honest spine, and the
> reason we built observation and provenance first: a model is only as good as its data
> and its leakage free validation, so the data and the validation harness come before any
> model.

### 1. Frozen decisions (V1)

| Axis | Decision |
| --- | --- |
| Ambition | Predict the Nino 3.4 anomaly at a 1 to 3 month lead. Our own model. Target: resemble the official plume, not out forecast NOAA. |
| Honesty | Uncertainty is first class: every forecast carries its spread, never a naked point. No skill is claimed that is not shown against the baselines. |
| Predictors | Persistence (the baseline to beat), warm water volume (the precursor king, leads ~2 seasons, NOAA PMEL), zonal winds / SOI, seasonality. |
| Method ladder | Baselines (persistence, climatology) then linear then ridge regression, then LIM. The Ham 2019 CNN is cited as an honest ceiling, not a target (it needed CMIP5 sims for enough data). |
| Validation | Walk forward (expanding window), scored by ACC and RMSE against the baselines, per lead month, exposing the spring predictability barrier. No future leakage, ever (a leakage guard is a test). |
| Data source | Our own Nino 3.4 history, computed on the SAME box and 1991-2020 climatology as V0. The model trains at MONTHLY cadence from the PSL OISST v2.1 monthly mean (sst.mon.mean.nc, the whole record in one light OPeNDAP pull); the daily transform is kept for the live oracle and for any fine grained window. Daily proved too heavy to backfill in bulk (~112 s per year over OPeNDAP), and Nino 3.4 is a monthly index, so monthly is both faster and the right cadence. WWV from NOAA PMEL. |
| Stack | numpy, pandas, xarray, scikit-learn, matplotlib. Tested modules under src/, NOT a notebook as the product (a notebook only to explore). Adding a dependency stays a decision. |
| Experiment log | `data/experiments.jsonl`, committed, one line per run (git native, not MLflow). |
| Comparison target | The official IRI/CPC plume probabilities. Find the machine readable door (for example the CPC probability table) before claiming resemblance. |

### 2. Finish criteria (V1, the GO threshold, machine verifiable)

| # | Criterion | Verdict |
| --- | --- | --- |
| 1 | The training dataset is committed: our own Nino 3.4 daily anomaly history (own transform) plus the WWV predictor, each traceable to its source, with a frozen fixture and an offline deterministic test. | Hard gate: fixture in, expected values out to 3 decimals, offline. |
| 2 | A walk forward harness scores any model by ACC and RMSE against the persistence and climatology baselines, per lead, with no future leakage. | Hard gate: a leakage guard test is green. |
| 3 | The forecast product carries its full spread, never a naked point. | Hard gate (structural) on a fixture. |
| 4 | Every model run is recorded in the experiment log. | Structural. |
| 5 | The official plume comparison target is ingested (machine readable), so "resembles the plume" is measurable. | Live report plus one read. |
| 6 | Docs do not lie (Trinity plus one read). | Mixed. |

### 3. Build sequence (V1)

1. **Backfill the training dataset** (the current front): our own Nino 3.4 daily anomaly history from PSL daily means via OPeNDAP box subset, plus the WWV predictor. Frozen fixture, offline test.
2. Baselines (persistence, climatology) plus the walk forward harness plus the experiment log. The thing every model must beat.
3. Linear then ridge regression on the predictors, scored against the baselines, per lead.
4. Find the machine readable plume door, score resemblance.
5. (Stretch) LIM. The browser lab grows to five tabs: Observation (live), Ingredients, Atelier, Skill bulletin, Forecast.

---

## Run contract, V0 (shipped 2026-08-13, kept for the record)

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

**Front: the training dataset (V1 build step 1).** Opened 2026-08-13.

DONE, the Nino 3.4 history:
- `data/history/nino34_monthly.csv` built: 539 months (1981-09 to 2026-07), our own anomaly, region mean, climatology mean, baseline, one consistent source (PSL OISST monthly mean), with a provenance sidecar. Latest 2026-07 at +2.090 C.
- Offline deterministic gate: `history.monthly_series` and `history.daily_series` each pinned to golden values on a frozen fixture (the 2023-24 monthly slice finds the real Dec 2023 El Nino peak at +2.011 C; the Jan 2024 daily slice at +2.123 C). `./run.sh test` green (50 tests).
- The dashboard grew an Ingredients tab: the 46 year record charted with the El Nino / La Nina bands, our own numbers, provenance shown. Verified in the browser.

DONE, the warm water volume (the precursor):
- `data/history/wwv_monthly.csv` ingested from NOAA PMEL: 558 months (1980-01 to 2026-06), volume and anomaly in 1e14 m^3, with a provenance sidecar. Latest anomaly 2026-06 at +3.004.
- Offline gate: `wwv.parse_wwv` pinned to golden values on a frozen 1997-98 slice (it finds the precursor peak in spring 1997, ahead of the late-1997 El Nino). `./run.sh test` green (56 tests).
- Surfaced in the Ingredients tab as a second chart under the Nino 3.4 history, with the two season lead noted.

DONE, the review:
- Adversarial reviewer pass: PASS. One medium finding (the 4 new fixtures were not in fixtures/MANIFEST.json, breaking the sha256 provenance convention). Fixed: a shared tools/manifest.py records source, timestamp, byte size, and sha256; all four capture tools now self-record; the manifest carries all 8 fixtures. Gate still green (56 tests).

Front complete (pending the closure commit).

**Front: baselines and the validation harness (V1 build step 2). DONE 2026-08-13.**
- `src/enso_watch/skill.py`: persistence and climatology baselines, a leakage free walk forward (the forecaster only ever sees history up to the issue month), and the two ENSO scores (RMSE in C, ACC the anomaly correlation). `src/enso_watch/experiments.py`: a git native JSONL run log.
- `tools/run_baselines.py` (`./run.sh baselines`) scores the baselines over our 539 month history and appends to `data/experiments.jsonl`.
- Real result: persistence ACC 0.942 at lead 1 decaying to 0.332 at lead 6, and by 6 months its RMSE (0.967) is worse than climatology (0.837), the honest crossover a model must beat. Climatology ACC is 0 (no skill) by construction.
- Offline gate: the leakage guard is a hard test (an index series forces a constant lead-length error, impossible if the future leaks). `./run.sh test` green (69 tests).
- The dashboard grew a Skill tab: the walk forward process drawn, the baseline scoreboard by lead, and the experiment log. Verified in the browser.

**Front: our own model (V1 build step 3). DONE 2026-08-13.**
- `src/enso_watch/model.py`: a ridge regression solved in closed form with numpy (no scikit-learn added), reading three predictors at the issue month (current Nino 3.4, warm water volume, and the season as sine and cosine of the month) to predict the anomaly a lead ahead. Standardized features, unregularized intercept.
- Scored by the SAME leakage free walk forward and the SAME RMSE/ACC as the baselines, on the same window. Leakage guard is a hard test (truncating every row after a target leaves the earlier forecast unchanged).
- Real result: the model beats persistence at every lead, and pulls away at long range where it matters: at 6 months ACC 0.509 vs persistence 0.332 (RMSE 0.72 vs 0.97). Its learned weights tell the story: at 6 months the warm water volume (0.413) outweighs today's temperature (0.271), the precursor carrying the signal.
- `./run.sh baselines` now prints and logs baselines plus the model; the Skill tab shows the model column (winning, highlighted) and a "what the model leans on" readout. `./run.sh test` green (77 tests).
- The whole lab UI was reworked for accessibility (plain-language lead-ins and a glossary per tab, an "experts vs us" panel), on operator feedback.

**Front: the official comparison (V1 build step 4, choice A "live snapshot"). DONE 2026-08-13.**
- Machine readable door found and verified live: the IRI numeric plume is retired ("we are no longer providing forecast data"), so the official target is the CPC ENSO probability table (phase chances per 3 month season). CPC defines the phases exactly as we do (+/-0.5 C, Nino 3.4, 1991-2020), so the comparison is apples to apples.
- `src/enso_watch/official_forecast.py` parses that table; `tools/ingest_cpc_forecast.py` (`./run.sh forecast`) writes `data/forecast/cpc_official.json` with provenance; a frozen fixture (`fixtures/cpc/roni_probabilities.html`, in the manifest) proves the parser offline.
- `model.py` gained the forward forecast (`forecast_forward`, train on all data, predict the next months), the honest bridge to probabilities (`phase_probs`, our forecast mean plus our measured spread as a Gaussian over the +/-0.5 thresholds), and `compare_to_official`.
- Real result: our simple model agrees with NOAA's official forecast at **98%** and calls the **same phase 4 of 4** near-term seasons. Where it differs, it hedges toward Neutral a little sooner (our wider, honest uncertainty). Our forward: a strong El Nino weakening slowly (+1.8 C now toward +1.3 C by December).
- The Forecast tab now shows the two side by side with the agreement number, season by season bars, and provenance. `./run.sh test` green (89 tests). Verified in the browser.

**Front: our forward forecast curve (V1 build step 4B). DONE 2026-08-13.**
- `compare_to_official` now also returns the forward series: our Nino 3.4 forecast for each of the next 6 months, each with its uncertainty (value plus or minus our measured miss at that lead). The dashboard attaches the recent actual tail for context.
- The Forecast tab draws it: the real record (solid) continued by our forecast (dashed) with a shaded uncertainty band that widens with lead, over the El Nino / La Nina threshold bands. Our forecast: a strong El Nino easing from about +1.8 C now to +1.3 C (give or take 0.7) by December. `./run.sh test` green (89 tests). Verified.

**Front: the peak forecast (timing and magnitude, with uncertainty). DONE 2026-08-13.**
Operator reframe: a fixed lead forecast is academic; what matters for impact is WHEN the event peaks and HOW HIGH. Built on two honest legs:
- Timing: El Nino events phase lock to the calendar. Strong ones peak November to January, so the timing is read from the empirical distribution of past strong peaks (6 events), not a fragile model. Weak El Ninos peak off season, which is why the timing conditions on strength.
- Magnitude: a plain linear fit of the eventual peak on the current Nino 3.4 and warm water volume, validated leave one year out so the band is a real out of sample miss.
- `src/enso_watch/peak.py`, tested (`tests/test_peak.py`, including a leave one out that must be positive on data a line cannot fit). The Forecast tab leads with it.
- Real result: this El Nino is projected to peak around December 2026 at about +3.19 C monthly mean (band +2.66 to +3.72), which would top even 2015. Nearest analogs, found from today's ocean state: 1997, 2023, 1982. `./run.sh test` green (94 tests).
- Correction after operator review: the peak is a MONTHLY mean (a single hot day, like the +2.69 in Observation, always sits above its month), and it is now issued from the freshest Nino 3.4 month (July), not the last month the warm water volume also covers (June). Issuing from June under read the surge (gave +2.72); July gives +3.19. The Forecast panel now states the monthly vs daily difference in plain words so the two numbers are not confused.

**Front: coherence and readability pass. DONE 2026-08-13.**
- Consistency fix: both the forward forecast and the peak now issue from the freshest Nino 3.4 month (July), not the last month the warm water volume also covers (June). The forecast plume's real line now extends through the latest month, so the model's under-shoot is visible, not hidden. The plume panel is relabelled the cautious month-ahead baseline (it leans to normal), pointing to the peak panel for the event's high point.
- A Data freshness strip leads the Observation tab: daily to its date and pull time (UTC), monthly, warm water volume, and official forecast, each with its own date, since they refresh at different rates. It states the daily vs monthly "two rulers" point in plain words.
- Hover tooltips on every chart (Observation, both Ingredients charts, the hindcast, the forecast plume) show the exact date and value under the cursor, with a vertical guide.
- `./run.sh test` green (94 tests), no console errors, Trinity clean.

The forecast oracle (V1) stands end to end: observation, ingredients, an honest judge, a model that beats the baselines, a forward forecast that agrees with NOAA at 99%, and a peak forecast (timing and magnitude with uncertainty). Parked for next time: a daily view of the current state, the historical skill comparison, and the impact track (the peak now feeds it). Nothing is committed yet.

## ✅ Done

- Scaffold laid (chef, pinned crews, roadmap, signatures, design).
- Sources verified live: OISST daily netCDF path and file naming, CPC Nino 3.4 control file, official ONI ascii, IRI plume.
- enso-watch made its own git repo (estate invariant: one repo per project). Initial commit sealed.
- Run contract frozen (this document).
- V0 fixtures captured and frozen (build step 2): OISST daily netCDF (2026-07-01, full global grid), CPC Nino 3.4 monthly control, official ONI seasonal ascii, plus the 1991 to 2020 daily climatology subset to the Nino 3.4 box (via OPeNDAP), each recorded in fixtures/MANIFEST.json with source url, retrieval timestamp, byte size, and sha256.
- Nino 3.4 computation built and gated (build step 3): area averaged box anomaly from OISST against the 1991 to 2020 box climatology, tested to the exact golden value at 3 decimals, offline, with a proven offline guard. Our raw region SST (29.215 C) matches the CPC control within 0.05 C. First hard gate green (./run.sh test, 9 tests). Passed adversarial review after fixing three robustness gaps (leap day policy, masked cell coverage, honest offline guard).
- JSON output contract built and gated (build step 4): the daily series and the status record, each carrying a complete provenance block, plus the ENSO phase and strength derived from the ONI thresholds and the gap to the CPC control (with its period). Structural gate (criterion 4) refuses any provenance hole, including a null field. `./run.sh emit` prints the product. 15 tests green. Passed adversarial review after fixing the null provenance hole and adding threshold and lag coverage.
- Live pull and smoke check built (build step 5): `./run.sh pull` downloads the real sources (via curl) and runs the same transform to write a dated JSON with honest live provenance; `./run.sh smoke` (criterion 2) reaches the real sources and confirms their shape, reporting without ever gating. Proven live against NOAA (resolved 2026-08-10 preliminary, all sources reachable and shape unchanged). The offline gate stays offline (network never a test dependency). 29 tests green. Passed adversarial review after switching network I/O from stdlib urllib to curl and fixing an HTTP status classification bug (a transient block must raise, only a real 404 means absent).
- Daily automation built, then repaired and proven (build step 6): the GitHub Actions scheduled workflow pulls, recomputes, and commits the dated JSON. It was born broken (a multi line commit message dedented to column 0 inside the run block, closing the YAML scalar, so GitHub rejected the whole file at startup: every run failed in 0s and no scheduled pull ever fired, from 2026-08-11 to 2026-08-13). Fixed 2026-08-13 (commit message onto two `-m` flags, plus `permissions: contents: write` for the auto push). Proven green end to end by a manual dispatch: the runner fetched real NOAA data and auto committed `data/enso-watch-2026-08-11.json` (anomaly +2.682 C, full provenance). Criterion 3 (workflow end to end, hard gate) now genuinely met. Recorded as signature S2.
- V0 shipped (build step 7): README written in the Astrolab spirit (what it does, what it costs, honest limits), decisions logged in this contract. V0, the observation oracle, is complete: a live daily JSON feed of the Nino 3.4 anomaly plus official ONI status, provenance on every number, refreshed and committed by the workflow with no hand on it.

## 🧊 Later

**V1, the forecast oracle.** Promoted to the current run contract at the top of this file (decision 2026-08-13: our own model, not aggregation). The two private artifacts that hold the full design plan (a simple README and a technical edition with code and maths) stay the reference for the maths and the five screen lab.

**Impact, a separate track.** Deferred by decision. "Impact" is scoped on its own, after observation and forecast are alive, never bolted onto V0 or V1.

**A private read only UI (under design).** A very basic, private URL where the operator sees the important numbers interactively, not raw JSON. Tabbed to mirror the three oracles: tab 1 observation (V0, live now), tab 2 forecast (V1), tab 3 impact (later track). Only tab 1 has data today, so the UI ships incrementally alongside the oracles. It must stay honest: it renders the committed JSON and its provenance, it invents nothing, and it never becomes a second source of truth (the JSON in git stays the truth). Shape and hosting to be scoped before building.

**Harness feedback.** Once the ingestion and provenance shapes prove out here, extract a reusable data crew into the-workspace (single sourced tooling, add on proof, not before).
