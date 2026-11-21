# Pre-registration v3: trackability curation on a realistically messy library (v9)

Status: written 2026-11-19 by Dhawal Kabra after the cv7 study (PREREG v2) and before any v9 training, including the
dose check. The owner approved writing, committing and proceeding; team signatures follow during the dose check.
Changes after this commit go to "Amendments" with a date and a reason.

**What is new, and why.** cv7 (PREREG v2) failed its primary test: plain curation lost to full at 55% because the
tracking score mixes how hard a motion type is with whether a clip is broken, so curation dropped hard clean gaits.
Two fixes found after cv7, so exploratory there, tied the oracle: stratified curation and **type-normalised curation**
(`curatedtn`, each clip's score divided by the median score of clean val clips of its own type; exploratory cv7 result
−0.032 vs full, CI [−0.099, −0.005]). v9 tests type-normalised curation **confirmatorily** on a new library that looks
more like real data: more motion types, few broken clips, broken clips inside real types, more kinds of breakage.
Everything from cv7, cv8 (cancelled) and before is exploratory and is not re-used as evidence.

## 1. Data: `data/clips_v9` (`curation/clips/make_v9.py`, frozen at the commit that records its counts below)

- **14 motion types:** walk_fwd, walk_back, side_step, turn_in_place, walk_turn, leg_lift (march, stomp, kick, tap),
  crouch, bow, sway, head, hop, dance, headbang, twist.
- **Clean clips per type:** 6 train, 3 val, 5 test, split by source; val and test sources never appear in train; test
  parameters mostly inside the train range.
- **Broken train clips, 20-25% of train,** each a broken copy of a clean train source of the same type. Labels are known
  by construction, and every "impossible" one is confirmed by a check:
  - impossible: balance shove (hold test fails), joint limit (kinematic check fails), hop take-off (take-off speed beyond
    the legs), speed (servo lag beyond the worst clean v7 walking gait), one foot held up too long (hold test with the
    raised foot fails);
  - corrupted (possible in principle, bad data): noise, glitch, foot skate.
- Counts, per-clip evidence and GIFs: `data/clips_v9/DATASET.md`, `results/clips_v9/gifs/` (filled in at the freeze
  commit, see Amendments).

## 2. Dose check (before the study; validation only)

- full vs clean-only (the clean train clips only), PPO 200M, seed 0, scored on the **val** clips (10 rollouts,
  original `score`); the test set is not touched.
- **Requirement:** val e(full) − val e(clean-only) ≥ 0.03. If not met, the breaks are made more severe (larger shoves,
  amplitudes, compression) and the check re-runs, at most 2 rounds, each recorded in Amendments before the next.
  If it still fails, the study runs anyway and is reported as "the contamination is tolerated".

## 3. Selection

- **Scoring policies:** three, seeds 0, 1, 2, PPO 300M on all train clips; every train clip scored with 10 rollouts.
- **Score:** `score_v3` (legs / 0.10 + keypoints / 0.02 + position / 0.05 + heading / 0.2 + tilt / 0.1, 3 per frame
  after a fall), fixed in advance from cv7; no label-based choice. AUC against the labels is reported, not used.
- **Selectors** (keep the top n = f × |train| with the cv7 coverage rule):
  - `curated`: ensemble score_v3, lowest first (ExBody2);
  - `curatedtn`: ensemble over scorers of score_v3(clip) / median score_v3 of the clean **val** clips of the clip's own
    type, each scorer's own evaluation; lowest first;
  - `kinematic`: kinematic check passes first (fixed random order), then by kinematic score;
  - `random`: one seeded draw per training seed;
  - `full`: everything. No oracle (owner's decision).
- **Keep-fractions:** 55, 65, 75, 85%. **Main fraction: 55%.**

## 4. Phase 1 (`run_curve.py --tag cv9`)

PPO with reference feed-forward, 200M steps, seeds 0-2, every selector × fraction, plus full. Test: nominal for every
run; pushes 0.3 / 0.6 m/s and friction × 0.6 at 55% and full; 10 rollouts per clip. Training cost as in PREREG v2.

## 5. Primary hypotheses and pass bar (main fraction, nominal test, original `score`)

- **H1:** `curatedtn` beats full and random.
- **H2:** `curated` beats full and random.
- **Pass for each:** both differences have the 97.5% source-level bootstrap CI entirely below 0 (Bonferroni over H1, H2),
  and no type's completion is more than 0.05 below full's. Robust pass: survives every single test-clip removal.
- **Test-clip rule:** a test clip is dropped from every comparison if every condition falls in at least half of its
  rollouts. Results are also reported without any type that is near failure for every condition (owner's decision:
  such types stay in training).

## 6. Secondary and exploratory

- Secondary (pre-registered, no bar, no correction): the curve; score_v2 / score_v3 / tilt; falls; pushes, friction;
  training cost; per-type results; per kind of break: the share each selector keeps, and AUC of the scores.
- Phases 2 and 3 below.

## 7. Phases 2 and 3 (after Phase 1)

- **f\*:** `curatedtn`'s keep-fraction with the lowest mean val e over the 3 seeds (final checkpoint, 10 rollouts,
  original score), **restricted to 55, 65, 75%**; 55% if within 0.01 of the best.
