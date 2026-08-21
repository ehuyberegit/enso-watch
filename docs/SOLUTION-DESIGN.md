# enso-watch, solution design: rebuilding the numbers, and the lens over them

> Status: proposed, 2026-08-17. This is a framing document, not a change. It descends from
> objective to data to program shape, and it ends at a machine verifiable definition of "done".
> Nothing is built until the run contract it implies is frozen and approved.
> Estate rules apply: English, provenance on every number, no em dashes.

## 0. Thesis

enso-watch already does the hard, unglamorous thing well: it computes the Nino 3.4 sea surface
temperature anomaly from raw NOAA OISST with correct cosine of latitude area weighting, a proper
land and sea mask, a fixed 1991 to 2020 daily climatology, and a documented leap day rule, and it
scores its own forecast with a leakage free walk forward. That foundation is sound and this design
keeps it.

What it does not yet do is the thing a working ENSO forecaster would check first. Three gaps:

1. **The index is not trend corrected.** A fixed 1991 to 2020 baseline folds the secular warming
   of the tropical Pacific into every "anomaly". In 2026 that is not a rounding error: it is the
   difference between an honest ENSO signal and one inflated by global warming. NOAA moved to the
   Relative ONI (RONI) for exactly this reason, and the official forecast we already compare against
   is RONI based. We compare a raw index to a relative one and call the small gap agreement.

2. **The forecast is a point plus a naive band.** The uncertainty is a single number (one root mean
   square error), reused everywhere, hiding both how it was measured and how it should grow with an
   incomplete current month or a spring initialization. There is no calibration check, no proper
   probabilistic score, no reliability diagram. A forecast product with no verified calibration is a
   forecast nobody should trust.

3. **Skill is reported as one scalar per lead.** ENSO skill is strongly seasonal (the spring
   predictability barrier). A single "ACC 0.51 at six months" number hides the one fact that decides
   whether a forecast issued today is worth reading.

This design rebuilds the numbers on a coherent, trend aware, fully probabilistic and reproducible
basis, and rethinks the lens (the private dashboard) around the one narrative that earns a data
scientist's trust: not "here is our forecast" but "here is our forecast, here is exactly how it was
measured, and here is our verified track record against honest baselines".

## 1. Design principles (the doctrine, made testable)

- **Truth first, provenance on every number.** No value ships without a complete, uniform
  provenance block. The machine refuses a hole anywhere.
- **Honest uncertainty is a first class output, never a decoration.** Every forecast is a
  distribution with a stated, decomposed, and calibrated spread. A thin input produces a wide band,
  visibly.
- **Reproducible to the digit.** One command rebuilds every committed number from frozen inputs and
  matches a golden to three decimals. Numbers cannot drift in silence (this already bit us once: the
  peak moved from +3.19 to +3.67 with no decision taken).
- **We benchmark ourselves, and we do not pretend to beat the dynamical models.** The value is
  transparency and reproducibility, not accuracy leadership. We report our skill relative to honest
  baselines and to the official forecast, and we state plainly where each wins.
- **Every claim is falsifiable offline.** The network is production only; the gate runs on fixtures.

## 2. Part A: the measurement layer (redo the numbers)

### A1. The warming trend, and a dual index (raw anomaly and RONI)

**Problem.** The Nino 3.4 anomaly against a fixed 1991 to 2020 climatology measures departure from a
past normal. The tropical Pacific has warmed since that normal, so part of today's +2.7 C is the
background trend, not the ENSO event. This is the central methodological issue in ENSO monitoring
today, and the reason NOAA CPC now publishes the Relative ONI.

**Design.** Compute both indices ourselves, from the same OISST field, and record both on every
record:

- **Raw anomaly** (unchanged): box mean minus the fixed 1991 to 2020 box climatology. Kept for
  continuity with the classic ONI and for full transparency.
- **RONI**, the relative index: the raw Nino 3.4 anomaly minus the area weighted SST anomaly of the
  tropical band (20 S to 20 N, all longitudes), computed against the same 1991 to 2020 baseline. This
  removes the basin wide warming that is common to the box and the tropics, leaving the ENSO signal.

