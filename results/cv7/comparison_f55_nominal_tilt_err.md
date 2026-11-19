# Study cv7, 55% keep-fraction, test nominal, tilt_err

56 test clips (30 bootstrap units: sources), 10 categories, metric `tilt_err`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curated | 0.039 | 0.976 | 0.72 | 1.00 |
| full | 0.035 | 0.976 | 0.38 | 1.00 |
| kinematic | 0.030 | 0.994 | 0.13 | 1.00 |
| oracle | 0.032 | 0.986 | 0.24 | 1.00 |
| random | 0.048 | 0.940 | 1.14 | 1.00 |
| checked | 0.030 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 0.038 | 0.988 | 0.36 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.004 [-0.003, +0.011] | +0.00 | -0.00 | -0.01 | +0.00 | +0.03 | -0.00 | +0.01 | +0.00 | +0.00 | +0.03 |
| kinematic | +0.009 [+0.001, +0.021] | +0.00 | -0.00 | +0.04 | -0.00 | +0.02 | +0.00 | +0.01 | +0.00 | -0.00 | +0.03 |
| oracle | +0.007 [-0.001, +0.015] | +0.00 | -0.00 | -0.00 | +0.00 | +0.03 | +0.00 | +0.02 | +0.00 | +0.00 | +0.03 |
| random | -0.009 [-0.026, +0.003] | +0.00 | +0.00 | -0.10 | +0.01 | -0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| checked | +0.009 [+0.003, +0.019] | +0.00 | +0.00 | +0.02 | +0.00 | +0.03 | +0.00 | +0.01 | +0.00 | +0.00 | +0.03 |
| curatedscore_f55 | +0.001 [-0.006, +0.010] | +0.00 | -0.00 | +0.01 | -0.00 | +0.01 | -0.00 | -0.01 | -0.00 | -0.00 | +0.01 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.062 (bar: ≥ −0.05): **no**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 20 | +0.009 [+0.001, +0.021] |
| kinematic | 20 | +0.007 [-0.001, +0.019] |
| oracle | 20 | +0.012 [+0.004, +0.025] |
| random | 20 | +0.002 [-0.004, +0.010] |
| checked | 20 | +0.010 [+0.002, +0.023] |
| curatedscore_f55 | 20 | -0.001 [-0.009, +0.008] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | +0.001 [-0.010, +0.010] |
| kinematic | 36 | +0.010 [+0.000, +0.028] |
| oracle | 36 | +0.003 [-0.007, +0.014] |
| random | 36 | -0.016 [-0.042, +0.003] |
| checked | 36 | +0.009 [+0.001, +0.022] |
| curatedscore_f55 | 36 | +0.002 [-0.008, +0.015] |


## Per clip (e)

| clip | category | curated | full | kinematic | oracle | random | checked | curatedscore_f55 |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.03 | 0.03 | 0.02 | 0.03 | 0.03 | 0.02 | 0.02 |
| `bow__pitch12deg__slow` | bow | 0.03 | 0.03 | 0.02 | 0.03 | 0.03 | 0.02 | 0.02 |
| `bow__pitch20deg__fast` | bow | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `bow__pitch20deg__slow` | bow | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `bow__pitch22deg__fast` | bow | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `bow__pitch22deg__slow` | bow | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `crouch__depth0.30__fast` | crouch | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 |
| `crouch__depth0.30__slow` | crouch | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 |
| `crouch__depth0.40__fast` | crouch | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 |
| `crouch__depth0.40__slow` | crouch | 0.04 | 0.04 | 0.04 | 0.04 | 0.03 | 0.04 | 0.04 |
| `crouch__depth0.70__fast` | crouch | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 |
| `crouch__depth0.70__slow` | crouch | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 |
| `head__look_tilt__fast` | head | 0.04 | 0.04 | 0.03 | 0.04 | 0.12 | 0.04 | 0.04 |
| `head__look_tilt__slow` | head | 0.04 | 0.04 | 0.04 | 0.04 | 0.14 | 0.04 | 0.05 |
| `head__nod_tilt__fast` | head | 0.17 | 0.15 | 0.07 | 0.17 | 0.24 | 0.13 | 0.11 |
| `head__nod_tilt__slow` | head | 0.17 | 0.27 | 0.04 | 0.16 | 0.28 | 0.08 | 0.14 |
| `head__shake__fast` | head | 0.04 | 0.03 | 0.03 | 0.04 | 0.21 | 0.03 | 0.05 |
| `head__shake__slow` | head | 0.04 | 0.03 | 0.03 | 0.04 | 0.11 | 0.03 | 0.04 |
| `march__lift0.02__gentle` | march | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `march__lift0.02__normal` | march | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `march__lift0.035__gentle` | march | 0.04 | 0.04 | 0.04 | 0.04 | 0.03 | 0.04 | 0.04 |
| `march__lift0.035__normal` | march | 0.04 | 0.03 | 0.04 | 0.04 | 0.02 | 0.03 | 0.05 |
| `march__lift0.03__gentle` | march | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| `march__lift0.03__normal` | march | 0.03 | 0.03 | 0.03 | 0.03 | 0.02 | 0.03 | 0.04 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 0.10 | 0.04 | 0.07 | 0.04 | 0.12 | 0.04 | 0.08 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 0.09 | 0.03 | 0.03 | 0.03 | 0.08 | 0.03 | 0.04 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 0.03 | 0.03 | 0.03 | 0.03 | 0.04 | 0.03 | 0.03 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.03 |
| `sway__amp0.015m__f0.5` | sway | 0.02 | 0.03 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `sway__amp0.015m__f1.0` | sway | 0.02 | 0.03 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `sway__amp0.01m__f0.5` | sway | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| `sway__amp0.01m__f1.0` | sway | 0.03 | 0.03 | 0.02 | 0.03 | 0.02 | 0.02 | 0.03 |
| `sway__amp0.025m__f0.5` | sway | 0.02 | 0.03 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `sway__amp0.025m__f1.0` | sway | 0.02 | 0.03 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.04 | 0.03 | 0.03 | 0.02 | 0.03 | 0.03 | 0.04 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 0.04 | 0.04 | 0.04 | 0.03 | 0.05 | 0.03 | 0.07 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 0.06 | 0.05 | 0.04 | 0.03 | 0.07 | 0.04 | 0.07 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 0.07 | 0.04 | 0.04 | 0.03 | 0.04 | 0.04 | 0.06 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 0.02 | 0.02 | 0.04 | 0.02 | 0.03 | 0.02 | 0.03 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 0.03 | 0.02 | 0.02 | 0.03 | 0.02 | 0.02 | 0.04 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 0.03 | 0.02 | 0.02 | 0.03 | 0.02 | 0.02 | 0.03 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 0.03 | 0.02 | 0.03 | 0.03 | 0.02 | 0.03 | 0.03 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 0.03 | 0.02 | 0.02 | 0.03 | 0.02 | 0.03 | 0.03 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.03 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.03 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 0.03 | 0.02 | 0.02 | 0.02 | 0.03 | 0.02 | 0.03 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.02 | 0.02 | 0.03 | 0.02 | 0.02 | 0.02 | 0.03 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 0.08 | 0.03 | 0.02 | 0.02 | 0.06 | 0.02 | 0.04 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.03 | 0.02 | 0.03 | 0.02 | 0.03 | 0.02 | 0.04 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 0.10 | 0.04 | 0.05 | 0.03 | 0.10 | 0.03 | 0.08 |
