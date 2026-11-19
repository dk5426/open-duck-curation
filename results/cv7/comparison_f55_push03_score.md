# Study cv7, 55% keep-fraction, test push03, score

56 test clips (30 bootstrap units: sources), 10 categories, metric `score`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curated | 0.729 | 0.900 | 2.48 | 1.00 |
| full | 0.693 | 0.909 | 1.92 | 1.00 |
| kinematic | 0.665 | 0.922 | 1.85 | 1.00 |
| oracle | 0.665 | 0.912 | 2.01 | 1.00 |
| random | 0.820 | 0.870 | 2.76 | 1.00 |
| checked | 0.647 | 0.926 | 1.71 | 1.00 |
| curatedscore_f55 | 0.711 | 0.910 | 2.20 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.036 [-0.059, +0.108] | +0.02 | -0.01 | -0.24 | +0.00 | +0.27 | +0.00 | +0.16 | +0.06 | +0.03 | +0.20 |
| kinematic | +0.064 [-0.002, +0.165] | -0.01 | -0.02 | +0.26 | -0.04 | +0.20 | +0.02 | +0.17 | -0.04 | -0.02 | +0.20 |
| oracle | +0.064 [-0.011, +0.141] | -0.01 | -0.01 | -0.00 | +0.03 | +0.31 | +0.01 | +0.17 | -0.01 | +0.05 | +0.23 |
| random | -0.091 [-0.254, +0.029] | +0.01 | +0.00 | -1.01 | +0.04 | +0.01 | -0.02 | +0.07 | +0.01 | -0.01 | +0.06 |
| checked | +0.082 [+0.021, +0.158] | -0.00 | -0.02 | +0.09 | +0.06 | +0.25 | +0.02 | +0.21 | +0.04 | +0.04 | +0.25 |
| curatedscore_f55 | +0.018 [-0.050, +0.106] | +0.00 | -0.01 | +0.13 | -0.09 | +0.16 | +0.02 | +0.03 | -0.02 | -0.05 | +0.07 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.070 (bar: ≥ −0.05): **no**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 20 | +0.099 [+0.027, +0.194] |
| kinematic | 20 | +0.081 [+0.008, +0.174] |
| oracle | 20 | +0.106 [+0.037, +0.195] |
| random | 20 | +0.038 [-0.024, +0.111] |
| checked | 20 | +0.120 [+0.040, +0.216] |
| curatedscore_f55 | 20 | +0.022 [-0.041, +0.098] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | +0.001 [-0.136, +0.097] |
| kinematic | 36 | +0.054 [-0.036, +0.208] |
| oracle | 36 | +0.041 [-0.069, +0.152] |
| random | 36 | -0.163 [-0.414, +0.013] |
| checked | 36 | +0.061 [-0.018, +0.164] |
| curatedscore_f55 | 36 | +0.016 [-0.085, +0.146] |


## Per clip (e)

