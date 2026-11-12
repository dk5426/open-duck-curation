# Infeasible-pool study `cinf`: plan, written before any results (2026-11-12)

Not part of the signed pre-registration: this study was added after st7 and the contamination sweep. This file fixes
the analysis and the predictions before the study's first result exists, so the outcome cannot shape them.

**Question.** Does trackability curation help when the training pool contains motions the robot cannot perform, as in
ExBody2's raw motion capture? And does a cheap kinematic check capture most of that benefit?

**Why this study.** In st7 and the sweep (cs30, camb, cs50), curation never beat full, and full was not hurt by
contamination. Every clip there passed our kinematic checks or was a geometric artifact the policy tolerated (cs50).

## Data: `data/clips_v5inf` (`curation/clips/make_infeasible.py`)

37 clean v5 train clips plus 55 infeasible ones (60% of the train set). Val and test are the clean v5 ones.

| Group | Clips | Passes the kinematic check |
|---|---|---|
| Rejected ambitious gaits (joint targets clipped to the range) | 28 | 0 |
| Rejected corrupted copies (also in cs50) | 16 | 0 |
| New impossible motions (leans, unbalanced bows, one leg, jump, crouch snap, sway and head whips) | 11 | 10 |

## Procedure (`run_study.py --tag cinf`)

1. Scoring policy on all 92 train clips (300M). Score every train clip with the original score (judging changes only).
2. τ candidates p25, p45, p65, p85 of the train scores. Each is trained **from scratch** for 100M, then scored on val
   (30 rollouts). τ* = lowest mean val score; ties within 0.02 go to the larger subset.
3. Coverage keeps the best clip of each category that val/test hold; train-only categories get no coverage slot.
4. Final policies, 200M, seeds 0, 1, 2:
   - full: all 92 clips;
   - curated: τ* subset;
   - random: matched in total duration to curated;
   - checked: the 47 clips that pass the kinematic check.
5. Test: nominal, push 0.3 and 0.6 m/s, friction × 0.6, 10 rollouts each.

## Analysis, fixed now

- **Primary:** test nominal, original score e (legs + body-frame keypoints, falls = 3).
- **Pass bar:** curated − full and curated − random both with the 95% paired bootstrap CI below 0, and no category's
  completion more than 0.05 below full's.
- **Secondary:**
  - curated − checked;
  - score_v2 (adds position and heading error) and its parts;
  - push and friction tests;
  - the share of each infeasible group that curation removed;
  - the scoring policy's fall rate per group (whether the "impossible" clips really are).

## Predictions

- **P1.** The scoring policy falls on most new impossible clips and scores the rejected gaits worse than the clean
  clips. Curation removes most of the infeasible clips while keeping most clean ones.
- **P2.** Full is worse than in st7 (e above about 0.42). This is the precondition for curation to help.
- **P3.** Curated beats full and random (the pass bar).
- **P4.** Checked lands between full and curated. The 10 impossible clips that pass the check still hurt it.

## What each outcome means

| Outcome | Reading |
|---|---|
| P2 false (full not hurt) | PPO tolerates even infeasible references here; curation cannot help, and the study ends as a null. |
| P2 true, P3 true, curated ≈ checked | Curation works when infeasible data exists, but a kinematic check captures most of it. |
| P2 true, P3 true, curated better than checked | Curation catches dynamic infeasibility that the kinematic check misses. |
| P2 true, P3 false | Infeasible data hurts, but our curation does not fix it; inspect what it kept. |
