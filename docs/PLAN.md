# Course project plan: feasibility-aware motion curation on Open Duck

**Date:** 2026-11-09. The audit is in `AUDIT.md`; the live status is in `TRACKER.md`.

**Task ids** (`S1.3`, `P.2` and so on) are shared with the tracker.

**Each task lists:**
- tasks: what to build;
- files: what it creates or changes;
- reuse: code or ideas to start from;
- done when: the acceptance check;
- cost: compute and time;
- risk.

## Contents

0. Scope and principles
1. Step 1: Simulation and baseline validation
2. Step 2: Reference-motion dataset
3. Step 3: Motion-tracking policy
4. Pre-registration (before any curated-vs-full training)
5. Step 4: Scoring and curation
6. Step 5: Evaluation and report
7. Stretch goals
8. Who does what (parallel tracks)
9. Milestones
10. Risks

---

## 0. Scope and principles

### Minimum viable path (sim-only, must be delivered)

- **Clips:** walk, turn and crouch only, about 32 clips.
- **Policy:** one tracking policy design.
- **Curation:** a scoring policy, then curation.
- **Comparison:** full vs curated vs random, 3 seeds each, on held-out clips, with a pre-registered analysis.
- **Report.**

### Stretch goals (only after the minimum path is on track)

- head and neck clips;
- a kinematic-curation baseline (LIMMT-style);
- a hardware demo of conservative clips;
- human-video retargeting.

### Principles

- **Fix the experiment before running it.** Splits, score, tolerances, selection rule, pass bars and statistics go into
  `PREREG.md` (§4) before the first scoring-policy run.
- **Same pipeline for every condition.** Architecture, observations, rewards, PPO settings and step budget are frozen
  once Step 3 passes. Only the clip list changes.
- **Measure before trusting a reward.**
  - Write the reward ledger (what does standing still earn vs doing the clip?) before training.
  - Check that every term varies over the range where the behaviour happens.
  - A tracking term whose error clip or deadband is below the typical error gives no gradient; a sum-of-squares pose
    term makes small joints nearly free to ignore.
- **Report the reference as a row:** the "perfect tracking" value of each metric, so errors read against it.
- **Evaluate several checkpoints, not just the last** (the middle one was often the best in earlier work).
- **Code locations:**
  - Our code stays on local branches of the Open Duck repos (`local/setup`), never pushed upstream.
  - New project code goes in `~/Desktop/OpenDuck/course_project/code/` or in Playground under
    `playground/open_duck_mini_v2/tracking/`.

---

## 1. Step 1: Simulation and baseline validation

| id | Task | Done when | Cost | Risk |
|---|---|---|---|---|
| S1.1 | Weigh the robot (whole; legs, head and trunk if it comes apart), compare with the model's 2.107 kg | Measured mass in `course_project/MODEL_MATCH.md`; if off by >10%, scale link masses in a local MJCF copy | 1 h at the robot | Low |
| S1.2 | **Single-joint step and chirp test on the stand**, one joint group at a time | Dead time, t63 and peak speed per group, robot vs sim, in `MODEL_MATCH.md`; the sim within 1 control step of dead time and 25% of t63 | ½ day; robot + owner | Robot time; servo protection on long chirps |
| S1.3 | Foot-contact switch check: polarity and timing | In walk logs, switch on/off lines up with stance in a slow-walk replay within 2 steps, or the mismatch is documented | 2 h, logs | Switches noisy; then drop contacts from the actor's observation |
| S1.4 | Loop timing (**done**) and the training delay distribution | Training action delay centred on the measured value (sampling uniformly in 0..N halves the mean delay); value written in `MODEL_MATCH.md` | 1 h | — |
| S1.5 | Domain-randomization fix: look up floor and torso ids by name | `randomize` ids checked in a unit test (friction varies across envs; trunk mass never negative) | 1 h | — |
| S1.6 | Baseline in the new env: stand + basic walk | The tracking env (S3.1), trained on gait clips only, walks the training clips in sim (no falls on 6 random 60 s runs, `duck_eval` style) | 1 pilot run (100M, ~1.6 h) | Depends on S3.1 |
| S1.7 | (Optional) Joint-offset calibration | Offsets measured with upstream's `find_soft_offsets.py`, written to the robot config by the owner | 1 h at the robot | Only matters for hardware |

**Details:**

- **S1.2:**
  - Write a robot-side test script that commands one joint group at a time while the duck hangs on the stand. It needs
    the owner present.
  - Compare against the same commands in sim on a fixed-base model.
  - **Reuse:** `tools/servo_sysid.py` and `tools/getup_target_replay.py`; metrics: cross-correlation lag of band-passed
    target vs position, gain and phase at the gait frequency, step-response t63/t90.
  - **Files:** `course_project/code/joint_step_test.py` (robot), `course_project/code/joint_step_sim.py`.
