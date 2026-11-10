# Reference-clip dataset v1

Built by `curation/clips/make_library.py` (S2.1–S2.6). GIFs of every clip: `results/clips_v1/<category>.gif`.
**Status: draft for team review.** The splits and the check rules become final only when `PREREG.md` is signed off.

## Contents

- **28 clips**, each 4 s at 50 Hz (200 frames). Train / val / test:
  13 / 4 / 11.
- **Dropped by the hard checks:** 6 clips: `side_step__dx0_dy-0.03_dth0__normal`, `side_step__dx0_dy0.03_dth0__normal`, `turn_in_place__dx0_dy0_dth0.30__normal`, `walk_fwd__dx0.06_dy0_dth0__gentle`, `walk_fwd__dx0.06_dy0_dth0__normal`, `walk_turn__dx0.04_dy0_dth0.15__normal`.
- **Categories:** forward walk, backward walk, side step, turn in place, walk while turning (gaits); crouch.
  Head and neck clips are a stretch goal.

## How the clips are made

- **Gaits** (`curation/clips/gen_gaits.sh`):
  - Placo reference generator, regenerated with joint-limit-respecting settings: walking height 0.220 m.
  - Upstream's 0.205 m bends the knee to 1.95 rad, past the model's ±1.57 rad limit. Every upstream gait failed the
    joint-limit check.
  - **13 sources** (walking directions), **2 variants** each: `normal` (single support 0.30 s, foot lift 2.5 cm) and
    `gentle` (0.40 s, 1.5 cm).
  - Head held at the home pose.
  - Base height recomputed so the planted sole touches the floor.
  - Body-frame velocities, and the yaw rate, are recomputed from the recorded orientation. The generator's stored yaw
    rate is about 40× too small.
- **Crouch** (`make_library.py:crouch_clip`):
  - Inverse kinematics with the trunk upright and both soles fixed; min-jerk down, hold, up.
  - **4 sources** (depth 25/50/75/100% of the deepest reachable crouch), **2 variants** (fast: 0.8 s moves, 1.0 s
    hold; slow: 1.5 s, 0.5 s).
  - The deepest crouch is only **8 mm**, because the model's knee limit (±1.57 rad)
    binds. The real knee reached 1.66 rad in robot logs, so the true limit is larger: robot test R3 in `ROBOT_TESTS.md`.
- **Splits:** drawn per **source**, stratified by category, seed 7, before variants are made. Both
  variants of a source always share a split (`splits.json`).

## Format (`library.npz` + `manifest.json`)

- `q`, `qd` (N, 200, 14): joint targets and velocities, model actuator order.
- `base_pos`, `base_quat` (wxyz): base pose.
- `lin_vel`, `ang_vel`: body-frame base velocity.
- `contacts` (N, 200, 2).
- `keypts` (N, 200, 5, 3): body-frame left foot, right foot, left knee, right knee, head.
- `length`.
- The manifest holds each clip's category, source, split, parameters and check report.

## Checks

- **Hard (clip dropped):**
  - every joint stays inside its range;
  - the feet stay at least 8 cm apart (self-collision proxy);
  - planted soles stay within 5 mm of the floor (no sinking or floating).
- **Soft (reported):**
  - peak joint speed against the STS3215's no-load 4.7 rad/s (⚠ in the table);
  - every gait is faster than the servos somewhere, mostly the knee swing.
  - How well a clip can actually be tracked is what the scoring step measures; that is the point of the study.

## Clips

