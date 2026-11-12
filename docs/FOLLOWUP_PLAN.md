# Follow-up studies `cunb`, `cunbd`, `cdroop`: plan, written before any results (2026-11-12)

Not part of the signed pre-registration. Same status as `docs/CINF_PLAN.md`: this file fixes the analysis and the
predictions before the first result, so the outcome cannot shape them.

## Why

The `cinf` scoring policy never fell on the 11 "impossible" clips and scored them easier than the clean ones (median
0.26 vs 0.46). Two reasons:

1. **Most of the pool was infeasible only on the robot, not in the simulator.** The env already rate-limits motor
   targets at 5.24 rad/s, and a static-hold test (`curation/clips/hold_test.py`) shows only 6 of the 55 infeasible
   clips cannot be held in the simulator (leans, unbalanced bows, one-leg stances; every clean held pose holds).
2. **The policy shrugs off small infeasibility.**
   - On a one-leg clip it keeps every joint on target (leg error 0.008 rad) and tips its whole body onto the raised
     foot.
   - The score is body-relative, so it cannot see this.
   - Only big leans make it fall: 5/5 at forward >= 11 cm and back >= 6 cm.

## Studies

All three use the same procedure as `cinf`:
- scoring policy, 300M;
- τ candidates p25 / p45 / p65 / p85, each trained from scratch for 100M;
- finals full / curated / random / checked, 200M, seeds 0, 1, 2;
- test nominal, push 0.3 / 0.6, friction × 0.6.

Each study is preceded by a smoke run. They run in this order, after `cinf`:

| Tag | Library | Servo model |
|---|---|---|
| `cunb` (B) | `data/clips_v5unb` | stock |
| `cunbd` (A+B) | `data/clips_v5unb` | `servo_droop` on |
| `cdroop` (A) | `data/clips_v5inf` | `servo_droop` on |

- **`data/clips_v5unb`** (`curation/clips/make_unbalanced.py`):
  - 37 clean train clips plus 45 big leans (55% of train): forward 10-16 cm and back 5-12 cm, three timings.
  - A lean is kept only if its held pose fails the hold test; all 45 fail.
  - 20 of the 45 pass the kinematic check, so `checked` = 57 clips.
- **`servo_droop`** (playground patch 0014, `TRACKING_OVERRIDES={"servo_droop": true}`):
  - The torque available in the direction of motion falls linearly to 0 at the 4.7 rad/s no-load speed, every physics
    substep.
  - It applies to the scoring policy, the training runs and every evaluation of that study.
  - Numbers from droop studies are therefore not comparable with stock-servo studies, only within the study.

## Analysis, fixed now

- **Primary:** test nominal, original score e.
- **Pass bar:** as in `cinf`. Curated − full and curated − random both with the 95% CI below 0, and no category's
  completion more than 0.05 below full's.
- **Secondary:**
  - curated − checked;
  - score_v2, and `score_v3` = score_v2 + tilt_err / 0.1 rad;
  - `tilt_err` alone: the angle between the robot's and the reference's gravity direction in the body frame, new in
    `eval_clips.py`;
  - push and friction tests;
  - the share of leans each τ removes;
  - the scoring policy's falls per lean size.

## Predictions

- **P1.** The scoring policy falls on most leans at forward >= 11 cm and back >= 6 cm, and scores them worse than every
  clean clip. Curation at τ* removes most leans and keeps most clean clips.
- **P2.** Full is worse than in st7 and `cinf` (e above about 0.43). Training on 55% unreachable leans costs it
  something. This is the precondition.
- **P3.** Curated beats full and random (the pass bar).
- **P4.** Checked lands between full and curated: it still holds 20 leans.
- **P5 (droop).** With the droop, every policy is slower and scores worse in absolute terms. More of the clean gaits and
  `clips_v5inf`'s fast clips become untrackable, so curation removes more. Whether that helps is open: no prediction.

| Outcome | Reading |
|---|---|
| P2 false in `cunb` | Even clips that make the policy fall do not hurt training here; curation cannot help, and the null holds across every pool tried. |
| P2 true, P3 true | Curation helps once the pool holds motions the simulated body cannot do, ExBody2's setting. |
| P2 true, P3 false | Unreachable clips hurt, but our curation does not fix it; inspect what it kept. |
