# Reference-clip datasets v9c50, v9c75

Built by `curation/clips/make_v9.py`; this file is written from `data/clips_v9c75/manifest.json`
(`python3 curation/clips/make_v9.py --verify data/clips_v9c75 --doc docs/DATASET_V9C.md`). GIFs of the clips_v9 clips (the
new broken clips have none yet): [`results/clips_v9/gifs/`](../results/clips_v9/gifs/README.md).

## Contents

- **546 clips**, 50 Hz, at most 4 s. Train / val / test: **336 / 42 /
  168**; 252 of the train clips are broken copies (75.0% of train).
- **Contamination of `data/clips_v9x`:** every clips_v9x clip is copied unchanged (same id, index and arrays, checked
  bit for bit by `--verify`), so the 84 clean train clips, val and test are exactly clips_v9x's; 227 broken train copies
  are appended (`"new_in": "v9c"`). With v9's 25 broken clips, every clean train clip has exactly **3** broken
  copies (18 per type, 252 in all). A copy's `copy` field is its round (v9's clips are copy 0): copy r is in every
  library with more than r copies per clip, so a smaller dose's library is the first rows of a larger one's:
  - `data/clips_v9c50`: 378 clips (the first 378 rows), train 168 = 84 clean + 84 broken (50%), 1 per clean train clip
  - `data/clips_v9c75`: 546 clips (the first 546 rows), train 336 = 84 clean + 252 broken (75%), 3 per clean train clip
- Broken copies are made by the v9 generator (`make_v9.py --contaminate`): copy r of a clean clip tries the impossible
  kinds its type allows in turn (rotated by clip and copy) and keeps the first that passes its check; parameters change
  with clip and copy (shove size and direction, compression, raised foot and lift, amplitude, hop height, noise seed),
  so no two clips are the same (checked by `--verify`). A clip no impossible kind passes is corrupted instead, and each
  round is topped up with corrupted clips, evenly across types, to v9's 16 impossible : 9 corrupted.
- 14 motion types. Clean clips per type: 6 train, 3 val, 12 test, split by source (a source's clips are all in one
  split); val / test sources are parameter values no train clip has, mostly inside the train range.
- Splits are fixed by design in `make_v9.py` (no random draw). Every actuated joint moves in the clean train clips.
- `leg_lift` merges march (Placo gaits) with keyframed stomp, kick and tap (weight shifted 4.5 cm).
- Keyframed clips are kept clean only if no more demanding than the clean v7 walking gaits on the reference-only
  measures of `dynamic_check.py`: servo lag ≤ **0.698 rad** and balance margin ≥ **-69.2 mm**
  (worst of 64 v7 gait clips), and hops within the legs' take-off speed.

| type | train clean | train broken | val | test |
|---|---|---|---|---|
| walk_fwd | 6 | 18 | 3 | 12 |
| walk_back | 6 | 18 | 3 | 12 |
| side_step | 6 | 18 | 3 | 12 |
| turn_in_place | 6 | 18 | 3 | 12 |
| walk_turn | 6 | 18 | 3 | 12 |
| leg_lift | 6 | 18 | 3 | 12 |
| crouch | 6 | 18 | 3 | 12 |
| bow | 6 | 18 | 3 | 12 |
| sway | 6 | 18 | 3 | 12 |
| head | 6 | 18 | 3 | 12 |
| hop | 6 | 18 | 3 | 12 |
| dance | 6 | 18 | 3 | 12 |
| headbang | 6 | 18 | 3 | 12 |
| twist | 6 | 18 | 3 | 12 |

## Broken clips

Each is a copy of a clean train clip of the same type (`derived_from`), in the train split only.
`feasibility` = {"infeasible", "corrupted": true, "family", "kind", "evidence"}.

- **impossible** (physics-verified, `infeasible: true`): shove (hold test fails on the shoved pose), joint_limit
  (targets clip at a joint limit), takeoff (the hop needs more take-off speed than the legs give), speed
  (time-compressed until the servo lag exceeds the worst clean v7 walking gait's, 0.698 rad),
  one_foot_long (a foot held up 2-3 s off balance; the hold test fails).
- **corrupted** (by construction, `infeasible: false`): noise (3-8 Hz jitter, 0.07 rad RMS), glitch (3 short pose
  jumps), foot_skate (a sole slides 3.5-4.5 cm while marked in contact).

| family | kind | clips |
|---|---|---|
| corrupted | foot_skate | 31 |
| corrupted | glitch | 27 |
| corrupted | noise | 32 |
| impossible | joint_limit | 19 |
| impossible | one_foot_long | 37 |
| impossible | shove | 80 |
| impossible | speed | 17 |
| impossible | takeoff | 9 |

**v9c50** (84 broken: 54 impossible = 64.3%, v9's mix is 64.0%; impossible clips
passing their check: **54 of 54**):

| type | shove | joint_limit | takeoff | speed | one_foot_long | noise | glitch | foot_skate | impossible | corrupted |
|---|---|---|---|---|---|---|---|---|---|---|
| walk_fwd | 2 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | 3 | 3 |
| walk_back | 1 | 0 | 0 | 0 | 0 | 1 | 2 | 2 | 1 | 5 |
| side_step | 4 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 4 | 2 |
| turn_in_place | 2 | 0 | 0 | 2 | 0 | 1 | 1 | 0 | 4 | 2 |
| walk_turn | 2 | 0 | 0 | 2 | 0 | 1 | 0 | 1 | 4 | 2 |
| leg_lift | 2 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | 4 | 2 |
| crouch | 3 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 4 | 2 |
| bow | 2 | 0 | 0 | 0 | 2 | 1 | 0 | 1 | 4 | 2 |
| sway | 2 | 0 | 0 | 0 | 2 | 1 | 0 | 1 | 4 | 2 |
| head | 2 | 0 | 0 | 0 | 2 | 1 | 0 | 1 | 4 | 2 |
| hop | 1 | 0 | 3 | 0 | 0 | 1 | 0 | 1 | 4 | 2 |
| dance | 1 | 2 | 0 | 0 | 1 | 1 | 0 | 1 | 4 | 2 |
| headbang | 1 | 3 | 0 | 0 | 1 | 0 | 1 | 0 | 5 | 1 |
| twist | 1 | 2 | 0 | 0 | 2 | 1 | 0 | 0 | 5 | 1 |
| **all** | **26** | **8** | **3** | **5** | **12** | **11** | **8** | **11** | **54** | **30** |

**v9c75** (252 broken: 162 impossible = 64.3%, v9's mix is 64.0%; impossible clips
passing their check: **162 of 162**):

| type | shove | joint_limit | takeoff | speed | one_foot_long | noise | glitch | foot_skate | impossible | corrupted |
|---|---|---|---|---|---|---|---|---|---|---|
| walk_fwd | 3 | 0 | 0 | 3 | 0 | 4 | 4 | 4 | 6 | 12 |
| walk_back | 1 | 0 | 0 | 0 | 0 | 6 | 6 | 5 | 1 | 17 |
| side_step | 12 | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 12 | 6 |
| turn_in_place | 4 | 0 | 0 | 6 | 0 | 3 | 3 | 2 | 10 | 8 |
| walk_turn | 2 | 0 | 0 | 8 | 0 | 2 | 3 | 3 | 10 | 8 |
| leg_lift | 9 | 2 | 0 | 0 | 2 | 2 | 1 | 2 | 13 | 5 |
| crouch | 8 | 0 | 0 | 0 | 5 | 2 | 1 | 2 | 13 | 5 |
| bow | 7 | 0 | 0 | 0 | 6 | 2 | 1 | 2 | 13 | 5 |
| sway | 7 | 0 | 0 | 0 | 6 | 2 | 1 | 2 | 13 | 5 |
| head | 7 | 0 | 0 | 0 | 6 | 2 | 1 | 2 | 13 | 5 |
| hop | 5 | 0 | 9 | 0 | 0 | 1 | 1 | 2 | 14 | 4 |
| dance | 5 | 5 | 0 | 0 | 4 | 2 | 1 | 1 | 14 | 4 |
| headbang | 5 | 6 | 0 | 0 | 4 | 1 | 1 | 1 | 15 | 3 |
| twist | 5 | 6 | 0 | 0 | 4 | 1 | 1 | 1 | 15 | 3 |
| **all** | **80** | **19** | **9** | **17** | **37** | **32** | **27** | **31** | **162** | **90** |

An impossible clip's check is read back from its manifest entry by `--verify` (shove / one_foot_long: the hold test
fails, sole IK error ≤ 30 mm, a raised sole ≥ 8 mm clear; speed: servo lag > 0.698 rad; takeoff: the hop
needs more take-off speed than the legs give; joint_limit: targets clipped at a limit). The table below lists every
broken clip of the largest dose; `copy` 0 is the smallest dose's set.

