# Course project audit: what exists, what is partial, what is missing

**Project:** feasibility-aware motion dataset curation on Open Duck Mini v2.
**Audit date:** 2026-11-09. Read-only audit: no training and no robot changes were made.

**Sources:**
- `~/Desktop/OpenDuck`: `SETUP.md`, `tools/`, `results/`, `robot_logs/`, `robot_patches/`, `policies/`, and the four
  upstream repos on branch `local/setup`.
- The training cluster copy (`runs/`).
- Lessons from the team's earlier biped motion-imitation work (not public); summarised here as design guidance.

## Contents

0. Summary
1. Step 1: Simulation and baseline validation
2. Step 2: Reference-motion dataset
3. Step 3: Motion-tracking policy
4. Step 4: Scoring and curation
5. Step 5: Evaluation and hardware
6. Upstream bugs and whether they matter for tracking
7. Compute budget
8. Literature and positioning
9. Notes on the proposal (pages 5–6)

---

## 0. Summary

| Core deliverable | Done | Partly there | Missing |
|---|---|---|---|
| Validated simulation environment | Pipeline reproduced; walker trained and deployed; robot recorder; robot-vs-sim tools; loop timing measured | Servo model checked against robot logs (joint following matches, body motion does not); IMU offset measured | Robot mass and geometry measured; a controlled servo step-response test; stationary-motion reward |
| Documented reference dataset | Upstream gait generator reproduced (240 gaits) | Raw generator output has root pose and toe positions | Crouch, turn-in-place and head clips; clip format with keypoints; feasibility checks; splits |
| Motion-selection procedure | Nothing | Design patterns from earlier biped work | Scoring policy, score formula, tolerances, selection rule |
| Controlled evaluation of curation | Evaluation pattern exists (`duck_eval.py`, per-segment metrics, seeds) | Nothing specific to curation | Held-out-clip evaluator, three conditions × 3 seeds, statistics |

Roughly **10% of the core deliverables** is done. Most of what exists is walking and get-up infrastructure, not motion
tracking.

---

## 1. Step 1: Simulation and baseline validation

### Exists

- **Pipeline:** Open Duck Playground reproduced end to end (`SETUP.md` → Status). It runs on MuJoCo Playground/MJX with
  brax PPO and versions pinned through `exclude-newer`.
- **Our walker:** `policies/ours_walker_full300M_258M.onnx` tracks commands better than upstream's `BEST_WALK_ONNX_2`.
  Tracking score 0.304 vs 0.411 (lower is better; `SETUP.md` → "Our policy vs BEST_WALK_ONNX_2",
  `results/final/*.json`). It runs on the robot.
- **Robot recorder (installed):** `robot_patches/recorder_20261030/`. It logs every 50 Hz step of walker and get-up runs
  to `~/duck_logs`: the observation, action, targets, joint positions, raw IMU, commands and loop time.
  `robot_logs/` holds the copies, about 70 files up to 2026-11-02.
- **Robot-vs-sim tools:**
  - `tools/robot_log_compare.py`: replays a walk log's commands in sim and compares tilt, gyro, joint tracking and
    contacts.
  - `tools/imu_plot.py`: per-axis IMU, robot vs sim.
  - `tools/servo_sysid.py`: command-to-motion lag, joint speed and follow gain, for robot logs and sim.
  - `tools/getup_target_replay.py`: open-loop replay of recorded targets in sim. Sweeps delay, torque, kp, a
    torque-speed curve, floor friction and softness, and trunk mass and CoM.
  - `tools/robot_loop_eval.py`: the robot's control loop reproduced in sim.
  - `tools/probe_deadzone.py`: maps the walker's command dead zone.
- **Measured onboard loop (Pi):**
  - Step interval: median 20.2 ms, p99 27.5 ms, maximum 97 ms.
  - Policy compute: median 8.2 ms.
  - The runtime's once-a-second voltage check makes one step about 26 ms late every second (86 times in 78 s).
  - Source: `robot_logs/20261030_135301_walk.npz` analysed with `tools/robot_log_compare.py`. The recorder's own stalls
    were fixed (`robot_patches/recorder_20261030/README.md`).
