# Study cv7, 55% keep-fraction, test fric06, score

56 test clips (30 bootstrap units: sources), 10 categories, metric `score`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curated | 0.512 | 0.979 | 0.65 | 1.00 |
| full | 0.500 | 0.976 | 0.37 | 1.00 |
| kinematic | 0.459 | 0.995 | 0.12 | 1.00 |
| oracle | 0.448 | 0.988 | 0.21 | 1.00 |
| random | 0.618 | 0.941 | 1.07 | 1.00 |
| checked | 0.456 | 0.992 | 0.17 | 1.00 |
| curatedscore_f55 | 0.485 | 0.990 | 0.23 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.012 [-0.083, +0.079] | +0.01 | +0.00 | -0.31 | +0.01 | +0.29 | +0.00 | +0.07 | +0.00 | +0.00 | +0.20 |
| kinematic | +0.053 [-0.005, +0.152] | -0.02 | -0.00 | +0.23 | -0.00 | +0.20 | -0.01 | +0.07 | -0.02 | -0.03 | +0.20 |
| oracle | +0.064 [-0.008, +0.137] | -0.00 | +0.00 | -0.00 | +0.02 | +0.31 | -0.00 | +0.13 | +0.05 | +0.04 | +0.24 |
| random | -0.106 [-0.286, +0.021] | +0.01 | -0.00 | -1.12 | +0.02 | +0.02 | -0.00 | +0.03 | +0.03 | -0.01 | +0.09 |
| checked | +0.056 [-0.002, +0.130] | -0.01 | -0.00 | +0.05 | +0.01 | +0.28 | -0.01 | +0.10 | +0.03 | +0.02 | +0.22 |
| curatedscore_f55 | +0.027 [-0.040, +0.118] | +0.00 | +0.00 | +0.14 | -0.03 | +0.25 | +0.00 | -0.01 | -0.03 | -0.06 | +0.11 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.057 (bar: ≥ −0.05): **no**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 20 | +0.062 [+0.014, +0.137] |
| kinematic | 20 | +0.050 [-0.004, +0.131] |
| oracle | 20 | +0.091 [+0.035, +0.171] |
| random | 20 | +0.022 [-0.013, +0.072] |
| checked | 20 | +0.075 [+0.020, +0.156] |
| curatedscore_f55 | 20 | +0.007 [-0.037, +0.071] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | -0.015 [-0.157, +0.080] |
| kinematic | 36 | +0.055 [-0.026, +0.203] |
| oracle | 36 | +0.049 [-0.058, +0.158] |
| random | 36 | -0.178 [-0.456, +0.017] |
| checked | 36 | +0.046 [-0.035, +0.156] |
| curatedscore_f55 | 36 | +0.038 [-0.064, +0.171] |


## Per clip (e)

