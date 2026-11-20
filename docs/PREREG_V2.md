# Pre-registration v2: when does trackability curation help, and does it beat a cheap filter? (DRAFT)

Status: draft for the team, 2026-11-15. Everything run before this file (dry run, st5-st7, the contamination sweep,
cinf, cunb, cunbd, cdroop) is **exploratory** and motivated this design; none of it is re-used as evidence here.
Changes after sign-off go to "Amendments" with a date and a reason.

## What we are doing

We ask whether choosing training clips by how well a robot can actually follow them (trackability curation, after
ExBody2) gives a better tracking policy on Open Duck Mini v2, and whether a cheaper filter does as well.
- **Data:** one fixed clip set of clean motions plus leans that run from easy to physically impossible. Every clip's
  feasibility is measured, not assumed.
- **Training:** policies on subsets chosen by different selectors, at several subset sizes, with several learning
  algorithms and ways of handling bad clips, 3 seeds each.
- **Comparison:** tracking error, falls, robustness and training cost on held-out clean motions.

## 1. Data: `data/clips_v7` (`curation/clips/make_v7.py`, frozen at the commit that adds this file)

- **Train, 82 clips:**
  - v5's 37 clean clips (walks forward and back, side steps, turns, march, crouch, bow, sway, head);
  - 45 leans: the base shifted forward U(1, 16) cm or back U(1, 10) cm with the soles fixed, random timing (seed 7).
- **Val:** v5's 18 clean clips, unchanged.
- **Test, 56 clips:**
  - v5's 18 clips plus 38 new ones from 20 new sources, two per category, so each category has 3 test sources;
  - every new parameter lies inside the category's training range;
  - two new variants failed the kinematic check and were dropped (side_step dy −0.025 normal, walk_turn 0.035 / −0.12
    normal).
- **Feasibility label of every train clip** (manifest `feasibility`):
  - `kinematic`: passes the joint-limit, foot-gap and sole check.
  - `static`: the hold test (`curation/clips/hold_test.py`). The robot is placed in the clip's most extreme held pose
    under its own servos for 2 s, and the result is holds, fails, or dynamic (no held pose).
  - `infeasible` = the static test fails.
  - **Measured counts:**
    - All 37 clean clips: none fails the hold test (10 hold, 27 dynamic).
    - Leans: 8 feasible (back ≤ 1.9 cm, forward ≤ 5.1 cm) and 37 infeasible (back ≥ 2.7 cm, forward ≥ 6.2 cm).
    - Only 9 leans, all extreme, fail the kinematic check. 28 infeasible leans pass it.

Why leans: they were the only contaminant in the exploratory studies that made the policy fall and hurt the full set.
Corrupted, ambitious and robot-only-infeasible clips did not.

## 2. Selection score and its validation

- **Scoring policies:** three, seeds 0, 1, 2, each PPO for 300M steps on all 82 train clips.
- **Scoring:** every train clip, 10 rollouts per scorer.
- **Candidate scores:**
  - `score`: legs rms / 0.10 + body-frame keypoints / 0.02; 3 per frame after a fall.
  - `score_v2`: + base position error / 5 cm + heading error / 0.2 rad.
  - `score_v3`: + whole-body tilt error / 0.1 rad.
  - `fall_rate`.
- **Validation:** the AUC of each candidate for flagging the measured-infeasible clips, averaged over the three
  scorers, and the Spearman rank correlation between scorers.
- **Choice:** the candidate with the highest mean AUC. Within 0.02 of the best, the original `score` wins.
- **Curation ranks clips** by the mean over the three scorers. Caveat: the AUC uses the feasibility labels, which a real
  user would not have; it validates the criterion on this dataset only.

## 3. Phase 1, PPO curve (`curation/study/run_curve.py --tag cv7`)

