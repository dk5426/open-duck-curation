# Study cv7, 55% keep-fraction, test nominal, score_v2

56 test clips (30 bootstrap units: sources), 10 categories, metric `score_v2`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curated | 1.035 | 0.976 | 0.72 | 1.00 |
| full | 1.015 | 0.976 | 0.38 | 1.00 |
| kinematic | 1.037 | 0.994 | 0.13 | 1.00 |
| oracle | 0.885 | 0.986 | 0.24 | 1.00 |
| random | 1.084 | 0.940 | 1.14 | 1.00 |
| checked | 0.917 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 1.126 | 0.988 | 0.36 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.020 [-0.092, +0.124] | +0.01 | +0.00 | -0.27 | -0.09 | +0.34 | -0.00 | +0.23 | +0.01 | -0.14 | +0.30 |
| kinematic | -0.002 [-0.139, +0.161] | -0.01 | -0.00 | +0.27 | -0.05 | +0.31 | -0.01 | +0.32 | -0.59 | -0.46 | +0.44 |
| oracle | +0.149 [+0.045, +0.265] | -0.01 | +0.01 | -0.02 | +0.05 | +0.43 | +0.00 | +0.43 | +0.24 | +0.06 | +0.54 |
| random | -0.049 [-0.256, +0.117] | +0.00 | +0.00 | -1.17 | -0.09 | +0.20 | -0.01 | +0.30 | +0.36 | -0.12 | +0.20 |
| checked | +0.118 [+0.030, +0.223] | -0.02 | +0.00 | +0.08 | -0.02 | +0.36 | +0.00 | +0.30 | +0.12 | +0.01 | +0.57 |
| curatedscore_f55 | -0.091 [-0.204, +0.033] | +0.01 | +0.00 | +0.13 | -0.08 | +0.19 | -0.00 | +0.04 | -0.55 | -0.41 | -0.16 |

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
| full | 20 | +0.103 [-0.067, +0.313] |
| kinematic | 20 | +0.045 [-0.212, +0.343] |
| oracle | 20 | +0.246 [+0.071, +0.482] |
| random | 20 | +0.098 [-0.063, +0.293] |
| checked | 20 | +0.193 [+0.032, +0.408] |
| curatedscore_f55 | 20 | -0.100 [-0.261, +0.061] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | -0.027 [-0.165, +0.082] |
| kinematic | 36 | -0.028 [-0.185, +0.175] |
| oracle | 36 | +0.096 [-0.030, +0.221] |
| random | 36 | -0.131 [-0.437, +0.099] |
| checked | 36 | +0.075 [-0.018, +0.199] |
| curatedscore_f55 | 36 | -0.085 [-0.239, +0.083] |


## Per clip (e)

