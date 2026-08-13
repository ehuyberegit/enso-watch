# enso-watch progress

> This file is a pointer, not a second tracker. The operational source of truth is
> `.claude/ROADMAP.md` (frozen run contract + Done/In progress/Later). The product story
> for a human is `README.md`. Keeping two full trackers guarantees drift, so this one
> stays a one screen snapshot and defers to the roadmap for detail.

> Last reconciled: 2026-08-13

## Where V0 stands

**V0, the observation oracle, is shipped and its automation is live.** A daily GitHub Actions
workflow pulls real NOAA data, recomputes the Nino 3.4 anomaly, and commits a dated JSON with
full provenance, with no hand on it. The offline machine gate is green (29 tests, `./run.sh test`).

- Latest committed record: `data/enso-watch-2026-08-11.json`, Nino 3.4 anomaly **+2.682 C**
  (moderate El Nino), produced and auto committed by the CI on 2026-08-13.
- The CI was born broken (a YAML dedent in the commit step made GitHub reject the workflow at
  startup, so nothing ran from 2026-08-11 to 2026-08-13) and was fixed and proven green end to
  end on 2026-08-13. Detail and the signature (S2) live in the roadmap and `.claude/signatures.md`.

## What is next

Not yet started, listed in `.claude/ROADMAP.md` under "Later":
- A private read only UI over the JSON, tabbed (observation / forecast / impact). Under design.
- V1, the forecast oracle (IRI/CPC ENSO plume). Known blocker: no clean downloadable plume file.
- Impact, a separate later track.

## Local commands

```bash
./run.sh test    # offline machine gate, 29 tests
./run.sh emit    # print the V0 JSON product from the frozen fixtures
./run.sh pull    # live daily pull, writes a dated JSON to data/
./run.sh smoke   # live source shape check, reports only, never gates
```

- Repo: https://github.com/ehuyberegit/enso-watch
- CI: https://github.com/ehuyberegit/enso-watch/actions