| clip | type | family | kind | copy | evidence |
|---|---|---|---|---|---|
| `dance__f1_a0.6__broken_joint_limit` | dance | impossible | joint_limit | 0 | {'f': 1, 'a': 1.4, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `dance__f1.25_a0.7__broken_joint_limit` | dance | impossible | joint_limit | 0 | {'f': 1.25, 'a': 1.568, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `dance__f2.5_a0.5__broken_joint_limit` | dance | impossible | joint_limit | 1 | {'f': 2.5, 'a': 1.666, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `dance__f2_a0.6__broken_joint_limit` | dance | impossible | joint_limit | 2 | {'f': 2, 'a': 1.764, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `dance__f1.75_a0.8__broken_joint_limit` | dance | impossible | joint_limit | 2 | {'f': 1.75, 'a': 1.89, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `headbang__f1_a0.25__broken_joint_limit` | headbang | impossible | joint_limit | 0 | {'f': 1, 'a': 0.95, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `headbang__f2_a0.5__broken_joint_limit` | headbang | impossible | joint_limit | 0 | {'f': 2, 'a': 1.0355, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `headbang__f3_a0.25__broken_joint_limit` | headbang | impossible | joint_limit | 0 | {'f': 3, 'a': 1.064, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `headbang__f2_a0.5__broken_joint_limitb` | headbang | impossible | joint_limit | 1 | {'f': 2, 'a': 1.1305, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `headbang__f2_a0.25__broken_joint_limit` | headbang | impossible | joint_limit | 2 | {'f': 2, 'a': 1.197, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `headbang__f1.5_a0.4__broken_joint_limit` | headbang | impossible | joint_limit | 2 | {'f': 1.5, 'a': 1.2825, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `kick__r0.03_tau0.4_dy0.045__broken_joint_limit` | leg_lift | impossible | joint_limit | 0 | {'r': 0.12, 'tau': 0.4, 'dy': 0.045, 'ik_foot_err_mm': 7.57}; joint-limit margin 0.000 rad |
| `kick__r0.03_tau0.4_dy0.045__broken_joint_limitb` | leg_lift | impossible | joint_limit | 2 | {'r': 0.135, 'tau': 0.4, 'dy': 0.045, 'ik_foot_err_mm': 21.33}; joint-limit margin 0.000 rad |
| `twist__f1.5_a0.3__broken_joint_limit` | twist | impossible | joint_limit | 0 | {'f': 1.5, 'a': 0.7085, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `twist__f1_a0.25__broken_joint_limit` | twist | impossible | joint_limit | 0 | {'f': 1, 'a': 0.728, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `twist__f1.5_a0.15__broken_joint_limit` | twist | impossible | joint_limit | 1 | {'f': 1.5, 'a': 0.754, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `twist__f1.5_a0.3__broken_joint_limitb` | twist | impossible | joint_limit | 1 | {'f': 1.5, 'a': 0.7735, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `twist__f1.5_a0.15__broken_joint_limitb` | twist | impossible | joint_limit | 2 | {'f': 1.5, 'a': 0.819, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `twist__f0.75_a0.2__broken_joint_limit` | twist | impossible | joint_limit | 2 | {'f': 0.75, 'a': 0.8775, 'ik_foot_err_mm': 0.01}; joint-limit margin 0.000 rad |
| `bow__pitch10deg__slow__broken_one_foot_long` | bow | impossible | one_foot_long | 0 | right foot up 2.6 s, 23.9 mm clear; hold test: lifted foot came down at 0.102 s |
| `bow__pitch25deg__fast__broken_one_foot_long` | bow | impossible | one_foot_long | 0 | left foot up 2.6 s, 25.8 mm clear; hold test: lifted foot came down at 0.098 s |
| `bow__pitch10deg__fast__broken_one_foot_long` | bow | impossible | one_foot_long | 1 | right foot up 2.6 s, 28.9 mm clear; hold test: lifted foot came down at 0.112 s |
| `bow__pitch18deg__slow__broken_one_foot_long` | bow | impossible | one_foot_long | 1 | left foot up 2.6 s, 30.8 mm clear; hold test: lifted foot came down at 0.11 s |
| `bow__pitch18deg__fast__broken_one_foot_long` | bow | impossible | one_foot_long | 2 | left foot up 2.6 s, 25.8 mm clear; hold test: lifted foot came down at 0.098 s |
| `bow__pitch25deg__slow__broken_one_foot_long` | bow | impossible | one_foot_long | 2 | left foot up 2.6 s, 9.6 mm clear; hold test: lifted foot came down at 0.056 s |
| `crouch__depth1.00__fast__broken_one_foot_long` | crouch | impossible | one_foot_long | 0 | left foot up 2.6 s, 26.5 mm clear; hold test: lifted foot came down at 0.102 s |
| `crouch__depth0.20__fast__broken_one_foot_long` | crouch | impossible | one_foot_long | 1 | right foot up 2.6 s, 26.7 mm clear; hold test: lifted foot came down at 0.112 s |
| `crouch__depth0.50__slow__broken_one_foot_long` | crouch | impossible | one_foot_long | 1 | left foot up 2.6 s, 22.5 mm clear; hold test: lifted foot came down at 0.096 s |
| `crouch__depth0.50__fast__broken_one_foot_long` | crouch | impossible | one_foot_long | 2 | left foot up 2.6 s, 37.0 mm clear; hold test: lifted foot came down at 0.134 s |
| `crouch__depth1.00__slow__broken_one_foot_long` | crouch | impossible | one_foot_long | 2 | right foot up 2.6 s, 35.2 mm clear; hold test: lifted foot came down at 0.14 s |
| `dance__f1.75_a0.8__broken_one_foot_long` | dance | impossible | one_foot_long | 0 | left foot up 2.6 s, 20.1 mm clear; hold test: lifted foot came down at 0.092 s |
| `dance__f1_a0.6__broken_one_foot_long` | dance | impossible | one_foot_long | 1 | right foot up 2.6 s, 19.5 mm clear; hold test: lifted foot came down at 0.096 s |
| `dance__f1.25_a0.7__broken_one_foot_long` | dance | impossible | one_foot_long | 1 | right foot up 2.6 s, 32.1 mm clear; hold test: lifted foot came down at 0.124 s |
| `dance__f2.5_a0.5__broken_one_foot_long` | dance | impossible | one_foot_long | 2 | right foot up 2.6 s, 36.4 mm clear; hold test: lifted foot came down at 0.132 s |
| `head__nod_a1__fast__broken_one_foot_long` | head | impossible | one_foot_long | 0 | left foot up 2.6 s, 19.4 mm clear; hold test: lifted foot came down at 0.092 s |
| `head__tilt_a1__slow__broken_one_foot_long` | head | impossible | one_foot_long | 0 | left foot up 2.6 s, 19.4 mm clear; hold test: lifted foot came down at 0.092 s |
| `head__nod_a1__slow__broken_one_foot_long` | head | impossible | one_foot_long | 1 | right foot up 2.6 s, 28.9 mm clear; hold test: lifted foot came down at 0.118 s |
| `head__shake_a1__fast__broken_one_foot_long` | head | impossible | one_foot_long | 1 | left foot up 2.6 s, 30.8 mm clear; hold test: lifted foot came down at 0.124 s |
| `head__shake_a1__slow__broken_one_foot_long` | head | impossible | one_foot_long | 2 | left foot up 2.6 s, 35.8 mm clear; hold test: lifted foot came down at 0.134 s |
| `head__tilt_a1__fast__broken_one_foot_long` | head | impossible | one_foot_long | 2 | right foot up 2.6 s, 33.9 mm clear; hold test: lifted foot came down at 0.13 s |
| `headbang__f1.5_a0.4__broken_one_foot_long` | headbang | impossible | one_foot_long | 0 | right foot up 2.6 s, 13.8 mm clear; hold test: lifted foot came down at 0.072 s |
| `headbang__f1_a0.25__broken_one_foot_long` | headbang | impossible | one_foot_long | 1 | right foot up 2.6 s, 28.9 mm clear; hold test: lifted foot came down at 0.116 s |
| `headbang__f3_a0.25__broken_one_foot_long` | headbang | impossible | one_foot_long | 1 | right foot up 2.6 s, 23.5 mm clear; hold test: lifted foot came down at 0.1 s |
| `headbang__f2_a0.5__broken_one_foot_long` | headbang | impossible | one_foot_long | 2 | right foot up 2.6 s, 33.9 mm clear; hold test: lifted foot came down at 0.12 s |
| `stomp__lift0.015_period1.6_dy0.045__broken_one_foot_long` | leg_lift | impossible | one_foot_long | 0 | left foot up 2.5 s, 17.5 mm clear; hold test: lifted foot came down at 0.09 s |
| `stomp__lift0.015_period1.6_dy0.045__broken_one_foot_longb` | leg_lift | impossible | one_foot_long | 1 | right foot up 2.2 s, 16.6 mm clear; hold test: lifted foot came down at 0.088 s |
| `sway__amp0.0100m__f0.5__broken_one_foot_long` | sway | impossible | one_foot_long | 0 | left foot up 2.6 s, 21.9 mm clear; hold test: lifted foot came down at 0.1 s |
| `sway__amp0.0300m__f0.5__broken_one_foot_long` | sway | impossible | one_foot_long | 0 | left foot up 2.6 s, 25.8 mm clear; hold test: lifted foot came down at 0.112 s |
| `sway__amp0.0100m__f0.5__broken_one_foot_longb` | sway | impossible | one_foot_long | 1 | right foot up 2.6 s, 29.0 mm clear; hold test: lifted foot came down at 0.118 s |
| `sway__amp0.0200m__f1.0__broken_one_foot_long` | sway | impossible | one_foot_long | 1 | left foot up 2.6 s, 30.8 mm clear; hold test: lifted foot came down at 0.122 s |
| `sway__amp0.0200m__f0.5__broken_one_foot_long` | sway | impossible | one_foot_long | 2 | left foot up 2.6 s, 35.8 mm clear; hold test: lifted foot came down at 0.132 s |
| `sway__amp0.0300m__f1.0__broken_one_foot_long` | sway | impossible | one_foot_long | 2 | right foot up 2.6 s, 33.9 mm clear; hold test: lifted foot came down at 0.13 s |
| `twist__f0.5_a0.3__broken_one_foot_long` | twist | impossible | one_foot_long | 0 | right foot up 2.6 s, 20.9 mm clear; hold test: lifted foot came down at 0.098 s |
| `twist__f0.75_a0.2__broken_one_foot_long` | twist | impossible | one_foot_long | 0 | right foot up 2.6 s, 12.3 mm clear; hold test: lifted foot came down at 0.07 s |
| `twist__f1_a0.25__broken_one_foot_long` | twist | impossible | one_foot_long | 1 | right foot up 2.6 s, 30.1 mm clear; hold test: lifted foot came down at 0.122 s |
| `twist__f1.5_a0.3__broken_one_foot_long` | twist | impossible | one_foot_long | 2 | right foot up 2.6 s, 35.8 mm clear; hold test: lifted foot came down at 0.136 s |
| `bow__pitch10deg__fast__broken_shove` | bow | impossible | shove | 0 | base +12 cm; hold test on frame 123: tipped at 0.26 s |
| `bow__pitch25deg__slow__broken_shove` | bow | impossible | shove | 0 | base +12 cm; hold test on frame 123: tipped at 0.25 s |
| `bow__pitch25deg__fast__broken_shove` | bow | impossible | shove | 1 | base +13 cm; hold test on frame 123: tipped at 0.246 s |
| `bow__pitch25deg__slow__broken_shoveb` | bow | impossible | shove | 1 | base +13 cm; hold test on frame 123: tipped at 0.242 s |
| `bow__pitch10deg__slow__broken_shove` | bow | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.194 s |
| `bow__pitch18deg__slow__broken_shove` | bow | impossible | shove | 2 | base -9 cm; hold test on frame 123: tipped at 0.234 s |
| `bow__pitch25deg__fast__broken_shoveb` | bow | impossible | shove | 2 | base +14 cm; hold test on frame 123: tipped at 0.246 s |
| `crouch__depth0.20__fast__broken_shove` | crouch | impossible | shove | 0 | base -7 cm; hold test on frame 123: moved at 0.29 s |
| `crouch__depth0.50__slow__broken_shove` | crouch | impossible | shove | 0 | base -7 cm; hold test on frame 123: moved at 0.284 s |
| `crouch__depth1.00__slow__broken_shove` | crouch | impossible | shove | 0 | base -7 cm; hold test on frame 123: moved at 0.292 s |
| `crouch__depth1.00__fast__broken_shove` | crouch | impossible | shove | 1 | base -8 cm; hold test on frame 123: moved at 0.25 s |
| `crouch__depth1.00__slow__broken_shoveb` | crouch | impossible | shove | 1 | base +13 cm; hold test on frame 123: sagged at 0.232 s |
| `crouch__depth0.20__slow__broken_shove` | crouch | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.24 s |
| `crouch__depth0.50__slow__broken_shoveb` | crouch | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.252 s |
| `crouch__depth1.00__fast__broken_shoveb` | crouch | impossible | shove | 2 | base +14 cm; hold test on frame 123: sagged at 0.216 s |
| `dance__f2_a0.6__broken_shove` | dance | impossible | shove | 0 | base +12 cm; hold test on frame 123: sagged at 0.256 s |
| `dance__f1.5_a0.5__broken_shove` | dance | impossible | shove | 1 | base +13 cm; hold test on frame 123: sagged at 0.232 s |
| `dance__f1.75_a0.8__broken_shove` | dance | impossible | shove | 1 | base -8 cm; hold test on frame 123: moved at 0.252 s |
| `dance__f1_a0.6__broken_shove` | dance | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.238 s |
| `dance__f1.25_a0.7__broken_shove` | dance | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.206 s |
| `head__nod_a1__slow__broken_shove` | head | impossible | shove | 0 | base +12 cm; hold test on frame 123: sagged at 0.262 s |
| `head__tilt_a1__fast__broken_shove` | head | impossible | shove | 0 | base -7 cm; hold test on frame 123: moved at 0.282 s |
| `head__tilt_a1__slow__broken_shove` | head | impossible | shove | 1 | base -8 cm; hold test on frame 123: moved at 0.268 s |
| `head__tilt_a1__fast__broken_shoveb` | head | impossible | shove | 1 | base +13 cm; hold test on frame 123: sagged at 0.238 s |
| `head__nod_a1__fast__broken_shove` | head | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.24 s |
| `head__shake_a1__fast__broken_shove` | head | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.238 s |
| `head__tilt_a1__slow__broken_shoveb` | head | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.238 s |
| `headbang__f2_a0.25__broken_shove` | headbang | impossible | shove | 0 | base +12 cm; hold test on frame 123: sagged at 0.254 s |
| `headbang__f1_a0.5__broken_shove` | headbang | impossible | shove | 1 | base +13 cm; hold test on frame 123: sagged at 0.246 s |
| `headbang__f1.5_a0.4__broken_shove` | headbang | impossible | shove | 1 | base +13 cm; hold test on frame 123: sagged at 0.22 s |
| `headbang__f1_a0.25__broken_shove` | headbang | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.246 s |
| `headbang__f3_a0.25__broken_shove` | headbang | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.242 s |
| `hop__h0.009_n2__broken_shove` | hop | impossible | shove | 0 | base +12 cm; hold test on frame 91: sagged at 0.262 s |
| `hop__h0.004_n2__broken_shove` | hop | impossible | shove | 1 | base -8 cm; hold test on frame 89: moved at 0.256 s |
| `hop__h0.005_n1__broken_shove` | hop | impossible | shove | 1 | base -8 cm; hold test on frame 69: moved at 0.264 s |
| `hop__h0.008_n1__broken_shove` | hop | impossible | shove | 2 | base -9 cm; hold test on frame 70: moved at 0.242 s |
| `hop__h0.007_n1__broken_shove` | hop | impossible | shove | 2 | base -9 cm; hold test on frame 69: moved at 0.242 s |
| `march__lift0.025__normal__broken_shove` | leg_lift | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.334 s |
| `march__lift0.025__gentle__broken_shove` | leg_lift | impossible | shove | 0 | base -7 cm; hold test on frame 128: moved at 0.336 s |
| `march__lift0.025__normal__broken_shoveb` | leg_lift | impossible | shove | 1 | base -8 cm; hold test on frame 120: moved at 0.31 s |
| `march__lift0.025__gentle__broken_shoveb` | leg_lift | impossible | shove | 1 | base -8 cm; hold test on frame 128: moved at 0.31 s |
| `kick__r0.03_tau0.4_dy0.045__broken_shove` | leg_lift | impossible | shove | 1 | base -8 cm; hold test on frame 138: moved at 0.264 s |
| `march__lift0.015__gentle__broken_shove` | leg_lift | impossible | shove | 2 | base -9 cm; hold test on frame 128: moved at 0.234 s |
| `march__lift0.025__normal__broken_shovebb` | leg_lift | impossible | shove | 2 | base -9 cm; hold test on frame 120: moved at 0.238 s |
| `march__lift0.025__gentle__broken_shovebb` | leg_lift | impossible | shove | 2 | base -9 cm; hold test on frame 128: moved at 0.234 s |
| `stomp__lift0.015_period1.6_dy0.045__broken_shove` | leg_lift | impossible | shove | 2 | base -9 cm; hold test on frame 117: moved at 0.206 s |
| `side_step__dx0_dy0.0175_dth0__normal__broken_shove` | side_step | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.334 s |
| `side_step__dx0_dy0.0175_dth0__gentle__broken_shove` | side_step | impossible | shove | 0 | base -7 cm; hold test on frame 128: moved at 0.336 s |
| `side_step__dx0_dy0.0125_dth0__normal__broken_shove` | side_step | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.334 s |
| `side_step__dx0_dy0.0125_dth0__gentle__broken_shove` | side_step | impossible | shove | 0 | base -7 cm; hold test on frame 128: moved at 0.338 s |
| `side_step__dx0_dy0.015_dth0__gentle__broken_shove` | side_step | impossible | shove | 1 | base -8 cm; hold test on frame 128: moved at 0.306 s |
| `side_step__dx0_dy0.0175_dth0__normal__broken_shoveb` | side_step | impossible | shove | 1 | base -8 cm; hold test on frame 120: moved at 0.308 s |
| `side_step__dx0_dy0.0175_dth0__gentle__broken_shoveb` | side_step | impossible | shove | 1 | base -8 cm; hold test on frame 128: moved at 0.308 s |
| `side_step__dx0_dy0.0125_dth0__normal__broken_shoveb` | side_step | impossible | shove | 1 | base -8 cm; hold test on frame 120: moved at 0.308 s |
| `side_step__dx0_dy0.0125_dth0__gentle__broken_shoveb` | side_step | impossible | shove | 1 | base -8 cm; hold test on frame 128: moved at 0.304 s |
| `side_step__dx0_dy0.015_dth0__normal__broken_shove` | side_step | impossible | shove | 2 | base -9 cm; hold test on frame 120: moved at 0.232 s |
| `side_step__dx0_dy0.0175_dth0__normal__broken_shovebb` | side_step | impossible | shove | 2 | base -9 cm; hold test on frame 120: moved at 0.23 s |
| `side_step__dx0_dy0.0125_dth0__normal__broken_shovebb` | side_step | impossible | shove | 2 | base -9 cm; hold test on frame 120: moved at 0.232 s |
| `sway__amp0.0200m__f1.0__broken_shove` | sway | impossible | shove | 0 | base -7 cm; hold test on frame 123: moved at 0.296 s |
| `sway__amp0.0300m__f1.0__broken_shove` | sway | impossible | shove | 0 | base -7 cm; hold test on frame 123: moved at 0.294 s |
| `sway__amp0.0300m__f0.5__broken_shove` | sway | impossible | shove | 1 | base -8 cm; hold test on frame 123: moved at 0.35 s |
| `sway__amp0.0300m__f1.0__broken_shoveb` | sway | impossible | shove | 1 | base -8 cm; hold test on frame 123: moved at 0.258 s |
| `sway__amp0.0100m__f1.0__broken_shove` | sway | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.25 s |
| `sway__amp0.0200m__f1.0__broken_shoveb` | sway | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.26 s |
| `sway__amp0.0300m__f0.5__broken_shoveb` | sway | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.296 s |
| `turn_in_place__dx0_dy0_dth0.15__gentle__broken_shove` | turn_in_place | impossible | shove | 0 | base -7 cm; hold test on frame 128: moved at 0.316 s |
| `turn_in_place__dx0_dy0_dth-0.15__normal__broken_shove` | turn_in_place | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.314 s |
| `turn_in_place__dx0_dy0_dth-0.15__normal__broken_shoveb` | turn_in_place | impossible | shove | 1 | base -8 cm; hold test on frame 120: moved at 0.288 s |
| `turn_in_place__dx0_dy0_dth-0.175__normal__broken_shove` | turn_in_place | impossible | shove | 1 | base -8 cm; hold test on frame 120: moved at 0.278 s |
| `twist__f1.5_a0.15__broken_shove` | twist | impossible | shove | 0 | base +12 cm; hold test on frame 123: sagged at 0.258 s |
| `twist__f0.5_a0.3__broken_shove` | twist | impossible | shove | 1 | base -8 cm; hold test on frame 123: moved at 0.242 s |
| `twist__f0.75_a0.2__broken_shove` | twist | impossible | shove | 1 | base +13 cm; hold test on frame 123: sagged at 0.234 s |
| `twist__f0.5_a0.15__broken_shove` | twist | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.206 s |
| `twist__f1_a0.25__broken_shove` | twist | impossible | shove | 2 | base -9 cm; hold test on frame 123: moved at 0.214 s |
| `walk_back__dx-0.02_dy0_dth0__normal__broken_shove` | walk_back | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.318 s |
| `walk_fwd__dx0.02_dy0_dth0__normal__broken_shove` | walk_fwd | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.312 s |
| `walk_fwd__dx0.0325_dy0_dth0__normal__broken_shove` | walk_fwd | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.308 s |
| `walk_fwd__dx0.02_dy0_dth0__normal__broken_shoveb` | walk_fwd | impossible | shove | 1 | base -8 cm; hold test on frame 120: moved at 0.276 s |
| `walk_turn__dx0.02_dy0_dth0.10__gentle__broken_shove` | walk_turn | impossible | shove | 0 | base -7 cm; hold test on frame 128: moved at 0.31 s |
| `walk_turn__dx0.02_dy0_dth-0.15__normal__broken_shove` | walk_turn | impossible | shove | 0 | base -7 cm; hold test on frame 120: moved at 0.312 s |
| `turn_in_place__dx0_dy0_dth-0.15__gentle__broken_speed` | turn_in_place | impossible | speed | 0 | ×2.0 faster; servo lag 0.73 rad > bar 0.70 |
| `turn_in_place__dx0_dy0_dth-0.175__gentle__broken_speed` | turn_in_place | impossible | speed | 0 | ×2.0 faster; servo lag 0.70 rad > bar 0.70 |
| `turn_in_place__dx0_dy0_dth-0.15__gentle__broken_speedb` | turn_in_place | impossible | speed | 1 | ×2.15 faster; servo lag 0.78 rad > bar 0.70 |
| `turn_in_place__dx0_dy0_dth-0.175__gentle__broken_speedb` | turn_in_place | impossible | speed | 1 | ×2.15 faster; servo lag 0.75 rad > bar 0.70 |
| `turn_in_place__dx0_dy0_dth-0.15__gentle__broken_speedbb` | turn_in_place | impossible | speed | 2 | ×2.3 faster; servo lag 0.81 rad > bar 0.70 |
| `turn_in_place__dx0_dy0_dth-0.175__gentle__broken_speedbb` | turn_in_place | impossible | speed | 2 | ×2.3 faster; servo lag 0.79 rad > bar 0.70 |
| `walk_fwd__dx0.04_dy0_dth0__gentle__broken_speed` | walk_fwd | impossible | speed | 0 | ×2.0 faster; servo lag 0.80 rad > bar 0.70 |
| `walk_fwd__dx0.04_dy0_dth0__gentle__broken_speedb` | walk_fwd | impossible | speed | 1 | ×2.15 faster; servo lag 0.84 rad > bar 0.70 |
| `walk_fwd__dx0.04_dy0_dth0__gentle__broken_speedbb` | walk_fwd | impossible | speed | 2 | ×2.3 faster; servo lag 0.89 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__normal__broken_speed` | walk_turn | impossible | speed | 0 | ×2.0 faster; servo lag 1.26 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__gentle__broken_speed` | walk_turn | impossible | speed | 0 | ×2.5 faster; servo lag 0.86 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__normal__broken_speedb` | walk_turn | impossible | speed | 1 | ×2.15 faster; servo lag 1.31 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__gentle__broken_speedb` | walk_turn | impossible | speed | 1 | ×2.15 faster; servo lag 0.74 rad > bar 0.70 |
| `walk_turn__dx0.02_dy0_dth-0.15__normal__broken_speed` | walk_turn | impossible | speed | 1 | ×2.15 faster; servo lag 1.21 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__normal__broken_speedbb` | walk_turn | impossible | speed | 2 | ×2.3 faster; servo lag 1.35 rad > bar 0.70 |
| `walk_turn__dx0.03_dy0_dth-0.15__gentle__broken_speedbb` | walk_turn | impossible | speed | 2 | ×2.3 faster; servo lag 0.81 rad > bar 0.70 |
| `walk_turn__dx0.02_dy0_dth-0.15__normal__broken_speedb` | walk_turn | impossible | speed | 2 | ×2.3 faster; servo lag 1.26 rad > bar 0.70 |
| `hop__h0.004_n2__broken_takeoff` | hop | impossible | takeoff | 0 | h 0.025 m: needs 0.79 m/s, legs give 0.50 |
| `hop__h0.006_n2__broken_takeoff` | hop | impossible | takeoff | 0 | h 0.03 m: needs 0.79 m/s, legs give 0.50 |
| `hop__h0.007_n1__broken_takeoff` | hop | impossible | takeoff | 0 | h 0.03 m: needs 0.79 m/s, legs give 0.50 |
| `hop__h0.008_n1__broken_takeoff` | hop | impossible | takeoff | 1 | h 0.033 m: needs 0.79 m/s, legs give 0.50 |
| `hop__h0.009_n2__broken_takeoff` | hop | impossible | takeoff | 1 | h 0.035 m: needs 0.79 m/s, legs give 0.50 |
| `hop__h0.007_n1__broken_takeoffb` | hop | impossible | takeoff | 1 | h 0.036 m: needs 0.79 m/s, legs give 0.50 |
| `hop__h0.006_n2__broken_takeoffb` | hop | impossible | takeoff | 2 | h 0.038 m: needs 0.88 m/s, legs give 0.50 |
| `hop__h0.005_n1__broken_takeoff` | hop | impossible | takeoff | 2 | h 0.04 m: needs 0.88 m/s, legs give 0.50 |
| `hop__h0.009_n2__broken_takeoffb` | hop | impossible | takeoff | 2 | h 0.041 m: needs 0.88 m/s, legs give 0.50 |
| `bow__pitch18deg__fast__broken_foot_skate` | bow | corrupted | foot_skate | 0 | left sole slides 4 cm over 103 frames in contact |
| `bow__pitch10deg__fast__broken_foot_skate` | bow | corrupted | foot_skate | 2 | left sole slides 4 cm over 105 frames in contact |
| `crouch__depth0.50__fast__broken_foot_skate` | crouch | corrupted | foot_skate | 0 | left sole slides 4 cm over 103 frames in contact |
| `crouch__depth0.20__fast__broken_foot_skate` | crouch | corrupted | foot_skate | 2 | left sole slides 4 cm over 105 frames in contact |
| `dance__f1.5_a0.5__broken_foot_skate` | dance | corrupted | foot_skate | 0 | left sole slides 4 cm over 103 frames in contact |
| `head__shake_a1__slow__broken_foot_skate` | head | corrupted | foot_skate | 0 | left sole slides 4 cm over 103 frames in contact |
| `head__nod_a1__slow__broken_foot_skate` | head | corrupted | foot_skate | 2 | left sole slides 4 cm over 105 frames in contact |
| `headbang__f1_a0.5__broken_foot_skate` | headbang | corrupted | foot_skate | 2 | right sole slides 4 cm over 105 frames in contact |
| `hop__h0.008_n1__broken_foot_skate` | hop | corrupted | foot_skate | 0 | left sole slides 4 cm over 40 frames in contact |
| `hop__h0.004_n2__broken_foot_skate` | hop | corrupted | foot_skate | 2 | left sole slides 4 cm over 75 frames in contact |
| `march__lift0.015__normal__broken_foot_skate` | leg_lift | corrupted | foot_skate | 1 | right sole slides 4 cm over 73 frames in contact |
| `march__lift0.015__gentle__broken_foot_skate` | leg_lift | corrupted | foot_skate | 1 | left sole slides 4 cm over 63 frames in contact |
| `side_step__dx0_dy0.015_dth0__normal__broken_foot_skate` | side_step | corrupted | foot_skate | 0 | left sole slides 4 cm over 65 frames in contact |
| `side_step__dx0_dy0.0175_dth0__gentle__broken_foot_skate` | side_step | corrupted | foot_skate | 2 | right sole slides 4 cm over 72 frames in contact |
| `sway__amp0.0100m__f1.0__broken_foot_skate` | sway | corrupted | foot_skate | 0 | left sole slides 4 cm over 103 frames in contact |
| `sway__amp0.0100m__f0.5__broken_foot_skate` | sway | corrupted | foot_skate | 2 | left sole slides 4 cm over 105 frames in contact |
| `turn_in_place__dx0_dy0_dth0.15__normal__broken_foot_skate` | turn_in_place | corrupted | foot_skate | 1 | right sole slides 4 cm over 73 frames in contact |
| `turn_in_place__dx0_dy0_dth0.15__gentle__broken_foot_skate` | turn_in_place | corrupted | foot_skate | 1 | left sole slides 4 cm over 63 frames in contact |
| `twist__f0.5_a0.3__broken_foot_skate` | twist | corrupted | foot_skate | 2 | right sole slides 4 cm over 105 frames in contact |
| `walk_back__dx-0.03_dy0_dth0__normal__broken_foot_skate` | walk_back | corrupted | foot_skate | 0 | left sole slides 4 cm over 65 frames in contact |
| `walk_back__dx-0.04_dy0_dth0__gentle__broken_foot_skate` | walk_back | corrupted | foot_skate | 0 | right sole slides 4 cm over 71 frames in contact |
| `walk_back__dx-0.02_dy0_dth0__gentle__broken_foot_skate` | walk_back | corrupted | foot_skate | 1 | left sole slides 4 cm over 63 frames in contact |
| `walk_back__dx-0.04_dy0_dth0__normal__broken_foot_skate` | walk_back | corrupted | foot_skate | 1 | right sole slides 4 cm over 73 frames in contact |
| `walk_back__dx-0.03_dy0_dth0__gentle__broken_foot_skate` | walk_back | corrupted | foot_skate | 2 | right sole slides 4 cm over 72 frames in contact |
| `walk_fwd__dx0.04_dy0_dth0__normal__broken_foot_skate` | walk_fwd | corrupted | foot_skate | 0 | left sole slides 4 cm over 65 frames in contact |
| `walk_fwd__dx0.02_dy0_dth0__gentle__broken_foot_skate` | walk_fwd | corrupted | foot_skate | 1 | left sole slides 4 cm over 63 frames in contact |
| `walk_fwd__dx0.02_dy0_dth0__normal__broken_foot_skate` | walk_fwd | corrupted | foot_skate | 2 | left sole slides 4 cm over 66 frames in contact |
| `walk_fwd__dx0.0325_dy0_dth0__gentle__broken_foot_skate` | walk_fwd | corrupted | foot_skate | 2 | right sole slides 4 cm over 72 frames in contact |
| `walk_turn__dx0.02_dy0_dth0.10__normal__broken_foot_skate` | walk_turn | corrupted | foot_skate | 0 | left sole slides 4 cm over 65 frames in contact |
| `walk_turn__dx0.02_dy0_dth0.10__normal__broken_foot_skateb` | walk_turn | corrupted | foot_skate | 2 | left sole slides 4 cm over 66 frames in contact |
| `walk_turn__dx0.02_dy0_dth0.10__gentle__broken_foot_skate` | walk_turn | corrupted | foot_skate | 2 | right sole slides 4 cm over 72 frames in contact |
| `bow__pitch10deg__slow__broken_glitch` | bow | corrupted | glitch | 1 | frame 48: head_roll, left_ankle, left_hip_pitch; frame 59: right_hip_pitch, neck_pitch; frame 101: left_hip_roll, head_yaw |
| `crouch__depth0.20__slow__broken_glitch` | crouch | corrupted | glitch | 0 | frame 50: right_knee, left_hip_roll, left_ankle; frame 134: right_ankle, neck_pitch; frame 171: left_ankle, head_yaw, head_roll |
| `dance__f2_a0.6__broken_glitch` | dance | corrupted | glitch | 1 | frame 130: left_ankle, neck_pitch, left_hip_pitch; frame 169: neck_pitch, head_pitch; frame 172: head_yaw, right_hip_yaw, left_hip_yaw |
| `head__nod_a1__fast__broken_glitch` | head | corrupted | glitch | 1 | frame 49: right_hip_roll, head_roll, left_hip_roll; frame 62: head_roll, left_hip_yaw, right_hip_yaw; frame 164: left_ankle, neck_pitch, right_hip_pitch |
| `headbang__f1_a0.5__broken_glitch` | headbang | corrupted | glitch | 0 | frame 56: left_knee, right_hip_roll; frame 130: head_roll, left_ankle, left_hip_roll; frame 174: right_hip_pitch, left_ankle |
| `hop__h0.006_n2__broken_glitch` | hop | corrupted | glitch | 1 | frame 36: left_hip_roll, left_knee; frame 74: head_roll, left_ankle, right_ankle; frame 96: right_knee, left_hip_pitch |
| `march__lift0.015__gentle__broken_glitch` | leg_lift | corrupted | glitch | 0 | frame 59: head_yaw, right_hip_roll; frame 86: left_ankle, left_hip_roll, left_hip_pitch; frame 173: left_hip_yaw, right_hip_pitch, head_roll |
| `side_step__dx0_dy0.015_dth0__gentle__broken_glitch` | side_step | corrupted | glitch | 0 | frame 50: right_hip_yaw, right_ankle, head_roll; frame 100: right_hip_roll, right_hip_yaw; frame 107: neck_pitch, left_knee |
| `side_step__dx0_dy0.0125_dth0__gentle__broken_glitch` | side_step | corrupted | glitch | 2 | frame 88: head_roll, left_hip_roll; frame 99: left_hip_yaw, right_hip_roll; frame 127: right_hip_yaw, head_roll, right_knee |
| `sway__amp0.0100m__f1.0__broken_glitch` | sway | corrupted | glitch | 1 | frame 64: neck_pitch, head_yaw; frame 111: left_hip_roll, right_hip_roll, right_hip_yaw; frame 152: head_yaw, right_ankle |
| `turn_in_place__dx0_dy0_dth0.15__normal__broken_glitch` | turn_in_place | corrupted | glitch | 0 | frame 69: neck_pitch, head_yaw, left_hip_roll; frame 85: right_hip_pitch, right_hip_yaw, right_ankle; frame 150: left_ankle, right_hip_roll, head_yaw |
| `turn_in_place__dx0_dy0_dth0.15__gentle__broken_glitch` | turn_in_place | corrupted | glitch | 2 | frame 55: left_hip_pitch, right_hip_pitch, head_roll; frame 135: head_yaw, right_hip_yaw; frame 173: head_yaw, right_knee |
| `turn_in_place__dx0_dy0_dth-0.15__normal__broken_glitch` | turn_in_place | corrupted | glitch | 2 | frame 32: left_knee, head_roll; frame 47: left_hip_roll, right_ankle; frame 155: right_hip_yaw, left_hip_yaw |
| `twist__f0.5_a0.15__broken_glitch` | twist | corrupted | glitch | 1 | frame 40: right_hip_yaw, neck_pitch; frame 123: left_ankle, neck_pitch, head_yaw; frame 150: neck_pitch, left_ankle |
| `walk_back__dx-0.02_dy0_dth0__gentle__broken_glitch` | walk_back | corrupted | glitch | 0 | frame 48: right_hip_pitch, left_hip_yaw; frame 132: head_pitch, left_hip_yaw, left_knee; frame 169: right_knee, left_hip_yaw |
| `walk_back__dx-0.04_dy0_dth0__normal__broken_glitch` | walk_back | corrupted | glitch | 0 | frame 121: left_hip_pitch, right_hip_pitch; frame 133: head_roll, right_hip_pitch; frame 146: right_hip_roll, left_hip_pitch, left_hip_yaw |
| `walk_back__dx-0.03_dy0_dth0__gentle__broken_glitch` | walk_back | corrupted | glitch | 1 | frame 49: head_pitch, neck_pitch, left_hip_yaw; frame 107: head_yaw, neck_pitch, left_knee; frame 126: right_hip_pitch, left_hip_yaw |
| `walk_back__dx-0.02_dy0_dth0__normal__broken_glitch` | walk_back | corrupted | glitch | 2 | frame 50: left_knee, left_hip_pitch, right_ankle; frame 94: neck_pitch, left_knee; frame 111: left_knee, right_hip_roll, head_pitch |
| `walk_back__dx-0.03_dy0_dth0__normal__broken_glitch` | walk_back | corrupted | glitch | 2 | frame 52: head_roll, right_ankle; frame 126: right_hip_yaw, left_hip_pitch, left_hip_roll; frame 161: head_roll, left_hip_roll, right_knee |
| `walk_back__dx-0.04_dy0_dth0__gentle__broken_glitch` | walk_back | corrupted | glitch | 2 | frame 87: head_pitch, left_knee, right_hip_pitch; frame 104: left_hip_roll, left_ankle; frame 134: head_pitch, left_hip_roll, right_hip_yaw |
| `walk_fwd__dx0.0325_dy0_dth0__gentle__broken_glitch` | walk_fwd | corrupted | glitch | 0 | frame 75: right_knee, right_ankle; frame 127: left_hip_pitch, right_knee, neck_pitch; frame 156: left_hip_yaw, right_knee |
| `walk_fwd__dx0.0325_dy0_dth0__normal__broken_glitch` | walk_fwd | corrupted | glitch | 1 | frame 82: head_yaw, right_hip_yaw; frame 89: left_ankle, right_hip_pitch, head_pitch; frame 109: head_roll, left_ankle, left_hip_yaw |
| `walk_fwd__dx0.02_dy0_dth0__gentle__broken_glitch` | walk_fwd | corrupted | glitch | 2 | frame 26: left_hip_yaw, right_ankle; frame 108: right_hip_roll, right_knee; frame 138: left_hip_yaw, neck_pitch, head_pitch |
| `walk_fwd__dx0.04_dy0_dth0__normal__broken_glitch` | walk_fwd | corrupted | glitch | 2 | frame 48: right_hip_pitch, head_roll; frame 123: left_ankle, left_hip_roll; frame 136: head_yaw, left_hip_yaw, left_hip_roll |
| `walk_turn__dx0.02_dy0_dth0.10__normal__broken_glitch` | walk_turn | corrupted | glitch | 1 | frame 30: right_hip_roll, head_pitch, left_knee; frame 45: left_hip_pitch, head_pitch; frame 138: right_hip_pitch, right_knee, neck_pitch |
| `walk_turn__dx0.02_dy0_dth0.10__gentle__broken_glitch` | walk_turn | corrupted | glitch | 1 | frame 31: left_hip_pitch, head_yaw, left_hip_yaw; frame 118: left_knee, head_yaw, left_hip_roll; frame 128: left_knee, left_hip_pitch |
| `walk_turn__dx0.02_dy0_dth-0.15__gentle__broken_glitch` | walk_turn | corrupted | glitch | 2 | frame 57: left_ankle, neck_pitch, left_hip_pitch; frame 126: right_ankle, right_hip_pitch, right_hip_roll; frame 164: left_knee, right_hip_roll, left_hip_pitch |
| `bow__pitch18deg__slow__broken_noise` | bow | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `bow__pitch18deg__fast__broken_noise` | bow | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `crouch__depth0.20__slow__broken_noise` | crouch | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `crouch__depth0.50__fast__broken_noise` | crouch | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `dance__f2.5_a0.5__broken_noise` | dance | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `dance__f1.5_a0.5__broken_noise` | dance | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `head__shake_a1__fast__broken_noise` | head | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `head__shake_a1__slow__broken_noise` | head | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `headbang__f2_a0.25__broken_noise` | headbang | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `hop__h0.005_n1__broken_noise` | hop | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `march__lift0.015__normal__broken_noise` | leg_lift | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `march__lift0.015__normal__broken_noiseb` | leg_lift | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `side_step__dx0_dy0.015_dth0__normal__broken_noise` | side_step | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `side_step__dx0_dy0.015_dth0__gentle__broken_noise` | side_step | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `sway__amp0.0200m__f0.5__broken_noise` | sway | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `sway__amp0.0200m__f0.5__broken_noiseb` | sway | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `turn_in_place__dx0_dy0_dth-0.175__normal__broken_noise` | turn_in_place | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `turn_in_place__dx0_dy0_dth0.15__normal__broken_noise` | turn_in_place | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `turn_in_place__dx0_dy0_dth-0.175__normal__broken_noiseb` | turn_in_place | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `twist__f0.5_a0.15__broken_noise` | twist | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `walk_back__dx-0.03_dy0_dth0__gentle__broken_noise` | walk_back | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `walk_back__dx-0.02_dy0_dth0__normal__broken_noise` | walk_back | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `walk_back__dx-0.03_dy0_dth0__normal__broken_noise` | walk_back | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `walk_back__dx-0.04_dy0_dth0__gentle__broken_noise` | walk_back | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `walk_back__dx-0.02_dy0_dth0__gentle__broken_noise` | walk_back | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `walk_back__dx-0.04_dy0_dth0__normal__broken_noise` | walk_back | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `walk_fwd__dx0.02_dy0_dth0__gentle__broken_noise` | walk_fwd | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `walk_fwd__dx0.04_dy0_dth0__normal__broken_noise` | walk_fwd | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `walk_fwd__dx0.0325_dy0_dth0__gentle__broken_noise` | walk_fwd | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |
| `walk_fwd__dx0.0325_dy0_dth0__normal__broken_noise` | walk_fwd | corrupted | noise | 2 | 0.07 rad RMS, 3-8 Hz |
| `walk_turn__dx0.02_dy0_dth-0.15__gentle__broken_noise` | walk_turn | corrupted | noise | 0 | 0.07 rad RMS, 3-8 Hz |
| `walk_turn__dx0.02_dy0_dth-0.15__gentle__broken_noiseb` | walk_turn | corrupted | noise | 1 | 0.07 rad RMS, 3-8 Hz |

## Departures (v9c)

- **Balance unit.** "Balanced across types" is read as one broken copy per clean train clip per dose round (6 per
  type at 84, 18 at 252), so each clean clip is broken equally often.
- **Head motion kept (v9 generator fix, v9c only).** v9's shove, one_foot_long (IK) and foot_skate seed each frame's
  IK from the previous solved frame, so the head joints stay at frame 0's pose and the head motion is lost (in v9:
  `head__nod_a1__slow__broken_shove`, `head__nod_a1__fast__broken_one_foot_long`, `dance__f1.5_a0.5__broken_foot_skate`;
  the latter two head clips are still for most of the clip). Left as is, two head clips with the same leg edit come out
  identical. v9c keeps each frame's head joints (not in the leg chains, so the leg solution is unchanged); v9's 25
  clips are kept exactly as built.
- **Whole single-support holds (v9c only).** v9's leg-lift hold picks the highest single-support frame, and for its
  stomp copy that is frame 138, so only 1.2 s of the recorded 2.5 s hold fits in the 4 s clip. v9c picks the highest
  frame whose whole hold fits. v9's clip is kept as built.
- **Kind mix per type.** The 16 : 9 mix is met per dose (64.3%), not per type. Gaits allow only shove (backwards,
  7-15 cm) and speed (2-3x), and most walk_fwd / walk_back / turn_in_place / walk_turn copies pass neither, so those
  types are mostly corrupted (walk_back 1 impossible of 18 at 75%); the top-up then makes fewer corrupted clips in the
  other types (up to 15 impossible of 18). Speed was not pushed past 3x, nor shoves past 15 cm.
- **Parameter schedules.** Shoves grow 3 cm per re-draw with 1 cm per copy (v9: 2 cm steps); non-gait shoves alternate
  forward / back; foot_skate alternates the foot and slides 3.5-4.5 cm (v9: left, 4 cm); hop take-off heights step 1 mm
  per slot (2.5-4.2 cm). "No two the same" is checked as exact array equality: a few copies differ only slightly
  (for example two hops 1 mm apart in height).

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
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 0: shove rejected (last: {"shove_m": -0.13, "ik_foot_err_mm": 128.7, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.082, "why": "sagged"}})
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.449, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.422, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 0: shove rejected (last: {"shove_m": -0.13, "ik_foot_err_mm": 142.4, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.186, "why": "sagged"}})
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 0: shove rejected (last: {"shove_m": -0.13, "ik_foot_err_mm": 137.5, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.184, "why": "moved"}})
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.42, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.362, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 0: shove rejected (last: {"shove_m": -0.13, "ik_foot_err_mm": 136.9, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.104, "why": "sagged"}})
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 0: shove rejected (last: {"shove_m": -0.13, "ik_foot_err_mm": 128.6, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.196, "why": "sagged"}})
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.42, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.355, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 0: shove rejected (last: {"shove_m": -0.13, "ik_foot_err_mm": 148.4, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.194, "why": "sagged"}})
- v9c75: side_step__dx0_dy0.015_dth0__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.575, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.0175_dth0__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.6, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.0125_dth0__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.384, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth0.15__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.404, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.349, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.521, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 0: shove rejected (last: {"shove_m": -0.13, "ik_foot_err_mm": 128.1, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.194, "why": "moved"}})
- v9c75: march__lift0.015__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.191, "lag_bar_rad": 0.698})
- v9c75: march__lift0.025__gentle copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.336, "lag_bar_rad": 0.698})
- v9c75: crouch__depth0.50__fast copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: crouch__depth1.00__slow copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: bow__pitch18deg__fast copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: bow__pitch25deg__slow copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: sway__amp0.0200m__f0.5 copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: sway__amp0.0300m__f1.0 copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: head__shake_a1__slow copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.022, "lag_bar_rad": 0.698})
- v9c75: head__tilt_a1__fast copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.011, "lag_bar_rad": 0.698})
- v9c75: hop__h0.008_n1 copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.242, "lag_bar_rad": 0.698})
- v9c75: hop__h0.007_n1 copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.242, "lag_bar_rad": 0.698})
- v9c75: dance__f2.5_a0.5 copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.007, "lag_bar_rad": 0.698})
- v9c75: headbang__f2_a0.5 copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.448, "lag_bar_rad": 0.698})
- v9c75: twist__f1.5_a0.3 copy 0: speed rejected (last: {"compression": 3.0, "rate_lag_rad": 0.135, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 0: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 0: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 0: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 0: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 0: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 0: no impossible kind passed; made corrupted
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 0: no impossible kind passed; made corrupted
- v9c75: copy 0: 14 clips whose impossible kind passed were made corrupted for v9's mix (54 impossible : 30 corrupted, target 54 : 30)
- v9c75: walk_fwd__dx0.02_dy0_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.425, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.02_dy0_dth0__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 142.2, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_fwd__dx0.02_dy0_dth0__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.243, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.438, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 165.0, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.422, "why": "moved"}})
- v9c75: walk_fwd__dx0.04_dy0_dth0__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 177.4, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.432, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__normal copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 159.5, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.358, "why": "moved"}})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 160.6, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.148, "why": "sagged"}})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.397, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.02_dy0_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.421, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.02_dy0_dth0__normal copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 144.1, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_back__dx-0.02_dy0_dth0__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 142.8, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.084, "why": "sagged"}})
- v9c75: walk_back__dx-0.02_dy0_dth0__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.243, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.425, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 163.8, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 177.4, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.186, "why": "moved"}})
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.343, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.426, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 156.2, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.184, "why": "moved"}})
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 154.5, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.338, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.015_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.431, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.0175_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.468, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.0125_dth0__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.397, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth0.15__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.39, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth0.15__normal copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 139.4, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: turn_in_place__dx0_dy0_dth0.15__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 132.2, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.19, "why": "moved"}})
- v9c75: turn_in_place__dx0_dy0_dth0.15__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.418, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth-0.15__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.39, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth-0.15__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 130.0, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.124, "why": "sagged"}})
- v9c75: turn_in_place__dx0_dy0_dth-0.175__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.39, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth-0.175__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 140.8, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_turn__dx0.03_dy0_dth-0.15__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 189.4, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.208, "why": "sagged"}})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.39, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__normal copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 148.0, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.214, "why": "moved"}})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 151.0, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.078, "why": "sagged"}})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.546, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 1: shove rejected (last: {"shove_m": -0.14, "ik_foot_err_mm": 165.9, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.525, "lag_bar_rad": 0.698})
- v9c75: march__lift0.015__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.197, "lag_bar_rad": 0.698})
- v9c75: march__lift0.025__normal copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.419, "lag_bar_rad": 0.698})
- v9c75: crouch__depth0.20__slow copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: crouch__depth1.00__fast copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: bow__pitch10deg__slow copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: bow__pitch25deg__fast copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.076, "lag_bar_rad": 0.698})
- v9c75: sway__amp0.0100m__f1.0 copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: sway__amp0.0300m__f0.5 copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: head__nod_a1__fast copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.12, "lag_bar_rad": 0.698})
- v9c75: head__tilt_a1__slow copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: hop__h0.006_n2 copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.226, "lag_bar_rad": 0.698})
- v9c75: hop__h0.009_n2 copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.226, "lag_bar_rad": 0.698})
- v9c75: dance__f2_a0.6 copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.003, "lag_bar_rad": 0.698})
- v9c75: headbang__f2_a0.25 copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.13, "lag_bar_rad": 0.698})
- v9c75: twist__f1.5_a0.15 copy 1: speed rejected (last: {"compression": 2.95, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.02_dy0_dth0__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 1: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.0325_dy0_dth0__normal copy 1: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.02_dy0_dth0__normal copy 1: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.02_dy0_dth0__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 1: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 1: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: turn_in_place__dx0_dy0_dth0.15__normal copy 1: no impossible kind passed; made corrupted
- v9c75: turn_in_place__dx0_dy0_dth0.15__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: walk_turn__dx0.02_dy0_dth0.10__normal copy 1: no impossible kind passed; made corrupted
- v9c75: walk_turn__dx0.02_dy0_dth0.10__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 1: no impossible kind passed; made corrupted
- v9c75: copy 1: 15 clips whose impossible kind passed were made corrupted for v9's mix (54 impossible : 30 corrupted, target 54 : 30)
- v9c75: walk_fwd__dx0.02_dy0_dth0__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 146.0, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_fwd__dx0.02_dy0_dth0__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.431, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.02_dy0_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.229, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.02_dy0_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 166.3, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.192, "why": "moved"}})
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 200.4, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.186, "why": "moved"}})
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.475, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 184.2, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.262, "why": "moved"}})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.447, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.364, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 185.3, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.128, "why": "sagged"}})
- v9c75: walk_back__dx-0.02_dy0_dth0__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 167.7, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.21, "why": "moved"}})
- v9c75: walk_back__dx-0.02_dy0_dth0__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.422, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.02_dy0_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.229, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.02_dy0_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 164.8, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.518, "why": "moved"}})
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 196.1, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.37, "why": "moved"}})
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.431, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.319, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 207.1, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.184, "why": "moved"}})
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 185.4, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.22, "why": "moved"}})
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.432, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.314, "lag_bar_rad": 0.698})
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 198.4, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.09, "why": "sagged"}})
- v9c75: side_step__dx0_dy0.015_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.523, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.015_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 126.0, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: side_step__dx0_dy0.0175_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.579, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.0175_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 143.7, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.196, "why": "sagged"}})
- v9c75: side_step__dx0_dy0.0125_dth0__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.47, "lag_bar_rad": 0.698})
- v9c75: side_step__dx0_dy0.0125_dth0__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 134.9, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.194, "why": "moved"}})
- v9c75: turn_in_place__dx0_dy0_dth0.15__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 156.0, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.162, "why": "sagged"}})
- v9c75: turn_in_place__dx0_dy0_dth0.15__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.415, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth0.15__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.358, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth0.15__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 164.4, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.132, "why": "sagged"}})
- v9c75: turn_in_place__dx0_dy0_dth-0.15__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 134.3, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: turn_in_place__dx0_dy0_dth-0.15__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.418, "lag_bar_rad": 0.698})
- v9c75: turn_in_place__dx0_dy0_dth-0.175__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 147.5, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: turn_in_place__dx0_dy0_dth-0.175__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.418, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.03_dy0_dth-0.15__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 197.9, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.216, "why": "moved"}})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 168.5, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.076, "why": "sagged"}})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__normal copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.431, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.439, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth0.10__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 168.6, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.082, "why": "sagged"}})
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__normal copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 179.2, "hold_frame": 120, "hold": {"held": false, "t_fail_s": 0.098, "why": "sagged"}})
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.532, "lag_bar_rad": 0.698})
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 2: shove rejected (last: {"shove_m": -0.15, "ik_foot_err_mm": 191.7, "hold_frame": 128, "hold": {"held": false, "t_fail_s": 0.198, "why": "sagged"}})
- v9c75: march__lift0.015__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.173, "lag_bar_rad": 0.698})
- v9c75: march__lift0.025__gentle copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.374, "lag_bar_rad": 0.698})
- v9c75: kick__r0.03_tau0.4_dy0.045 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.324, "lag_bar_rad": 0.698})
- v9c75: crouch__depth0.20__fast copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: crouch__depth0.50__slow copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: bow__pitch10deg__fast copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: bow__pitch18deg__slow copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: sway__amp0.0100m__f0.5 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: sway__amp0.0200m__f1.0 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: head__nod_a1__slow copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: head__shake_a1__fast copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.265, "lag_bar_rad": 0.698})
- v9c75: hop__h0.004_n2 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.206, "lag_bar_rad": 0.698})
- v9c75: hop__h0.005_n1 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.199, "lag_bar_rad": 0.698})
- v9c75: dance__f1.5_a0.5 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: dance__f1.75_a0.8 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.027, "lag_bar_rad": 0.698})
- v9c75: headbang__f1_a0.5 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.265, "lag_bar_rad": 0.698})
- v9c75: headbang__f1.5_a0.4 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.279, "lag_bar_rad": 0.698})
- v9c75: twist__f0.5_a0.3 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: twist__f0.75_a0.2 copy 2: speed rejected (last: {"compression": 2.9, "rate_lag_rad": 0.0, "lag_bar_rad": 0.698})
- v9c75: walk_fwd__dx0.02_dy0_dth0__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.02_dy0_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.04_dy0_dth0__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.0325_dy0_dth0__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_fwd__dx0.0325_dy0_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.02_dy0_dth0__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.02_dy0_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.03_dy0_dth0__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.03_dy0_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.04_dy0_dth0__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_back__dx-0.04_dy0_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: side_step__dx0_dy0.015_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: side_step__dx0_dy0.0175_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: side_step__dx0_dy0.0125_dth0__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: turn_in_place__dx0_dy0_dth0.15__normal copy 2: no impossible kind passed; made corrupted
- v9c75: turn_in_place__dx0_dy0_dth0.15__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: turn_in_place__dx0_dy0_dth-0.15__normal copy 2: no impossible kind passed; made corrupted
- v9c75: turn_in_place__dx0_dy0_dth-0.175__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_turn__dx0.02_dy0_dth0.10__normal copy 2: no impossible kind passed; made corrupted
- v9c75: walk_turn__dx0.02_dy0_dth0.10__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: walk_turn__dx0.02_dy0_dth-0.15__gentle copy 2: no impossible kind passed; made corrupted
- v9c75: copy 2: 9 clips whose impossible kind passed were made corrupted for v9's mix (54 impossible : 30 corrupted, target 54 : 30)

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
| `walk_fwd__dx0.0225_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.028 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 4.9 |
| `walk_fwd__dx0.024_dy0_dth0__normal` | walk_fwd | test (v9x) | vx +0.042 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.3 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | test | vx +0.044 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.4 |
| `walk_fwd__dx0.0275_dy0_dth0__normal` | walk_fwd | test | vx +0.049 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.7 |
| `walk_fwd__dx0.029_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.036 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 5.9 |
| `walk_fwd__dx0.031_dy0_dth0__normal` | walk_fwd | test (v9x) | vx +0.055 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.1 |
| `walk_fwd__dx0.034_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.042 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 7.7 |
| `walk_fwd__dx0.035_dy0_dth0__gentle` | walk_fwd | test | vx +0.043 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 8.6 |
| `walk_fwd__dx0.0365_dy0_dth0__normal` | walk_fwd | test (v9x) | vx +0.064 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 12.0 |
| `walk_fwd__dx0.039_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.049 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.1 |
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
| `walk_back__dx-0.021_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.026 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 4.8 |
| `walk_back__dx-0.0225_dy0_dth0__normal` | walk_back | test | vx -0.040 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.2 |
| `walk_back__dx-0.024_dy0_dth0__normal` | walk_back | test (v9x) | vx -0.042 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.3 |
| `walk_back__dx-0.026_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.033 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 5.4 |
| `walk_back__dx-0.0275_dy0_dth0__gentle` | walk_back | test | vx -0.034 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 5.6 |
| `walk_back__dx-0.029_dy0_dth0__normal` | walk_back | test (v9x) | vx -0.051 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.9 |
| `walk_back__dx-0.031_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.0325_dy0_dth0__normal` | walk_back | test | vx -0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.034_dy0_dth0__normal` | walk_back | test (v9x) | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.0375_dy0_dth0__gentle` | walk_back | test | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.039_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
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
| `side_step__dx0_dy-0.0135_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy -0.027, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `side_step__dx0_dy-0.0155_dth0__normal` | side_step | test (v9x) | vx +0.000 m/s, vy -0.035, yaw +0.02 rad/s; normal (lift 2.5 cm) | 13.6 |
| `side_step__dx0_dy-0.0175_dth0__gentle` | side_step | test | vx -0.002 m/s, vy -0.032, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `side_step__dx0_dy-0.019_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy -0.034, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.3 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | test | vx -0.002 m/s, vy -0.041, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.7 |
| `side_step__dx0_dy0.0135_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy +0.007, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 10.9 |
| `side_step__dx0_dy0.0145_dth0__normal` | side_step | test (v9x) | vx +0.000 m/s, vy +0.018, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.3 |
| `side_step__dx0_dy0.016_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy +0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.5 |
| `side_step__dx0_dy0.019_dth0__normal` | side_step | test (v9x) | vx +0.000 m/s, vy +0.026, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.5 |
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
| `turn_in_place__dx0_dy0_dth-0.125__gentle` | turn_in_place | test (v9x) | vx +0.002 m/s, vy -0.017, yaw -0.14 rad/s; gentle (lift 1.5 cm) | 6.2 |
| `turn_in_place__dx0_dy0_dth-0.14__normal` | turn_in_place | test (v9x) | vx +0.002 m/s, vy -0.017, yaw -0.22 rad/s; normal (lift 2.5 cm) | 9.7 |
| `turn_in_place__dx0_dy0_dth-0.16__normal` | turn_in_place | test (v9x) | vx +0.002 m/s, vy -0.019, yaw -0.26 rad/s; normal (lift 2.5 cm) | 10.6 |
| `turn_in_place__dx0_dy0_dth-0.19__normal` | turn_in_place | test (v9x) | vx +0.003 m/s, vy -0.021, yaw -0.31 rad/s; normal (lift 2.5 cm) | 13.9 |
| `turn_in_place__dx0_dy0_dth-0.20__normal` | turn_in_place | test | vx +0.002 m/s, vy -0.021, yaw -0.33 rad/s; normal (lift 2.5 cm) | 13.9 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | test | vx +0.004 m/s, vy -0.023, yaw -0.28 rad/s; gentle (lift 1.5 cm) | 11.3 |
| `turn_in_place__dx0_dy0_dth0.10__gentle` | turn_in_place | test | vx -0.002 m/s, vy -0.007, yaw +0.13 rad/s; gentle (lift 1.5 cm) | 5.2 |
| `turn_in_place__dx0_dy0_dth0.14__gentle` | turn_in_place | test (v9x) | vx -0.003 m/s, vy -0.006, yaw +0.18 rad/s; gentle (lift 1.5 cm) | 6.3 |
| `turn_in_place__dx0_dy0_dth0.16__gentle` | turn_in_place | test (v9x) | vx -0.005 m/s, vy -0.005, yaw +0.20 rad/s; gentle (lift 1.5 cm) | 8.0 |
| `turn_in_place__dx0_dy0_dth0.175__normal` | turn_in_place | test | vx -0.002 m/s, vy +0.002, yaw +0.32 rad/s; normal (lift 2.5 cm) | 9.6 |
| `turn_in_place__dx0_dy0_dth0.19__gentle` | turn_in_place | test (v9x) | vx -0.004 m/s, vy -0.005, yaw +0.23 rad/s; gentle (lift 1.5 cm) | 9.4 |
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
| `walk_turn__dx0.0225_dy0_dth0.05__gentle` | walk_turn | test (v9x) | vx +0.027 m/s, vy -0.009, yaw +0.07 rad/s; gentle (lift 1.5 cm) | 5.7 |
| `walk_turn__dx0.025_dy0_dth-0.10__gentle` | walk_turn | test (v9x) | vx +0.032 m/s, vy -0.014, yaw -0.11 rad/s; gentle (lift 1.5 cm) | 10.4 |
| `walk_turn__dx0.025_dy0_dth-0.18__normal` | walk_turn | test | vx +0.046 m/s, vy -0.018, yaw -0.29 rad/s; normal (lift 2.5 cm) | 17.9 |
| `walk_turn__dx0.025_dy0_dth0.12__normal` | walk_turn | test | vx +0.042 m/s, vy -0.003, yaw +0.22 rad/s; normal (lift 2.5 cm) | 9.6 |
| `walk_turn__dx0.0275_dy0_dth-0.06__normal` | walk_turn | test (v9x) | vx +0.049 m/s, vy -0.011, yaw -0.09 rad/s; normal (lift 2.5 cm) | 11.9 |
| `walk_turn__dx0.02_dy0_dth-0.12__normal` | walk_turn | test (v9x) | vx +0.037 m/s, vy -0.015, yaw -0.19 rad/s; normal (lift 2.5 cm) | 14.5 |
| `walk_turn__dx0.02_dy0_dth0.07__normal` | walk_turn | test (v9x) | vx +0.034 m/s, vy -0.004, yaw +0.14 rad/s; normal (lift 2.5 cm) | 8.9 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | test | vx +0.044 m/s, vy -0.014, yaw -0.13 rad/s; gentle (lift 1.5 cm) | 12.4 |
| `walk_turn__dx0.035_dy0_dth0.08__gentle` | walk_turn | test | vx +0.041 m/s, vy -0.009, yaw +0.10 rad/s; gentle (lift 1.5 cm) | 11.1 |
| `walk_turn__dx0.03_dy0_dth-0.13__gentle` | walk_turn | test (v9x) | vx +0.040 m/s, vy -0.015, yaw -0.14 rad/s; gentle (lift 1.5 cm) | 11.5 |
| `walk_turn__dx0.03_dy0_dth0.06__gentle` | walk_turn | test (v9x) | vx +0.035 m/s, vy -0.009, yaw +0.08 rad/s; gentle (lift 1.5 cm) | 10.1 |
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
| `kick__r0.025_tau0.45_dy0.045` | leg_lift | test (v9x) | r 0.025, tau 0.45, dy 0.045 | 4.7 |
| `kick__r0.035_tau0.4_dy0.045` | leg_lift | test (v9x) | r 0.035, tau 0.4, dy 0.045 | 4.7 |
| `kick__r0.045_tau0.5_dy0.045` | leg_lift | test | r 0.045, tau 0.5, dy 0.045 | 4.7 |
| `march__lift0.016__normal` | leg_lift | test (v9x) | vx -0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 1.6 cm) | 5.9 |
| `march__lift0.0175__gentle` | leg_lift | test | vx -0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.8 cm) | 4.7 |
| `march__lift0.0215__gentle` | leg_lift | test (v9x) | vx -0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 2.1 cm) | 5.5 |
| `march__lift0.024__normal` | leg_lift | test (v9x) | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.4 cm) | 8.1 |
| `march__lift0.03__normal` | leg_lift | test | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 3.0 cm) | 9.4 |
| `stomp__lift0.0175_period1.5_dy0.045` | leg_lift | test (v9x) | lift 0.0175, period 1.5, dy 0.045 | 3.5 |
| `stomp__lift0.025_period1.2_dy0.045` | leg_lift | test | lift 0.025, period 1.2, dy 0.045 | 4.7 |
| `tap__reach0.025_period1.4_dy0.045` | leg_lift | test (v9x) | reach 0.025, period 1.4, dy 0.045 | 3.5 |
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
| `crouch__depth0.25__fast` | crouch | test (v9x) | depth 3.0 mm, down/up 0.8 s | 0.1 |
| `crouch__depth0.30__slow` | crouch | test | depth 3.6 mm, down/up 1.5 s | 0.1 |
| `crouch__depth0.33__slow` | crouch | test (v9x) | depth 4.0 mm, down/up 1.5 s | 0.1 |
| `crouch__depth0.40__fast` | crouch | test | depth 4.8 mm, down/up 0.8 s | 0.2 |
| `crouch__depth0.42__fast` | crouch | test (v9x) | depth 5.0 mm, down/up 0.8 s | 0.2 |
| `crouch__depth0.58__slow` | crouch | test (v9x) | depth 7.0 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.60__slow` | crouch | test | depth 7.2 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.70__fast` | crouch | test (v9x) | depth 8.4 mm, down/up 0.8 s | 0.4 |
| `crouch__depth0.75__fast` | crouch | test | depth 9.0 mm, down/up 0.8 s | 0.4 |
| `crouch__depth0.80__slow` | crouch | test (v9x) | depth 9.6 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.90__slow` | crouch | test | depth 10.8 mm, down/up 1.5 s | 0.3 |
| `crouch__depth0.95__fast` | crouch | test (v9x) | depth 11.4 mm, down/up 0.8 s | 0.5 |
| `bow__pitch10deg__fast` | bow | train | pitch 10°, down/up 0.8 s | 0.9 |
| `bow__pitch10deg__slow` | bow | train | pitch 10°, down/up 1.5 s | 0.5 |
| `bow__pitch18deg__fast` | bow | train | pitch 18°, down/up 0.8 s | 1.7 |
| `bow__pitch18deg__slow` | bow | train | pitch 18°, down/up 1.5 s | 1.0 |
| `bow__pitch25deg__fast` | bow | train | pitch 25°, down/up 0.8 s | 2.3 |
| `bow__pitch25deg__slow` | bow | train | pitch 25°, down/up 1.5 s | 1.3 |
| `bow__pitch13deg__fast` | bow | val | pitch 13°, down/up 0.8 s | 1.1 |
| `bow__pitch20deg__slow` | bow | val | pitch 20°, down/up 1.5 s | 1.1 |
| `bow__pitch23deg__fast` | bow | val | pitch 23°, down/up 0.8 s | 2.1 |
| `bow__pitch11deg__fast` | bow | test (v9x) | pitch 11°, down/up 0.8 s | 0.9 |
| `bow__pitch12.5deg__slow` | bow | test (v9x) | pitch 12.5°, down/up 1.5 s | 0.6 |
| `bow__pitch12deg__slow` | bow | test | pitch 12°, down/up 1.5 s | 0.6 |
| `bow__pitch14.5deg__fast` | bow | test (v9x) | pitch 14.5°, down/up 0.8 s | 1.3 |
| `bow__pitch15deg__fast` | bow | test | pitch 15°, down/up 0.8 s | 1.4 |
| `bow__pitch16deg__slow` | bow | test (v9x) | pitch 16°, down/up 1.5 s | 0.8 |
| `bow__pitch17deg__slow` | bow | test | pitch 17°, down/up 1.5 s | 0.9 |
| `bow__pitch19deg__fast` | bow | test (v9x) | pitch 19°, down/up 0.8 s | 1.8 |
| `bow__pitch20.5deg__slow` | bow | test (v9x) | pitch 20.5°, down/up 1.5 s | 1.1 |
| `bow__pitch22deg__fast` | bow | test | pitch 22°, down/up 0.8 s | 2.1 |
| `bow__pitch23.5deg__fast` | bow | test (v9x) | pitch 23.5°, down/up 0.8 s | 2.2 |
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
| `sway__amp0.0110m__f1.0` | sway | test (v9x) | ±11.0 mm at 1.0 Hz | 0.6 |
| `sway__amp0.0135m__f0.5` | sway | test | ±13.5 mm at 0.5 Hz | 0.4 |
| `sway__amp0.0145m__f0.5` | sway | test (v9x) | ±14.5 mm at 0.5 Hz | 0.5 |
| `sway__amp0.0160m__f1.0` | sway | test (v9x) | ±16.0 mm at 1.0 Hz | 0.9 |
| `sway__amp0.0175m__f1.0` | sway | test | ±17.5 mm at 1.0 Hz | 1.0 |
| `sway__amp0.0190m__f0.5` | sway | test (v9x) | ±19.0 mm at 0.5 Hz | 0.6 |
| `sway__amp0.0215m__f1.0` | sway | test (v9x) | ±21.5 mm at 1.0 Hz | 1.2 |
| `sway__amp0.0225m__f0.5` | sway | test | ±22.5 mm at 0.5 Hz | 0.8 |
| `sway__amp0.0240m__f0.5` | sway | test (v9x) | ±24.0 mm at 0.5 Hz | 0.8 |
| `sway__amp0.0275m__f1.0` | sway | test | ±27.5 mm at 1.0 Hz | 1.6 |
| `sway__amp0.0285m__f1.0` | sway | test (v9x) | ±28.5 mm at 1.0 Hz | 1.6 |
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
| `head__look_around_a0.9__fast` | head | test (v9x) | look around ×0.9 at 1.0 Hz | 1.8 |
| `head__look_tilt_a0.8__fast` | head | test (v9x) | look tilt ×0.8 at 1.0 Hz | 1.6 |
| `head__look_tilt_a1__fast` | head | test | look tilt ×1.0 at 1.0 Hz | 2.0 |
| `head__nod_a0.85__slow` | head | test | nod ×0.85 at 0.5 Hz | 1.4 |
| `head__nod_a0.9__fast` | head | test (v9x) | nod ×0.9 at 1.0 Hz | 2.3 |
| `head__nod_tilt_a0.8__slow` | head | test (v9x) | nod tilt ×0.8 at 0.5 Hz | 1.3 |
| `head__nod_tilt_a1__slow` | head | test | nod tilt ×1.0 at 0.5 Hz | 1.6 |
| `head__shake_a0.75__slow` | head | test (v9x) | shake ×0.75 at 0.5 Hz | 1.5 |
| `head__shake_a0.85__fast` | head | test | shake ×0.85 at 1.0 Hz | 2.7 |
| `head__shake_a0.9__slow` | head | test (v9x) | shake ×0.9 at 0.5 Hz | 1.8 |
| `head__tilt_a0.7__fast` | head | test | tilt ×0.7 at 1.0 Hz | 1.3 |
| `head__tilt_a0.9__slow` | head | test (v9x) | tilt ×0.9 at 0.5 Hz | 1.1 |
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
| `hop__h0.0042_n1` | hop | test (v9x) | h 0.0042, n 1 | 5.5 |
| `hop__h0.0048_n2` | hop | test (v9x) | h 0.0048, n 2 | 5.5 |
| `hop__h0.0052_n2` | hop | test (v9x) | h 0.0052, n 2 | 5.5 |
| `hop__h0.0058_n1` | hop | test (v9x) | h 0.0058, n 1 | 5.5 |
| `hop__h0.0065_n2` | hop | test | h 0.0065, n 2 | 5.5 |
| `hop__h0.0068_n2` | hop | test (v9x) | h 0.0068, n 2 | 5.5 |
| `hop__h0.006_n1` | hop | test | h 0.006, n 1 | 5.5 |
| `hop__h0.0072_n1` | hop | test (v9x) | h 0.0072, n 1 | 5.5 |
| `hop__h0.0075_n1` | hop | test | h 0.0075, n 1 | 5.5 |
| `hop__h0.0082_n2` | hop | test (v9x) | h 0.0082, n 2 | 5.5 |
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
| `dance__f1.1_a0.55` | dance | test (v9x) | f 1.1, a 0.55 | 0.9 |
| `dance__f1.25_a0.55` | dance | test | f 1.25, a 0.55 | 1.1 |
| `dance__f1.3_a0.75` | dance | test (v9x) | f 1.3, a 0.75 | 1.5 |
| `dance__f1.4_a0.65` | dance | test (v9x) | f 1.4, a 0.65 | 1.4 |
| `dance__f1.6_a0.55` | dance | test (v9x) | f 1.6, a 0.55 | 1.4 |
| `dance__f1.75_a0.5` | dance | test | f 1.75, a 0.5 | 1.4 |
| `dance__f1.9_a0.7` | dance | test (v9x) | f 1.9, a 0.7 | 2.1 |
| `dance__f1_a0.75` | dance | test | f 1, a 0.75 | 1.2 |
| `dance__f2.1_a0.55` | dance | test (v9x) | f 2.1, a 0.55 | 1.8 |
| `dance__f2.25_a0.65` | dance | test | f 2.25, a 0.65 | 2.3 |
| `dance__f2.4_a0.6` | dance | test (v9x) | f 2.4, a 0.6 | 2.2 |
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
| `headbang__f1.25_a0.3` | headbang | test (v9x) | f 1.25, a 0.3 | 2.3 |
| `headbang__f1.25_a0.45` | headbang | test (v9x) | f 1.25, a 0.45 | 3.5 |
| `headbang__f1.5_a0.35` | headbang | test | f 1.5, a 0.35 | 3.3 |
| `headbang__f1.75_a0.3` | headbang | test (v9x) | f 1.75, a 0.3 | 3.3 |
| `headbang__f1.75_a0.4` | headbang | test (v9x) | f 1.75, a 0.4 | 4.4 |
| `headbang__f1_a0.4` | headbang | test | f 1, a 0.4 | 2.5 |
| `headbang__f2.25_a0.25` | headbang | test (v9x) | f 2.25, a 0.25 | 3.5 |
| `headbang__f2.25_a0.4` | headbang | test (v9x) | f 2.25, a 0.4 | 5.6 |
| `headbang__f2.5_a0.2` | headbang | test | f 2.5, a 0.2 | 3.1 |
| `headbang__f2.75_a0.25` | headbang | test (v9x) | f 2.75, a 0.25 | 4.2 |
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
| `twist__f0.6_a0.2` | twist | test (v9x) | f 0.6, a 0.2 | 0.9 |
| `twist__f0.75_a0.25` | twist | test | f 0.75, a 0.25 | 1.2 |
| `twist__f0.7_a0.175` | twist | test (v9x) | f 0.7, a 0.175 | 0.8 |
| `twist__f0.8_a0.3` | twist | test (v9x) | f 0.8, a 0.3 | 1.5 |
| `twist__f0.9_a0.15` | twist | test (v9x) | f 0.9, a 0.15 | 0.8 |
| `twist__f1.1_a0.25` | twist | test (v9x) | f 1.1, a 0.25 | 1.7 |
| `twist__f1.25_a0.15` | twist | test | f 1.25, a 0.15 | 1.2 |
| `twist__f1.2_a0.2` | twist | test (v9x) | f 1.2, a 0.2 | 1.5 |
| `twist__f1.4_a0.25` | twist | test (v9x) | f 1.4, a 0.25 | 2.2 |
| `twist__f1.5_a0.2` | twist | test | f 1.5, a 0.2 | 1.9 |
| `twist__f1_a0.3` | twist | test | f 1, a 0.3 | 1.9 |
