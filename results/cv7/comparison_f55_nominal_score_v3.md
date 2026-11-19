# Study cv7, 55% keep-fraction, test nominal, score_v3

56 test clips (30 bootstrap units: sources), 10 categories, metric `score_v3`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curated | 1.375 | 0.976 | 0.72 | 1.00 |
| full | 1.306 | 0.976 | 0.38 | 1.00 |
| kinematic | 1.329 | 0.994 | 0.13 | 1.00 |
| oracle | 1.174 | 0.986 | 0.24 | 1.00 |
| random | 1.414 | 0.940 | 1.14 | 1.00 |
| checked | 1.198 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 1.477 | 0.988 | 0.36 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.069 [-0.053, +0.199] | +0.01 | -0.04 | -0.21 | -0.05 | +0.56 | -0.05 | +0.31 | +0.04 | -0.11 | +0.55 |
| kinematic | +0.046 [-0.111, +0.242] | +0.03 | -0.01 | +0.40 | -0.06 | +0.48 | +0.01 | +0.36 | -0.56 | -0.47 | +0.64 |
| oracle | +0.201 [+0.074, +0.348] | -0.00 | +0.00 | -0.06 | +0.05 | +0.66 | +0.00 | +0.58 | +0.24 | +0.10 | +0.79 |
| random | -0.039 [-0.260, +0.141] | +0.01 | +0.02 | -1.22 | -0.04 | +0.19 | -0.01 | +0.31 | +0.40 | -0.12 | +0.23 |
| checked | +0.177 [+0.067, +0.313] | +0.02 | +0.01 | +0.12 | -0.01 | +0.57 | +0.02 | +0.39 | +0.15 | +0.02 | +0.82 |
| curatedscore_f55 | -0.102 [-0.226, +0.040] | +0.02 | +0.00 | +0.11 | -0.12 | +0.26 | -0.01 | -0.04 | -0.57 | -0.45 | -0.10 |

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
| full | 20 | +0.179 [-0.029, +0.447] |
| kinematic | 20 | +0.097 [-0.203, +0.455] |
| oracle | 20 | +0.352 [+0.119, +0.667] |
| random | 20 | +0.110 [-0.069, +0.330] |
| checked | 20 | +0.279 [+0.065, +0.568] |
| curatedscore_f55 | 20 | -0.119 [-0.299, +0.072] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | +0.007 [-0.136, +0.144] |
| kinematic | 36 | +0.018 [-0.160, +0.261] |
| oracle | 36 | +0.118 [-0.027, +0.271] |
| random | 36 | -0.121 [-0.451, +0.125] |
| checked | 36 | +0.120 [+0.009, +0.267] |
| curatedscore_f55 | 36 | -0.093 [-0.259, +0.099] |


## Per clip (e)

