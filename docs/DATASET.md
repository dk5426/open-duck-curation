# Reference-clip dataset (clips_v4)

Built by `curation/clips/make_library.py`; this file is written by `curation/clips/write_dataset_doc.py` from
`data/clips_v4/manifest.json`. GIFs of every clip: `results/clips_v4/<category>.gif` (kinematic replay).
**Status: draft for team review.** The splits and the check rules become final only when `PREREG.md` is signed off.

## Contents

- **74 clips**, 50 Hz, up to 4 s. Train / val / test:
  **37 / 18 / 19**.
- Model knee limit 1.66 rad (measured on the robot; the stock model has 1.57). Deepest crouch with
  every joint 0.03 rad inside its range: 12.0 mm.
- **Dropped by the hard checks (12):** `side_step__dx0_dy-0.03_dth0__normal`, `side_step__dx0_dy0.03_dth0__normal`, `turn_in_place__dx0_dy0_dth0.30__normal`, `walk_fwd__dx0.05_dy0_dth0__normal`, `walk_fwd__dx0.06_dy0_dth0__gentle`, `walk_fwd__dx0.06_dy0_dth0__normal`, `walk_turn__dx0.03_dy0_dth-0.10__normal`, `walk_turn__dx0.04_dy0_dth-0.30__gentle`, `walk_turn__dx0.04_dy0_dth-0.30__normal`, `walk_turn__dx0.04_dy0_dth0.15__normal`, `walk_turn__dx0.04_dy0_dth0.30__gentle`, `walk_turn__dx0.04_dy0_dth0.30__normal`.

| category | sources | clips train / val / test | sources train / val / test |
|---|---|---|---|
| walk_fwd | 4 | 3 / 2 / 2 | 2 / 1 / 1 |
| walk_back | 3 | 2 / 2 / 2 | 1 / 1 / 1 |
| side_step | 4 | 3 / 2 / 1 | 2 / 1 / 1 |
| turn_in_place | 4 | 4 / 1 / 2 | 2 / 1 / 1 |
| walk_turn | 6 | 7 / 1 / 2 | 4 / 1 / 1 |
| march | 3 | 2 / 2 / 2 | 1 / 1 / 1 |
| crouch | 5 | 6 / 2 / 2 | 3 / 1 / 1 |
| bow | 4 | 4 / 2 / 2 | 2 / 1 / 1 |
| sway | 3 | 2 / 2 / 2 | 1 / 1 / 1 |
| head | 4 | 4 / 2 / 2 | 2 / 1 / 1 |

## How the clips are made

