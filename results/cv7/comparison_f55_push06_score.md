# Study cv7, 55% keep-fraction, test push06, score

56 test clips (30 bootstrap units: sources), 10 categories, metric `score`. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| curated | 1.268 | 0.681 | 6.73 | 0.40 |
| full | 1.265 | 0.681 | 6.55 | 0.40 |
| kinematic | 1.232 | 0.696 | 6.35 | 0.40 |
| oracle | 1.232 | 0.690 | 6.42 | 0.40 |
| random | 1.355 | 0.655 | 6.93 | 0.30 |
| checked | 1.240 | 0.691 | 6.49 | 0.50 |
| curatedscore_f55 | 1.262 | 0.686 | 6.60 | 0.40 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.003 [-0.065, +0.046] | -0.00 | +0.03 | -0.21 | +0.03 | +0.14 | -0.01 | +0.01 | +0.02 | +0.02 | +0.07 |
| kinematic | +0.036 [-0.007, +0.101] | -0.03 | +0.04 | +0.12 | +0.04 | +0.16 | -0.00 | +0.02 | -0.01 | +0.00 | +0.08 |
| oracle | +0.037 [-0.015, +0.086] | -0.01 | +0.02 | -0.00 | +0.05 | +0.16 | +0.00 | +0.03 | +0.03 | +0.05 | +0.11 |
| random | -0.087 [-0.226, +0.013] | -0.02 | +0.00 | -0.86 | +0.06 | +0.06 | -0.02 | -0.02 | -0.00 | -0.01 | +0.04 |
| checked | +0.029 [-0.015, +0.077] | -0.01 | +0.03 | +0.01 | +0.05 | +0.13 | -0.01 | +0.04 | -0.01 | +0.01 | +0.11 |
| curatedscore_f55 | +0.006 [-0.043, +0.058] | -0.01 | +0.03 | +0.04 | -0.03 | +0.11 | -0.01 | -0.02 | -0.03 | -0.01 | +0.02 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.039 (bar: ≥ −0.05): **yes**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch20deg__fast, bow__pitch20deg__slow, bow__pitch22deg__fast, bow__pitch22deg__slow, crouch__depth0.70__fast, crouch__depth0.70__slow, turn_in_place__dx0_dy0_dth-0.25__gentle, turn_in_place__dx0_dy0_dth-0.25__normal, turn_in_place__dx0_dy0_dth-0.30__gentle, turn_in_place__dx0_dy0_dth-0.30__normal, turn_in_place__dx0_dy0_dth0.20__gentle, turn_in_place__dx0_dy0_dth0.20__normal, walk_fwd__dx0.025_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.03_dy0_dth0__gentle, walk_fwd__dx0.03_dy0_dth0__normal, walk_fwd__dx0.045_dy0_dth0__gentle, walk_fwd__dx0.045_dy0_dth0__normal, walk_turn__dx0.035_dy0_dth-0.12__gentle, walk_turn__dx0.04_dy0_dth0.15__gentle

**inside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 20 | +0.021 [-0.016, +0.062] |
| kinematic | 20 | +0.016 [-0.025, +0.061] |
| oracle | 20 | +0.033 [-0.008, +0.082] |
| random | 20 | -0.011 [-0.048, +0.028] |
| checked | 20 | +0.029 [-0.011, +0.076] |
| curatedscore_f55 | 20 | -0.004 [-0.048, +0.043] |

**outside**

| vs | clips | Δe [95% CI] |
|---|---|---|
| full | 36 | -0.007 [-0.109, +0.056] |
| kinematic | 36 | +0.048 [-0.014, +0.148] |
| oracle | 36 | +0.039 [-0.039, +0.111] |
| random | 36 | -0.129 [-0.345, +0.023] |
| checked | 36 | +0.029 [-0.035, +0.098] |
| curatedscore_f55 | 36 | +0.012 [-0.060, +0.088] |


## Per clip (e)