RONI becomes the headline for phase and strength classification (El Nino, neutral, La Nina), so our
classification is consistent with the official forecast we compare against. The raw anomaly stays
visible, and the gap between the two is recorded and charted: it is itself an honest measure of how
much warming is inflating the classic index.

**Cost.** The tropical band average needs the full OISST tropics, not just the box, on both the
daily field and the climatology. The monthly spine already pulls the whole record; the daily edge
pulls one global file per day, so the tropical mean is a wider average of data we already download. A
one time capture of the tropical band 1991 to 2020 climatology is added as a frozen fixture.

### A2. The anomaly engine, audited and unified

The current daily engine is correct. This design makes it the single canonical engine used by every
path (daily edge, monthly spine, climatology), so there is exactly one definition of "our number":

- cosine of latitude area weighting, land and mask cells excluded from both field and weights
  (already correct, kept and covered by a test that a masked cell changes nothing),
- one box constant (5 S to 5 N, 170 W to 120 W) and one baseline constant (1991 to 2020), imported
  everywhere, never redefined,
- the 365 day daily climatology with the fixed February 29 to February 28 rule (kept, tested),
- an explicit grid alignment check between field and climatology (already present, kept).

Everything downstream (monthly means, RONI, the model inputs) is derived from this one engine, so a
change to the method changes every number coherently and the golden suite catches any drift.

### A3. Preliminary versus final reconciliation

OISST ships a preliminary file within a day and a final file about two weeks later, and the values
revise. Today we stamp `preliminary` or `final` in provenance but never go back to replace a
preliminary value once its final lands, and the daily edge silently lags about two days.

**Design.**
- The daily record carries both the data date and the pull date, and states the lag in plain words
  in the product and the README (it is currently left to be inferred).
- A reconciliation step, on each pull, re-fetches any recent day still marked preliminary whose final
  is now available, replaces the value, flips the flag to final, and records the revision (old value,
  new value, revised at) in the provenance so the correction is auditable, never silent.

### A4. The current month nowcast (the honest live edge)

**Problem.** The monthly index needs a complete month. The live edge runs ahead: early in a month we
have only a few days. Feeding a five day average into a model trained on complete months (which is
what the peak and forward forecast do today) is a category error, and it is what made the peak swing
without a decision.

**Design.** The current, incomplete month enters everywhere as an **estimate of its own eventual
monthly mean, with an uncertainty that shrinks as the month fills**:

- point estimate: the mean of the days observed so far (near unbiased for a plateauing signal),
- its uncertainty: the standard error of that partial mean as an estimate of the full month mean,
  derived from the historical within month day to day variance of the index and the number of days
  still missing. Early month, wide; month end, near zero.

This single object replaces the raw "freshest month" input in the model, the forward forecast, and
the peak. It delivers the product requirement (the number refines every day as we pull) while making
the refinement honest: a five day month shows a wide band, a twenty five day month a tight one.

### A5. One provenance shape, enforced everywhere

Today the structural gate covers only the V0 output. The three V1 artifacts (the two monthly history
sidecars, the official forecast snapshot) each carry a hand rolled block of a different shape, with
no preliminary or final status, enforced by nothing.

**Design.** One provenance block definition (source name, dataset version, retrieval url, pull
timestamp, preliminary or final status), used by every artifact, and one structural test that walks
every committed artifact family and turns red if a single required field is missing, empty, or null,
proven red by an injected hole. This is the chef's own rule ("no number ships without a complete
provenance block") finally made universal.

## 3. Part B: the forecast layer (redo the model, honestly)

### B1. From a point forecast to a predictive distribution

Every forecast horizon returns a **distribution**, not a number with a bolted on band. In practice a
calibrated predictive mean and standard deviation (and, where the distribution is skewed, quantiles),
from which the phase probabilities and the fan chart are read. The point forecast becomes the median
of that distribution, not a separate object.

### B2. Uncertainty, decomposed and calibrated

The current spread is one root mean square error, reused. This design decomposes the predictive
variance into its real sources and then verifies the total is honest:

