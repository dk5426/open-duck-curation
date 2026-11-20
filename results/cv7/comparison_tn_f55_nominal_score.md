# Study cv7, type-normalised curation at 55% (exploratory)

56 test clips (30 bootstrap units: sources), 10 categories, metric `score`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curatedtn | 0.469 | 0.983 | 0.29 | 1.00 |
| full | 0.501 | 0.976 | 0.38 | 1.00 |
| random | 0.624 | 0.940 | 1.14 | 1.00 |
| curated | 0.519 | 0.976 | 0.72 | 1.00 |
| oracle | 0.451 | 0.986 | 0.24 | 1.00 |
| kinematic | 0.461 | 0.994 | 0.13 | 1.00 |
| curatedstrat | 0.461 | 0.986 | 0.38 | 1.00 |

## curatedtn minus each other condition (paired over test clips; negative = curatedtn better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | -0.032 [-0.099, -0.005] | +0.01 | +0.00 | -0.19 | -0.01 | -0.02 | -0.00 | -0.05 | -0.00 | -0.03 | -0.03 |
| random | -0.155 [-0.321, -0.038] | +0.01 | -0.01 | -1.02 | +0.00 | -0.29 | -0.01 | -0.10 | +0.02 | -0.04 | -0.16 |
| curated | -0.050 [-0.122, +0.030] | -0.00 | -0.00 | +0.10 | -0.01 | -0.31 | -0.01 | -0.14 | -0.01 | -0.03 | -0.24 |
| oracle | +0.018 [-0.037, +0.083] | -0.01 | -0.00 | +0.09 | +0.01 | +0.00 | -0.01 | +0.01 | +0.05 | +0.02 | +0.01 |
| kinematic | +0.008 [-0.049, +0.120] | -0.02 | -0.01 | +0.35 | -0.02 | -0.10 | -0.02 | -0.05 | -0.03 | -0.05 | -0.03 |
| curatedstrat | +0.008 [-0.037, +0.077] | +0.02 | +0.01 | +0.17 | -0.01 | -0.05 | +0.00 | -0.03 | +0.05 | -0.01 | -0.11 |

## P.9 pass bar

- curatedtn beats full with the CI excluding 0: **yes**
- curatedtn beats random with the CI excluding 0: **yes**
- worst per-category completion drop vs full: +0.000 (bar: ≥ −0.05): **yes**
- **pass: yes**

## Leave-one-clip-out: curatedtn minus each condition with each test clip dropped

| vs | Δe range | CI upper bound range | drops that flip the CI past 0 |
|---|---|---|---|
| full | -0.034 .. -0.019 | -0.007 .. -0.003 | none |
| random | -0.159 .. -0.124 | -0.041 .. -0.029 | none |
| curated | -0.056 .. -0.039 | -0.001 .. +0.040 | `head__nod_tilt__slow` |
| oracle | +0.011 .. +0.019 | +0.046 .. +0.089 | none |
| kinematic | -0.018 .. +0.014 | +0.037 .. +0.127 | none |
| curatedstrat | -0.005 .. +0.015 | +0.028 .. +0.085 | none |

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 20 | -0.025 [-0.046, -0.007] |
| random | 20 | -0.069 [-0.131, -0.026] |
| curated | 20 | -0.093 [-0.185, -0.033] |
| oracle | 20 | +0.008 [-0.003, +0.020] |
| kinematic | 20 | -0.037 [-0.052, -0.021] |
| curatedstrat | 20 | -0.028 [-0.081, +0.001] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | -0.036 [-0.135, +0.002] |
| random | 36 | -0.203 [-0.460, -0.022] |
| curated | 36 | -0.027 [-0.127, +0.089] |
| oracle | 36 | +0.023 [-0.062, +0.123] |
| kinematic | 36 | +0.033 [-0.055, +0.205] |
| curatedstrat | 36 | +0.029 [-0.038, +0.131] |


## Per clip (e)