| clip | category | curated | full | kinematic | oracle | random | checked | curatedscore_f55 |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.31 | 0.30 | 0.31 | 0.31 | 0.30 | 0.32 | 0.30 |
| `bow__pitch12deg__slow` | bow | 0.30 | 0.30 | 0.31 | 0.31 | 0.31 | 0.31 | 0.30 |
| `bow__pitch20deg__fast` | bow | 0.34 | 0.32 | 0.34 | 0.35 | 0.34 | 0.36 | 0.33 |
| `bow__pitch20deg__slow` | bow | 0.33 | 0.32 | 0.33 | 0.33 | 0.32 | 0.34 | 0.32 |
| `bow__pitch22deg__fast` | bow | 0.34 | 0.33 | 0.35 | 0.36 | 0.35 | 0.37 | 0.34 |
| `bow__pitch22deg__slow` | bow | 0.33 | 0.34 | 0.34 | 0.34 | 0.33 | 0.35 | 0.33 |
| `crouch__depth0.30__fast` | crouch | 0.31 | 0.30 | 0.30 | 0.30 | 0.30 | 0.31 | 0.30 |
| `crouch__depth0.30__slow` | crouch | 0.30 | 0.30 | 0.31 | 0.30 | 0.30 | 0.30 | 0.30 |
| `crouch__depth0.40__fast` | crouch | 0.30 | 0.30 | 0.31 | 0.30 | 0.30 | 0.30 | 0.30 |
| `crouch__depth0.40__slow` | crouch | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 |
| `crouch__depth0.70__fast` | crouch | 0.30 | 0.30 | 0.30 | 0.29 | 0.30 | 0.30 | 0.30 |
| `crouch__depth0.70__slow` | crouch | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 |
| `head__look_tilt__fast` | head | 0.31 | 0.34 | 0.34 | 0.32 | 1.38 | 0.33 | 0.32 |
| `head__look_tilt__slow` | head | 0.31 | 0.33 | 0.34 | 0.31 | 1.33 | 0.32 | 0.32 |
| `head__nod_tilt__fast` | head | 1.71 | 2.18 | 1.17 | 1.87 | 2.80 | 1.72 | 1.29 |
| `head__nod_tilt__slow` | head | 1.75 | 2.72 | 0.55 | 1.65 | 2.86 | 1.06 | 1.37 |
| `head__shake__fast` | head | 0.44 | 0.50 | 0.47 | 0.46 | 2.45 | 0.51 | 0.44 |
| `head__shake__slow` | head | 0.35 | 0.41 | 0.38 | 0.39 | 1.07 | 0.44 | 0.36 |
| `march__lift0.02__gentle` | march | 0.56 | 0.61 | 0.66 | 0.56 | 0.70 | 0.57 | 0.59 |
| `march__lift0.02__normal` | march | 0.69 | 0.87 | 0.74 | 0.66 | 0.75 | 0.75 | 0.76 |
| `march__lift0.035__gentle` | march | 0.91 | 1.00 | 1.03 | 0.95 | 1.10 | 0.96 | 0.99 |
| `march__lift0.035__normal` | march | 1.53 | 1.51 | 1.45 | 1.29 | 1.47 | 1.45 | 1.66 |
| `march__lift0.03__gentle` | march | 0.75 | 0.82 | 0.87 | 0.76 | 0.96 | 0.78 | 0.81 |
| `march__lift0.03__normal` | march | 1.04 | 1.20 | 1.05 | 0.97 | 1.06 | 1.10 | 1.18 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 1.93 | 1.36 | 1.61 | 1.32 | 1.90 | 1.41 | 1.49 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 2.30 | 1.56 | 1.46 | 1.46 | 1.75 | 1.47 | 1.62 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 1.13 | 1.17 | 1.04 | 1.00 | 1.14 | 1.12 | 1.11 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 1.35 | 1.26 | 1.36 | 1.23 | 1.14 | 1.27 | 1.73 |
| `sway__amp0.015m__f0.5` | sway | 0.30 | 0.30 | 0.31 | 0.30 | 0.31 | 0.30 | 0.30 |
| `sway__amp0.015m__f1.0` | sway | 0.31 | 0.31 | 0.31 | 0.31 | 0.32 | 0.30 | 0.31 |
| `sway__amp0.01m__f0.5` | sway | 0.29 | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 |
| `sway__amp0.01m__f1.0` | sway | 0.30 | 0.30 | 0.30 | 0.30 | 0.31 | 0.29 | 0.30 |
| `sway__amp0.025m__f0.5` | sway | 0.32 | 0.33 | 0.33 | 0.32 | 0.33 | 0.32 | 0.32 |
| `sway__amp0.025m__f1.0` | sway | 0.37 | 0.37 | 0.37 | 0.36 | 0.39 | 0.36 | 0.37 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 1.64 | 1.66 | 1.34 | 1.56 | 1.62 | 1.66 | 1.63 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 2.85 | 2.22 | 2.51 | 2.13 | 2.14 | 2.07 | 2.89 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 1.84 | 1.93 | 1.58 | 1.70 | 1.79 | 1.92 | 1.90 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 3.09 | 2.62 | 2.07 | 2.38 | 2.60 | 2.51 | 2.80 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 1.52 | 1.41 | 1.72 | 1.29 | 1.44 | 1.41 | 1.25 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 1.72 | 1.43 | 1.51 | 1.03 | 1.23 | 1.31 | 1.95 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 1.51 | 1.45 | 1.40 | 1.08 | 1.09 | 1.36 | 1.44 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 1.23 | 1.24 | 2.30 | 1.37 | 1.05 | 1.23 | 2.24 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 1.79 | 1.72 | 1.67 | 1.14 | 1.15 | 1.43 | 1.77 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 1.31 | 1.36 | 2.66 | 1.41 | 1.11 | 1.35 | 2.54 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 1.77 | 1.71 | 1.76 | 1.14 | 1.21 | 1.50 | 1.76 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 1.29 | 1.34 | 2.63 | 1.33 | 1.14 | 1.31 | 2.48 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.80 | 1.00 | 1.16 | 0.68 | 1.02 | 0.81 | 0.88 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.94 | 1.17 | 1.55 | 1.02 | 0.96 | 1.09 | 1.85 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.79 | 1.08 | 1.21 | 0.73 | 1.15 | 0.85 | 0.93 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 1.04 | 1.15 | 1.81 | 1.12 | 1.10 | 1.16 | 1.85 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 1.36 | 1.15 | 1.09 | 0.96 | 1.31 | 0.95 | 1.44 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 1.51 | 1.71 | 2.36 | 1.57 | 1.63 | 1.52 | 1.91 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 2.33 | 1.20 | 1.16 | 1.02 | 1.38 | 1.07 | 2.32 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 1.26 | 1.40 | 1.13 | 1.16 | 1.27 | 1.14 | 1.28 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 1.39 | 1.50 | 1.51 | 1.37 | 1.41 | 1.31 | 2.14 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 2.27 | 1.94 | 1.68 | 1.54 | 2.37 | 1.42 | 2.13 |