| clip | category | curated | full | kinematic | oracle | random | checked | curatedscore_f55 |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.57 | 0.56 | 0.59 | 0.58 | 0.56 | 0.58 | 0.57 |
| `bow__pitch12deg__slow` | bow | 0.32 | 0.31 | 0.34 | 0.32 | 0.31 | 0.33 | 0.32 |
| `bow__pitch20deg__fast` | bow | 0.36 | 0.34 | 0.37 | 0.36 | 0.35 | 0.37 | 0.35 |
| `bow__pitch20deg__slow` | bow | 0.45 | 0.44 | 0.46 | 0.46 | 0.44 | 0.46 | 0.45 |
| `bow__pitch22deg__fast` | bow | 0.61 | 0.60 | 0.63 | 0.62 | 0.60 | 0.63 | 0.61 |
| `bow__pitch22deg__slow` | bow | 0.60 | 0.58 | 0.61 | 0.61 | 0.59 | 0.57 | 0.60 |
| `crouch__depth0.30__fast` | crouch | 0.40 | 0.43 | 0.43 | 0.43 | 0.41 | 0.44 | 0.43 |
| `crouch__depth0.30__slow` | crouch | 0.53 | 0.52 | 0.57 | 0.56 | 0.52 | 0.53 | 0.53 |
| `crouch__depth0.40__fast` | crouch | 0.40 | 0.40 | 0.43 | 0.40 | 0.40 | 0.48 | 0.43 |
| `crouch__depth0.40__slow` | crouch | 0.39 | 0.39 | 0.39 | 0.39 | 0.39 | 0.40 | 0.39 |
| `crouch__depth0.70__fast` | crouch | 0.37 | 0.37 | 0.37 | 0.37 | 0.37 | 0.38 | 0.37 |
| `crouch__depth0.70__slow` | crouch | 0.53 | 0.54 | 0.54 | 0.53 | 0.54 | 0.54 | 0.53 |
| `head__look_tilt__fast` | head | 0.68 | 0.69 | 0.68 | 0.67 | 1.47 | 0.68 | 0.68 |
| `head__look_tilt__slow` | head | 0.38 | 0.44 | 0.40 | 0.39 | 1.30 | 0.39 | 0.39 |
| `head__nod_tilt__fast` | head | 1.42 | 1.89 | 0.98 | 1.53 | 2.43 | 1.52 | 1.02 |
| `head__nod_tilt__slow` | head | 1.47 | 2.51 | 0.37 | 1.37 | 2.59 | 0.77 | 1.12 |
| `head__shake__fast` | head | 0.35 | 0.49 | 0.47 | 0.47 | 2.19 | 0.45 | 0.43 |
| `head__shake__slow` | head | 0.53 | 0.27 | 0.37 | 0.40 | 0.88 | 0.47 | 0.41 |
| `march__lift0.02__gentle` | march | 0.72 | 0.59 | 0.70 | 0.60 | 0.57 | 0.60 | 0.74 |
| `march__lift0.02__normal` | march | 0.66 | 0.64 | 0.78 | 0.61 | 0.61 | 0.57 | 0.64 |
| `march__lift0.035__gentle` | march | 0.77 | 0.78 | 0.82 | 0.77 | 0.76 | 0.73 | 0.91 |
| `march__lift0.035__normal` | march | 0.83 | 0.83 | 0.87 | 0.87 | 0.81 | 0.81 | 1.03 |
| `march__lift0.03__gentle` | march | 0.73 | 0.86 | 0.75 | 0.63 | 0.76 | 0.67 | 0.84 |
| `march__lift0.03__normal` | march | 0.71 | 0.71 | 0.77 | 0.74 | 0.66 | 0.70 | 0.78 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 1.24 | 0.95 | 1.18 | 0.93 | 1.41 | 1.01 | 1.04 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 1.45 | 0.68 | 0.69 | 0.63 | 1.11 | 0.75 | 0.94 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 0.60 | 0.57 | 0.61 | 0.51 | 0.74 | 0.55 | 0.58 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.67 | 0.67 | 0.69 | 0.65 | 0.65 | 0.66 | 0.77 |
| `sway__amp0.015m__f0.5` | sway | 0.84 | 0.85 | 0.83 | 0.85 | 0.85 | 0.85 | 0.85 |
| `sway__amp0.015m__f1.0` | sway | 0.65 | 0.62 | 0.60 | 0.60 | 0.66 | 0.59 | 0.59 |
| `sway__amp0.01m__f0.5` | sway | 0.28 | 0.28 | 0.28 | 0.27 | 0.28 | 0.28 | 0.28 |
| `sway__amp0.01m__f1.0` | sway | 0.57 | 0.57 | 0.57 | 0.56 | 0.57 | 0.57 | 0.56 |
| `sway__amp0.025m__f0.5` | sway | 1.10 | 1.15 | 1.06 | 1.08 | 1.13 | 1.03 | 1.10 |
| `sway__amp0.025m__f1.0` | sway | 0.85 | 0.82 | 0.83 | 0.85 | 0.91 | 0.82 | 0.82 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.83 | 0.79 | 0.60 | 0.60 | 0.84 | 0.57 | 0.71 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 0.96 | 0.85 | 0.81 | 0.87 | 1.00 | 0.79 | 1.03 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 1.13 | 0.92 | 0.94 | 0.91 | 1.08 | 0.95 | 0.99 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 1.33 | 0.94 | 1.08 | 1.08 | 1.12 | 0.97 | 1.29 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 0.77 | 0.67 | 0.65 | 0.65 | 0.65 | 0.56 | 0.83 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 0.77 | 0.63 | 0.64 | 0.64 | 0.63 | 0.69 | 0.76 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 0.65 | 0.58 | 0.60 | 0.62 | 0.69 | 0.65 | 0.58 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 0.72 | 0.69 | 0.84 | 0.67 | 0.63 | 0.68 | 0.75 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 0.57 | 0.50 | 0.49 | 0.46 | 0.48 | 0.47 | 0.52 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 0.90 | 0.82 | 1.01 | 0.95 | 0.94 | 0.93 | 0.94 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 0.80 | 0.66 | 0.72 | 0.95 | 0.83 | 0.67 | 0.78 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 0.80 | 0.84 | 1.01 | 0.87 | 0.83 | 0.82 | 0.96 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.45 | 0.47 | 0.56 | 0.40 | 0.49 | 0.42 | 0.46 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.71 | 0.69 | 0.74 | 0.76 | 0.72 | 0.71 | 0.73 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.45 | 0.46 | 0.49 | 0.42 | 0.49 | 0.44 | 0.45 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 0.64 | 0.64 | 0.67 | 0.61 | 0.63 | 0.62 | 0.74 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 0.74 | 0.62 | 0.62 | 0.59 | 0.69 | 0.58 | 0.74 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.97 | 0.92 | 0.97 | 0.87 | 1.01 | 0.92 | 1.11 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 0.94 | 0.61 | 0.62 | 0.58 | 0.69 | 0.57 | 0.66 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 0.69 | 0.68 | 0.63 | 0.63 | 0.69 | 0.60 | 0.68 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.85 | 0.84 | 0.84 | 0.81 | 0.93 | 0.83 | 1.14 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 1.11 | 0.66 | 0.70 | 0.65 | 1.03 | 0.61 | 0.85 |