| clip | category | curated | full | kinematic | oracle | random | checked | curatedscore_f55 |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.17 | 0.16 | 0.19 | 0.17 | 0.17 | 0.19 | 0.17 |
| `bow__pitch12deg__slow` | bow | 0.17 | 0.16 | 0.19 | 0.17 | 0.16 | 0.18 | 0.17 |
| `bow__pitch20deg__fast` | bow | 0.21 | 0.20 | 0.23 | 0.22 | 0.21 | 0.23 | 0.21 |
| `bow__pitch20deg__slow` | bow | 0.19 | 0.19 | 0.20 | 0.20 | 0.18 | 0.21 | 0.19 |
| `bow__pitch22deg__fast` | bow | 0.22 | 0.21 | 0.24 | 0.23 | 0.22 | 0.24 | 0.22 |
| `bow__pitch22deg__slow` | bow | 0.21 | 0.20 | 0.22 | 0.21 | 0.19 | 0.22 | 0.20 |
| `crouch__depth0.30__fast` | crouch | 0.12 | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.30__slow` | crouch | 0.12 | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.40__fast` | crouch | 0.12 | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.40__slow` | crouch | 0.12 | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.70__fast` | crouch | 0.11 | 0.11 | 0.11 | 0.11 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.70__slow` | crouch | 0.11 | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 | 0.11 |
| `head__look_tilt__fast` | head | 0.13 | 0.14 | 0.16 | 0.13 | 1.12 | 0.14 | 0.11 |
| `head__look_tilt__slow` | head | 0.12 | 0.13 | 0.13 | 0.12 | 1.12 | 0.13 | 0.11 |
| `head__nod_tilt__fast` | head | 1.45 | 1.88 | 0.91 | 1.55 | 2.46 | 1.46 | 0.91 |
| `head__nod_tilt__slow` | head | 1.29 | 2.51 | 0.33 | 1.14 | 2.57 | 0.75 | 1.02 |
| `head__shake__fast` | head | 0.24 | 0.32 | 0.29 | 0.25 | 2.13 | 0.34 | 0.22 |
| `head__shake__slow` | head | 0.16 | 0.26 | 0.20 | 0.19 | 0.71 | 0.27 | 0.16 |
| `march__lift0.02__gentle` | march | 0.43 | 0.44 | 0.45 | 0.39 | 0.46 | 0.42 | 0.42 |
| `march__lift0.02__normal` | march | 0.51 | 0.51 | 0.51 | 0.47 | 0.50 | 0.50 | 0.51 |
| `march__lift0.035__gentle` | march | 0.66 | 0.66 | 0.64 | 0.63 | 0.63 | 0.65 | 0.68 |
| `march__lift0.035__normal` | march | 0.82 | 0.79 | 0.84 | 0.84 | 0.77 | 0.81 | 0.93 |
| `march__lift0.03__gentle` | march | 0.56 | 0.56 | 0.56 | 0.53 | 0.56 | 0.55 | 0.56 |
| `march__lift0.03__normal` | march | 0.71 | 0.68 | 0.71 | 0.70 | 0.66 | 0.69 | 0.77 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 1.07 | 0.65 | 0.93 | 0.61 | 1.23 | 0.68 | 0.69 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 1.31 | 0.62 | 0.62 | 0.62 | 1.06 | 0.63 | 0.67 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 0.57 | 0.54 | 0.57 | 0.50 | 0.60 | 0.54 | 0.50 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.67 | 0.67 | 0.68 | 0.65 | 0.65 | 0.65 | 0.76 |
| `sway__amp0.015m__f0.5` | sway | 0.15 | 0.15 | 0.16 | 0.15 | 0.15 | 0.16 | 0.15 |
| `sway__amp0.015m__f1.0` | sway | 0.16 | 0.16 | 0.17 | 0.17 | 0.17 | 0.17 | 0.17 |
| `sway__amp0.01m__f0.5` | sway | 0.14 | 0.13 | 0.14 | 0.14 | 0.14 | 0.14 | 0.14 |
| `sway__amp0.01m__f1.0` | sway | 0.14 | 0.14 | 0.15 | 0.14 | 0.15 | 0.15 | 0.14 |
| `sway__amp0.025m__f0.5` | sway | 0.20 | 0.20 | 0.21 | 0.21 | 0.21 | 0.21 | 0.20 |
| `sway__amp0.025m__f1.0` | sway | 0.26 | 0.25 | 0.26 | 0.26 | 0.26 | 0.26 | 0.25 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.62 | 0.59 | 0.55 | 0.54 | 0.62 | 0.55 | 0.60 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 0.87 | 0.83 | 0.81 | 0.77 | 0.88 | 0.78 | 0.99 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 0.78 | 0.71 | 0.66 | 0.60 | 0.80 | 0.66 | 0.72 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 1.09 | 0.92 | 0.95 | 0.86 | 0.94 | 0.91 | 1.08 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 0.57 | 0.50 | 0.59 | 0.46 | 0.59 | 0.47 | 0.56 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 0.68 | 0.63 | 0.64 | 0.60 | 0.63 | 0.62 | 0.74 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 0.49 | 0.47 | 0.46 | 0.42 | 0.46 | 0.45 | 0.45 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 0.66 | 0.67 | 0.72 | 0.65 | 0.63 | 0.66 | 0.75 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 0.52 | 0.50 | 0.48 | 0.44 | 0.49 | 0.47 | 0.48 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 0.70 | 0.71 | 0.77 | 0.67 | 0.67 | 0.69 | 0.80 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 0.51 | 0.49 | 0.48 | 0.44 | 0.48 | 0.47 | 0.48 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 0.70 | 0.71 | 0.78 | 0.67 | 0.67 | 0.69 | 0.79 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.42 | 0.44 | 0.46 | 0.40 | 0.46 | 0.41 | 0.41 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.60 | 0.60 | 0.63 | 0.57 | 0.59 | 0.59 | 0.69 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.44 | 0.45 | 0.48 | 0.42 | 0.47 | 0.44 | 0.44 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 0.63 | 0.63 | 0.66 | 0.60 | 0.62 | 0.62 | 0.74 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 0.63 | 0.59 | 0.60 | 0.54 | 0.62 | 0.57 | 0.63 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.83 | 0.81 | 0.86 | 0.78 | 0.84 | 0.79 | 0.97 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 0.87 | 0.59 | 0.55 | 0.54 | 0.69 | 0.55 | 0.64 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 0.54 | 0.52 | 0.53 | 0.49 | 0.55 | 0.51 | 0.55 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.83 | 0.80 | 0.82 | 0.77 | 0.83 | 0.80 | 0.94 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 1.09 | 0.62 | 0.63 | 0.59 | 0.93 | 0.59 | 0.77 |
