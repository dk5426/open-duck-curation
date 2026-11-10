# Pre-registration: does trackability-based curation help? (DRAFT)

**Status: draft, not frozen.** Nothing in Step 4 (scoring policy) or Step 5 (final runs) starts until all four team
members sign off below. After sign-off, this file changes only through a dated amendment at the bottom that says why.

**Code these rules refer to:**
- `curation/eval/eval_clips.py`: score and per-clip metrics.
- `playground/open_duck_mini_v2/tracking.py`: training environment.
- `data/clips_v1/`: dataset.

## P.1 Clips and splits

- Dataset `data/clips_v1` (`docs/DATASET.md`): 28 clips, 4 s each, gaits and crouches.
- The split is per **source** (13 gait directions, 4 crouch depths), stratified by category, seed 7. Both variants of
  a source share its split.
- **Train 13 / val 4 / test 11 clips.** The split file (`splits.json`) is hashed and the hash is written here at
  sign-off.

**Open issues the team must settle before sign-off:**

1. **Validation set is thin.** 4 clips (two turn-in-place, two crouch) leaves some categories with no validation clip.
   - Option A: re-split with 2 val sources per category where possible.
   - Option B: choose τ by cross-validation over training clips instead.
2. **Crouch clips teach nothing yet.**
   - Standing still earns 98% of perfect tracking (reward ledger, `results/reward_ledger_v1.json`), because the model's
     knee limit caps them at 8 mm.
   - Either drop the crouch category from v1 or, after robot test R3 measures the real knee range, regenerate deeper
     crouches.

## P.2 Per-clip score (lower is better)

Over R = 10 rollouts per clip:
- deterministic policy;
- observation noise and 0–1 step action delay on;
- domain randomization off;
- start at frame 0.

    e(clip) = mean over ALL frames of the clip [ E_dof(t) / τ_dof + E_key(t) / τ_key ]

- `E_dof`: leg-joint rms error (rad).
- `E_key`: mean body-frame distance of the 5 keypoints (feet, knees, head) (m).
- **τ_dof = 0.10 rad, τ_key = 0.02 m.**
- **Early termination:** the fall frame and every frame after it score `E_FAIL = 3` (three tolerance units), so a clip
  cannot look good by ending early.
- **Also recorded, not part of e:** completion, falls, torque saturation (≥95% of the limit), joint-limit proximity,
  velocity and yaw-rate error.

**Open:** check τ against the pilot's error spread. If almost every clip scores below 1 or above 2.5, the score does
not separate clips; adjust τ once, before sign-off.

## P.3 Selection rule (whole clips)

1. A training clip is kept if `e ≤ τ` **and** completion ≥ 0.8.
2. **Coverage:** every category keeps its best clip by `e`, provided that clip's completion is ≥ 0.5. A clip below 0.5
   completion is never kept for coverage.
3. Variants are scored and selected individually; there is no source-level grouping at selection.

## P.4 Choosing τ (on validation, then frozen)

- **Candidates:** the 40th, 55th, 70th and 85th percentiles of the training-clip scores under the scoring policy.
- **For each candidate:**
  1. fine-tune the scoring policy for 50M steps on the selected subset D_τ;
  2. score the **validation** clips (P.2).
- **Pick:** τ* is the candidate with the lowest mean validation score. Ties within 0.05 go to the larger subset.
- **Freeze:** τ* and the curated clip list are written here.

## P.5 Random control

- Clips drawn uniformly from the training pool until the total duration matches the curated set's within 10%. All
  clips are 4 s, so that means the same number of clips.
- **One fresh draw per seed** (3 draws, seeds 0/1/2), recorded here before training.

## P.6 Training (every final policy)

- **Recipe:** `tracking.py` at the tagged commit (S3.8), default config, PPO settings as `BerkeleyHumanoidJoystickFlatTerrain` with `episode_length` 200.
- **Budget:** 200M environment steps, from scratch (not from the scoring policy), seeds 0, 1, 2.
- **Conditions:**
  - **full:** all train clips;
  - **curated:** D_τ*;
  - **random:** P.5;
  - optional fourth: **kinematic** baseline, a subset of the same size ranked by a kinematic-only score (peak joint
    speed relative to the servo, hip-roll demand, joint-limit margin). It tests whether policy scoring beats a cheap
    score.

## P.7 Test metrics

- **Clips:** every test clip, R = 10 rollouts, as P.2.
- **Per clip:** e, completion, falls, legs and head rms, keypoint error, velocity and yaw-rate error.
- **Coverage:** the share of categories in which the policy completes at least one test clip with completion ≥ 0.8.
- **Perturbation test:** fixed lateral pushes of 0.3 and 0.6 m/s base velocity at t = 1.5 s, plus floor friction × 0.6,
  on every test clip. Completion and e are reported separately.

## P.8 Statistics

- **Per test clip:** average over the 3 seeds.
- **Comparisons:** curated − full and curated − random, as paired differences over test clips.
- **Uncertainty:** 95% bootstrap confidence intervals (10,000 resamples over clips; seeds resampled within clips).
- **Reporting:** per category and aggregate. With 11 test clips, report effect sizes with CIs, not significance stars.

## P.9 Pass bar: "curation helps"

Both must hold:
1. Curated beats **both** full and random on mean test e, with each CI excluding 0.
2. Curated's completion is not lower than full's by more than 0.05 in any category.

## P.10 Checkpoints

- **Evaluated:** 100M, 150M and 200M for every policy; all are reported.
- **Pre-registered result:** the 200M checkpoint.

## Sign-off

| Name | Date |
|---|---|
| Dhawal Kabra | |
| Kanad Patel | |
| Neer Patel | |
| Pierrick Rugery | |

## Amendments

(none)
