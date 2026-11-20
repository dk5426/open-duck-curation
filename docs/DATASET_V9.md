# Reference-clip dataset v9

Built by `curation/clips/make_v9.py`; this file is written from `data/clips_v9/manifest.json`
(`python3 curation/clips/make_v9.py --verify data/clips_v9 --doc docs/DATASET_V9.md`). GIFs of every clip, labelled
with split and broken kind: [`results/clips_v9/gifs/`](../results/clips_v9/gifs/README.md).

## Contents

- **221 clips**, 50 Hz, at most 4 s. Train / val / test: **109 / 42 /
  70**; 25 of the train clips are broken copies (22.9% of train).
- 14 motion types. Clean clips per type: 6 train, 3 val, 5 test, split by source (a source's clips are all in one
  split); val / test sources are parameter values no train clip has, mostly inside the train range.
- Splits are fixed by design in `make_v9.py` (no random draw). Every actuated joint moves in the clean train clips.
- `leg_lift` merges march (Placo gaits) with keyframed stomp, kick and tap (weight shifted 4.5 cm).
- Keyframed clips are kept clean only if no more demanding than the clean v7 walking gaits on the reference-only
  measures of `dynamic_check.py`: servo lag ≤ **0.698 rad** and balance margin ≥ **-69.2 mm**
  (worst of 64 v7 gait clips), and hops within the legs' take-off speed.

| type | train clean | train broken | val | test |
|---|---|---|---|---|
| walk_fwd | 6 | 2 | 3 | 5 |
| walk_back | 6 | 2 | 3 | 5 |
| side_step | 6 | 1 | 3 | 5 |
| turn_in_place | 6 | 2 | 3 | 5 |
| walk_turn | 6 | 2 | 3 | 5 |
| leg_lift | 6 | 2 | 3 | 5 |
| crouch | 6 | 2 | 3 | 5 |
| bow | 6 | 1 | 3 | 5 |
| sway | 6 | 2 | 3 | 5 |
| head | 6 | 2 | 3 | 5 |
| hop | 6 | 2 | 3 | 5 |
| dance | 6 | 2 | 3 | 5 |
| headbang | 6 | 2 | 3 | 5 |
| twist | 6 | 1 | 3 | 5 |

## Broken clips

Each is a copy of a clean train clip of the same type (`derived_from`), in the train split only.
`feasibility` = {"infeasible", "corrupted": true, "family", "kind", "evidence"}.