- **Phase 2:** PPO without feed-forward, SAC, ARS, DAgger, FastTD3 (the runner of commit ee1cc3a), equal wall-clock
  budget (the mean Phase 1 PPO run); conditions full, curated, curatedtn, kinematic, random at f*; 3 seeds. Accepted
  departures, reported as limitations: SAC's critic sees only the actor's observation; FastTD3 runs without
  torch.compile; the DAgger teacher's own training is not charged to its budget.
- **Phase 3 (PPO, 3 seeds),** each against full and curatedtn at f*: soft weighting, failure-prioritised sampling,
  curriculum, adaptive tracking tolerance, repair (impossible breaks replaced by their largest feasible version;
  corrupted ones filtered). Implementation details go into Amendments before Phase 3 runs.

## 8. Predictions (before any v9 result)

- **P1.** The dose check passes: full is worse than clean-only on val by ≥ 0.03.
- **P2.** H1 passes; H2 does not (plain curation still drops hard clean types).
- **P3.** curatedtn keeps a smaller share of impossible breaks than curated, and both keep corrupted breaks at higher
  rates than impossible ones.
- **P4.** Off-policy learners (SAC, FastTD3) show a larger full − curatedtn gap than PPO; PPO without feed-forward too.

## Sign-off

| Name | Date |
|---|---|
| Dhawal Kabra | 2026-11-19 (in chat) |
| Kanad Patel | |
| Neer Patel | |
| Pierrick Rugery | |

## Amendments
- 2026-11-20, data freeze before any v9 training: `data/clips_v9` at commit c2a07be (`docs/DATASET_V9.md`). 221
  clips: train 109 = 84 clean (6 per type) + 25 broken (22.9%; 16 impossible: 5 shove, 3 joint limit, 2 take-off,
  3 speed, 3 one foot long; 9 corrupted: 3 noise, 3 glitch, 3 foot skate), val 42 (3 per type), test 70 (5 per type).
  Departures from §1 recorded in DATASET_V9.md: gait shoves are 7 cm backwards (12 cm forward is out of the legs'
  reach), the speed bar is 0.698 rad (worst of 64 clean v7 gait clips), 9 clean gait sources that failed the kinematic
  check were swapped for spares. Clean-only for the dose check = the 84 train clips with `feasibility.corrupted` false.
  The dose check's full run is named cv9_full_s0 and is re-used as Phase 1's full seed 0 (same settings).
- 2026-11-21, f\* (§7) before any Phase 2 run: mean val e of curatedtn (final checkpoint, 10 rollouts, original
  score) 55% 0.386, 65% 0.366, 75% 0.370 -> **f\* = 65%** (`results/cv9/fstar.json`). The Phase 1 runner scored
  validation only at the main fraction, so these 9 evaluations were run separately on CPU. Phase 2 budget: the mean
  cv9 PPO run is 1.552 h (48 runs), within 0.6% of cv7's, so cv7's calibrated step counts are reused
  (`results/cv9/phase2_calibration.json`). Before Phase 2, a smoke run per learner (curatedtn, seed 0, short budgets) on
  v9 must produce a test evaluation. Phase 2 learners in order PPO without feed-forward, SAC, DAgger, ARS, FastTD3.
  `phase2_analysis.py` uses curatedtn as the reference condition when there is no oracle (P4: full − curatedtn gap vs
  PPO's).
