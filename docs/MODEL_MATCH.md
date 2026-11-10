# Simulation vs the real robot (Step 1)

What is known about how well the training model matches our duck, what has been measured, and what still needs the
robot (test ids refer to `ROBOT_TESTS.md`). Updated 2026-11-09.

| Aspect | Model (`scene_flat_terrain_backlash.xml`) | Robot (measured) | Status |
|---|---|---|---|
| Mass | 2.107 kg total | not measured | **R2** |
| Knee range | ±1.57 rad (also in the generator's URDF) | reached **1.66 rad** in walk logs, so the real limit is wider | **R3**; it caps the crouch at 8 mm |
| Other leg ranges | hip pitch −1.22…0.52 (left), hip roll ±0.44, ankle ±1.57 | hip pitch reached −1.235 (left) and 1.239 (right), just past the model | **R3** |
| Servo | position actuator kp 17.1, no velocity damping, torque limit 3.23 N·m; leg backlash ±0.5° | STS3215 7.4 V (firmware 3.10, model 9.3), runtime kp 22 (legs) / 8 (head), kd 0; datasheet stall ≈ 1.9 N·m; overload protection: 80% load for 2 s → 20% torque | see below |
| Joint following | sim fed the robot's exact targets | leg joints differ by 0.056 rad on average; lag sim 0.101 vs robot 0.105 rad (36 recorded get-ups, `tools/getup_target_replay.py`) | matches for leg joints |
| Step response | sim prediction for a +0.3 rad step on the stand: dead time 1 step, t63 80 ms, t90 100 ms, overshoot 20–32%, peak 4 rad/s; 1–2 Hz lag ≈ 50 ms (`results/joint_step_sim.json`) | not measured | **R4** (`curation/robot/joint_step_test.py`, compare with `joint_step_sim.py --robot`) |
| IMU | accelerometer at home (−1.22, −1.95, 9.54) | (−0.15, −4.22, 7.94): 17.5° apart and 8% low | **R5** |
| Foot switches | sole-floor contact | toggle live, but agree with kinematic stance 46% as wired vs 74% if left/right are swapped (`results/foot_switch_check.md`) | **R1** |
| Contact geometry | only the soles collide (walker); 13 boxes for get-up | only 12 of 36 real resting poses are stable in sim: the shell shape differs | fine for walking/crouching; matters for falls |
| Control loop | 50 Hz, policy step 20 ms | median 20.2 ms, p99 27.5 ms, policy compute 8.2 ms; a 26 ms late step once a second (voltage check) | matched |
| Action scale | 0.25 | 0.25 since 2026-10-30 (was 0.2) | matched |

## Choices made for training (S1.4)

- **Action delay: 0–1 control steps, uniform.**
  - On the robot the policy runs and its targets are written within the same 20 ms step (compute 8.2 ms).
  - Open-loop replay matched the robot best with 0–1 steps of delay; more delay made it worse.
  - The occasional 26 ms step is covered by the 1-step case.
- **No extra servo model.**
  - The replay test found the sim's joints already follow the robot's targets like the real ones.
  - Weaker torque, softer gains or a torque-speed curve all matched worse.
  - Revisit after R4.
- **Foot contacts stay in the actor's observation.** Whether the actor reads the switches as they are, swapped, or
  not at all is decided after R1.

## What would change the model after Wednesday

| If… | then… |
|---|---|
| R2 mass differs from 2.107 kg by >10% | scale link masses |
| R3 knee range is wider | raise the joint range, then regenerate deeper crouch clips |
| R4 shows a dead time or overshoot different from the sim's | add a delay or a damping term, then re-run the replay check |
| R1 confirms the swap | fix the wiring or the runtime mapping, before any hardware run |