| id | category | split | parameters | peak joint speed (rad/s) | joint-limit margin (rad) |
|---|---|---|---|---|---|
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | train | vx -0.001 m/s, vy -0.048, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 14.5 ⚠ | 0.028 |
| `side_step__dx0_dy0.03_dth0__gentle` | side_step | test | vx -0.001 m/s, vy +0.027, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 14.0 ⚠ | 0.045 |
| `turn_in_place__dx0_dy0_dth-0.15__gentle` | turn_in_place | val | vx +0.003 m/s, vy -0.018, yaw -0.16 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 8.6 ⚠ | 0.078 |
| `turn_in_place__dx0_dy0_dth-0.15__normal` | turn_in_place | val | vx +0.002 m/s, vy -0.018, yaw -0.24 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 10.0 ⚠ | 0.188 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | test | vx +0.004 m/s, vy -0.025, yaw -0.34 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.8 ⚠ | 0.048 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | test | vx +0.004 m/s, vy -0.029, yaw -0.50 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 16.2 ⚠ | 0.190 |
| `turn_in_place__dx0_dy0_dth0.15__gentle` | turn_in_place | train | vx -0.003 m/s, vy -0.005, yaw +0.19 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 6.9 ⚠ | 0.138 |
| `turn_in_place__dx0_dy0_dth0.15__normal` | turn_in_place | train | vx -0.002 m/s, vy +0.001, yaw +0.27 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.3 ⚠ | 0.174 |
| `turn_in_place__dx0_dy0_dth0.30__gentle` | turn_in_place | train | vx -0.006 m/s, vy -0.002, yaw +0.36 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.7 ⚠ | 0.060 |
| `walk_back__dx-0.02_dy0_dth0__gentle` | walk_back | test | vx -0.025 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 4.7 ⚠ | 0.140 |
| `walk_back__dx-0.02_dy0_dth0__normal` | walk_back | test | vx -0.035 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.0 ⚠ | 0.175 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | train | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 6.0 ⚠ | 0.140 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | train | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 10.0 ⚠ | 0.175 |
| `walk_fwd__dx0.02_dy0_dth0__gentle` | walk_fwd | test | vx +0.025 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 4.7 ⚠ | 0.140 |
| `walk_fwd__dx0.02_dy0_dth0__normal` | walk_fwd | test | vx +0.035 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.0 ⚠ | 0.175 |
| `walk_fwd__dx0.04_dy0_dth0__gentle` | walk_fwd | train | vx +0.049 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.0 ⚠ | 0.049 |
| `walk_fwd__dx0.04_dy0_dth0__normal` | walk_fwd | train | vx +0.070 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 15.1 ⚠ | 0.175 |
| `walk_turn__dx0.04_dy0_dth-0.15__gentle` | walk_turn | test | vx +0.051 m/s, vy -0.015, yaw -0.16 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 13.5 ⚠ | 0.014 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | test | vx +0.071 m/s, vy -0.015, yaw -0.24 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 18.1 ⚠ | 0.005 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | train | vx +0.047 m/s, vy -0.009, yaw +0.19 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 13.2 ⚠ | 0.028 |
| `crouch__depth0.25__fast` | crouch | val | depth 2.0 mm, down/up 0.8 s, hold 1.0 s | 0.1 | 0.152 |
| `crouch__depth0.25__slow` | crouch | val | depth 2.0 mm, down/up 1.5 s, hold 0.5 s | 0.1 | 0.152 |
| `crouch__depth0.50__fast` | crouch | train | depth 4.0 mm, down/up 0.8 s, hold 1.0 s | 0.2 | 0.114 |
| `crouch__depth0.50__slow` | crouch | train | depth 4.0 mm, down/up 1.5 s, hold 0.5 s | 0.1 | 0.114 |
| `crouch__depth0.75__fast` | crouch | test | depth 6.0 mm, down/up 0.8 s, hold 1.0 s | 0.3 | 0.076 |
| `crouch__depth0.75__slow` | crouch | test | depth 6.0 mm, down/up 1.5 s, hold 0.5 s | 0.1 | 0.076 |
| `crouch__depth1.00__fast` | crouch | train | depth 8.0 mm, down/up 0.8 s, hold 1.0 s | 0.4 | 0.039 |
| `crouch__depth1.00__slow` | crouch | train | depth 8.0 mm, down/up 1.5 s, hold 0.5 s | 0.2 | 0.039 |
