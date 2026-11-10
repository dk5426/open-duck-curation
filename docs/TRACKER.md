# Course project tracker

**The live tracker is a shared web page; ask Dhawal for the link.** Update status, owner, evidence and next action
there. This file is a snapshot of it.

**How to use it:**
- Update a row whenever a task changes state.
- Mark **done** only with evidence on disk: a file, a result or a commit.
- Task ids match `PLAN.md`. Owners stay blank until the team assigns them.

## Summary (updated 2026-11-09)

1. **Core deliverables: ~10% done.** Infrastructure exists (pipeline, walker, robot recorder, robot-vs-sim tools); the
   dataset, tracking env, scoring and evaluation are not started.
2. **Current blockers:**
   - The course deadlines are unknown, so milestone dates are blank.
   - The team must assign owners and pick the clip categories.
3. **Next 1:** S3.1, the tracking env skeleton (longest task; start now with gait clips).
4. **Next 2:** S2.1 + S2.2, the clip format and gait clips from raw Placo recordings (yaw bug fixed).
5. **Next 3:** S1.1 + S1.2, weigh the robot and the single-joint step test on the stand (owner at the robot).

## Already done (evidence on disk)

| id | step | task | owner | status | evidence | done when | next action |
|---|---|---|---|---|---|---|---|
| D.1 | 1 | Reproduce Open Duck Playground pipeline (install, references, 300M walker) | | done | `SETUP.md` Status 1a–1f; cluster `runs/full_300M` | Walker trains and exports | — |
| D.2 | 1 | Our walker beats `BEST_WALK_ONNX_2` in sim | | done | `policies/ours_walker_full300M_258M.onnx`; tracking score 0.304 vs 0.411 (`results/final/*.json`, `SETUP.md`) | Better tracking, same survival | — |
| D.3 | 1/5 | Walker runs on the robot; walker switch between ours and BEST2 | | done | `robot_patches/walker_switch_20261030/`; robot walk logs in `robot_logs/2026103*_walk.npz` | Walks on the robot | — |
| D.4 | 1 | Robot step recorder (50 Hz: obs, actions, targets, joints, raw IMU, timing) | | done | `robot_patches/recorder_20261030/` (installed, `1a21db15`, later builds); ~70 logs in `robot_logs/` | Logs every step, no late loop steps | Reuse for hardware tests |
| D.5 | 1 | Onboard loop timing measured | | done | `robot_logs/20261030_135301_walk.npz` via `tools/robot_log_compare.py`: 20.2 ms median, p99 27.5 ms, compute 8.2 ms, a 26 ms late step each second (voltage check) | Measured | Use in S1.4 |
| D.6 | 1 | Robot-vs-sim analysis tools | | done | `tools/robot_log_compare.py`, `imu_plot.py`, `servo_sysid.py`, `getup_target_replay.py`, `getup_side_by_side.py`, `robot_loop_eval.py`, `surface_eval.py`, `probe_deadzone.py` | Run on real logs | Extend in S1.2 |
| D.7 | 1 | Servo joint following: sim vs robot (open-loop target replay, 36 get-ups) | | done | `tools/getup_target_replay.py`; leg joints differ by 0.056 rad, lag sim 0.101 / robot 0.105; delay, torque, kp and speed-curve changes make it worse | Servo model checked | Confirm with S1.2 |
| D.8 | 1 | Servo hardware identified (STS3215 7.4 V, firmware 3.10, model 9.3, protection 80% / 2 s → 20%) | | done | `tools/servo_read_versions.py`; protection read 2026-10-30 | Read from all 14 servos | Use in S2.4 speed limits |
| D.9 | 1 | Foot switches wired and read | | done | `feet_contacts.py` (GPIO D22/D27); switches toggle 916/947 times in 32 walk logs | Live signal | Accuracy in S1.3 |
| D.10 | 1 | IMU mounting offset measured (17.5°, 8% low); walker insensitive in sim | | done | `tools/imu_offset_eval.py`; `robot_patches/imu_corr_20261030/` | Measured | Decide whether tracking uses the correction |
| D.11 | — | Get-up policy (sim 40/40, 21/21 recorded robot starts at 60–100% torque) | | done (sim) | `policies/getup_real2_80M.onnx`; `results/round2/` | Sim gates | Not part of this project; robot success low (power) |
| D.12 | 4 | Literature check (ExBody2 venue, LIMMT and others) | | done | `AUDIT.md` §8 | Citations verified or flagged | Use in report |
| D.13 | — | Audit, plan, tracker | | done | `course_project/AUDIT.md`, `PLAN.md`, `TRACKER.md` | Written | Team review |