- **Servo hardware identified:**
  - Feetech STS3215, 7.4 V version, firmware 3.10, model 9.3. Max voltage limit 8.0 V. Overload protection: 80% load
    for 2 s drops the servo to 20% torque.
  - Read with `tools/servo_read_versions.py` and the protection-register read on 2026-10-30.
  - Gains on the robot: kp 22 (servo units) on the legs, 8 on the head.
- **Foot-contact switches are wired and read:**
  - `Open_Duck_Mini_Runtime/mini_bdx_runtime/mini_bdx_runtime/feet_contacts.py` reads GPIO D22/D27 with pull-ups.
  - In the robot logs they toggle 916/947 times over 32 walk files and read in-contact 83%/82% of the time (73% while
    moving). Their accuracy against true contact has **not** been checked.

### Partly there

- **Servo model vs robot (tested 2026-11-02 on 36 recorded get-ups):**
  - Sim fed the robot's exact joint targets moves its leg joints like the robot: 0.056 rad mean difference, and the same
    lag (sim 0.101 rad, robot 0.105 rad).
  - Command delay, weaker torque, softer kp and a torque-speed curve all made the match **worse**. The servo model
    is therefore not the gap for joint following.
- **Body motion does not match:**
  - Uprightness diverges 5–6× above the sim's own noise floor once the body pushes on the floor (about 1 s in).
  - Floor friction and softness, trunk mass and CoM do not fix it.
  - Only 12 of 36 real resting poses are stable in the sim, which points at **contact geometry**: 13 collision boxes
    against a rounded shell plus attachments.
- **IMU mounting offset:**
  - At the home pose the robot's accelerometer reads 17.5° away from the model's, and 8% low.
  - Corrected for the get-up only (`robot_patches/imu_corr_20261030/`).
  - The walker was shown insensitive to it in sim (`tools/imu_offset_eval.py`).
- **Model parameters (backlash scene):**
  - Total mass 2.107 kg.
  - kp 17.11, kv 0, torque limit 3.23 N·m. The 7.4 V STS3215 is published at about 1.9 N·m stall, unverified.
  - Backlash ±0.0087 rad on 10 leg joints.
  - Action delay 0–2 steps, sampled uniformly.
- **Contact geometry:**
  - Upstream: only the soles collide (`SETUP.md` findings).
  - Ours: a get-up variant with 13 collision boxes and self-collision (`tools/make_getup_model.py`,
    `getup_real*.py`).
  - For walking and crouching, sole-only contact is probably adequate. For anything near a fall it is not.

### Missing

- **Weigh the real robot,** whole and ideally by assembly. Nobody has measured it. Upstream's model is 2.107 kg.
- **A controlled step and chirp test of single joints** on the stand: dead time, rise time, maximum speed. Everything so
  far comes from closed-loop logs. Useful metrics: per-joint lag from cross-correlation of the band-passed target and
  measured position, gain and phase at the gait frequency, and step-response t63/t90.
- **Joint offsets:** all 14 are 0.0 in the robot's `duck_config.json`, never calibrated. Upstream has
  `find_soft_offsets.py`.
- **Action scale:** sim timing matches the robot (50 Hz). The robot now runs action scale 0.25, as in training; it was
  0.2 until 2026-10-30.
- **A stationary-motion reward** (see §3).

---

## 2. Step 2: Reference-motion dataset

### Exists

- **Upstream generator:** `Open_Duck_reference_motion_generator` (Placo walk engine, `scripts/auto_waddle.py`).
  - Sweep grid from `robots/open_duck_mini_v2/auto_gait.json`:
    - dx -0.04…0.06 and dy -0.03…0.03, in steps of 0.02;
    - dθ -0.3…0.3, in steps of 0.07;
    - 240 gaits in total. The grid's speeds are per-step displacements.
  - We reproduced it exactly (`SETUP.md`).
- **Raw recordings are richer than the training reference.** Each raw frame holds root position and quaternion,
  14 joints, **left/right toe positions**, base linear and angular velocity, joint velocities and toe velocities
  (`gait_generator.py` lines 94–95).
  - `fit_poly.py` then cuts this down to a 40-number frame: 16 joint positions, 16 joint velocities, 2 contacts, 3 base
    linear velocities, 3 base angular velocities.
  - That frame has no root position, no orientation and no keypoints (`SETUP.md` findings).
- **Turning in place:** gaits with dx = dy = 0 and dθ ≠ 0 are in the sweep.

### Partly there

