# Study cv7, stratified curation at 55%

56 test clips (30 bootstrap units: sources), 10 categories, metric `score`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curatedstrat | 0.461 | 0.986 | 0.38 | 1.00 |
| curated | 0.519 | 0.976 | 0.72 | 1.00 |
| full | 0.501 | 0.976 | 0.38 | 1.00 |
| oracle | 0.451 | 0.986 | 0.24 | 1.00 |
| kinematic | 0.461 | 0.994 | 0.13 | 1.00 |

## curatedstrat minus each other condition (paired over test clips; negative = curatedstrat better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| curated | -0.059 [-0.127, -0.003] | -0.02 | -0.01 | -0.07 | -0.01 | -0.27 | -0.01 | -0.10 | -0.06 | -0.02 | -0.13 |
| full | -0.041 [-0.127, +0.007] | -0.01 | -0.00 | -0.35 | +0.00 | +0.03 | -0.01 | -0.02 | -0.05 | -0.02 | +0.09 |
| oracle | +0.009 [-0.053, +0.059] | -0.02 | -0.01 | -0.08 | +0.02 | +0.05 | -0.01 | +0.05 | -0.00 | +0.02 | +0.13 |
| kinematic | -0.000 [-0.046, +0.075] | -0.03 | -0.01 | +0.19 | -0.01 | -0.05 | -0.02 | -0.01 | -0.08 | -0.04 | +0.08 |

## P.9 pass bar

- curatedstrat beats full with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.022 (bar: ≥ −0.05): **yes**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| curated | 20 | -0.065 [-0.135, -0.017] |
| full | 20 | +0.004 [-0.027, +0.056] |
| oracle | 20 | +0.037 [+0.005, +0.090] |
| kinematic | 20 | -0.008 [-0.036, +0.042] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| curated | 36 | -0.055 [-0.156, +0.031] |
| full | 36 | -0.065 [-0.196, -0.001] |
| oracle | 36 | -0.006 [-0.097, +0.071] |
| kinematic | 36 | +0.004 [-0.062, +0.119] |


## Per clip (e)

| clip | category | curatedstrat | curated | full | oracle | kinematic |
|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.15 | 0.17 | 0.17 | 0.17 | 0.19 |
| `bow__pitch12deg__slow` | bow | 0.15 | 0.17 | 0.17 | 0.17 | 0.19 |
| `bow__pitch20deg__fast` | bow | 0.20 | 0.22 | 0.20 | 0.23 | 0.24 |
| `bow__pitch20deg__slow` | bow | 0.18 | 0.20 | 0.19 | 0.20 | 0.21 |
| `bow__pitch22deg__fast` | bow | 0.21 | 0.23 | 0.21 | 0.23 | 0.24 |
| `bow__pitch22deg__slow` | bow | 0.20 | 0.21 | 0.20 | 0.22 | 0.22 |
| `crouch__depth0.30__fast` | crouch | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 |
| `crouch__depth0.30__slow` | crouch | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 |
| `crouch__depth0.40__fast` | crouch | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 |
| `crouch__depth0.40__slow` | crouch | 0.11 | 0.12 | 0.11 | 0.12 | 0.12 |
| `crouch__depth0.70__fast` | crouch | 0.11 | 0.12 | 0.11 | 0.11 | 0.12 |
| `crouch__depth0.70__slow` | crouch | 0.11 | 0.12 | 0.12 | 0.12 | 0.12 |
| `head__look_tilt__fast` | head | 0.12 | 0.13 | 0.14 | 0.13 | 0.16 |
| `head__look_tilt__slow` | head | 0.11 | 0.12 | 0.13 | 0.12 | 0.13 |
| `head__nod_tilt__fast` | head | 1.53 | 1.41 | 1.91 | 1.55 | 0.93 |
| `head__nod_tilt__slow` | head | 1.02 | 1.50 | 2.52 | 1.38 | 0.33 |
| `head__shake__fast` | head | 0.21 | 0.23 | 0.32 | 0.25 | 0.29 |
| `head__shake__slow` | head | 0.17 | 0.16 | 0.26 | 0.19 | 0.19 |
| `march__lift0.02__gentle` | march | 0.41 | 0.42 | 0.43 | 0.38 | 0.45 |
| `march__lift0.02__normal` | march | 0.49 | 0.51 | 0.51 | 0.47 | 0.51 |
| `march__lift0.035__gentle` | march | 0.65 | 0.66 | 0.65 | 0.62 | 0.64 |
| `march__lift0.035__normal` | march | 0.83 | 0.82 | 0.79 | 0.84 | 0.84 |
| `march__lift0.03__gentle` | march | 0.55 | 0.56 | 0.56 | 0.52 | 0.56 |
| `march__lift0.03__normal` | march | 0.70 | 0.70 | 0.67 | 0.70 | 0.71 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 0.74 | 1.11 | 0.66 | 0.62 | 0.94 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 0.67 | 1.30 | 0.62 | 0.62 | 0.62 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 0.52 | 0.58 | 0.54 | 0.50 | 0.57 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.66 | 0.67 | 0.66 | 0.65 | 0.68 |
| `sway__amp0.015m__f0.5` | sway | 0.14 | 0.15 | 0.15 | 0.16 | 0.17 |
| `sway__amp0.015m__f1.0` | sway | 0.16 | 0.17 | 0.17 | 0.18 | 0.18 |
| `sway__amp0.01m__f0.5` | sway | 0.13 | 0.14 | 0.13 | 0.14 | 0.15 |
| `sway__amp0.01m__f1.0` | sway | 0.14 | 0.15 | 0.14 | 0.15 | 0.15 |
| `sway__amp0.025m__f0.5` | sway | 0.20 | 0.20 | 0.21 | 0.21 | 0.21 |
| `sway__amp0.025m__f1.0` | sway | 0.25 | 0.26 | 0.25 | 0.26 | 0.26 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.55 | 0.63 | 0.60 | 0.54 | 0.55 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 0.80 | 0.87 | 0.84 | 0.76 | 0.80 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 0.66 | 0.81 | 0.72 | 0.63 | 0.68 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 0.89 | 1.16 | 0.93 | 0.86 | 0.94 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 0.57 | 0.58 | 0.50 | 0.46 | 0.59 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 0.64 | 0.68 | 0.63 | 0.59 | 0.63 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 0.42 | 0.49 | 0.47 | 0.41 | 0.46 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 0.62 | 0.65 | 0.65 | 0.63 | 0.72 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 0.43 | 0.52 | 0.49 | 0.43 | 0.48 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 0.65 | 0.69 | 0.70 | 0.65 | 0.77 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 0.43 | 0.52 | 0.49 | 0.42 | 0.48 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 0.65 | 0.68 | 0.70 | 0.65 | 0.77 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.41 | 0.41 | 0.43 | 0.38 | 0.46 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.58 | 0.60 | 0.60 | 0.56 | 0.63 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.42 | 0.43 | 0.45 | 0.41 | 0.48 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 0.62 | 0.63 | 0.64 | 0.60 | 0.66 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 0.57 | 0.62 | 0.59 | 0.54 | 0.60 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.81 | 0.83 | 0.82 | 0.78 | 0.86 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 0.58 | 0.92 | 0.59 | 0.53 | 0.55 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 0.54 | 0.54 | 0.52 | 0.49 | 0.53 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.84 | 0.84 | 0.80 | 0.78 | 0.83 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 0.95 | 1.11 | 0.63 | 0.58 | 0.65 |
