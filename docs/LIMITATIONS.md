# Limitations and how to read the cv7 results

Written 2026-11-17 for the report, while Phase 1 (cv7) was finishing. Each item says what it limits and what we did
about it.

## 1. The oracle has a home advantage

The oracle (the physics filter) uses the hold test, and the contaminants in clips_v7 are leans, which are exactly what
the hold test measures. So in this dataset the oracle sees the true labels by construction, while curation has to infer
them from tracking error.
- **Read "oracle beats curated" as:** a direct check of the property that makes a clip infeasible beats a proxy for it.
  It does **not** show that a physics filter beats curation on every kind of bad clip.
- **Mitigation:** the kinematic filter is the fair cheap baseline. It does not see the hold-test labels, and it also
  beats curation at every keep-fraction measured so far.

## 2. Only static infeasibility was tested

The hold test checks balance in one held pose. Dynamic infeasibility passes it, for example motion too fast for the
servos, too much torque, flight phases, sliding feet or friction limits.
- We tried dynamic contaminants in the exploratory studies (cs30, cs50, camb, cinf, cdroop). The simulator plus
  feed-forward PPO tolerated all of them: no falls, and no effect of curation (`docs/CONTAMINATION_SWEEP.md`,
  `docs/CINF_PLAN.md`, `docs/FOLLOWUP_PLAN.md`).
  - The target rate limit (5.24 rad/s) turns "too fast" into "slower".
  - The feed-forward lets the policy lag behind impossible parts.
  - The original score ignored base motion.
- **So the conclusion is scoped:** for balance-infeasible clips, a physics check beats trackability ranking. For
  dynamically infeasible clips, we could not make them hurt in this simulator, so neither selector is tested there.
  Whether curation helps against dynamic infeasibility that does hurt needs a stricter actuator model or robot data.

## 3. The hold-test labels are static and binary

- Label stability: 1 of 55 held poses is borderline (`data/clips_v7/label_stability.json`).
- But "infeasible" means "the robot cannot hold this pose still with its servos". A policy can still approximate a
  near-boundary lean by actively balancing:
  - the 10 infeasible leans that curated keeps at 55% are 2.7–4.2 cm back or 6.2–7.0 cm forward;
  - the scoring policies never fell on them (`results/cv7/MECHANISM.md`).
- Those clips may be harmless to train on. The measured damage comes from the clean clips curation drops, not from the
  leans it keeps.

## 4. One contaminant family, one robot, one simulator

All confirmatory evidence uses leans on Open Duck Mini v2 in MuJoCo Playground (MJX), with PPO and reference
feed-forward. Phase 2 (other learners) and Phase 3 (other ways to handle bad clips) test part of the generality; the
robot, the simulator and the contaminant family stay fixed.

## 5. Curation is implemented once, not iterated

- We score with three policies trained once on all clips, rank globally, and cut at a fixed keep-fraction, which is
  ExBody2's basic recipe.
- ExBody2 and later work refine this: they iterate scoring and training, choose per-motion thresholds, or keep coverage
  within each motion family. The coverage rule here (at least one clip per val / test category) is weak.
- **Mitigation (exploratory):** stratified curation (`curatedstrat`), which keeps a proportional share of every
  category before ranking globally, at 55% and at f*.

## 6. Multiple comparisons

- There is one primary result: curated vs full and random at 55%, nominal test, original score (PREREG v2 §7).
- Everything else is labelled SECONDARY (pre-registered, no pass bar, no correction) or EXPLORATORY (added after
  results were seen), both in `SUMMARY.md` and in the report.
- Exploratory items:
  - the mechanism analysis;
  - stratified curation;
  - any per-category reading.
- Phases 2 and 3 run at f*, which is chosen to suit curation, so they read as "curation at its best size".

## 7. Simulation only

Every number is from simulation. The robot demo (`docs/ROBOT_DEMO_PLAN.md`) is a qualitative check, not a test of
the hypothesis.

## 8. Process incidents (no result affected)

The PREREG v2 amendments record each one:
- a scheduler misreading a refused launch;
- a duplicate scoring run, whose scorer stayed a single clean run;
- a stale GPU lock that idled one GPU for about 20 h.