- **S1.3:** reuse `tools/robot_log_compare.py`.

**What we already know:**
- Sim joints follow commanded targets like the robot's: open-loop replay of 36 robot get-ups gave 0.056 rad
  difference.
- Contact geometry is not right (only 12 of 36 resting poses match).
- For walking and crouching on the soles, the sole-only model is probably enough. **Terminate episodes on any non-sole
  contact** rather than modelling the shell.

---

## 2. Step 2: Reference-motion dataset

| id | Task | Done when | Cost | Risk |
|---|---|---|---|---|
| S2.1 | Clip format and library builder | One `npz` + `manifest.json`. Per clip: `q` (14), `qd`, base position, quaternion, velocity and yaw rate (body frame), foot contacts, keypoints (body-relative: feet, knees, hips, head), category, parameters, split, fps. Loads in JAX | 1 day | — |
| S2.2 | Gait clips from the Placo generator's **raw recordings** (not the polynomial fit) | ~12 source gaits (forward speed × 3, back, side, turn-in-place × 3, turn while walking), yaw rate recomputed from quaternions (bug fixed), keypoints by FK | 1 day | Placo only reaches the speeds in `auto_gait.json` |
| S2.3 | Crouch generator: depth × duration, feet flat, IK | ~8 source crouches (3 depths × 2–3 durations, plus crouch → step); joint-limited, min-jerk | 1–2 days | IK; foot slip at the bottom of a deep crouch |
| S2.4 | Feasibility checker | Every clip reports: joint-limit margin, peak joint speed vs the measured servo speed (S1.2), foot-foot gap (self-collision), lowest-sole penetration and sole tilt, support margin, peak hip-roll demand. A clip failing a hard check is dropped **before** splitting | 1 day | Thresholds; tie them to S1.2 |
| S2.5 | Splits **by source** before making variants | `splits.json` with train / val / test by source family, stratified by category (e.g. 60/20/20); variants inherit their source's split | 2 h | Few sources per category; see §4 |
| S2.6 | Variants within each split | Controlled variations: speed ±, turn rate ±, crouch depth ±, duration ±. Target **~32 clips** total, ~2–4 s each | ½ day | Variants too alike: the score barely separates them |
| S2.7 | `DATASET.md` + one GIF per clip | Table: clip, category, parameters, split, length, check results; GIFs from a kinematic replay | ½ day | — |
| S2.8 | (Stretch) Head and neck clips | 4–6 slow head clips, stationary and while walking; only after the lower body is reliable | 1 day | Head kp 8 on the robot |

**Reuse:**

- **S2.1:** one npz + manifest; blend clip ends into the home pose.
- **S2.2:**
  - `Open_Duck_reference_motion_generator/scripts/auto_waddle.py` + `gait_generator.py`. The raw frames hold root
    pose and toe positions.
  - Fix `compute_angular_velocity` in a local copy.
- **S2.3:** min-jerk keys, IK for flat feet, a `check()` per clip.
- **S2.4:**
  - Joint-limit margin, sole penetration and tilt, foot gap, hip-roll demand.
  - In earlier biped work, hip-roll demand predicted trouble better than ZMP or DCM.
- **S2.8:** min-jerk head trajectories.

**Files:**
- `course_project/code/clips/{gen_gaits.py, gen_crouch.py, gen_head.py, check_clips.py, build_library.py}`
- `course_project/data/clips_v1/`

---

## 3. Step 3: Motion-tracking policy

| id | Task | Done when | Cost | Risk |
|---|---|---|---|---|
| S3.1 | Tracking env in Playground/MJX (`tracking.py`) | Loads the library; samples a training clip and a random start frame; runs a clip to its end, then terminates or loops; passes a CPU check (`tools/check_*.py` pattern) | 3–4 days | Biggest build; start early |
| S3.2 | Observations | **Actor:** gyro, accelerometer, joint position − home, 0.05·joint velocity, last 3 actions, motor targets, foot contacts, a short history, the reference q, the desired base velocity and yaw rate (body frame), and a short preview (+0.1, +0.2, +0.4 s). No phase, no clip id. **Critic:** the actor input plus true base velocity, height and orientation, contact forces, DR parameters | in S3.1 | Preview length vs observation size |
| S3.3 | Rewards (bounded, measured) | Gaussian tracking of joints (legs and head **separately weighted**), body-relative keypoints and base velocity/yaw rate (**body frame**); foot-slip, action-rate and torque-near-limit penalties; alive bonus; **no command gating, no stand-still cost.** The reward ledger (S3.4) shows every clip pays more for tracking than for standing | 1 day | Saturated terms |
| S3.4 | Reward ledger | For each category: reward per step of perfect tracking vs standing still vs falling at t = 1 s. Perfect > stand by ≥30% in every category | ½ day | — |
| S3.5 | Terminations and DR | Terminate on non-sole contact, tilt > 0.8 rad, keypoint error > a bound. DR: S1.5 ids, friction, mass ±10%, kp ±10%, action delay from S1.4, IMU noise | in S3.1 | — |
| S3.6 | Pilot training on **all train clips** | 100–150M steps; every category tracked at all (no category at zero completion); reward terms not flat | 2–3 pilot runs, ~2 h each | May need reward iteration |
| S3.7 | Per-clip evaluator (`eval_clips.py`) | Per clip × R rollouts: completion, fall time, joint rms (legs, head), body-relative keypoint error, base-velocity and yaw-rate error, torque-limit and joint-limit hits; the reference as a row; json + csv | 1–2 days | Needed by Steps 4–5 |
| S3.8 | Freeze the recipe | A tagged commit; config hash written in `PREREG.md` | — | — |

