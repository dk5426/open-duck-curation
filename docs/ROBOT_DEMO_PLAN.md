# Robot demo plan (R7): curated vs physics-filtered policy on the real Open Duck

Status: plan, 2026-11-17. Qualitative demo for the report, not a test of the hypothesis. A team member runs the robot;
nothing here is run remotely.

## What we show

- **Policies:**
  - the physics-filter (oracle) policy at f* (expected 70%, the best sim condition);
  - the curated policy at 55% (the pre-registered main fraction).
  - Optional: full.
  - For each condition, the seed whose test e is closest to its condition's mean, so no seed is cherry-picked.
- **Clips:** 3 conservative test clips that every condition completes in sim without falls, plus the 1–2 categories
  where curated loses most in sim (side step, walk + turn, both at "gentle"). Final list chosen from the cv7 test results
  before the session and written here.
- **Record per run:**
  - completion (no fall, no hand catch);
  - leg joint tracking error from the logged joint positions against the reference (same definition as `legs_rms`);
  - loop timing;
  - a phone video.
  - 3 attempts per clip per policy, in alternating order (A, B, A, B, ...) so battery and temperature drift hit both.

## What has to be built first (sim side, about 1 day)

1. **Tracking runtime.** The upstream runtime feeds a velocity-command walker. The tracking policy needs its own
   observation, which includes the reference clip state (see `tracking.py` in the playground patches). Write
   `curation/robot/track_clip.py`:
   - loads an ONNX policy and one clip from `data/clips_v7/library.npz`;
   - builds the observation exactly as `tracking.py` does;
   - applies target = ref_q(t+1) + 0.25·a with the same 5.24 rad/s rate limit;
   - runs at the policy rate;
   - logs everything to `~/duck_logs`.
2. **Sim-in-the-loop check of the runtime.** Run `track_clip.py` against the MuJoCo model with the same ONNX and
   confirm it matches `eval_clips.py` on the same clip (within noise) before the robot sees it.
3. **Export** the chosen checkpoints to ONNX with the existing export path, and check that the ONNX and the JAX policy
   give the same actions on recorded observations.
4. **Safety:**
   - start from the home pose;
   - ramp gains over 1 s;
   - stop on a tilt over 35° or a lost IMU;
   - someone holds the stand line for the first attempt of every clip.

## Preconditions from `docs/ROBOT_TESTS.md`

- **R1:** foot-switch mapping, if the tracking observation uses contacts.
- **R2:** mass.
- **R4:** servo step response.

If R4 shows a large lag mismatch, note it next to the demo results; it changes the sim-to-real reading, not the study.

## Output

- `results/robot_demo/`: logs, a per-run table, a summary of 1–2 paragraphs;
- one side-by-side video per clip for the report.