- **Keep-fractions:** 40, 55, 70 and 85% of the 82 train clips (33, 45, 57, 70 clips). **Main point: 55%.**
- **Selectors:**
  - curated: lowest ensemble score first.
  - kinematic, the cheap filter: clips that pass the kinematic check first, in the oracle's fixed random order, then
    failing ones by kinematic score.
  - oracle, also a practical physics filter (as in KungfuBot's centre-of-mass / centre-of-pressure filter): clips the
    hold test does not fail first, in a fixed random order, then failing ones by increasing lean size.
  - random: one seeded draw per training seed.
  - full: all 82 clips, the reference.
- **Coverage, the same rule for every selector:** each category held by val / test keeps at least one clip.
- **Training:** PPO, reference feed-forward tracking env (playground patches 0010-0013), 200M steps, seeds 0, 1, 2.
  Runs: 4 fractions × 4 selectors × 3 seeds = 48, plus full × 3.
- **Test:** nominal for every run. Push 0.3 / 0.6 m/s and friction × 0.6 for the main fraction and full. 10 rollouts
  per clip.
- **Training cost** (main fraction and full):
  - wall-clock and M steps per hour from the checkpoint times;
  - validation e (5 rollouts) at 25 / 50 / 75 / 100% of training;
  - steps and hours to reach validation e ≤ 1.1 × the best final validation e.

## 4. Phase 2, other algorithms (55% only)

- **Conditions:** full, curated, kinematic, random and oracle at the Phase 2/3 keep-fraction f* (see Amendments,
  2026-11-16; 55% unless the rule picks another), using the Phase 1 subsets (selection held fixed;
  only the learner changes), 3 seeds each.
- **Budget:** equal wall-clock, the mean wall-clock of the Phase 1 PPO 200M runs.

| Algorithm | Mathematical basis | Why |
|---|---|---|
| SAC | off-policy, maximum-entropy soft Q-learning | its replay buffer keeps re-using bad clips |
| FastTD3 | off-policy deterministic policy gradient, clipped double-Q, distributional critic | modern parallel-simulation off-policy method |
| DAgger distillation | supervised imitation of a PPO teacher on states the student visits | ExBody2's teacher-student pipeline |
| ARS | derivative-free random search | no gradient and no value function |
| PPO without reference feed-forward | same algorithm, targets = home + action (**an ablation, not a new method**) | tests whether the feed-forward is why bad clips are tolerated |

## 5. Phase 3, other ways to handle bad clips (PPO, 3 seeds each)

Each method is compared against full, curated at f* and oracle at f* (f* as in Phase 2).

| Method | Definition |
|---|---|
| Soft weighting | train on all clips, sampling probability ∝ exp(−ê / median ê) (ê = ensemble score) |
| Failure-prioritised sampling | probability ∝ 0.1 + the clip's recent episode failure rate, refreshed during training |
| Curriculum | the training set grows from the 40% curated subset to all clips by ensemble rank, linearly over training |
| Adaptive tracking tolerance | each clip's reward tolerances scale with its running tracking error (KungfuBot) |
| Repair | each infeasible lean is replaced by the largest same-direction lean that passes the hold test, same timing |

Exact implementation details (refresh intervals, error averaging) go into Amendments before Phase 3 starts, before any
Phase 3 result exists.

## 6. Metrics and statistics

- **Primary:** mean test e (original `score`), nominal, PPO, main fraction.
- **Secondary:**
  - score_v2, score_v3, tilt error;
  - falls and completion;
  - push and friction tests;
  - the full curve;
  - training cost;
  - Phases 2 and 3.
- **Statistics:** for each test clip, the mean over the 3 seeds. Differences are paired over test clips. 95% bootstrap
  CIs (10,000 resamples) resample **whole motion sources**, then one seed per condition within each clip.
- **Sensitivity:** leave-one-test-clip-out. The Δ range, and any single clip whose removal moves the CI across 0.

## 7. Pass bar ("curation helps", Phase 1, main fraction, primary metric)

- curated − full and curated − random: 95% CI entirely below 0;
- no category's completion more than 0.05 below full's.
- **Reported alongside, no bar:**
  - curated − kinematic and curated − oracle;
  - whether the pass survives every single-clip removal ("robust pass").

## 8. Predictions (written before any v7 result)

- **P1.** Full is hurt: its test e exceeds the clean-only level of the exploratory studies (about 0.42) by more than
  0.03, and it falls on some test clips.
- **P2.** Curated passes the bar at 55%.
- **P3.** Oracle ≤ curated ≤ kinematic in test e at 55%; curated is within 0.02 of oracle.
- **P4.** The off-policy learners (SAC, FastTD3) are hurt more by the leans than PPO: a larger full − oracle gap.
- **P5.** PPO without feed-forward is hurt more than PPO.
- **P6.** At 55%, curated reaches the validation threshold in fewer steps than full.

| Outcome | Reading |
|---|---|
| P1 false | Even with measured-infeasible leans at 55% of the pool, PPO tolerates them; curation has nothing to fix in this setting. |
| P1, P2 true; curated ≈ oracle ≈ kinematic | Curation helps, but a cheap filter captures it. |
| P1, P2 true; curated ≈ oracle < kinematic | Curation finds dynamic infeasibility the cheap kinematic filter misses. |
| P2 true but not robust | The gain rests on a few test clips; report as fragile. |

## Sign-off

| Name | Date |
|---|---|
| Dhawal Kabra | |
| Kanad Patel | |
| Neer Patel | |
| Pierrick Rugery | |

## Amendments
- 2026-11-15: approved by Dhawal Kabra in chat before any v7 result; team signatures to follow.
- 2026-11-15, before any v7 result: training cost also reports each selector's own overhead. For curated, that is the
  three scoring policies' GPU-hours plus scoring the train clips; the kinematic check and hold test take seconds of
  CPU. Curation's total compute is compared with the cheap filters' on that basis.
- 2026-11-15, before any v7 subset or result: (1) the kinematic selector is a pass / fail filter mirroring the oracle
  (check-passing clips first in the same fixed random order). The drafted ranking by kinematic score rated slow held
  leans easier than clean gaits: in the smoke test it kept 26 leans and dropped about half the clean gaits, which would
  have made it a straw man. (2) The headline training cost is M steps to the validation threshold. Wall-clock stays
  secondary because evaluations share the GPU with training. (3) Subset tables also list the clean clips kept.
- 2026-11-15, same amendment: added `checked`, every clip passing the kinematic check at its natural size (73 clips),
  3 seeds, evaluated like the main fraction and compared with curated at 55% (no pass bar). This is how the check is
  used in practice; a pass / fail filter forced to a fixed fraction only pads with random clips.
- 2026-11-15, before any v7 result: label stability (`curation/clips/label_stability.py`, `<lib>/label_stability.json`).
  Every held pose was re-tested under 27 perturbations: friction × 0.8 / 1 / 1.2, servo gains × 0.9 / 1 / 1.1, test frame
  ±5, and 3 s holds. A clip is borderline when fewer than 80% of these agree with its label. Result: 1 of 55 is borderline
  (`lean__33`, +5.1 cm, labelled feasible, fails 44% of perturbed tests). Every other label agrees in all 27. The analysis
  reports the selection AUCs without borderline clips and how many each subset keeps. The dataset and its labels are
  unchanged. Remaining caveat: the hold test is static, so it does not test the move into the pose or active balance.
- 2026-11-15 21:30, after the scoring policies and before any final result: selection validation picked `score_v3`
  (AUC 0.862 vs the original score's 0.835, beyond the 0.02 margin). Because that choice used the feasibility labels,
  the main fraction is also trained curated by the original score (`curatedscore_f55`, 3 seeds; no labels needed, which
  is what a real user would run) and reported beside curated. The pass bar stays on curated as pre-registered.
- 2026-11-15 21:30: the driver stopped at 21:12. Its scheduler misread a "GPU busy" launch refusal as a failed run when
  it polled more than 2 minutes after the launch. Fixed in `run_study.Scheduler`: a refusal is now recognised by
  launch.txt not being written. No run or result was affected.

- 2026-11-16, no result affected: a driver restart at 14:17 on 11-15 re-queued `cv7_score_s0` while it was still
  running, and the copy started on GPU 2 at 16:26, 20 s before the original finished. It trained a second, identical
  seed-0 run into the same folder. Scoring used the original's final checkpoint (`2026_11_15_162703_300482560`), so the
  s0 scorer is a single clean run. The copy left GPU 1's lock behind, which idled GPU 1 until 11-16 13:00.
  `tools/launch_train.sh` now refuses to start a run that is already live in its folder and reclaims a lock whose
  process is gone.
- 2026-11-16, before any Phase 1 curve result at 40 / 70 / 85% and before any Phase 2 / 3 run (owner's request):
  Phases 2 and 3 run at **f\***, the keep-fraction where curated does best, chosen on **validation** clips only.
  After Phase 1, each curated final run (4 fractions × 3 seeds) is evaluated on the 18 validation clips at its final
  checkpoint (10 rollouts, original `score`). f\* = the fraction with the lowest mean over the 3 seeds; if 55% is within
  0.01 of the best, 55% is kept. The test set plays no part in the choice. All selectors in Phases 2 / 3 use their
  Phase 1 subsets at f\*. The Phase 1 pass bar stays at 55%. Because f\* is picked to suit curated, Phase 2 / 3
  comparisons are read as "curation at its best size", and the report says so. Seen before this amendment: test results
  of 6 finished runs at 55% only (checked, curated, curated by the original score).
- 2026-11-17, after interim Phase 1 results (40 / 55 / 70%), all **exploratory**:
  (1) mechanism analysis `curation/analysis/mechanism.py` -> `results/cv7/MECHANISM.md` (score overlap, what curated
  drops, the dropped share against curated − oracle per category);
  (2) stratified curation `curatedstrat` at the main fraction and f* (3 seeds each): the curated ranking with a
  proportional floor, so each val / test category first keeps its best ceil(f × n) train clips (55%: 31 clean, 6
  infeasible, against curated's 27 and 10). It answers "is the weak coverage rule why curation loses?". It is run by
  the cv7 driver's second pass (`--fstar --strat`) after Phase 1;
  (3) SUMMARY.md labels one PRIMARY result (curated vs full / random at 55%, nominal, original score); everything else
  is SECONDARY or EXPLORATORY; limitations in `docs/LIMITATIONS.md`; robot demo plan in `docs/ROBOT_DEMO_PLAN.md`.
- 2026-11-19, after Phase 1 and before any Phase 2 run: Phase 2 implementation (`curation/study/train_alt.py`,
  `fasttd3_duck.py`, `run_phase2.py`, `curation/analysis/phase2_analysis.py`). Every learner trains on the Phase 1
  subset files, env, randomization and observation; every policy is tested by the Phase 1 evaluator (`eval_clips.py`,
  nominal, 10 rollouts). PPO is not rerun: its Phase 1 runs are the reference row.
  (1) **Budget:** equal wall-clock = 1.562 h, the mean start-to-exit time of the 63 Phase 1 PPO 200M runs. Each learner's
  step count is fixed in advance from its measured throughput in a smoke run on an otherwise idle GPU
  (`results/cv7/phase2_calibration.json`): SAC 23.8M, ARS 31.5M, DAgger 93.9M, FastTD3 54.3M env steps.
  (2) **PPO without feed-forward:** Phase 1's runner unchanged with `ref_feedforward=False`, 200M steps.
  (3) **SAC (brax):** the critic sees the actor observation (brax SAC has no asymmetric critic); actor and critic
  512-256-128; MuJoCo Playground's SAC config with discount 0.97 and a 1M replay buffer (its 4M does not fit the 16 GB
  GPUs).
  (4) **ARS (brax):** linear policy on the normalized actor observation, 60 directions, top 20, step 0.015, noise 0.025.
  (5) **DAgger (brax online DAgger):** the teacher is the Phase 1 PPO final policy of the same condition and seed, so a
  student sees only its own condition's clips; the student is PPO's policy network, trained by L2 on the teacher's
  mean action; the teacher acts only in the first iteration. Its teacher's 1.56 h is not charged to its budget.
  (6) **FastTD3:** the authors' code (github.com/younggyoseo/FastTD3) and Playground defaults, in its own torch venv,
  with our env behind its Playground bridge (actor on the actor observation, critic on the privileged one). Deviations
  for the 16 GB GPUs: replay 2048 steps per env (1024 envs), 256 evaluation envs, `torch.compile` off (Triton cannot
  compile its kernels on these GPUs), no rendering. The trained actor is exported to JAX for the evaluator; export
  and torch actor agree to 5e-6.
  (7) If a run's wall-clock lands far from the budget (another job on the GPU), the step count is not changed; the
  report gives each run's wall-clock.
  Conditions: full, curated, kinematic, oracle, random at the Phase 2 fraction, 3 seeds each.
- 2026-11-19, after Phase 1, all **exploratory** (owner's request; order: this, then the wild-clip study, then Phase 2):
  (1) selection-score candidates from the scoring policies' evaluations only (`curation/analysis/score_candidates.py`
  -> `results/cv7/SCORE_CANDIDATES.md`): type-normalised score, learning progress, balance only, a val-based
  threshold. AUC feasible vs infeasible: type-normalised against the clean val clips 0.978, balance 0.966, current
  score_v3 0.861, learning progress 0.59-0.60; the threshold keeps 72-81 of 82 clips.
  (2) `curatedtn_f55`: curation by the type-normalised score (score_v3 over the median score_v3 of the clean val clips
  of the clip's motion group; crouch, bow, sway, head and lean form one "stationary" group), same coverage rule, 45
  clips: 35 clean, 2 infeasible. 3 seeds, 200M, launched 11-19 before any of its results (`run_curve.py --tn`).
  Caveat: grouping leans with the stationary moves uses knowing that a lean is a held pose.
  (3) Wild-clip study, planned: keyframed hop, kick, stomp, tap, dance, headbang, twist clips swept from gentle to
  beyond the robot (`curation/clips/make_wild.py`), mixed with the clean v7 clips, no leans. No feasibility labels and
  no oracle: conditions full, curated, type-normalised curation, kinematic, random. A reference-only physics check
  (`curation/clips/dynamic_check.py`) marks every v7 walking gait infeasible, so it is reported as a description only.
  Test set: the clean v7 test clips plus held-out gentle wild variants. Test-clip rule, fixed before any result: a
  test clip is dropped from the analysis if every condition falls in at least half of its rollouts.