**Reuse:**

- **Design:** lean actor input, bounded Gaussian terms, tracking split into legs and neck.
- **Our env skeleton:** `playground/open_duck_mini_v2/joystick.py` (observation, delay, noise), `getup.py` (DR by name,
  privileged state).
- **Evaluator:** per-clip repeated rollouts; our `tools/duck_eval.py` (seeds, CPU MuJoCo).

**Files:** `Open_Duck_Playground/playground/open_duck_mini_v2/tracking.py` (+ registration in `runner.py`),
`course_project/code/eval_clips.py`, `course_project/code/reward_ledger.py`.

---

## 4. Pre-registration (`course_project/PREREG.md`, written before S4.1 and frozen)

| id | Item | Proposal (team decides; numbers are starting points) |
|---|---|---|
| P.1 | Clip splits | `splits.json` from S2.5, by source, stratified by category; committed with its hash |
| P.2 | Per-clip score | Over R = 10 rollouts (DR on, fixed seeds): `e = mean_t[ E_dof(t)/τ_dof + E_key(t)/τ_key ]` over the **full clip length**. After a fall, each remaining frame scores `e_fail = 3` (an explicit early-termination penalty). τ_dof = 0.10 rad, τ_key = 2 cm, set from the S3.6 pilot's error spread on easy clips. Also recorded, not scored: completion rate, falls, torque-limit fraction |
| P.3 | Selection rule | Keep a whole clip if `e ≤ τ` **and** completion ≥ 0.8. Coverage: each category keeps at least its best 2 clips that pass completion ≥ 0.5; a clip failing that is never kept for coverage |
| P.4 | Choosing τ on validation | τ from a fixed candidate set (the 40/55/70/85th percentiles of train-clip scores). For each τ: a short fine-tune (50M from the scoring policy) on D_τ, scored on **validation** clips with P.2. Pick the τ with the best mean validation score; ties go to the larger set. Freeze τ |
| P.5 | Random control | Clips drawn uniformly from the train pool until the duration matches the curated set within 10%; **a new draw per seed** (3 draws), recorded |
| P.6 | Training budget | Each final policy: same recipe (S3.8), **200M steps**, trained from scratch (not from the scoring policy), seeds {0, 1, 2} |
| P.7 | Test metrics | On every test clip, R = 10 rollouts: completion, falls, joint rms, keypoint error, base-velocity / yaw-rate error, category coverage (share of categories with completion ≥ 0.8); plus the fixed perturbation test (S5.3) |
| P.8 | Comparison and statistics | Primary: mean test score (P.2) and completion, curated vs full and curated vs random. Per test clip, average the 3 seeds; paired differences over clips; 95% bootstrap CI (resample clips and seeds, 10k). Report per category and in aggregate. With few test clips, report effect sizes and CIs, not significance stars |
| P.9 | Pass bars ("curation helps") | Curated beats **both** full and random on the primary score with CI excluding 0, **and** completion is not lower than full's by more than 0.05 on any category |
| P.10 | Checkpoint rule | Evaluate checkpoints at 100/150/200M; report all; the pre-registered result uses 200M |

---

## 5. Step 4: Scoring and curation

| id | Task | Done when | Cost |
|---|---|---|---|
| S4.1 | Scoring policy on the full train pool | 300M steps, recipe S3.8 | ~4.7 GPU-h |
| S4.2 | Score every train and val clip (P.2) | `scores.csv` (clip, e, completion, falls, limits) + a ranked plot | ~1 h CPU or batched GPU |
| S4.3 | τ selection on validation (P.4) | 4 × 50M fine-tunes; chosen τ and the curated list written and frozen | ~3.2 GPU-h |
| S4.4 | Random subsets (P.5) | 3 draws written | minutes |
| S4.5 | (Stretch) Kinematic baseline subset | LIMMT-style score: penetration, joint speed, foot slide in a kinematic replay, self-collision, jerk, hip-roll demand; same duration as curated | ½ day |