- **Keypoints:** toe positions exist in the raw recordings. Other body keypoints (knees, hips, head) would come from
  forward kinematics of the joint angles, which is easy in MuJoCo.

### Missing

- **Crouch clips:** the Placo walk engine makes gaits only. Crouch-depth and duration variants need our own generator.
  Joint-space interpolation with min-jerk keys and IK for flat feet will do.
- **Head and neck clips:** the generator moves no head. Simple joint-space trajectories are enough
  (simple min-jerk joint trajectories).
- **A common clip format for all categories:**
  - joint targets, joint velocities, base pose and velocity, foot contacts, body-relative keypoints, category and
    parameters, train/val/test split.
  - Suggested layout: one npz holding every clip plus a JSON manifest.
- **Feasibility checks:**
  - joint limits and margins, joint velocity, self-collision, ground penetration and sole flatness, support margin;
  - all must run on our MuJoCo model.
  - Useful checks: joint-limit margin, lowest-sole penetration and sole tilt, support margin, foot-to-foot gap, hip-roll demand.
- **Splits:** source trajectories split into train/val/test **before** variants are generated. Earlier work had no split; we should.
- **The yaw-rate bug** (§6) must be fixed in any gait clip we export.

---

## 3. Step 3: Motion-tracking policy

### Exists

- **PPO infrastructure:** `runner.py`, export to ONNX, checkpointing. Brax PPO supports an asymmetric critic through
  `privileged_state`; all our envs already return one.
- **Deployable observation layout and the robot contract:** joints, IMU, contacts, last 3 actions, motor targets
  (`joystick.py`, the runtime). The robot runs any ONNX with the same contract.
- **Robot-side infrastructure:**
  - a skill-switching runtime (walker switch, get-up button);
  - a soft start;
  - the recorder.
- **Imitation reward (upstream, `custom_rewards.py:reward_imitation`):**
  - It **is switched off at zero command**: `reward *= cmd_norm > 0.01`, with `cmd_norm` the base-velocity command only.
  - At the same time `cost_stand_still` (`common/rewards.py`, weight −0.2) penalises any departure from the default pose
    at zero command, head included unless `ignore_head=True`.
  - So a commanded crouch or head motion at zero base velocity earns **no** imitation reward and is **penalised**.
  - The term also drops the head joints, uses an unbounded `-15·Σ(q−q_ref)²` joint term (a sum of squares, under which small joints
    barely count), and leaves the orientation term unused.

### Missing

- **A reference-conditioned tracking env.** None exists today; the walker is command-conditioned with a phase clock.
  It needs:
  - a multi-clip loader;
  - reference plus preview in the actor observation;
  - body-relative keypoint tracking;
  - base-motion tracking in the body frame, not the world frame;
  - foot-slip and constraint penalties;
  - terminations;
  - an asymmetric critic.
- **Suggested design:** a compact actor input (sensors, short history and a short window of upcoming reference
  frames; no phase or clip id) and bounded Gaussian tracking terms, written in JAX/MJX.
- **A reward ledger before training:** price "do the clip" against "stand still" for every category.

---

## 4. Step 4: Scoring and curation

### Exists

- Per-command metrics and seeds in `duck_eval.py` and `score_tracking.py`, for the walker.
- Patterns from earlier biped work:
  - a repeated-rollout per-clip harness (survival, joint rms, jerk, peak torque per clip);
  - pre-registered per-clip pass bars;
  - failure-weighted clip sampling, which **did not beat uniform sampling** there.

### Missing (all of it)

- A scoring policy trained on the full training pool.
- A per-clip score: keypoint and joint error normalised by tolerances, plus an early-termination penalty, completion,
  falls and actuator-limit hits.
- A selection rule that keeps whole clips and category coverage, with thresholds chosen on validation and frozen.
- A cheap baseline: kinematic-only curation.
- None of these existed before. The design is new work.

---

## 5. Step 5: Evaluation and hardware

### Exists

- **Evaluation harness pattern:** per segment, survival plus achieved velocity, 3 seeds, random 60 s runs, both scenes
  (`tools/duck_eval.py`). Robot-loop and surface variants (`robot_loop_eval.py`, `surface_eval.py`).
- **Hardware:** the robot walks with our walker. Get-up is unreliable: at best 2 of 8 robot attempts succeeded, and 2
  Pi brownouts happened in 23 attempts (power supply). Timing and joint tracking can be measured from logs today.