- **Gaits** (`curation/clips/gen_gaits.sh`, Placo reference generator):
  - walking height 0.220 m, so the knee stays inside its range (upstream's 0.205 m bends it to 1.95 rad);
  - sources = walking directions (and foot-lift heights for `march`), 2 variants each: `normal` (single support
    0.30 s, foot lift 2.5 cm) and `gentle` (0.40 s, 1.5 cm);
  - head held at home; base height recomputed so the planted sole touches the floor; body-frame velocities and yaw rate
    recomputed from the recorded orientation (the generator's stored yaw rate is about 40× too small).
- **Crouch:** inverse kinematics, trunk upright, both soles fixed; min-jerk down, hold, up. Sources = depth as a
  fraction of the deepest crouch; variants fast (0.8 s moves, 1.0 s hold) / slow (1.5 s, 0.5 s).
- **Bow:** trunk pitched forward with the centre of mass kept over the feet; sources = pitch; variants fast / slow.
- **Sway:** the base sways fore-aft with the soles fixed; sources = amplitude; variants = frequency.
- **Head:** nod, shake, look around, tilt with the legs at home; variants = frequency.
- **Splits:** drawn per **source** after the checks (only sources with a passing variant), stratified by category,
  seed 7: 1 val and 1 test source when a category has ≥ 3 sources, 1 val when it has 2, the rest
  train. Both variants of a source share its split (`splits.json`).

## Format (`library.npz` + `manifest.json`)

- `q`, `qd` (N, T, 14): joint targets and velocities, model actuator order.
- `base_pos`, `base_quat` (wxyz): base pose. `lin_vel`, `ang_vel`: body-frame base velocity.
- `contacts` (N, T, 2). `keypts` (N, T, 5, 3): body-frame left foot, right foot, left knee, right knee, head.
- `length`: real frames per clip (shorter clips are padded with their last frame).
- The manifest holds each clip's category, source, split, parameters and check report.

## Checks

- **Hard (clip dropped):** every joint inside its range; feet at least 8 cm apart (self-collision proxy); planted
  soles within 5 mm of the floor.
- **Soft (⚠ in the table):** peak joint speed above the STS3215's no-load 4.7 rad/s. How well a clip can actually be
  tracked is what the scoring step measures; that is the point of the study.

## Clips

| id | category | split | parameters | peak joint speed (rad/s) | joint-limit margin (rad) |
|---|---|---|---|---|---|
| `walk_fwd__dx0.02_dy0_dth0__gentle` | walk_fwd | val | vx +0.025 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 4.7 ⚠ | 0.140 |
| `walk_fwd__dx0.02_dy0_dth0__normal` | walk_fwd | val | vx +0.035 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.0 ⚠ | 0.175 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | test | vx +0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 6.1 ⚠ | 0.140 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | test | vx +0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 10.0 ⚠ | 0.175 |
| `walk_fwd__dx0.04_dy0_dth0__gentle` | walk_fwd | train | vx +0.049 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.0 ⚠ | 0.049 |
| `walk_fwd__dx0.04_dy0_dth0__normal` | walk_fwd | train | vx +0.070 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 15.1 ⚠ | 0.175 |
| `walk_fwd__dx0.05_dy0_dth0__gentle` | walk_fwd | train | vx +0.061 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 12.7 ⚠ | 0.014 |
| `walk_back__dx-0.02_dy0_dth0__gentle` | walk_back | test | vx -0.025 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 4.7 ⚠ | 0.140 |
| `walk_back__dx-0.02_dy0_dth0__normal` | walk_back | test | vx -0.035 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.0 ⚠ | 0.175 |
| `walk_back__dx-0.03_dy0_dth0__gentle` | walk_back | val | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 6.0 ⚠ | 0.140 |
| `walk_back__dx-0.03_dy0_dth0__normal` | walk_back | val | vx -0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 10.0 ⚠ | 0.175 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | train | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 6.0 ⚠ | 0.140 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | train | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 10.0 ⚠ | 0.175 |
| `side_step__dx0_dy-0.015_dth0__gentle` | side_step | val | vx -0.001 m/s, vy -0.029, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.6 ⚠ | 0.086 |
| `side_step__dx0_dy-0.015_dth0__normal` | side_step | val | vx +0.000 m/s, vy -0.034, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 13.4 ⚠ | 0.174 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | train | vx -0.001 m/s, vy -0.048, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 14.5 ⚠ | 0.028 |
| `side_step__dx0_dy0.015_dth0__gentle` | side_step | train | vx -0.000 m/s, vy +0.009, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 10.8 ⚠ | 0.140 |
| `side_step__dx0_dy0.015_dth0__normal` | side_step | train | vx +0.000 m/s, vy +0.019, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.4 ⚠ | 0.175 |
| `side_step__dx0_dy0.03_dth0__gentle` | side_step | test | vx -0.001 m/s, vy +0.027, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 14.0 ⚠ | 0.045 |
| `turn_in_place__dx0_dy0_dth-0.15__gentle` | turn_in_place | train | vx +0.003 m/s, vy -0.018, yaw -0.16 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 8.6 ⚠ | 0.078 |
| `turn_in_place__dx0_dy0_dth-0.15__normal` | turn_in_place | train | vx +0.002 m/s, vy -0.018, yaw -0.24 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 10.0 ⚠ | 0.188 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | test | vx +0.004 m/s, vy -0.025, yaw -0.34 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.8 ⚠ | 0.048 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | test | vx +0.004 m/s, vy -0.029, yaw -0.50 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 16.2 ⚠ | 0.190 |
| `turn_in_place__dx0_dy0_dth0.15__gentle` | turn_in_place | train | vx -0.003 m/s, vy -0.005, yaw +0.19 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 6.9 ⚠ | 0.138 |
| `turn_in_place__dx0_dy0_dth0.15__normal` | turn_in_place | train | vx -0.002 m/s, vy +0.001, yaw +0.27 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.3 ⚠ | 0.174 |
| `turn_in_place__dx0_dy0_dth0.30__gentle` | turn_in_place | val | vx -0.006 m/s, vy -0.002, yaw +0.36 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.7 ⚠ | 0.060 |
| `walk_turn__dx0.02_dy0_dth-0.15__gentle` | walk_turn | train | vx +0.027 m/s, vy -0.017, yaw -0.16 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.2 ⚠ | 0.140 |
| `walk_turn__dx0.02_dy0_dth-0.15__normal` | walk_turn | train | vx +0.036 m/s, vy -0.016, yaw -0.24 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 13.4 ⚠ | 0.051 |
| `walk_turn__dx0.02_dy0_dth0.15__gentle` | walk_turn | train | vx +0.021 m/s, vy -0.007, yaw +0.19 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.2 ⚠ | 0.059 |
| `walk_turn__dx0.02_dy0_dth0.15__normal` | walk_turn | train | vx +0.033 m/s, vy -0.001, yaw +0.27 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.5 ⚠ | 0.176 |
| `walk_turn__dx0.03_dy0_dth-0.10__gentle` | walk_turn | val | vx +0.039 m/s, vy -0.014, yaw -0.11 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.0 ⚠ | 0.140 |
| `walk_turn__dx0.03_dy0_dth0.10__gentle` | walk_turn | train | vx +0.035 m/s, vy -0.009, yaw +0.13 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 11.6 ⚠ | 0.139 |
| `walk_turn__dx0.03_dy0_dth0.10__normal` | walk_turn | train | vx +0.051 m/s, vy -0.004, yaw +0.19 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 9.9 ⚠ | 0.176 |
| `walk_turn__dx0.04_dy0_dth-0.15__gentle` | walk_turn | test | vx +0.051 m/s, vy -0.015, yaw -0.16 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 13.5 ⚠ | 0.014 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | test | vx +0.071 m/s, vy -0.015, yaw -0.24 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 18.1 ⚠ | 0.005 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | train | vx +0.047 m/s, vy -0.009, yaw +0.19 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 13.2 ⚠ | 0.028 |
| `march__lift0.015__gentle` | march | train | vx -0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 1.5 cm) | 4.1 | 0.140 |
| `march__lift0.015__normal` | march | train | vx -0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 1.5 cm) | 5.6 ⚠ | 0.176 |
| `march__lift0.025__gentle` | march | val | vx +0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 2.5 cm) | 6.1 ⚠ | 0.138 |
| `march__lift0.025__normal` | march | val | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 2.5 cm) | 8.3 ⚠ | 0.175 |
| `march__lift0.035__gentle` | march | test | vx +0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (single support 0.4 s, lift 3.5 cm) | 7.8 ⚠ | 0.137 |
| `march__lift0.035__normal` | march | test | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (single support 0.3 s, lift 3.5 cm) | 10.5 ⚠ | 0.174 |
| `crouch__depth0.20__fast` | crouch | val | depth 2.4 mm, down/up 0.8 s, hold 1.0 s | 0.1 | 0.234 |
| `crouch__depth0.20__slow` | crouch | val | depth 2.4 mm, down/up 1.5 s, hold 0.5 s | 0.1 | 0.234 |
| `crouch__depth0.40__fast` | crouch | test | depth 4.8 mm, down/up 0.8 s, hold 1.0 s | 0.2 | 0.188 |
| `crouch__depth0.40__slow` | crouch | test | depth 4.8 mm, down/up 1.5 s, hold 0.5 s | 0.1 | 0.188 |
| `crouch__depth0.60__fast` | crouch | train | depth 7.2 mm, down/up 0.8 s, hold 1.0 s | 0.3 | 0.143 |
| `crouch__depth0.60__slow` | crouch | train | depth 7.2 mm, down/up 1.5 s, hold 0.5 s | 0.2 | 0.143 |
| `crouch__depth0.80__fast` | crouch | train | depth 9.6 mm, down/up 0.8 s, hold 1.0 s | 0.4 | 0.100 |
| `crouch__depth0.80__slow` | crouch | train | depth 9.6 mm, down/up 1.5 s, hold 0.5 s | 0.2 | 0.100 |
| `crouch__depth1.00__fast` | crouch | train | depth 12.0 mm, down/up 0.8 s, hold 1.0 s | 0.5 | 0.057 |
| `crouch__depth1.00__slow` | crouch | train | depth 12.0 mm, down/up 1.5 s, hold 0.5 s | 0.3 | 0.057 |
| `bow__pitch10deg__fast` | bow | val | trunk pitch 10°, down/up 0.8 s, hold 1.0 s | 0.9 | 0.288 |
| `bow__pitch10deg__slow` | bow | val | trunk pitch 10°, down/up 1.5 s, hold 0.5 s | 0.5 | 0.288 |
| `bow__pitch15deg__fast` | bow | train | trunk pitch 15°, down/up 0.8 s, hold 1.0 s | 1.4 | 0.288 |
| `bow__pitch15deg__slow` | bow | train | trunk pitch 15°, down/up 1.5 s, hold 0.5 s | 0.8 | 0.288 |
| `bow__pitch20deg__fast` | bow | test | trunk pitch 20°, down/up 0.8 s, hold 1.0 s | 1.9 | 0.288 |
| `bow__pitch20deg__slow` | bow | test | trunk pitch 20°, down/up 1.5 s, hold 0.5 s | 1.1 | 0.288 |
| `bow__pitch25deg__fast` | bow | train | trunk pitch 25°, down/up 0.8 s, hold 1.0 s | 2.3 | 0.165 |
| `bow__pitch25deg__slow` | bow | train | trunk pitch 25°, down/up 1.5 s, hold 0.5 s | 1.3 | 0.165 |
| `sway__amp0.01m__f0.5` | sway | val | fore-aft sway ±10 mm at 0.5 Hz | 0.3 | 0.277 |
| `sway__amp0.01m__f1.0` | sway | val | fore-aft sway ±10 mm at 1.0 Hz | 0.6 | 0.277 |
| `sway__amp0.02m__f0.5` | sway | train | fore-aft sway ±20 mm at 0.5 Hz | 0.7 | 0.277 |
| `sway__amp0.02m__f1.0` | sway | train | fore-aft sway ±20 mm at 1.0 Hz | 1.1 | 0.277 |
| `sway__amp0.03m__f0.5` | sway | test | fore-aft sway ±30 mm at 0.5 Hz | 1.1 | 0.277 |
| `sway__amp0.03m__f1.0` | sway | test | fore-aft sway ±30 mm at 1.0 Hz | 1.7 | 0.277 |
| `head__look_around__fast` | head | val | head look around at 1.0 Hz | 2.0 | 0.281 |
| `head__look_around__slow` | head | val | head look around at 0.5 Hz | 1.3 | 0.281 |
| `head__nod__fast` | head | test | head nod at 1.0 Hz | 2.5 | 0.281 |
| `head__nod__slow` | head | test | head nod at 0.5 Hz | 1.6 | 0.281 |
| `head__shake__fast` | head | train | head shake at 1.0 Hz | 3.1 | 0.281 |
| `head__shake__slow` | head | train | head shake at 0.5 Hz | 2.0 | 0.281 |
| `head__tilt__fast` | head | train | head tilt at 1.0 Hz | 1.9 | 0.224 |
| `head__tilt__slow` | head | train | head tilt at 0.5 Hz | 1.2 | 0.224 |