| clip | category | curatedtn | full | random | curated | oracle | kinematic | curatedstrat |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.17 | 0.17 | 0.17 | 0.17 | 0.17 | 0.19 | 0.15 |
| `bow__pitch12deg__slow` | bow | 0.17 | 0.17 | 0.16 | 0.17 | 0.17 | 0.19 | 0.15 |
| `bow__pitch20deg__fast` | bow | 0.22 | 0.20 | 0.21 | 0.22 | 0.23 | 0.24 | 0.20 |
| `bow__pitch20deg__slow` | bow | 0.20 | 0.19 | 0.19 | 0.20 | 0.20 | 0.21 | 0.18 |
| `bow__pitch22deg__fast` | bow | 0.22 | 0.21 | 0.22 | 0.23 | 0.23 | 0.24 | 0.21 |
| `bow__pitch22deg__slow` | bow | 0.21 | 0.20 | 0.20 | 0.21 | 0.22 | 0.22 | 0.20 |
| `crouch__depth0.30__fast` | crouch | 0.12 | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.30__slow` | crouch | 0.12 | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.40__fast` | crouch | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.40__slow` | crouch | 0.12 | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 | 0.11 |
| `crouch__depth0.70__fast` | crouch | 0.11 | 0.11 | 0.12 | 0.12 | 0.11 | 0.12 | 0.11 |
| `crouch__depth0.70__slow` | crouch | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.12 | 0.11 |
| `head__look_tilt__fast` | head | 0.12 | 0.14 | 1.13 | 0.13 | 0.13 | 0.16 | 0.12 |
| `head__look_tilt__slow` | head | 0.12 | 0.13 | 1.13 | 0.12 | 0.12 | 0.13 | 0.11 |
| `head__nod_tilt__fast` | head | 1.63 | 1.91 | 2.47 | 1.41 | 1.55 | 0.93 | 1.53 |
| `head__nod_tilt__slow` | head | 1.78 | 2.52 | 2.59 | 1.50 | 1.38 | 0.33 | 1.02 |
| `head__shake__fast` | head | 0.32 | 0.32 | 2.20 | 0.23 | 0.25 | 0.29 | 0.21 |
| `head__shake__slow` | head | 0.19 | 0.26 | 0.78 | 0.16 | 0.19 | 0.19 | 0.17 |
| `march__lift0.02__gentle` | march | 0.41 | 0.43 | 0.46 | 0.42 | 0.38 | 0.45 | 0.41 |
| `march__lift0.02__normal` | march | 0.50 | 0.51 | 0.50 | 0.51 | 0.47 | 0.51 | 0.49 |
| `march__lift0.035__gentle` | march | 0.63 | 0.65 | 0.63 | 0.66 | 0.62 | 0.64 | 0.65 |
| `march__lift0.035__normal` | march | 0.83 | 0.79 | 0.77 | 0.82 | 0.84 | 0.84 | 0.83 |
| `march__lift0.03__gentle` | march | 0.53 | 0.56 | 0.56 | 0.56 | 0.52 | 0.56 | 0.55 |
| `march__lift0.03__normal` | march | 0.70 | 0.67 | 0.65 | 0.70 | 0.70 | 0.71 | 0.70 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 0.63 | 0.66 | 1.21 | 1.11 | 0.62 | 0.94 | 0.74 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 0.62 | 0.62 | 1.09 | 1.30 | 0.62 | 0.62 | 0.67 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 0.51 | 0.54 | 0.61 | 0.58 | 0.50 | 0.57 | 0.52 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.65 | 0.66 | 0.65 | 0.67 | 0.65 | 0.68 | 0.66 |
| `sway__amp0.015m__f0.5` | sway | 0.15 | 0.15 | 0.16 | 0.15 | 0.16 | 0.17 | 0.14 |
| `sway__amp0.015m__f1.0` | sway | 0.16 | 0.17 | 0.18 | 0.17 | 0.18 | 0.18 | 0.16 |
| `sway__amp0.01m__f0.5` | sway | 0.13 | 0.13 | 0.14 | 0.14 | 0.14 | 0.15 | 0.13 |
| `sway__amp0.01m__f1.0` | sway | 0.14 | 0.14 | 0.15 | 0.15 | 0.15 | 0.15 | 0.14 |
| `sway__amp0.025m__f0.5` | sway | 0.20 | 0.21 | 0.21 | 0.20 | 0.21 | 0.21 | 0.20 |
| `sway__amp0.025m__f1.0` | sway | 0.25 | 0.25 | 0.26 | 0.26 | 0.26 | 0.26 | 0.25 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.55 | 0.60 | 0.63 | 0.63 | 0.54 | 0.55 | 0.55 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 0.75 | 0.84 | 0.89 | 0.87 | 0.76 | 0.80 | 0.80 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 0.64 | 0.72 | 0.84 | 0.81 | 0.63 | 0.68 | 0.66 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 0.88 | 0.93 | 0.95 | 1.16 | 0.86 | 0.94 | 0.89 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 0.48 | 0.50 | 0.58 | 0.58 | 0.46 | 0.59 | 0.57 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 0.62 | 0.63 | 0.63 | 0.68 | 0.59 | 0.63 | 0.64 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 0.48 | 0.47 | 0.46 | 0.49 | 0.41 | 0.46 | 0.42 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 0.64 | 0.65 | 0.62 | 0.65 | 0.63 | 0.72 | 0.62 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 0.51 | 0.49 | 0.48 | 0.52 | 0.43 | 0.48 | 0.43 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 0.67 | 0.70 | 0.66 | 0.69 | 0.65 | 0.77 | 0.65 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 0.50 | 0.49 | 0.47 | 0.52 | 0.42 | 0.48 | 0.43 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 0.67 | 0.70 | 0.66 | 0.68 | 0.65 | 0.77 | 0.65 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.41 | 0.43 | 0.46 | 0.41 | 0.38 | 0.46 | 0.41 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.58 | 0.60 | 0.59 | 0.60 | 0.56 | 0.63 | 0.58 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.42 | 0.45 | 0.47 | 0.43 | 0.41 | 0.48 | 0.42 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 0.61 | 0.64 | 0.63 | 0.63 | 0.60 | 0.66 | 0.62 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 0.55 | 0.59 | 0.63 | 0.62 | 0.54 | 0.60 | 0.57 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.79 | 0.82 | 0.84 | 0.83 | 0.78 | 0.86 | 0.81 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 0.55 | 0.59 | 0.70 | 0.92 | 0.53 | 0.55 | 0.58 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 0.50 | 0.52 | 0.55 | 0.54 | 0.49 | 0.53 | 0.54 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.79 | 0.80 | 0.83 | 0.84 | 0.78 | 0.83 | 0.84 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 0.60 | 0.63 | 1.00 | 1.11 | 0.58 | 0.65 | 0.95 |