- **Irreducible spread**: the out of sample residual variance of the model at that lead (what the
  model cannot explain even with perfect inputs).
- **Parameter uncertainty**: the spread of the fitted coefficients, from a block bootstrap of the
  training years (monthly ENSO data is autocorrelated, so an ordinary bootstrap understates it; we
  resample in blocks of contiguous months).
- **Input uncertainty**: the current month nowcast uncertainty from A4, propagated through the linear
  model to the forecast.

These combine into one predictive standard deviation per horizon. It is then **calibrated and
checked**: a probability integral transform (PIT) histogram and a reliability diagram over the
walk forward say whether the stated spread matches reality (are the 80 percent intervals right 80
percent of the time). A forecast whose intervals are not calibrated is fixed, not shipped.

### B3. Baselines that deserve the name, with confidence intervals

Persistence and climatology are kept, and the missing serious bar is added:

- **Damped persistence**, x(t+tau) = rho^tau x(t), the autoregressive baseline that is the real
  standard for ENSO. Naive persistence is too easy to beat; damped persistence is the honest bar.

Every skill number (root mean square error, anomaly correlation, and the probabilistic scores below)
is reported with a **block bootstrap confidence interval**, so "the model beats damped persistence at
six months" is a statement with an interval, not a point. The effective sample size is far smaller
than the month count because of autocorrelation, and the interval says so.

### B4. The spring predictability barrier, shown not hidden

ENSO skill collapses for forecasts that must cross boreal spring. A single scalar per lead hides
this. This design reports skill as a **matrix over issue month and target season**, and the dashboard
draws it as a heatmap. A forecast issued in April for the following autumn is honestly marked as low
skill; one issued in August for winter is marked high. This is the single most useful honesty upgrade
for a reader deciding whether today's forecast is worth trusting.

### B5. A proper verification suite (the credibility core)

Deterministic scores (root mean square error, anomaly correlation) are kept, and the probabilistic
verification a serious product must have is added, all computed offline over the leakage free
walk forward:

- **CRPS** (continuous ranked probability score): scores the full predictive distribution, not just
  its mean. Lower is better; reported against the baselines' CRPS.
- **RPSS** (ranked probability skill score) for the three phase forecast, referenced to climatology:
  the standard categorical ENSO forecast score. Positive means beating climatology.
- **Reliability diagram and PIT histogram**: the calibration check from B2, surfaced.
- **Sharpness**: the width of our intervals, so calibration is not bought with uselessly wide bands.

### B6. The model: a reduced form linear model now, a Linear Inverse Model as the named target

The shipped model stays a small, interpretable, closed form ridge regression on honest predictors
(current Nino 3.4, warm water volume, season), and this design states plainly what it is and what it
is not:

- It is a **reduced form linear forecast**: a regularized linear map from a few physical predictors
  at the issue month to the anomaly a lead ahead, validated out of sample. Its coefficients are
  interpretable (at long lead the warm water volume outweighs today's temperature, which is the
  physical precursor doing its job).
- The principled target it approximates is a **Linear Inverse Model** (Penland and Sardeshmukh),
  dx/dt = Lx + noise, whose state x is the leading empirical orthogonal functions of tropical Pacific
  SST (and ideally subsurface heat content), and whose forecast operator is G(tau) = exp(L tau). A
  minimal LIM on a handful of indices is a natural, honest upgrade path, named here as future work,
  not oversold as shipped. Positioning the ridge as the reduced form of a known physical model, and
  saying so, is more credible than dressing a regression as something it is not.

### B7. The peak forecast, on the honest footing

The peak (when the current event peaks and how high) is rebuilt on A4 and B2:

- it issues from the current month nowcast, not a raw partial month, so it refines daily,
- its band is the propagated predictive spread from B2 (input plus parameter plus residual), so a
  peak built on five days of data shows a visibly wider band than one built on a full month,
- the training and prediction predictor months are aligned (today the model trains on complete
  Augusts but predicts from a five day August and a two month stale warm water volume; that
  incoherence is removed),
- the timing stays empirical (strong events phase lock to November through January), read from the
  distribution of past strong peaks with its small sample stated,
