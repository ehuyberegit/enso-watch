# ROADMAP: enso-watch

> Operational source of truth. At the top: the current work's run contract.
> Rule: "Done" = integrated, green (machine gate), reviewed.

## >> DIRECTION UNDER RE-SCOPING (discovery reopened 2026-08-21). READ FIRST.

> Do not execute the contracts below yet. This session went back to method stage 1 (discovery)
> and the north star moved. Two objectives now stand above every technical contract here:
>
> 1. **Product north star: impact.** The real goal is to predict, in time, the SOCIAL and
>    ENVIRONMENTAL consequences of the ENSO signal (the "impact" oracle). Observation (V0) and
>    forecast (V1) are the FOUNDATION for this, not the goal. Honest hard part: ENSO shifts
>    regional probabilities, it does not decide local weather, so impact must link our signal to
>    impact data (yields, floods, prices, displacement) without claiming causality we lack. Two
>    scoping questions still open: which consequence first (agriculture / floods-droughts / food
>    prices) and which region first (Peru, Horn of Africa, Indonesia, Australia).
> 2. **Personal objective: learn data science.** Use this project to learn the craft and play with
>    linear regressions Jupyter-notebook style (turn the lambda knob, add/drop predictors, watch
>    RMSE and ACC move). Proposed resolution, pending CEO validation: a free `notebooks/` lab vs
>    the gated `src/` that ships; isolated lab deps in a `requirements-lab.txt` (jupyter, pandas,
>    scikit-learn) so the product stays light (numpy + netCDF4). "Play in the notebook, promote to
>    the module."
>
> The technical path already drafted this session stays valid but PARKED under these two:
> - `docs/SOLUTION-DESIGN.md`: the full rebuild (RONI dual index, probabilistic + calibrated
>   forecast, verification suite with CRPS/RPSS/reliability, four-screen UI). Companion PDF scoping
>   on the Desktop (`enso-watch-scoping-2026-08-19.pdf`).
> - The "data hardening" contract just below was written this session, then itself superseded by the
>   re-scoping. Treat it as the technical backlog, not the current work.
> - One decision open for the CEO: D1, the headline index (RONI vs the raw fixed-baseline anomaly).
>
> Next when work resumes: finish discovery (impact opportunity map on evidence, the two scoping
> questions), then requirements (stage 2), then LLD (stage 4), THEN a run contract. We skipped
> 1, 2, 4 this session and jumped to design; the re-scoping corrects that.

---

## 🚦 RUN CONTRACT, current work. Data hardening: close the two real holes in the truth store

> Decision 2026-08-17, frozen, and it REPLACES the "data reboot" contract written on 2026-08-13
> and never executed. That contract asked for a from-scratch rebuild of the data layer. The audit
> below checks its eight criteria one by one against the code as it actually stands, and six of
> them are already met by the layer built for V0 and V1, which has been feeding a green daily
> automation since 2026-08-13. A rebuild would re-earn what is already green. So the reboot is
> retired and only its unmet criteria survive, as a hardening pass. Erwan arbitrated option 2
> (extract the unmet criteria) over executing or dropping the reboot whole.
>
> What the reboot got right and stays true, as standing law rather than work to do: the MONTHLY
> whole-record pull is the spine and the daily transform is the edge; the clean machine-readable
> door (netCDF or ascii) is captured and frozen BEFORE any parser is written; an automation is
> not "done" until one real dispatch has committed a JSON visible in the Actions tab (S2).

