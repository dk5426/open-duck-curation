# Study cv7, stratified curation at 85%

56 test clips (30 bootstrap units: sources), 10 categories, metric `score`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curatedstrat | 0.458 | 0.990 | 0.13 | 1.00 |
| curated | 0.462 | 0.989 | 0.18 | 1.00 |
| full | 0.501 | 0.976 | 0.38 | 1.00 |
| oracle | 0.435 | 1.000 | 0.02 | 1.00 |
| kinematic | 0.454 | 0.997 | 0.08 | 1.00 |

## curatedstrat minus each other condition (paired over test clips; negative = curatedstrat better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| curated | -0.004 [-0.074, +0.069] | -0.00 | -0.00 | -0.01 | +0.00 | +0.00 | -0.00 | -0.02 | +0.00 | +0.00 | -0.01 |
| full | -0.043 [-0.150, +0.006] | +0.02 | +0.01 | -0.34 | +0.00 | -0.00 | +0.01 | -0.05 | -0.02 | -0.02 | -0.02 |
| oracle | +0.023 [-0.008, +0.106] | +0.01 | -0.00 | +0.23 | +0.00 | -0.01 | -0.00 | -0.01 | +0.01 | -0.00 | -0.01 |
| kinematic | +0.004 [-0.039, +0.078] | -0.00 | -0.01 | +0.13 | -0.00 | -0.02 | -0.01 | -0.02 | -0.01 | -0.01 | -0.02 |

## P.9 pass bar

- curatedstrat beats full with the CI excluding 0: **no**
- worst per-category completion drop vs full: +0.000 (bar: ≥ −0.05): **yes**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| curated | 20 | -0.006 [-0.017, +0.003] |
| full | 20 | -0.018 [-0.040, +0.000] |
| oracle | 20 | -0.005 [-0.016, +0.005] |
| kinematic | 20 | -0.014 [-0.025, -0.004] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| curated | 36 | -0.003 [-0.120, +0.099] |
| full | 36 | -0.057 [-0.222, +0.017] |
| oracle | 36 | +0.038 [-0.009, +0.165] |
| kinematic | 36 | +0.013 [-0.053, +0.125] |


## Per clip (e)