- and the estimate never drops below what the event has already reached (kept).

The issue month rule becomes a single frozen, written decision with its reason, so the number moves
only when the ocean moves, never because the code changed its mind.

### B8. Benchmark against the official forecast, RONI consistent

With RONI as our classification index (A1), our phase probabilities and the CPC RONI based
probabilities are finally the same kind of object, and the agreement number becomes meaningful rather
than approximate. We keep reporting, honestly, that a transparent statistical model hedges toward
neutral sooner than the dynamical ensemble, and we show where the official is sharper.

## 4. Part C: the lens, redesigned (verification first)

The dashboard is a private, read only lens over the committed JSON. It invents nothing and is never a
second source of truth. Today it has five tabs (Observation, Ingredients, Skill, Forecast, Impact)
organized by ingredient. This design reorganizes it around the question a data scientist actually
asks, in four screens.

### Screen 1: Now

Where the Pacific is, honestly. The headline is RONI with its phase and strength; the raw anomaly
sits beside it with the gap labeled ("the fixed baseline reads +2.7; removing the tropical warming
trend gives RONI +X; the difference is the warming, not the event"). The live daily edge shows the
current month nowcast as a point with its shrinking band, dated, with the two rulers (daily versus
monthly) stated in plain words. Full provenance one click away on every number.

### Screen 2: Forecast

Not a naked line. A **fan chart**: the observed record continued by our predictive distribution as
shaded quantile bands that widen with lead, over the El Nino and La Nina threshold lines, with the
official forecast drawn as a reference. Below it, the three phase probability bars, ours against CPC,
season by season. Beside it, the peak as a distribution (timing from the empirical strong peak
months, magnitude with its decomposed band). Every band is honest and labeled; nothing is a single
naked number.

### Screen 3: Track record (the trust screen, new)

This is what earns credibility, and today it is scattered inside a "Skill" tab. One screen:

- the walk forward skill of the model against persistence, damped persistence, and climatology, by
  lead, each with its block bootstrap confidence interval,
- the **spring barrier heatmap**: skill by issue month and target season,
- the probabilistic scores (CRPS, RPSS) against the baselines,
- the **reliability diagram and PIT histogram**: are our stated probabilities calibrated,
- the git native experiment log, every run reproducible.

A reader who distrusts the forecast comes here first and leaves either convinced or with a precise
reason not to be. That is the point.

### Screen 4: Data and methods

Provenance and method transparency as a first class screen: every source with its retrieval url and
timestamp, the anomaly method in plain words, the RONI and warming trend discussion, the preliminary
to final reconciliation policy, and a one line reproducibility statement (the command that rebuilds
every number and matches the golden). The classic ONI control and our gap to it live here.

### Design principles for the lens

- Uncertainty is never hidden: fan charts and bands, never a naked line, never a single number
  without its spread.
- Reference lines always present: baselines and the official forecast drawn alongside ours, so every
  claim is contextual.
- Provenance is always one interaction away from any number.
- Colorblind safe palette, keyboard reachable, plain language lead in and a glossary per screen
  (kept from the current UI, which already did this well), honest empty states for tracks with no
  data yet.
- The truth stays the JSON in git; the derived series the lens reads is rebuilt on every serve and is
  never committed.

## 5. Part D: reproducibility and the golden regression suite

The rebuild is only trustworthy if it is pinned. This design adds:

- **A golden regression suite**: frozen fixture inputs and their expected outputs to three decimals,
  for the raw anomaly, RONI, the monthly spine at known events (the December 2023 peak), the daily
  edge, the nowcast on a partial month fixture, the model skill on a fixed window, and the peak. Any
  method change that moves a number turns a golden red on purpose, so the change is a decision, not a
  drift.
- **One reproduce command**: rebuilds every committed number from the frozen inputs offline and
  verifies the goldens, so "reproducible to the digit" is a command anyone can run, not a claim.

## 6. Machine verifiable finish criteria (the GO threshold)

All offline, behind the socket guard, decided by `./run.sh test` exiting 0, plus the smoke reporting.

| # | Criterion | What the machine checks |
| --- | --- | --- |
| 1 | Dual index | Every record carries both the raw anomaly and RONI; RONI drives the phase and strength; a fixture pins both to golden values to three decimals. |
| 2 | One anomaly engine | The daily edge, the monthly spine, and RONI all call one engine; a masked cell changes nothing; the grid alignment check is live. |
| 3 | Reconciliation | A preliminary value whose final is available is replaced, the flag flips, and the revision is recorded; tested on a two version fixture. |
| 4 | Nowcast uncertainty | The current month estimate's band is strictly wider on a few day fixture than on a full month fixture; near unbiased on a flat month fixture. |
| 5 | Provenance universal | One block shape on every artifact family; the structural gate turns red on an injected hole anywhere. |
| 6 | Predictive distribution | Every forecast horizon returns a mean and a calibrated spread; the point forecast is its median. |
| 7 | Uncertainty decomposed | The predictive variance is the sum of residual, parameter (block bootstrap), and input components; tested that removing input uncertainty narrows the band. |
| 8 | Calibration | The PIT histogram and reliability over the walk forward are within tolerance; an intentionally miscalibrated forecast fails the check. |
| 9 | Baselines and CIs | Damped persistence is scored; every skill number carries a block bootstrap confidence interval. |
| 10 | Seasonal skill | Skill is reported as an issue month by target season matrix, not a scalar. |
| 11 | Probabilistic scores | CRPS and RPSS are computed against the baselines over the walk forward. |
| 12 | Peak honest | The peak issues from the nowcast, its band is the decomposed spread, training and prediction months are aligned, and the issue month rule is a frozen written decision. |
| 13 | Reproducible | One command rebuilds every committed number and matches the goldens to three decimals. |
| 14 | Gate green | The full suite passes offline behind the socket guard, with all new tests. |

Smoke (reports, never gates): all six live doors reachable and shape unchanged (OISST daily, OISST
monthly spine, the tropical band source for RONI, PMEL warm water volume, CPC ONI control, CPC RONI
probabilities).

## 7. Build sequence (each layer demonstrable before the next)

The method's descent: build a thin working spine end to end, then deepen. Never finish one layer in
isolation; keep it demonstrable.

1. **Provenance unification and the golden harness first** (small, unblocks everything, makes drift
   impossible from here on).
2. **The dual index**: RONI alongside the raw anomaly, one engine, the tropical climatology fixture,
   goldens. Recompute the monthly spine and the daily edge on it.
3. **The nowcast**: the current month estimate with uncertainty, replacing the raw partial month.
4. **The probabilistic forecast**: predictive distribution, decomposed and calibrated uncertainty,
   damped persistence, bootstrap confidence intervals.
5. **The verification suite**: seasonal skill matrix, CRPS, RPSS, reliability, PIT.
6. **The peak, rebuilt** on the nowcast and the decomposed band, issue month decision frozen.
7. **The lens, redesigned** around the four screens, reading the rebuilt JSON.
8. **The reproduce command and the README**: the warming trend and RONI explained, the lag stated,
   reproducibility one line.

## 8. Non-goals, risks, and honest limits

- **We do not claim to beat the dynamical ensembles.** The value is transparency, provenance, and a
  verified track record, not accuracy leadership. The dashboard says so.
- **No new heavy dependency by default.** RONI, the nowcast, the bootstrap, CRPS, RPSS, and the
  calibration checks are all a few lines of numpy on data we already have. A full Linear Inverse Model
  with an EOF state would be the first change that might justify a new dependency, and it is out of
  scope here, named as future work.
- **Small sample honesty.** A few dozen years and a handful of strong El Ninos mean wide bands and
  fragile peak analogs. This is stated everywhere, never hidden. The bands are wide because the truth
  is uncertain, not because the method is sloppy.
- **RONI is a choice, not a law.** Making RONI the headline is a defensible, current, official aligned
  choice; the raw anomaly stays fully visible so a reader who wants the classic ONI has it, with the
  gap between them charted as the warming signal it is.
- **The baseline stays 1991 to 2020, fixed, forever, never changed silently.** RONI removes the trend
  by subtraction, not by moving the baseline.