| clip | category | curated | full | kinematic | oracle | random | checked | curatedscore_f55 |
|---|---|---|---|---|---|---|---|---|
| `bow__pitch12deg__fast` | bow | 0.88 | 0.90 | 0.87 | 0.86 | 0.85 | 0.82 | 0.87 |
| `bow__pitch12deg__slow` | bow | 0.64 | 0.65 | 0.69 | 0.64 | 0.65 | 0.68 | 0.64 |
| `bow__pitch20deg__fast` | bow | 0.51 | 0.49 | 0.55 | 0.53 | 0.49 | 0.53 | 0.52 |
| `bow__pitch20deg__slow` | bow | 0.77 | 0.75 | 0.79 | 0.78 | 0.82 | 0.77 | 0.80 |
| `bow__pitch22deg__fast` | bow | 0.80 | 0.78 | 0.81 | 0.81 | 0.80 | 0.82 | 0.80 |
| `bow__pitch22deg__slow` | bow | 0.93 | 0.99 | 1.01 | 0.94 | 1.00 | 0.97 | 0.93 |
| `crouch__depth0.30__fast` | crouch | 1.03 | 0.99 | 1.01 | 0.88 | 0.99 | 1.01 | 0.99 |
| `crouch__depth0.30__slow` | crouch | 0.80 | 0.76 | 0.81 | 0.80 | 0.88 | 0.78 | 0.76 |
| `crouch__depth0.40__fast` | crouch | 0.86 | 0.86 | 0.84 | 0.87 | 0.87 | 0.79 | 0.82 |
| `crouch__depth0.40__slow` | crouch | 0.70 | 0.68 | 0.65 | 0.70 | 0.67 | 0.64 | 0.68 |
| `crouch__depth0.70__fast` | crouch | 0.57 | 0.58 | 0.58 | 0.63 | 0.59 | 0.59 | 0.58 |
| `crouch__depth0.70__slow` | crouch | 0.80 | 0.72 | 0.63 | 0.76 | 0.77 | 0.76 | 0.78 |
| `head__look_tilt__fast` | head | 0.88 | 0.90 | 0.91 | 0.90 | 1.64 | 0.85 | 0.88 |
| `head__look_tilt__slow` | head | 0.70 | 0.61 | 0.61 | 0.63 | 1.44 | 0.60 | 0.59 |
| `head__nod_tilt__fast` | head | 1.56 | 1.85 | 1.34 | 1.71 | 2.45 | 1.63 | 1.49 |
| `head__nod_tilt__slow` | head | 1.68 | 2.51 | 0.96 | 1.58 | 2.59 | 1.40 | 1.62 |
| `head__shake__fast` | head | 0.63 | 0.75 | 0.85 | 0.64 | 2.20 | 0.86 | 0.61 |
| `head__shake__slow` | head | 0.63 | 0.71 | 0.67 | 0.65 | 0.94 | 0.71 | 0.63 |
| `march__lift0.02__gentle` | march | 1.70 | 1.71 | 1.71 | 1.70 | 1.71 | 1.70 | 1.71 |
| `march__lift0.02__normal` | march | 1.61 | 1.59 | 1.63 | 1.61 | 1.62 | 1.61 | 1.57 |
| `march__lift0.035__gentle` | march | 1.29 | 1.23 | 1.22 | 1.21 | 1.22 | 1.22 | 1.27 |
| `march__lift0.035__normal` | march | 1.44 | 1.38 | 1.37 | 1.39 | 1.28 | 1.26 | 1.63 |
| `march__lift0.03__gentle` | march | 1.66 | 1.65 | 1.66 | 1.65 | 1.65 | 1.65 | 1.67 |
| `march__lift0.03__normal` | march | 1.54 | 1.50 | 1.39 | 1.41 | 1.39 | 1.50 | 1.58 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 1.74 | 1.62 | 1.61 | 1.60 | 1.71 | 1.64 | 1.63 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | 1.71 | 1.38 | 1.32 | 1.40 | 1.55 | 1.38 | 1.44 |
| `side_step__dx0_dy0.02_dth0__gentle` | side_step | 1.58 | 1.57 | 1.60 | 1.57 | 1.60 | 1.58 | 1.58 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 1.56 | 1.45 | 1.43 | 1.40 | 1.51 | 1.49 | 1.50 |
| `sway__amp0.015m__f0.5` | sway | 0.94 | 0.94 | 0.95 | 0.94 | 0.95 | 0.95 | 0.94 |
| `sway__amp0.015m__f1.0` | sway | 0.79 | 0.79 | 0.80 | 0.79 | 0.80 | 0.80 | 0.79 |
| `sway__amp0.01m__f0.5` | sway | 0.63 | 0.63 | 0.52 | 0.57 | 0.66 | 0.57 | 0.65 |
| `sway__amp0.01m__f1.0` | sway | 0.64 | 0.64 | 0.65 | 0.64 | 0.65 | 0.65 | 0.64 |
| `sway__amp0.025m__f0.5` | sway | 1.32 | 1.35 | 1.35 | 1.35 | 1.31 | 1.38 | 1.34 |
| `sway__amp0.025m__f1.0` | sway | 1.10 | 1.10 | 1.15 | 1.11 | 1.19 | 1.11 | 1.11 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 1.53 | 1.54 | 1.50 | 1.51 | 1.56 | 1.48 | 1.54 |
| `turn_in_place__dx0_dy0_dth-0.25__normal` | turn_in_place | 1.58 | 1.61 | 1.62 | 1.64 | 1.65 | 1.58 | 1.69 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 1.63 | 1.61 | 1.65 | 1.65 | 1.68 | 1.66 | 1.67 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 1.66 | 1.62 | 1.54 | 1.58 | 1.62 | 1.58 | 1.67 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | 1.62 | 1.60 | 1.60 | 1.58 | 1.59 | 1.58 | 1.61 |
| `turn_in_place__dx0_dy0_dth0.20__normal` | turn_in_place | 1.63 | 1.58 | 1.64 | 1.52 | 1.66 | 1.52 | 1.58 |
| `walk_back__dx-0.025_dy0_dth0__gentle` | walk_back | 1.23 | 1.22 | 1.21 | 1.20 | 1.25 | 1.21 | 1.22 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | 1.54 | 1.57 | 1.59 | 1.57 | 1.56 | 1.60 | 1.66 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | 1.34 | 1.19 | 1.23 | 1.20 | 1.34 | 1.26 | 1.36 |
| `walk_back__dx-0.035_dy0_dth0__normal` | walk_back | 1.59 | 1.68 | 1.68 | 1.60 | 1.58 | 1.66 | 1.65 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | 1.73 | 1.65 | 1.71 | 1.64 | 1.74 | 1.71 | 1.72 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | 1.69 | 1.71 | 1.74 | 1.71 | 1.65 | 1.75 | 1.69 |
| `walk_fwd__dx0.025_dy0_dth0__gentle` | walk_fwd | 1.33 | 1.33 | 1.35 | 1.33 | 1.36 | 1.33 | 1.33 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 1.56 | 1.60 | 1.54 | 1.54 | 1.59 | 1.55 | 1.63 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 1.60 | 1.60 | 1.62 | 1.60 | 1.62 | 1.60 | 1.59 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 1.55 | 1.39 | 1.54 | 1.40 | 1.47 | 1.46 | 1.36 |
| `walk_fwd__dx0.045_dy0_dth0__gentle` | walk_fwd | 1.53 | 1.53 | 1.54 | 1.52 | 1.61 | 1.52 | 1.57 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 1.65 | 1.65 | 1.61 | 1.56 | 1.66 | 1.67 | 1.78 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 1.67 | 1.65 | 1.63 | 1.62 | 1.65 | 1.62 | 1.65 |
| `walk_turn__dx0.03_dy0_dth0.20__gentle` | walk_turn | 1.61 | 1.60 | 1.61 | 1.59 | 1.58 | 1.59 | 1.61 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 1.60 | 1.49 | 1.52 | 1.46 | 1.52 | 1.48 | 1.61 |
| `walk_turn__dx0.04_dy0_dth0.15__gentle` | walk_turn | 1.55 | 1.42 | 1.37 | 1.30 | 1.51 | 1.30 | 1.48 |
