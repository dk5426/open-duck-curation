# Study cv7, 55% keep-fraction, test nominal, score

56 test clips (30 bootstrap units: sources), 10 categories, metric `score`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curated | 0.519 | 0.976 | 0.72 | 1.00 |
| full | 0.501 | 0.976 | 0.38 | 1.00 |
| kinematic | 0.461 | 0.994 | 0.13 | 1.00 |
| oracle | 0.451 | 0.986 | 0.24 | 1.00 |
| random | 0.624 | 0.940 | 1.14 | 1.00 |
| checked | 0.456 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 0.492 | 0.988 | 0.36 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.018 [-0.075, +0.085] | +0.01 | +0.01 | -0.29 | +0.01 | +0.29 | +0.00 | +0.08 | +0.01 | +0.00 | +0.22 |
| kinematic | +0.058 [-0.004, +0.163] | -0.02 | -0.00 | +0.25 | -0.01 | +0.21 | -0.01 | +0.09 | -0.02 | -0.03 | +0.21 |
| oracle | +0.068 [-0.006, +0.144] | -0.00 | +0.00 | -0.01 | +0.02 | +0.32 | -0.00 | +0.15 | +0.06 | +0.04 | +0.26 |
| random | -0.105 [-0.286, +0.023] | +0.01 | -0.00 | -1.12 | +0.02 | +0.03 | -0.00 | +0.03 | +0.04 | -0.01 | +0.08 |
| checked | +0.064 [+0.003, +0.142] | -0.01 | -0.00 | +0.08 | +0.01 | +0.29 | -0.01 | +0.12 | +0.03 | +0.02 | +0.24 |
| curatedscore_f55 | +0.027 [-0.040, +0.118] | +0.00 | +0.00 | +0.14 | -0.03 | +0.24 | +0.00 | -0.01 | -0.03 | -0.06 | +0.11 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.062 (bar: ≥ −0.05): **no**
- **pass: no**

## Leave-one-clip-out: curated minus each condition with each test clip dropped

| vs | Δe range | CI upper bound range | drops that flip the CI past 0 |
|---|---|---|---|
| full | +0.006 .. +0.037 | +0.064 .. +0.090 | none |
| kinematic | +0.038 .. +0.061 | +0.108 .. +0.168 | none |
| oracle | +0.057 .. +0.072 | +0.127 .. +0.149 | none |
| random | -0.111 .. -0.071 | +0.018 .. +0.029 | none |
| checked | +0.051 .. +0.067 | +0.112 .. +0.149 | none |
| curatedscore_f55 | +0.016 .. +0.030 | +0.087 .. +0.124 | none |

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 20 | +0.069 [+0.015, +0.152] |
| kinematic | 20 | +0.057 [-0.003, +0.147] |
| oracle | 20 | +0.102 [+0.039, +0.192] |
| random | 20 | +0.024 [-0.016, +0.080] |
| checked | 20 | +0.084 [+0.022, +0.174] |
| curatedscore_f55 | 20 | +0.010 [-0.039, +0.081] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | -0.010 [-0.149, +0.082] |
| kinematic | 36 | +0.059 [-0.024, +0.219] |
| oracle | 36 | +0.050 [-0.061, +0.160] |
| random | 36 | -0.176 [-0.457, +0.019] |
| checked | 36 | +0.052 [-0.031, +0.168] |
| curatedscore_f55 | 36 | +0.036 [-0.066, +0.168] |


## Per clip (e)