## Project tasks

| id | step | task | owner | status | evidence | done when | next action |
|---|---|---|---|---|---|---|---|
| S1.1 | 1 | Weigh the robot, compare with model (2.107 kg) | | not started | | Mass in `MODEL_MATCH.md`; masses scaled if >10% off | Owner weighs the duck |
| S1.2 | 1 | Single-joint step / chirp test on the stand, robot vs sim | | not started | | Dead time within 1 step, t63 within 25% | Write `joint_step_test.py`; book robot time |
| S1.3 | 1 | Foot-switch polarity / timing check | | not started | | Switch edges vs stance within 2 steps | Analyse walk logs |
| S1.4 | 1 | Training delay centred on measured value | | in progress | D.5 | Delay distribution written in `MODEL_MATCH.md` | Pick distribution |
| S1.5 | 1 | DR ids by name (floor, trunk) | | not started | Pattern in `getup.py:make_randomizer` | Unit test passes | Port into tracking env |
| S1.6 | 1 | Stand + walk in the tracking env | | not started | | 6/6 random 60 s runs | After S3.1 |
| S1.7 | 1 | Joint-offset calibration (optional) | | not started | | Offsets in robot config | Owner at robot |
| S2.1 | 2 | Clip format + library builder | | not started | | npz + manifest loads in JAX | Agree format with track C on day 1 |
| S2.2 | 2 | Gait clips from raw Placo recordings, yaw fixed, keypoints | | not started | Generator reproduced (D.1) | ~12 source gaits | Local copy of `gait_generator.py` |
| S2.3 | 2 | Crouch generator | | not started | | ~8 source crouches | Min-jerk + IK |
| S2.4 | 2 | Feasibility checker | | not started | | Every clip has a check report | |
| S2.5 | 2 | Splits by source | | not started | | `splits.json` committed | After S2.2/S2.3 |
| S2.6 | 2 | Variants (~32 clips) | | not started | | Library v1 built | |
| S2.7 | 2 | `DATASET.md` + GIFs | | not started | | Doc + GIF per clip | |
| S2.8 | 2 | Head / neck clips (stretch) | | not started | | 4–6 clips | After M3 |
| S3.1 | 3 | Tracking env in MJX | | not started | Skeletons: `joystick.py`, `getup.py` | CPU check passes | **Start now** |
| S3.2 | 3 | Observations (actor + privileged critic) | | not started | | In S3.1 | |
| S3.3 | 3 | Rewards (no command gating) | | not started | Gating found: `custom_rewards.py` `reward *= cmd_norm > 0.01`; `cost_stand_still` | Ledger passes | |
| S3.4 | 3 | Reward ledger | | not started | | Perfect > stand by ≥30% per category | |
| S3.5 | 3 | Terminations + DR | | not started | | In S3.1 | |
| S3.6 | 3 | Pilot on all train clips | | not started | | Every category > 0 completion | GPU 0 booking |
| S3.7 | 3 | Per-clip evaluator | | not started | Pattern: `tools/duck_eval.py` | json/csv per clip | |
| S3.8 | 3 | Freeze recipe | | not started | | Tagged commit | |
| P.1–P.10 | 4 | Pre-registration (`PREREG.md`) | | not started | Draft in `PLAN.md` §4 | Signed off by the team, committed before S4.1 | Team review of the draft |
| S4.1 | 4 | Scoring policy (300M) | | not started | | Trained | After P frozen |
| S4.2 | 4 | Score train + val clips | | not started | | `scores.csv` | |
| S4.3 | 4 | τ on validation | | not started | | τ + curated list frozen | |
| S4.4 | 4 | Random subsets (3 draws) | | not started | | Lists written | |
| S4.5 | 4 | Kinematic baseline subset (stretch) | | not started | | List written | |
| S5.1 | 5 | 9 final runs | | not started | | 9 × 200M | |
| S5.2 | 5 | Test evaluation | | not started | | Per-clip csv | |
| S5.3 | 5 | Perturbation test | | not started | | Results per policy | |
| S5.4 | 5 | Statistics + figures | | not started | | Tables with CIs | |
| S5.5 | 5 | Report | | not started | | Submitted | |
| S5.6 | 5 | Hardware demo (stretch) | | not started | Recorder (D.4) | Completion / tracking / timing on 2–3 clips | |