- **impossible** (physics-verified, `infeasible: true`): shove (hold test fails on the shoved pose), joint_limit
  (targets clip at a joint limit), takeoff (the hop needs more take-off speed than the legs give), speed
  (time-compressed until the servo lag exceeds the worst clean v7 walking gait's, 0.698 rad),
  one_foot_long (a foot held up 2-3 s off balance; the hold test fails).
- **corrupted** (by construction, `infeasible: false`): noise (3-8 Hz jitter, 0.07 rad RMS), glitch (3 short pose
  jumps), foot_skate (the left sole slides 4 cm while marked in contact).

| family | kind | clips |
|---|---|---|
| corrupted | foot_skate | 3 |
| corrupted | glitch | 3 |
| corrupted | noise | 3 |
| impossible | joint_limit | 3 |
| impossible | one_foot_long | 3 |
| impossible | shove | 5 |
| impossible | speed | 3 |
| impossible | takeoff | 2 |

| clip | type | family | kind | evidence |
|---|---|---|---|---|
| `dance__f1_a0.6__broken_joint_limit` | dance | impossible | joint_limit | {'f': 1, 'a': 1.4, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `headbang__f1_a0.25__broken_joint_limit` | headbang | impossible | joint_limit | {'f': 1, 'a': 0.95, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `kick__r0.03_tau0.4_dy0.045__broken_joint_limit` | leg_lift | impossible | joint_limit | {'r': 0.12, 'tau': 0.4, 'dy': 0.045, 'ik_foot_err_mm': 7.57}; joint-limit margin 0.000 rad |
| `head__nod_a1__fast__broken_one_foot_long` | head | impossible | one_foot_long | left foot up 2.6 s, 19.4 mm clear; hold test: lifted foot came down at 0.092 s |
| `stomp__lift0.015_period1.6_dy0.045__broken_one_foot_long` | leg_lift | impossible | one_foot_long | left foot up 2.5 s, 17.5 mm clear; hold test: lifted foot came down at 0.09 s |
| `sway__amp0.0100m__f0.5__broken_one_foot_long` | sway | impossible | one_foot_long | left foot up 2.6 s, 21.9 mm clear; hold test: lifted foot came down at 0.1 s |
| `bow__pitch10deg__fast__broken_shove` | bow | impossible | shove | base +12 cm; hold test on frame 123: tipped at 0.26 s |
| `crouch__depth0.20__fast__broken_shove` | crouch | impossible | shove | base -7 cm; hold test on frame 123: moved at 0.29 s |
| `head__nod_a1__slow__broken_shove` | head | impossible | shove | base +12 cm; hold test on frame 123: sagged at 0.262 s |
| `walk_back__dx-0.02_dy0_dth0__normal__broken_shove` | walk_back | impossible | shove | base -7 cm; hold test on frame 120: moved at 0.318 s |
| `walk_fwd__dx0.02_dy0_dth0__normal__broken_shove` | walk_fwd | impossible | shove | base -7 cm; hold test on frame 120: moved at 0.312 s |
| `turn_in_place__dx0_dy0_dth-0.15__gentle__broken_speed` | turn_in_place | impossible | speed | ×2.0 faster; servo lag 0.73 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__normal__broken_speed` | walk_turn | impossible | speed | ×2.0 faster; servo lag 1.26 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__gentle__broken_speed` | walk_turn | impossible | speed | ×2.5 faster; servo lag 0.86 rad > bar 0.70 |
| `hop__h0.004_n2__broken_takeoff` | hop | impossible | takeoff | h 0.025 m: needs 0.79 m/s, legs give 0.50 |
| `hop__h0.006_n2__broken_takeoff` | hop | impossible | takeoff | h 0.03 m: needs 0.79 m/s, legs give 0.50 |
| `dance__f1.5_a0.5__broken_foot_skate` | dance | corrupted | foot_skate | left sole slides 4 cm over 103 frames in contact |
| `side_step__dx0_dy0.015_dth0__normal__broken_foot_skate` | side_step | corrupted | foot_skate | left sole slides 4 cm over 65 frames in contact |
| `sway__amp0.0100m__f1.0__broken_foot_skate` | sway | corrupted | foot_skate | left sole slides 4 cm over 103 frames in contact |
| `crouch__depth0.20__slow__broken_glitch` | crouch | corrupted | glitch | frame 50: right_knee, left_hip_roll, left_ankle; frame 134: right_ankle, neck_pitch; frame 171: left_ankle, head_yaw, head_roll |
| `headbang__f1_a0.5__broken_glitch` | headbang | corrupted | glitch | frame 56: left_knee, right_hip_roll; frame 130: head_roll, left_ankle, left_hip_roll; frame 174: right_hip_pitch, left_ankle |
| `walk_back__dx-0.02_dy0_dth0__gentle__broken_glitch` | walk_back | corrupted | glitch | frame 48: right_hip_pitch, left_hip_yaw; frame 132: head_pitch, left_hip_yaw, left_knee; frame 169: right_knee, left_hip_yaw |
| `turn_in_place__dx0_dy0_dth-0.175__normal__broken_noise` | turn_in_place | corrupted | noise | 0.07 rad RMS, 3-8 Hz |
| `twist__f0.5_a0.15__broken_noise` | twist | corrupted | noise | 0.07 rad RMS, 3-8 Hz |
| `walk_fwd__dx0.02_dy0_dth0__gentle__broken_noise` | walk_fwd | corrupted | noise | 0.07 rad RMS, 3-8 Hz |

## Generation notes

- walk_fwd__dx0.06_dy0_dth0 (train) failed the checks; replaced by a spare
- side_step__dx0_dy-0.02_dth0 (train) failed the checks; replaced by a spare
- side_step__dx0_dy-0.0225_dth0 (train) failed the checks; replaced by a spare
- side_step__dx0_dy0.03_dth0 (train) failed the checks; replaced by a spare
- side_step__dx0_dy-0.0275_dth0 (train) failed the checks; replaced by a spare
- turn_in_place__dx0_dy0_dth0.30 (train) failed the checks; replaced by a spare
- walk_turn__dx0.04_dy0_dth0.15 (train) failed the checks; replaced by a spare
- walk_turn__dx0.04_dy0_dth0.10 (train) failed the checks; replaced by a spare
- walk_turn__dx0.03_dy0_dth-0.10 (train) failed the checks; replaced by a spare
- side_step speed: candidate from side_step__dx0_dy0.015_dth0__normal rejected ({"compression": 3.0, "rate_lag_rad": 0.432, "lag_bar_rad": 0.698})
- side_step speed: candidate from side_step__dx0_dy0.015_dth0__gentle rejected ({"compression": 3.0, "rate_lag_rad": 0.575, "lag_bar_rad": 0.698})
- side_step speed: candidate from side_step__dx0_dy0.0175_dth0__normal rejected ({"compression": 3.0, "rate_lag_rad": 0.436, "lag_bar_rad": 0.698})
- side_step speed: candidate from side_step__dx0_dy0.0175_dth0__gentle rejected ({"compression": 3.0, "rate_lag_rad": 0.6, "lag_bar_rad": 0.698})
- side_step speed: candidate from side_step__dx0_dy0.0125_dth0__normal rejected ({"compression": 3.0, "rate_lag_rad": 0.427, "lag_bar_rad": 0.698})
- side_step speed: candidate from side_step__dx0_dy0.0125_dth0__gentle rejected ({"compression": 3.0, "rate_lag_rad": 0.384, "lag_bar_rad": 0.698})
- speed: side_step had no clip past the lag bar at 2-3x; used walk_turn (walk_turn__dx0.03_dy0_dth-0.15__normal) instead
- turn_in_place speed: candidate from turn_in_place__dx0_dy0_dth0.15__normal rejected ({"compression": 3.0, "rate_lag_rad": 0.381, "lag_bar_rad": 0.698})
- turn_in_place speed: candidate from turn_in_place__dx0_dy0_dth0.15__gentle rejected ({"compression": 3.0, "rate_lag_rad": 0.404, "lag_bar_rad": 0.698})
- turn_in_place speed: candidate from turn_in_place__dx0_dy0_dth-0.15__normal rejected ({"compression": 3.0, "rate_lag_rad": 0.376, "lag_bar_rad": 0.698})

## Clean clips

| clip | type | split | parameters | peak joint speed (rad/s) |
|---|---|---|---|---|
| `walk_fwd__dx0.02_dy0_dth0__gentle` | walk_fwd | train | vx +0.025 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 4.7 |
| `walk_fwd__dx0.02_dy0_dth0__normal` | walk_fwd | train | vx +0.035 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.0 |
| `walk_fwd__dx0.0325_dy0_dth0__gentle` | walk_fwd | train | vx +0.040 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.7 |
| `walk_fwd__dx0.0325_dy0_dth0__normal` | walk_fwd | train | vx +0.057 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.3 |
| `walk_fwd__dx0.04_dy0_dth0__gentle` | walk_fwd | train | vx +0.049 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.0 |
| `walk_fwd__dx0.04_dy0_dth0__normal` | walk_fwd | train | vx +0.070 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 15.1 |
| `walk_fwd__dx0.015_dy0_dth0__normal` | walk_fwd | val | vx +0.026 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 8.7 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | val | vx +0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_fwd__dx0.05_dy0_dth0__gentle` | walk_fwd | val | vx +0.061 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.7 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | test | vx +0.044 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.4 |
| `walk_fwd__dx0.0275_dy0_dth0__normal` | walk_fwd | test | vx +0.049 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.7 |
| `walk_fwd__dx0.035_dy0_dth0__gentle` | walk_fwd | test | vx +0.043 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 8.6 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | test | vx +0.079 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 13.9 |
| `walk_fwd__dx0.055_dy0_dth0__gentle` | walk_fwd | test | vx +0.068 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.9 |
| `walk_back__dx-0.02_dy0_dth0__gentle` | walk_back | train | vx -0.025 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 4.7 |
| `walk_back__dx-0.02_dy0_dth0__normal` | walk_back | train | vx -0.035 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.0 |
| `walk_back__dx-0.03_dy0_dth0__gentle` | walk_back | train | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.03_dy0_dth0__normal` | walk_back | train | vx -0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | train | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | train | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.015_dy0_dth0__normal` | walk_back | val | vx -0.026 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 8.7 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | val | vx -0.044 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.4 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | val | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.0225_dy0_dth0__normal` | walk_back | test | vx -0.040 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.2 |
| `walk_back__dx-0.0275_dy0_dth0__gentle` | walk_back | test | vx -0.034 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 5.6 |
| `walk_back__dx-0.0325_dy0_dth0__normal` | walk_back | test | vx -0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.0375_dy0_dth0__gentle` | walk_back | test | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.045_dy0_dth0__normal` | walk_back | test | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (lift 2.5 cm) | 9.9 |
| `side_step__dx0_dy0.0125_dth0__gentle` | side_step | train | vx -0.000 m/s, vy +0.005, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 10.3 |
| `side_step__dx0_dy0.0125_dth0__normal` | side_step | train | vx +0.000 m/s, vy +0.015, yaw +0.02 rad/s; normal (lift 2.5 cm) | 8.9 |
| `side_step__dx0_dy0.015_dth0__gentle` | side_step | train | vx -0.000 m/s, vy +0.009, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 10.8 |
| `side_step__dx0_dy0.015_dth0__normal` | side_step | train | vx +0.000 m/s, vy +0.019, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.4 |
| `side_step__dx0_dy0.0175_dth0__gentle` | side_step | train | vx +0.000 m/s, vy +0.012, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `side_step__dx0_dy0.0175_dth0__normal` | side_step | train | vx +0.000 m/s, vy +0.024, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `side_step__dx0_dy-0.015_dth0__normal` | side_step | val | vx +0.000 m/s, vy -0.034, yaw +0.02 rad/s; normal (lift 2.5 cm) | 13.4 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | val | vx -0.001 m/s, vy -0.048, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 14.5 |
| `side_step__dx0_dy0.025_dth0__gentle` | side_step | val | vx -0.001 m/s, vy +0.021, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.5 |
| `side_step__dx0_dy-0.0175_dth0__gentle` | side_step | test | vx -0.002 m/s, vy -0.032, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | test | vx -0.002 m/s, vy -0.041, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.7 |
| `side_step__dx0_dy0.0225_dth0__normal` | side_step | test | vx +0.000 m/s, vy +0.033, yaw +0.02 rad/s; normal (lift 2.5 cm) | 14.1 |
| `side_step__dx0_dy0.0275_dth0__gentle` | side_step | test | vx -0.002 m/s, vy +0.024, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 14.4 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | test | vx +0.000 m/s, vy +0.028, yaw +0.02 rad/s; normal (lift 2.5 cm) | 11.1 |
| `turn_in_place__dx0_dy0_dth-0.15__gentle` | turn_in_place | train | vx +0.003 m/s, vy -0.018, yaw -0.16 rad/s; gentle (lift 1.5 cm) | 8.6 |
| `turn_in_place__dx0_dy0_dth-0.15__normal` | turn_in_place | train | vx +0.002 m/s, vy -0.018, yaw -0.24 rad/s; normal (lift 2.5 cm) | 10.0 |
| `turn_in_place__dx0_dy0_dth-0.175__gentle` | turn_in_place | train | vx +0.003 m/s, vy -0.019, yaw -0.19 rad/s; gentle (lift 1.5 cm) | 10.8 |
| `turn_in_place__dx0_dy0_dth-0.175__normal` | turn_in_place | train | vx +0.002 m/s, vy -0.020, yaw -0.28 rad/s; normal (lift 2.5 cm) | 11.8 |
| `turn_in_place__dx0_dy0_dth0.15__gentle` | turn_in_place | train | vx -0.003 m/s, vy -0.005, yaw +0.19 rad/s; gentle (lift 1.5 cm) | 6.9 |
| `turn_in_place__dx0_dy0_dth0.15__normal` | turn_in_place | train | vx -0.002 m/s, vy +0.001, yaw +0.27 rad/s; normal (lift 2.5 cm) | 9.3 |
| `turn_in_place__dx0_dy0_dth-0.10__normal` | turn_in_place | val | vx +0.001 m/s, vy -0.014, yaw -0.16 rad/s; normal (lift 2.5 cm) | 9.1 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | val | vx +0.004 m/s, vy -0.029, yaw -0.50 rad/s; normal (lift 2.5 cm) | 16.2 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | val | vx -0.004 m/s, vy -0.004, yaw +0.25 rad/s; gentle (lift 1.5 cm) | 10.2 |
| `turn_in_place__dx0_dy0_dth-0.20__normal` | turn_in_place | test | vx +0.002 m/s, vy -0.021, yaw -0.33 rad/s; normal (lift 2.5 cm) | 13.9 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | test | vx +0.004 m/s, vy -0.023, yaw -0.28 rad/s; gentle (lift 1.5 cm) | 11.3 |
| `turn_in_place__dx0_dy0_dth0.10__gentle` | turn_in_place | test | vx -0.002 m/s, vy -0.007, yaw +0.13 rad/s; gentle (lift 1.5 cm) | 5.2 |
| `turn_in_place__dx0_dy0_dth0.175__normal` | turn_in_place | test | vx -0.002 m/s, vy +0.002, yaw +0.32 rad/s; normal (lift 2.5 cm) | 9.6 |
| `turn_in_place__dx0_dy0_dth0.25__normal` | turn_in_place | test | vx -0.004 m/s, vy +0.006, yaw +0.45 rad/s; normal (lift 2.5 cm) | 13.5 |
| `walk_turn__dx0.02_dy0_dth-0.15__gentle` | walk_turn | train | vx +0.027 m/s, vy -0.017, yaw -0.16 rad/s; gentle (lift 1.5 cm) | 11.2 |
| `walk_turn__dx0.02_dy0_dth-0.15__normal` | walk_turn | train | vx +0.036 m/s, vy -0.016, yaw -0.24 rad/s; normal (lift 2.5 cm) | 13.4 |
| `walk_turn__dx0.02_dy0_dth0.10__gentle` | walk_turn | train | vx +0.023 m/s, vy -0.008, yaw +0.13 rad/s; gentle (lift 1.5 cm) | 9.6 |
| `walk_turn__dx0.02_dy0_dth0.10__normal` | walk_turn | train | vx +0.034 m/s, vy -0.003, yaw +0.19 rad/s; normal (lift 2.5 cm) | 9.0 |
| `walk_turn__dx0.03_dy0_dth-0.15__gentle` | walk_turn | train | vx +0.039 m/s, vy -0.016, yaw -0.16 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `walk_turn__dx0.03_dy0_dth-0.15__normal` | walk_turn | train | vx +0.054 m/s, vy -0.015, yaw -0.24 rad/s; normal (lift 2.5 cm) | 18.3 |
| `walk_turn__dx0.02_dy0_dth0.15__gentle` | walk_turn | val | vx +0.021 m/s, vy -0.007, yaw +0.19 rad/s; gentle (lift 1.5 cm) | 11.2 |
| `walk_turn__dx0.03_dy0_dth0.10__normal` | walk_turn | val | vx +0.051 m/s, vy -0.004, yaw +0.19 rad/s; normal (lift 2.5 cm) | 9.9 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | val | vx +0.071 m/s, vy -0.015, yaw -0.24 rad/s; normal (lift 2.5 cm) | 18.1 |
| `walk_turn__dx0.025_dy0_dth-0.18__normal` | walk_turn | test | vx +0.046 m/s, vy -0.018, yaw -0.29 rad/s; normal (lift 2.5 cm) | 17.9 |
| `walk_turn__dx0.025_dy0_dth0.12__normal` | walk_turn | test | vx +0.042 m/s, vy -0.003, yaw +0.22 rad/s; normal (lift 2.5 cm) | 9.6 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | test | vx +0.044 m/s, vy -0.014, yaw -0.13 rad/s; gentle (lift 1.5 cm) | 12.4 |
| `walk_turn__dx0.035_dy0_dth0.08__gentle` | walk_turn | test | vx +0.041 m/s, vy -0.009, yaw +0.10 rad/s; gentle (lift 1.5 cm) | 11.1 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | test | vx +0.050 m/s, vy -0.000, yaw +0.36 rad/s; normal (lift 2.5 cm) | 15.4 |
| `kick__r0.03_tau0.4_dy0.045` | leg_lift | train | r 0.03, tau 0.4, dy 0.045 | 4.7 |
| `march__lift0.015__gentle` | leg_lift | train | vx -0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 4.1 |
| `march__lift0.015__normal` | leg_lift | train | vx -0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 1.5 cm) | 5.6 |
| `march__lift0.025__gentle` | leg_lift | train | vx +0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 2.5 cm) | 6.1 |
| `march__lift0.025__normal` | leg_lift | train | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 8.3 |
| `stomp__lift0.015_period1.6_dy0.045` | leg_lift | train | lift 0.015, period 1.6, dy 0.045 | 3.5 |
| `march__lift0.02__normal` | leg_lift | val | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.0 cm) | 7.1 |
| `stomp__lift0.02_period1.4_dy0.045` | leg_lift | val | lift 0.02, period 1.4, dy 0.045 | 3.5 |
| `tap__reach0.03_period1.2_dy0.045` | leg_lift | val | reach 0.03, period 1.2, dy 0.045 | 3.7 |
| `kick__r0.045_tau0.5_dy0.045` | leg_lift | test | r 0.045, tau 0.5, dy 0.045 | 4.7 |
| `march__lift0.0175__gentle` | leg_lift | test | vx -0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.8 cm) | 4.7 |
| `march__lift0.03__normal` | leg_lift | test | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 3.0 cm) | 9.4 |
| `stomp__lift0.025_period1.2_dy0.045` | leg_lift | test | lift 0.025, period 1.2, dy 0.045 | 4.7 |
| `tap__reach0.035_period1.4_dy0.045` | leg_lift | test | reach 0.035, period 1.4, dy 0.045 | 3.5 |
| `crouch__depth0.20__fast` | crouch | train | depth 2.4 mm, down/up 0.8 s | 0.1 |
| `crouch__depth0.20__slow` | crouch | train | depth 2.4 mm, down/up 1.5 s | 0.1 |
| `crouch__depth0.50__fast` | crouch | train | depth 6.0 mm, down/up 0.8 s | 0.3 |
| `crouch__depth0.50__slow` | crouch | train | depth 6.0 mm, down/up 1.5 s | 0.1 |
| `crouch__depth1.00__fast` | crouch | train | depth 12.0 mm, down/up 0.8 s | 0.5 |
| `crouch__depth1.00__slow` | crouch | train | depth 12.0 mm, down/up 1.5 s | 0.3 |
| `crouch__depth0.35__fast` | crouch | val | depth 4.2 mm, down/up 0.8 s | 0.2 |
| `crouch__depth0.65__slow` | crouch | val | depth 7.8 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.85__fast` | crouch | val | depth 10.2 mm, down/up 0.8 s | 0.5 |
| `crouch__depth0.30__slow` | crouch | test | depth 3.6 mm, down/up 1.5 s | 0.1 |
| `crouch__depth0.40__fast` | crouch | test | depth 4.8 mm, down/up 0.8 s | 0.2 |
| `crouch__depth0.60__slow` | crouch | test | depth 7.2 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.75__fast` | crouch | test | depth 9.0 mm, down/up 0.8 s | 0.4 |
| `crouch__depth0.90__slow` | crouch | test | depth 10.8 mm, down/up 1.5 s | 0.3 |
| `bow__pitch10deg__fast` | bow | train | pitch 10°, down/up 0.8 s | 0.9 |
| `bow__pitch10deg__slow` | bow | train | pitch 10°, down/up 1.5 s | 0.5 |
| `bow__pitch18deg__fast` | bow | train | pitch 18°, down/up 0.8 s | 1.7 |
| `bow__pitch18deg__slow` | bow | train | pitch 18°, down/up 1.5 s | 1.0 |
| `bow__pitch25deg__fast` | bow | train | pitch 25°, down/up 0.8 s | 2.3 |
| `bow__pitch25deg__slow` | bow | train | pitch 25°, down/up 1.5 s | 1.3 |
| `bow__pitch13deg__fast` | bow | val | pitch 13°, down/up 0.8 s | 1.1 |
| `bow__pitch20deg__slow` | bow | val | pitch 20°, down/up 1.5 s | 1.1 |
| `bow__pitch23deg__fast` | bow | val | pitch 23°, down/up 0.8 s | 2.1 |
| `bow__pitch12deg__slow` | bow | test | pitch 12°, down/up 1.5 s | 0.6 |
| `bow__pitch15deg__fast` | bow | test | pitch 15°, down/up 0.8 s | 1.4 |
| `bow__pitch17deg__slow` | bow | test | pitch 17°, down/up 1.5 s | 0.9 |
| `bow__pitch22deg__fast` | bow | test | pitch 22°, down/up 0.8 s | 2.1 |
| `bow__pitch24deg__slow` | bow | test | pitch 24°, down/up 1.5 s | 1.2 |
| `sway__amp0.0100m__f0.5` | sway | train | ±10.0 mm at 0.5 Hz | 0.3 |
| `sway__amp0.0100m__f1.0` | sway | train | ±10.0 mm at 1.0 Hz | 0.6 |
| `sway__amp0.0200m__f0.5` | sway | train | ±20.0 mm at 0.5 Hz | 0.7 |
| `sway__amp0.0200m__f1.0` | sway | train | ±20.0 mm at 1.0 Hz | 1.1 |
| `sway__amp0.0300m__f0.5` | sway | train | ±30.0 mm at 0.5 Hz | 1.1 |
| `sway__amp0.0300m__f1.0` | sway | train | ±30.0 mm at 1.0 Hz | 1.7 |
| `sway__amp0.0125m__f1.0` | sway | val | ±12.5 mm at 1.0 Hz | 0.7 |
| `sway__amp0.0150m__f0.5` | sway | val | ±15.0 mm at 0.5 Hz | 0.5 |
| `sway__amp0.0250m__f1.0` | sway | val | ±25.0 mm at 1.0 Hz | 1.4 |
| `sway__amp0.0135m__f0.5` | sway | test | ±13.5 mm at 0.5 Hz | 0.4 |
| `sway__amp0.0175m__f1.0` | sway | test | ±17.5 mm at 1.0 Hz | 1.0 |
| `sway__amp0.0225m__f0.5` | sway | test | ±22.5 mm at 0.5 Hz | 0.8 |
| `sway__amp0.0275m__f1.0` | sway | test | ±27.5 mm at 1.0 Hz | 1.6 |
| `sway__amp0.0325m__f0.5` | sway | test | ±32.5 mm at 0.5 Hz | 1.2 |
| `head__nod_a1__fast` | head | train | nod ×1.0 at 1.0 Hz | 2.5 |
| `head__nod_a1__slow` | head | train | nod ×1.0 at 0.5 Hz | 1.6 |
| `head__shake_a1__fast` | head | train | shake ×1.0 at 1.0 Hz | 3.1 |
| `head__shake_a1__slow` | head | train | shake ×1.0 at 0.5 Hz | 2.0 |
| `head__tilt_a1__fast` | head | train | tilt ×1.0 at 1.0 Hz | 1.9 |
| `head__tilt_a1__slow` | head | train | tilt ×1.0 at 0.5 Hz | 1.2 |
| `head__look_around_a1__slow` | head | val | look around ×1.0 at 0.5 Hz | 1.3 |
| `head__nod_a0.7__fast` | head | val | nod ×0.7 at 1.0 Hz | 1.8 |
| `head__shake_a0.7__slow` | head | val | shake ×0.7 at 0.5 Hz | 1.4 |
| `head__look_tilt_a1__fast` | head | test | look tilt ×1.0 at 1.0 Hz | 2.0 |
| `head__nod_a0.85__slow` | head | test | nod ×0.85 at 0.5 Hz | 1.4 |
| `head__nod_tilt_a1__slow` | head | test | nod tilt ×1.0 at 0.5 Hz | 1.6 |
| `head__shake_a0.85__fast` | head | test | shake ×0.85 at 1.0 Hz | 2.7 |
| `head__tilt_a0.7__fast` | head | test | tilt ×0.7 at 1.0 Hz | 1.3 |
| `hop__h0.004_n2` | hop | train | h 0.004, n 2 | 5.5 |
| `hop__h0.005_n1` | hop | train | h 0.005, n 1 | 5.5 |
| `hop__h0.006_n2` | hop | train | h 0.006, n 2 | 5.5 |
| `hop__h0.007_n1` | hop | train | h 0.007, n 1 | 5.5 |
| `hop__h0.008_n1` | hop | train | h 0.008, n 1 | 5.5 |
| `hop__h0.009_n2` | hop | train | h 0.009, n 2 | 5.5 |
| `hop__h0.0045_n1` | hop | val | h 0.0045, n 1 | 5.5 |
| `hop__h0.0055_n2` | hop | val | h 0.0055, n 2 | 5.5 |
| `hop__h0.0085_n1` | hop | val | h 0.0085, n 1 | 5.5 |
| `hop__h0.0035_n2` | hop | test | h 0.0035, n 2 | 5.5 |
| `hop__h0.0065_n2` | hop | test | h 0.0065, n 2 | 5.5 |
| `hop__h0.006_n1` | hop | test | h 0.006, n 1 | 5.5 |
| `hop__h0.0075_n1` | hop | test | h 0.0075, n 1 | 5.5 |
| `hop__h0.0095_n1` | hop | test | h 0.0095, n 1 | 5.5 |
| `dance__f1.25_a0.7` | dance | train | f 1.25, a 0.7 | 1.4 |
| `dance__f1.5_a0.5` | dance | train | f 1.5, a 0.5 | 1.2 |
| `dance__f1.75_a0.8` | dance | train | f 1.75, a 0.8 | 2.2 |
| `dance__f1_a0.6` | dance | train | f 1, a 0.6 | 1.0 |
| `dance__f2.5_a0.5` | dance | train | f 2.5, a 0.5 | 1.9 |
| `dance__f2_a0.6` | dance | train | f 2, a 0.6 | 1.9 |
| `dance__f1.25_a0.6` | dance | val | f 1.25, a 0.6 | 1.2 |
| `dance__f1.5_a0.7` | dance | val | f 1.5, a 0.7 | 1.6 |
| `dance__f2.25_a0.5` | dance | val | f 2.25, a 0.5 | 1.7 |
| `dance__f1.25_a0.55` | dance | test | f 1.25, a 0.55 | 1.1 |
| `dance__f1.75_a0.5` | dance | test | f 1.75, a 0.5 | 1.4 |
| `dance__f1_a0.75` | dance | test | f 1, a 0.75 | 1.2 |
| `dance__f2.25_a0.65` | dance | test | f 2.25, a 0.65 | 2.3 |
| `dance__f2_a0.45` | dance | test | f 2, a 0.45 | 1.4 |
| `headbang__f1.5_a0.4` | headbang | train | f 1.5, a 0.4 | 3.7 |
| `headbang__f1_a0.25` | headbang | train | f 1, a 0.25 | 1.6 |
| `headbang__f1_a0.5` | headbang | train | f 1, a 0.5 | 3.1 |
| `headbang__f2_a0.25` | headbang | train | f 2, a 0.25 | 3.1 |
| `headbang__f2_a0.5` | headbang | train | f 2, a 0.5 | 6.2 |
| `headbang__f3_a0.25` | headbang | train | f 3, a 0.25 | 4.6 |
| `headbang__f1.5_a0.25` | headbang | val | f 1.5, a 0.25 | 2.3 |
| `headbang__f1_a0.35` | headbang | val | f 1, a 0.35 | 2.2 |
| `headbang__f2.5_a0.3` | headbang | val | f 2.5, a 0.3 | 4.6 |
| `headbang__f1.5_a0.35` | headbang | test | f 1.5, a 0.35 | 3.3 |
| `headbang__f1_a0.4` | headbang | test | f 1, a 0.4 | 2.5 |
| `headbang__f2.5_a0.2` | headbang | test | f 2.5, a 0.2 | 3.1 |
| `headbang__f2_a0.35` | headbang | test | f 2, a 0.35 | 4.4 |
| `headbang__f3_a0.2` | headbang | test | f 3, a 0.2 | 3.7 |
| `twist__f0.5_a0.15` | twist | train | f 0.5, a 0.15 | 0.6 |
| `twist__f0.5_a0.3` | twist | train | f 0.5, a 0.3 | 1.2 |
| `twist__f0.75_a0.2` | twist | train | f 0.75, a 0.2 | 0.9 |
| `twist__f1.5_a0.15` | twist | train | f 1.5, a 0.15 | 1.4 |
| `twist__f1.5_a0.3` | twist | train | f 1.5, a 0.3 | 2.8 |
| `twist__f1_a0.25` | twist | train | f 1, a 0.25 | 1.6 |
| `twist__f0.6_a0.25` | twist | val | f 0.6, a 0.25 | 1.1 |
| `twist__f1.25_a0.25` | twist | val | f 1.25, a 0.25 | 2.0 |
| `twist__f1_a0.2` | twist | val | f 1, a 0.2 | 1.3 |
| `twist__f0.5_a0.2` | twist | test | f 0.5, a 0.2 | 0.8 |
| `twist__f0.75_a0.25` | twist | test | f 0.75, a 0.25 | 1.2 |
| `twist__f1.25_a0.15` | twist | test | f 1.25, a 0.15 | 1.2 |
| `twist__f1.5_a0.2` | twist | test | f 1.5, a 0.2 | 1.9 |
| `twist__f1_a0.3` | twist | test | f 1, a 0.3 | 1.9 |