| clip | category | curated | full | kinematic | oracle | random | checked | curatedscore_f55 |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.17 | 0.17 | 0.19 | 0.17 | 0.17 | 0.19 | 0.18 |
| `bow__pitch12deg__slow` | bow | 0.17 | 0.17 | 0.19 | 0.17 | 0.16 | 0.18 | 0.17 |
| `bow__pitch20deg__fast` | bow | 0.22 | 0.20 | 0.24 | 0.23 | 0.21 | 0.23 | 0.22 |
| `bow__pitch20deg__slow` | bow | 0.20 | 0.19 | 0.21 | 0.20 | 0.19 | 0.21 | 0.20 |
| `bow__pitch22deg__fast` | bow | 0.23 | 0.21 | 0.24 | 0.23 | 0.22 | 0.24 | 0.22 |
| `bow__pitch22deg__slow` | bow | 0.21 | 0.20 | 0.22 | 0.22 | 0.20 | 0.22 | 0.21 |
| `crouch__depth0.30__fast` | crouch | 0.12 | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 |
| `crouch__depth0.30__slow` | crouch | 0.12 | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 |
| `crouch__depth0.40__fast` | crouch | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 |
| `crouch__depth0.40__slow` | crouch | 0.12 | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 |
| `crouch__depth0.70__fast` | crouch | 0.12 | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.70__slow` | crouch | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 |
| `head__look_tilt__fast` | head | 0.13 | 0.14 | 0.16 | 0.13 | 1.13 | 0.14 | 0.12 |
| `head__look_tilt__slow` | head | 0.12 | 0.13 | 0.13 | 0.12 | 1.13 | 0.13 | 0.11 |
| `head__nod_tilt__fast` | head | 1.41 | 1.91 | 0.93 | 1.55 | 2.47 | 1.47 | 0.97 |
| `head__nod_tilt__slow` | head | 1.50 | 2.52 | 0.33 | 1.38 | 2.59 | 0.76 | 1.13 |
| `head__shake__fast` | head | 0.23 | 0.32 | 0.29 | 0.25 | 2.20 | 0.33 | 0.22 |
| `head__shake__slow` | head | 0.16 | 0.26 | 0.19 | 0.19 | 0.78 | 0.27 | 0.16 |
| `march__lift0.02__gentle` | march | 0.42 | 0.43 | 0.45 | 0.38 | 0.46 | 0.42 | 0.42 |
| `march__lift0.02__normal` | march | 0.51 | 0.51 | 0.51 | 0.47 | 0.50 | 0.50 | 0.51 |
| `march__lift0.035__gentle` | march | 0.66 | 0.65 | 0.64 | 0.62 | 0.63 | 0.64 | 0.67 |
| `march__lift0.035__normal` | march | 0.82 | 0.79 | 0.84 | 0.84 | 0.77 | 0.81 | 0.93 |
| `march__lift0.03__gentle` | march | 0.56 | 0.56 | 0.56 | 0.52 | 0.56 | 0.55 | 0.56 |
| `march__lift0.03__normal` | march | 0.70 | 0.67 | 0.71 | 0.70 | 0.65 | 0.69 | 0.77 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 1.11 | 0.66 | 0.94 | 0.62 | 1.21 | 0.68 | 0.76 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 1.30 | 0.62 | 0.62 | 0.62 | 1.09 | 0.63 | 0.68 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 0.58 | 0.54 | 0.57 | 0.50 | 0.61 | 0.54 | 0.52 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.67 | 0.66 | 0.68 | 0.65 | 0.65 | 0.65 | 0.76 |
| `sway__amp0.015m__f0.5` | sway | 0.15 | 0.15 | 0.17 | 0.16 | 0.16 | 0.16 | 0.15 |
| `sway__amp0.015m__f1.0` | sway | 0.17 | 0.17 | 0.18 | 0.18 | 0.18 | 0.17 | 0.17 |
| `sway__amp0.01m__f0.5` | sway | 0.14 | 0.13 | 0.15 | 0.14 | 0.14 | 0.14 | 0.14 |
| `sway__amp0.01m__f1.0` | sway | 0.15 | 0.14 | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 |
| `sway__amp0.025m__f0.5` | sway | 0.20 | 0.21 | 0.21 | 0.21 | 0.21 | 0.21 | 0.20 |
| `sway__amp0.025m__f1.0` | sway | 0.26 | 0.25 | 0.26 | 0.26 | 0.26 | 0.26 | 0.25 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.63 | 0.60 | 0.55 | 0.54 | 0.63 | 0.55 | 0.61 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 0.87 | 0.84 | 0.80 | 0.76 | 0.89 | 0.78 | 0.99 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 0.81 | 0.72 | 0.68 | 0.63 | 0.84 | 0.67 | 0.75 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 1.16 | 0.93 | 0.94 | 0.86 | 0.95 | 0.91 | 1.11 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 0.58 | 0.50 | 0.59 | 0.46 | 0.58 | 0.47 | 0.57 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 0.68 | 0.63 | 0.63 | 0.59 | 0.63 | 0.62 | 0.74 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 0.49 | 0.47 | 0.46 | 0.41 | 0.46 | 0.45 | 0.45 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 0.65 | 0.65 | 0.72 | 0.63 | 0.62 | 0.64 | 0.74 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 0.52 | 0.49 | 0.48 | 0.43 | 0.48 | 0.46 | 0.48 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 0.69 | 0.70 | 0.77 | 0.65 | 0.66 | 0.68 | 0.80 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 0.52 | 0.49 | 0.48 | 0.42 | 0.47 | 0.46 | 0.47 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 0.68 | 0.70 | 0.77 | 0.65 | 0.66 | 0.67 | 0.79 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.41 | 0.43 | 0.46 | 0.38 | 0.46 | 0.41 | 0.41 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.60 | 0.60 | 0.63 | 0.56 | 0.59 | 0.59 | 0.69 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.43 | 0.45 | 0.48 | 0.41 | 0.47 | 0.43 | 0.43 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 0.63 | 0.64 | 0.66 | 0.60 | 0.63 | 0.62 | 0.73 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 0.62 | 0.59 | 0.60 | 0.54 | 0.63 | 0.56 | 0.63 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.83 | 0.82 | 0.86 | 0.78 | 0.84 | 0.79 | 0.97 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 0.92 | 0.59 | 0.55 | 0.53 | 0.70 | 0.55 | 0.64 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 0.54 | 0.52 | 0.53 | 0.49 | 0.55 | 0.51 | 0.56 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.84 | 0.80 | 0.83 | 0.78 | 0.83 | 0.80 | 0.95 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 1.11 | 0.63 | 0.65 | 0.58 | 1.00 | 0.60 | 0.81 |