### Missing

- A held-out-clip evaluator for tracking (completion, falls, joint and keypoint error, base-motion tracking, coverage).
- The 3 conditions × 3 seeds design and the statistics.
- A fixed perturbation test for tracking: timed pushes at fixed clip times, the same for every policy.
- World-space accuracy on hardware needs external tracking, which we don't have. It should be reported as not
  measured.

---

## 6. Upstream bugs and whether they matter for tracking

Source: `SETUP.md` → "Findings about the upstream pipeline".

| Bug | Affects a tracking task? | What to do |
|---|---|---|
| Reference yaw rate ~40× too small (`gait_generator.py:compute_angular_velocity`) | **Yes**, for every turning clip: base-motion targets would ask for no turning | Fix in our clip export, or recompute yaw rate from the recorded quaternions |
| Imitation compares world-frame velocities under random spawn yaw | **Yes**: base-motion tracking is wrong unless the robot faces +x | Track in the body/heading frame |
| Orientation term computed but unused; reads joint angles as a quaternion | Yes, if reused | Write our own orientation term from the stored quaternion |
| Imitation gated off at zero command; stand-still cost at zero command | **Yes**, for crouch and head clips | New reward without command gating (§3) |
| Domain-randomization ids hardcoded wrong (floor = trunk mesh, torso = massless `base`) | Yes: friction and CoM randomization silently off, about half the envs get negative mass | Look ids up by name, as our get-up env does (`getup.py:make_randomizer`) |
| Accelerometer +1.3 offset is a no-op in training but applied in `mujoco_infer.py` | Yes, for any sim evaluation through `MjInfer`; harmless in training | Remove the offset from evaluation, as `robot_loop_eval.py` does |
| Reference covers less than the command range | Mostly no: clips replace commands | Check that the clip parameters sit inside what the robot can do |
| Only soles collide | Small for walking and crouching; large for any fall | Keep sole-only for tracking; terminate on body contact |

---

## 7. Compute budget

### Measured throughput

- Walker env (sole contacts only): 300M steps in 4 h 40 min on one A4000, about 64M steps per hour.
- Get-up with self-collision boxes: about 21M steps per hour (box-box collision is about 3× slower).
- A tracking env with sole-only contact should be close to the walker figure. This must be verified in the first pilot.

### Budget

Assumes 200M steps per policy and the walker's throughput:

| Item | Runs | Steps | GPU hours |
|---|---|---|---|
| Pilot and reward-tuning runs | 4 | 4 × 100M | 6.3 |
| Scoring policy (full training pool) | 1 | 300M | 4.7 |
| Per-clip scoring rollouts (repeated, CPU or batched GPU) | — | — | ~1 |
| Full / curated / random × 3 seeds | 9 | 9 × 200M | 28 |
| Cheap kinematic-curation baseline × 3 seeds (stretch) | 3 | 3 × 200M | 9.4 |
| Held-out evaluation and perturbation tests (CPU) | — | — | ~2 CPU-h |
| **Total** | | | **~40 GPU-h core, ~50 with the baseline** |

- On one GPU (GPU 0), that is about 2 days of continuous training for the core study, about 2.5 days with the baseline.
- Other GPUs on the box belong to other people. Use them only if the owner arranges it.
- If tracking needs 300M per policy, add about 50%.

---

## 8. Literature and positioning

A literature check on 2026-11-09 read the primary pages. Anything marked "unverified" must be checked before it is
cited.

### ExBody2

- **Citation:** Ji, Peng, Liu, Li, Yang, Cheng, Wang. *ExBody2: Advanced Expressive Humanoid Whole-Body Control.*
  arXiv:2412.13196, v1 Dec 2024, v2 Mar 2025. https://arxiv.org/abs/2412.13196
- **Venue: none found.** The project page cites it as an arXiv preprint (2024). **Cite it as arXiv 2024**
  unless the team has a venue link.
- **How it curates:**
  - A base policy π₀ is trained on all 1,919 CMU clips.
  - Each clip gets `e(s) = α·E_key + β·E_dof` with α = 0.1, β = 0.9.
  - Candidate thresholds τ ∈ {0.075 … 0.175} come from the error distribution's CDF. Training resumes on each
    D_τ, and a greedy pick gives τ* = 0.15.