| clip | category | curated | full | kinematic | oracle | random | checked | curatedscore_f55 |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.56 | 0.57 | 0.53 | 0.56 | 0.55 | 0.53 | 0.53 |
| `bow__pitch12deg__slow` | bow | 0.57 | 0.58 | 0.54 | 0.56 | 0.57 | 0.53 | 0.55 |
| `bow__pitch20deg__fast` | bow | 0.56 | 0.53 | 0.53 | 0.56 | 0.55 | 0.55 | 0.54 |
| `bow__pitch20deg__slow` | bow | 0.55 | 0.53 | 0.51 | 0.55 | 0.53 | 0.53 | 0.52 |
| `bow__pitch22deg__fast` | bow | 0.56 | 0.53 | 0.54 | 0.58 | 0.57 | 0.57 | 0.55 |
| `bow__pitch22deg__slow` | bow | 0.55 | 0.53 | 0.52 | 0.55 | 0.53 | 0.54 | 0.52 |
| `crouch__depth0.30__fast` | crouch | 0.68 | 0.73 | 0.68 | 0.68 | 0.65 | 0.67 | 0.67 |
| `crouch__depth0.30__slow` | crouch | 0.68 | 0.71 | 0.69 | 0.67 | 0.66 | 0.66 | 0.68 |
| `crouch__depth0.40__fast` | crouch | 0.68 | 0.72 | 0.68 | 0.68 | 0.65 | 0.66 | 0.67 |
| `crouch__depth0.40__slow` | crouch | 0.67 | 0.72 | 0.68 | 0.67 | 0.65 | 0.66 | 0.68 |
| `crouch__depth0.70__fast` | crouch | 0.68 | 0.73 | 0.70 | 0.68 | 0.67 | 0.69 | 0.69 |
| `crouch__depth0.70__slow` | crouch | 0.69 | 0.73 | 0.70 | 0.68 | 0.66 | 0.69 | 0.68 |
| `head__look_tilt__fast` | head | 0.70 | 0.74 | 0.62 | 0.72 | 1.72 | 0.70 | 0.77 |
| `head__look_tilt__slow` | head | 0.70 | 0.77 | 0.78 | 0.74 | 1.70 | 0.71 | 0.80 |
| `head__nod_tilt__fast` | head | 2.44 | 2.79 | 1.59 | 2.61 | 3.34 | 2.33 | 1.93 |
| `head__nod_tilt__slow` | head | 2.36 | 3.24 | 0.90 | 2.32 | 3.42 | 1.73 | 1.90 |
| `head__shake__fast` | head | 0.79 | 0.76 | 0.76 | 0.89 | 3.04 | 0.83 | 0.92 |
| `head__shake__slow` | head | 0.76 | 0.71 | 0.72 | 0.83 | 1.87 | 0.73 | 0.80 |
| `march__lift0.02__gentle` | march | 0.74 | 0.78 | 0.84 | 0.75 | 0.87 | 0.78 | 0.76 |
| `march__lift0.02__normal` | march | 0.89 | 1.04 | 0.90 | 0.86 | 0.91 | 0.93 | 0.97 |
| `march__lift0.035__gentle` | march | 1.28 | 1.36 | 1.42 | 1.30 | 1.44 | 1.33 | 1.36 |
| `march__lift0.035__normal` | march | 1.92 | 1.81 | 1.88 | 1.69 | 1.71 | 1.79 | 2.20 |
| `march__lift0.03__gentle` | march | 1.03 | 1.09 | 1.16 | 1.03 | 1.22 | 1.06 | 1.08 |
| `march__lift0.03__normal` | march | 1.36 | 1.46 | 1.35 | 1.27 | 1.27 | 1.38 | 1.58 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 2.76 | 1.79 | 2.19 | 1.69 | 2.77 | 1.84 | 2.25 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 3.00 | 1.86 | 1.78 | 1.75 | 2.38 | 1.79 | 2.02 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 1.46 | 1.43 | 1.36 | 1.28 | 1.56 | 1.40 | 1.43 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 1.57 | 1.46 | 1.55 | 1.44 | 1.33 | 1.47 | 2.04 |
| `sway__amp0.015m__f0.5` | sway | 0.54 | 0.59 | 0.53 | 0.53 | 0.54 | 0.52 | 0.55 |
| `sway__amp0.015m__f1.0` | sway | 0.54 | 0.58 | 0.52 | 0.52 | 0.52 | 0.50 | 0.56 |
| `sway__amp0.01m__f0.5` | sway | 0.57 | 0.63 | 0.57 | 0.59 | 0.58 | 0.56 | 0.58 |
| `sway__amp0.01m__f1.0` | sway | 0.56 | 0.62 | 0.55 | 0.56 | 0.56 | 0.53 | 0.57 |
| `sway__amp0.025m__f0.5` | sway | 0.54 | 0.59 | 0.55 | 0.54 | 0.56 | 0.53 | 0.55 |
| `sway__amp0.025m__f1.0` | sway | 0.60 | 0.63 | 0.59 | 0.58 | 0.64 | 0.57 | 0.61 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 2.00 | 1.92 | 1.62 | 1.79 | 1.95 | 1.96 | 2.02 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 3.29 | 2.62 | 2.95 | 2.41 | 2.61 | 2.41 | 3.51 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 2.37 | 2.39 | 2.00 | 2.01 | 2.45 | 2.32 | 2.63 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 3.67 | 3.00 | 2.48 | 2.64 | 2.98 | 2.88 | 3.39 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 1.76 | 1.62 | 2.16 | 1.51 | 1.76 | 1.64 | 1.50 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 2.01 | 1.66 | 1.73 | 1.29 | 1.47 | 1.55 | 2.34 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 1.71 | 1.63 | 1.58 | 1.25 | 1.26 | 1.53 | 1.62 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 1.50 | 1.47 | 2.53 | 1.65 | 1.27 | 1.47 | 2.55 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 1.99 | 1.91 | 1.86 | 1.34 | 1.33 | 1.61 | 1.95 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 1.60 | 1.61 | 2.91 | 1.70 | 1.35 | 1.61 | 2.87 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 1.98 | 1.89 | 1.95 | 1.34 | 1.38 | 1.67 | 1.94 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 1.58 | 1.58 | 2.88 | 1.61 | 1.38 | 1.56 | 2.81 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.98 | 1.18 | 1.37 | 0.86 | 1.24 | 1.04 | 1.07 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 1.13 | 1.37 | 1.79 | 1.20 | 1.13 | 1.28 | 2.18 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.97 | 1.25 | 1.42 | 0.92 | 1.36 | 1.07 | 1.12 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 1.23 | 1.35 | 2.06 | 1.29 | 1.28 | 1.35 | 2.16 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 1.71 | 1.33 | 1.31 | 1.15 | 1.57 | 1.15 | 1.72 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 1.74 | 1.95 | 2.64 | 1.77 | 1.88 | 1.75 | 2.20 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 3.04 | 1.45 | 1.40 | 1.24 | 1.95 | 1.30 | 2.72 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 1.50 | 1.61 | 1.37 | 1.39 | 1.49 | 1.37 | 1.53 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 1.64 | 1.72 | 1.76 | 1.60 | 1.66 | 1.55 | 2.51 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 3.08 | 2.30 | 2.18 | 1.85 | 3.24 | 1.74 | 2.88 |