### Audit of the reboot's eight criteria, 2026-08-17 (evidence, not opinion)

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Offline deterministic gate | **MET** | `./run.sh test`: 94 tests, 0.34 s, exit 0, behind the socket guard (`tests/test_offline_guard.py`). |
| 2 | Monthly history committed | **MET** | `data/history/nino34_monthly.csv` (539 months, 1981-09 to 2026-07) with its provenance sidecar; `tests/test_history.py` pins the golden endpoints and finds the real Dec 2023 peak on a frozen monthly fixture slice. |
| 3 | Daily edge committed | **MET** | `tests/test_nino34.py::test_golden_transform` and the daily golden in `tests/test_history.py`, both on frozen fixtures; prelim/final flag carried (see the committed dated JSONs). |
| 4 | Provenance complete on EVERY record | **NOT MET** | The structural gate (`tests/test_output.py::test_every_record_has_complete_provenance`, `provenance.is_complete`) covers ONLY the V0 output (daily series and status). The three V1 artifacts each carry a hand-rolled block of a different shape, with no preliminary/final status, enforced by nothing: the two `data/history/*.provenance.json` sidecars (`source_name` / `dataset` / `pulled_at_utc`) and the block inside `data/forecast/cpc_official.json` (`source_url` / `phase_definition`). Neither `history.py`, `wwv.py`, `official_forecast.py` nor `peak.py` references the provenance module at all. Against the chef's own rule ("no number ships without a complete provenance block"), one hole is red. |
| 5 | CPC control gap recorded | **MET** | `our_nino34_vs_official` plus `control_period` are in the status record and golden-tested (`test_status_golden`); visible live in the committed JSON (gap 1.245, control 2026-06). |
| 6 | Leap-day rule tested | **MET** | `tests/test_units.py::ClimatologyIndexTest::test_feb29_falls_back_to_feb28`. |
| 7 | Live smoke covers the live doors | **PARTLY MET** | `./run.sh smoke` watches 3 doors (OISST daily, CPC ONI, CPC control). Three doors that feed shipped numbers are unwatched: the PSL OISST monthly mean (the spine), the PMEL warm water volume (the model's precursor), and the CPC probability table, which is the only HTML door and therefore the likeliest to drift in silence. |
| 8 | Automation proven green end to end | **MET** | One manual dispatch green 2026-08-13, then four scheduled runs green (13, 14, 15, 16 August), each committing its dated JSON with `permissions: contents: write`. |

Two findings surfaced by the audit itself, outside the reboot's original eight, folded into this contract:

- **The daily pull lags two days, and nowhere says so.** The 2026-08-16 run committed `data/enso-watch-2026-08-14.json`: OISST preliminary latency, not a bug, but the freshest number the product shows is always about two days old and that must be stated, not inferred.
- **Signature S2 is still marked open** in `.claude/signatures.md` although it is now proven closed by five green runs.

### 1. Measurable objective (the observable result)

The truth store keeps every guarantee it already has, and gains the two it only pretended to
have: provenance enforced by the machine on EVERY shipped number (not just the V0 output), and
a live smoke that watches EVERY door we actually read. What we show when done: a green offline
gate that goes red if any artifact anywhere has a provenance hole, and a smoke run reporting on
six doors.

### 2. Machine-verifiable finish criteria (the GO threshold)

| # | Criterion | What the machine checks | Verdict |
| --- | --- | --- | --- |
| A | One provenance shape, everywhere | Every shipped artifact (the dated daily JSON, the two monthly history sidecars, the official forecast snapshot) carries the SAME block: source name, dataset version, retrieval URL, pull timestamp, preliminary/final status. | Hard gate (structural). |
| B | The gate refuses a hole anywhere | One test walks every committed artifact family and fails if a single required field is missing, empty, or null. Proven by an injected hole (a deliberately incomplete block must turn it red). | Hard gate: one hole = red. |
| C | The smoke watches all six doors | `./run.sh smoke` reaches and shape-checks OISST daily, CPC ONI, CPC control, PSL OISST monthly, PMEL warm water volume, and the CPC probability table, and reports each one. | Reports only, never blocks. |
| D | The lag is stated where the number is read | The daily record's latency (data date versus pull date) is explicit in the product and in the README, not left to be inferred. | Structural: the field/line exists. |
| E | The gate stays green | `./run.sh test` still exits 0 offline behind the socket guard, with the new tests included. | Hard gate. |

**GO threshold**: A, B, D and E green, and the smoke (C) reports on six doors without a blocking error.

### 3. Non-goals (the scope-creep guardrail)

- No rebuild of what the audit found green. Criteria 1, 2, 3, 5, 6 and 8 are settled; touching them is out of scope.
- No forecast or model work. The V1 track sits on this data and has its own contract below, including the issue-month decision still to freeze.
- No impact track.
- No new shipped UI surface. The private local dashboard stays a read-only lens.
- No new dependency beyond the pinned set (numpy, netCDF4) unless declared as a decision.
- No change to the fixed 1991-2020 baseline, ever, silently.
- Network is never a test dependency: the gate stays offline on fixtures, the smoke stays outside it.

### 4. Degrees of freedom (I decide alone)

The exact provenance field names in the unified block (as long as one shape holds everywhere and
covers the five required facts), how the artifact walk is implemented, file layout under `src/`,
the fixture slices, whether to delegate mechanical bulk to the worker. Curl over stdlib urllib
for live network I/O stays decided.

### 5. Escalation rules (the only list allowed to wake the CEO)

Destructive or irreversible operation beyond a git-recoverable edit · any spend (e.g. a paid data
key) · a contradiction inside this contract · a security decision · discovering that unifying the
provenance shape would force a change to a published number.

### 6. Parking protocol

Any taste decision or form ambiguity met along the way (dashboard look, naming aesthetics) goes
to the parking lot and the run continues on another front. The run never blocks on a taste call.

### Autonomous-run clauses

- **① Stop bound** (stop clean at the first reached): objective met · OR first taste blocker · OR the budget/time set at launch.
- **② Decision rule**: objective AND reversible (bug, robustness, local refactor) decided alone behind the reviewer gate before "Done"; sensitive AND ambiguous (taste, irreversible, security) parked.
- **③ Required end state**: nothing unfinished dangling without a flagged reason · the machine gate green · this roadmap updated in the same commit · the self-review written.

### Build sequence (data hardening)

1. **Unify the provenance shape**: one block definition, already in `provenance.py`, extended to serve the monthly history sidecars and the forecast snapshot (adding the missing dataset version and preliminary/final status). Rewrite the three artifacts to it, without changing a single number.
2. **The universal structural gate**: one test that walks every artifact family and refuses any hole, proven red on an injected incomplete block.
3. **The smoke, widened to six doors**: add the PSL monthly, the PMEL warm water volume, and the CPC probability table, each with its own shape check. Still reporting, never gating.
4. **State the lag**: the daily latency written into the product and the README.
5. **Close S2** in `.claude/signatures.md` with the five green runs as evidence.

---

## Run contract, V1 the forecast oracle (Projet A, sits ON the data socle)

> **Open, and to freeze before V1 is called done (flagged 2026-08-17).** The forecast's issue
> month (which month the model predicts from, given that the daily edge runs ahead of the last
> complete monthly value) was re-tuned reactively during the 2026-08-13 session, and that swung
> the peak figure from about +2.72 C to +3.19 C. The commit says so itself. This must become one
> explicit, written decision with its reason, not a value adjusted per reaction. Until it is
> frozen, the peak number is provisional.
>
> Evidence that this is not cosmetic, read off the dashboard on 2026-08-17: the peak now issues
> from 2026-08, a PROVISIONAL month averaging only 5 days, and reads +3.67 C (band 3.32 to 4.02).
> It has drifted from the +3.19 C recorded on 2026-08-13 with no decision taken in between: the
> figure simply follows whichever month is freshest, however thin. The frozen decision must say
> how many days a provisional month needs before the peak is allowed to issue from it.

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

The forecast oracle (V1) stands end to end: observation, ingredients, an honest judge, a model that beats the baselines, a forward forecast that agrees with NOAA at 99%, and a peak forecast (timing and magnitude with uncertainty). Parked for next time: a daily view of the current state, the historical skill comparison, and the impact track (the peak now feeds it). Committed 2026-08-13 (`0f5a9c5`), with one honest caveat carried into the V1 contract above: the forecast's issue month was tuned reactively and is not yet a frozen decision.

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