- **What it reports:** filtered vs unfiltered MPKPE 0.100 vs 0.113 and MPJPE 0.108 vs 0.136 in sim; MPJPE on the robot
  0.107 vs 0.136. Velocity error is slightly worse with filtering.
- **No random-subset baseline.** That is the gap our design (full / curated / random, duration-matched) fills.

### Other software and methods

- **Open Duck Mini / Playground / reference generator:** A. Pirrone (apirrone), Apache-2.0, GitHub repos. There is no
  paper; cite the repos with an access date. Its imitation reward follows Disney's BD-X paper.
- **DAgger:** Ross, Gordon, Bagnell, AISTATS 2011, PMLR 15:627–635. Confirmed. It is now out of scope (§9).

### Closest related work

| Work | What it does | How we use it |
|---|---|---|
| **LIMMT, Less is More for Motion Tracking** (Guan et al., ICML 2026, arXiv:2606.06953) | Most direct competitor. Each clip is replayed in sim and scored `S = 100 − Σ wᵢ·violations` (floating, penetration, joint velocity, foot slide, self-collision, jerk), with no tracking policy. Reports curated 3% vs random 3% of AMASS: 95.6 vs 83.8% success | **Its score is the natural cheap, non-policy baseline**, and our study must beat it |
| GMT (Chen et al., arXiv:2506.14770, 2025, venue unverified) | Rule filter, then a preliminary policy drops low-completion clips; adaptive sampling | Failure-weighted sampling baseline |
| BeyondMimic (Liao et al., arXiv:2508.08241, 2025) | Adaptive sampling of failure-prone segments within a clip | Curriculum baseline |
| KungfuBot / PBHC (Xie et al., NeurIPS 2025, arXiv:2506.12851) | Physics filter (CoM–CoP) | Kinematic/physics baseline |
| H2O (He et al., arXiv:2403.04436, 2024; IROS venue unverified) | "Sim-to-data": a privileged imitator screens motions | Same idea as ExBody2, earlier |
| PHC (Luo et al., ICCV 2023) | Hard-negative mining | Background |
| MaskedMimic (Tessler et al., TOG/SIGGRAPH Asia 2024) | Prioritised sampling | Background |
| ASAP (He et al., RSS 2025) | Keeps the motions a tracker can follow | Background |

**Takeaway:**
- "Curation helps" has been shown on humanoids at AMASS scale.
- What is new here:
  - a small, heavily constrained biped;
  - a parametric dataset of 20–40 clips with controlled difficulty;
  - a duration-matched random control;
  - a test of whether **policy-based** scoring beats a **kinematic** score on such a robot.
- With only 20–40 clips the statistics will be thin. The plan accounts for that.

---

## 9. Notes on the proposal (pages 5–6, the version we follow)

Only pages 5–6 of the PDF are the proposal; pages 1–4 are an earlier draft and are not used.

| Point in the proposal | Note |
|---|---|
| "Building on ExBody2" | ExBody2 is an arXiv preprint (2024, v2 2025) with no venue found (§8). Cite it as arXiv 2024 |
| Score combines keypoint and joint errors normalised by tolerances, with an explicit early-termination penalty | The tolerances and the penalty size are not given yet; `PLAN.md` P.2 proposes τ_dof = 0.10 rad, τ_key = 2 cm and a failure value of 3 per remaining frame, all to be fixed before scoring |
| Thresholds chosen on validation data, fixed before testing | The procedure for choosing them is open; `PLAN.md` P.4 proposes short fine-tunes on each candidate subset, scored on validation clips |
| Random subset matched approximately to the curated duration | One draw or several? `PLAN.md` P.5 proposes one draw per seed |
| Three seeds per condition, same held-out clips | With ~32 clips the held-out set is small; report effect sizes and bootstrap CIs (P.8) |
| Curation versus "full pool" and "random" | A close prior work (LIMMT, ICML 2026) already shows curated beats random with a kinematic score and no tracking policy (§8). A kinematic-score arm makes our result stronger; the proposal does not list one |
| Foot-contact signals in the actor observation | The switches work on the robot (they toggle), but their accuracy is unchecked (`PLAN.md` S1.3) |
| Policy timing matched to the measured onboard loop | Measured: 20.2 ms median step, 27.5 ms p99, a 26 ms late step each second (§1) |