**Reuse:** S2.4's checks feed S4.5. Failure-weighted clip sampling did **not** beat uniform sampling in earlier work;
it is not used here.

---

## 6. Step 5: Evaluation and report

| id | Task | Done when | Cost |
|---|---|---|---|
| S5.1 | Train 9 final policies: full / curated / random × 3 seeds | All 9 at 200M with checkpoints | ~28 GPU-h (~2 days on one GPU) |
| S5.2 | Evaluate on test clips (P.7) | Per-clip csv for all 9 policies × checkpoints | ~2 CPU-h |
| S5.3 | Perturbation test | Fixed pushes (e.g. 3 directions × 2 magnitudes at fixed clip times), friction ×0.6, kp ×0.8; same for every policy | in S5.2 |
| S5.4 | Statistics (P.8) and figures | Table and plots per category; CIs; per-clip error vs score | 1 day |
| S5.5 | Report | Methods (from PREREG), dataset doc, results, limitations (policy-dependent trackability, small clip count, sim-only) | ~1 week of writing, in parallel |
| S5.6 | (Stretch) Hardware | 2–3 conservative clips (slow walk, shallow crouch) on the robot with the recorder; completion, joint rms, loop timing; owner present; battery full | ½ day at the robot |

---

## 7. Stretch goals (in order)

1. Kinematic-curation baseline (S4.5): 3 extra seeds, ~9.4 GPU-h. **Recommended:** it answers "is policy scoring
   worth it?" (LIMMT).
2. Head and neck clips (S2.8), added as a category in a second run of the study.
3. Hardware validation (S5.6).
4. Human-video retargeting: optional, out of core scope.

---

## 8. Who does what (parallel tracks)

Owners are left blank in the tracker until the team assigns them. A natural split:

| Track | Tasks | Needs |
|---|---|---|
| A: robot and sim match | S1.1, S1.2, S1.3, S1.7, S5.6 | The robot (whoever has it) |
| B: dataset | S2.1–S2.8, S4.5 | CPU |
| C: tracking env | S1.5, S3.1–S3.6, S3.8 | Cluster GPU for pilots |
| D: evaluation and statistics | S3.7, P.1–P.10, S4.2, S5.2–S5.4, report skeleton | CPU |

**Order of work:**
- Tracks A, B, C and D start in parallel.
- C needs B's library format (S2.1) by the time S3.1 loads clips. Agree it on day 1.
- D needs S3.7's metric definitions to write PREREG.

---

## 9. Milestones

**The course deadlines are not known yet, so the dates are blank.** The durations are estimates from today.

| Milestone | Contains | Estimated effort | Date |
|---|---|---|---|
| M1: sim match + clip format | S1.1–S1.5, S2.1 | Week 1 | _ask owner_ |
| M2: dataset v1 | S2.2–S2.7 | Week 2 | _ask owner_ |
| M3: tracking pilot passes | S3.1–S3.7 | Weeks 2–3 | _ask owner_ |
| M4: pre-registration frozen | P.1–P.10, S3.8 | End of week 3 | _ask owner_ |
| M5: scoring + curation | S4.1–S4.4 | Week 4 (~1 GPU-day) | _ask owner_ |
| M6: final runs + evaluation | S5.1–S5.4 | Weeks 4–5 (~2 GPU-days) | _ask owner_ |
| M7: report | S5.5 | Week 6 | _ask owner_ |

---

## 10. Risks (full list; the top 5 are in the reply to the owner)

1. **The tracking env takes longer than planned.** It is the largest build. Mitigation: start S3.1 on day 1 with gait
   clips only; add crouch later.
2. **Curation effect too small to see with ~32 clips and 3 seeds.** Mitigation: controlled difficulty (S2.6) so some
   clips are genuinely hard; paired per-clip statistics; report CIs.
3. **The score separates nothing.**
   - Either the pilot policy tracks everything (no hard clips), or nothing (all fail).
   - Mitigation: choose variant ranges from the S3.6 pilot so the score spreads; check the spread before freezing.
4. **The reward pays for standing still** (the most common failure in earlier biped work). Mitigation: the ledger (S3.4) and per-term
   operating-range checks before every pilot.
5. **Compute on one shared GPU.** ~40–50 GPU-h. Mitigation: book GPU 0 early; pilots at 100M; ask about other GPUs only
   through the owner.
6. **Sim-real body mismatch** (contacts, mass). Not on the minimum path. Matters for the hardware stretch only.
   Mitigation: S1.1, S1.2; terminate on non-sole contact.
7. **Robot power**: brownouts during hard motions. Hardware stretch only; conservative clips, full battery.