| clip | category | curatedstrat | curated | full | oracle | kinematic |
|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.19 | 0.19 | 0.17 | 0.18 | 0.19 |
| `bow__pitch12deg__slow` | bow | 0.18 | 0.19 | 0.17 | 0.18 | 0.19 |
| `bow__pitch20deg__fast` | bow | 0.23 | 0.23 | 0.20 | 0.21 | 0.23 |
| `bow__pitch20deg__slow` | bow | 0.21 | 0.21 | 0.19 | 0.20 | 0.21 |
| `bow__pitch22deg__fast` | bow | 0.23 | 0.24 | 0.21 | 0.22 | 0.24 |
| `bow__pitch22deg__slow` | bow | 0.22 | 0.22 | 0.20 | 0.21 | 0.22 |
| `crouch__depth0.30__fast` | crouch | 0.12 | 0.12 | 0.11 | 0.13 | 0.13 |
| `crouch__depth0.30__slow` | crouch | 0.12 | 0.12 | 0.11 | 0.13 | 0.13 |
| `crouch__depth0.40__fast` | crouch | 0.12 | 0.12 | 0.12 | 0.13 | 0.13 |
| `crouch__depth0.40__slow` | crouch | 0.12 | 0.12 | 0.11 | 0.13 | 0.13 |
| `crouch__depth0.70__fast` | crouch | 0.12 | 0.12 | 0.11 | 0.12 | 0.13 |
| `crouch__depth0.70__slow` | crouch | 0.12 | 0.12 | 0.12 | 0.12 | 0.13 |
| `head__look_tilt__fast` | head | 0.14 | 0.13 | 0.14 | 0.15 | 0.13 |
| `head__look_tilt__slow` | head | 0.13 | 0.12 | 0.13 | 0.13 | 0.13 |
| `head__nod_tilt__fast` | head | 1.20 | 1.43 | 1.91 | 0.63 | 1.01 |
| `head__nod_tilt__slow` | head | 1.12 | 1.07 | 2.52 | 0.45 | 0.50 |
| `head__shake__fast` | head | 0.42 | 0.32 | 0.32 | 0.30 | 0.39 |
| `head__shake__slow` | head | 0.23 | 0.25 | 0.26 | 0.21 | 0.32 |
| `march__lift0.02__gentle` | march | 0.42 | 0.42 | 0.43 | 0.42 | 0.41 |
| `march__lift0.02__normal` | march | 0.50 | 0.50 | 0.51 | 0.49 | 0.50 |
| `march__lift0.035__gentle` | march | 0.64 | 0.64 | 0.65 | 0.64 | 0.64 |
| `march__lift0.035__normal` | march | 0.83 | 0.82 | 0.79 | 0.83 | 0.84 |
| `march__lift0.03__gentle` | march | 0.55 | 0.55 | 0.56 | 0.55 | 0.55 |
| `march__lift0.03__normal` | march | 0.70 | 0.70 | 0.67 | 0.70 | 0.71 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 0.67 | 0.65 | 0.66 | 0.68 | 0.70 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 0.62 | 0.60 | 0.62 | 0.64 | 0.66 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 0.53 | 0.55 | 0.54 | 0.55 | 0.54 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.66 | 0.65 | 0.66 | 0.66 | 0.67 |
| `sway__amp0.015m__f0.5` | sway | 0.16 | 0.17 | 0.15 | 0.17 | 0.17 |
| `sway__amp0.015m__f1.0` | sway | 0.18 | 0.18 | 0.17 | 0.18 | 0.19 |
| `sway__amp0.01m__f0.5` | sway | 0.14 | 0.15 | 0.13 | 0.15 | 0.16 |
| `sway__amp0.01m__f1.0` | sway | 0.15 | 0.16 | 0.14 | 0.16 | 0.17 |
| `sway__amp0.025m__f0.5` | sway | 0.22 | 0.22 | 0.21 | 0.22 | 0.23 |
| `sway__amp0.025m__f1.0` | sway | 0.27 | 0.28 | 0.25 | 0.27 | 0.28 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.55 | 0.56 | 0.60 | 0.56 | 0.57 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 0.78 | 0.78 | 0.84 | 0.79 | 0.80 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 0.63 | 0.67 | 0.72 | 0.66 | 0.67 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 0.87 | 0.90 | 0.93 | 0.89 | 0.90 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 0.47 | 0.49 | 0.50 | 0.48 | 0.48 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 0.63 | 0.62 | 0.63 | 0.62 | 0.63 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 0.45 | 0.45 | 0.47 | 0.44 | 0.46 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 0.64 | 0.64 | 0.65 | 0.63 | 0.65 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 0.47 | 0.46 | 0.49 | 0.45 | 0.48 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 0.67 | 0.67 | 0.70 | 0.66 | 0.68 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 0.47 | 0.46 | 0.49 | 0.45 | 0.47 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 0.67 | 0.68 | 0.70 | 0.66 | 0.68 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 0.41 | 0.41 | 0.43 | 0.43 | 0.41 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.59 | 0.59 | 0.60 | 0.58 | 0.60 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 0.43 | 0.43 | 0.45 | 0.45 | 0.44 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 0.62 | 0.62 | 0.64 | 0.62 | 0.63 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 0.56 | 0.57 | 0.59 | 0.58 | 0.57 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.80 | 0.80 | 0.82 | 0.79 | 0.82 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 0.56 | 0.56 | 0.59 | 0.58 | 0.58 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 0.51 | 0.52 | 0.52 | 0.52 | 0.51 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.79 | 0.81 | 0.80 | 0.79 | 0.81 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 0.60 | 0.61 | 0.63 | 0.62 | 0.65 |
