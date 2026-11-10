# Dry run (not pre-registered), test clips, nominal, head excluded

17 test clips, 9 categories (excluded: head). Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| full | 1.134 | 0.975 | 0.94 | 0.89 |
| curated | 1.333 | 0.906 | 3.06 | 0.89 |
| random | 1.114 | 0.971 | 1.47 | 1.00 |
| kinematic | 1.082 | 0.948 | 2.18 | 0.89 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.199 [+0.090, +0.345] | +0.01 | +0.18 | +0.20 | -0.16 | +0.81 | +0.14 | +0.07 | +0.16 | +0.20 |
| random | +0.219 [+0.119, +0.367] | +0.09 | +0.07 | +0.14 | +0.22 | +0.89 | +0.10 | +0.11 | +0.19 | +0.17 |
| kinematic | +0.251 [+0.111, +0.431] | +0.08 | +0.24 | +0.33 | -0.16 | +1.04 | -0.04 | +0.20 | +0.25 | +0.10 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.397 (bar: ≥ −0.05): **no**
- **pass: no**

## Per clip (e)

| clip | category | full | curated | random | kinematic |
|---|---|---|---|---|---|
| `bow__pitch20deg__fast` | bow | 0.57 | 0.59 | 0.51 | 0.50 |
| `bow__pitch20deg__slow` | bow | 0.58 | 0.58 | 0.48 | 0.50 |
| `crouch__depth0.40__fast` | crouch | 0.38 | 0.56 | 0.49 | 0.31 |
| `crouch__depth0.40__slow` | crouch | 0.37 | 0.56 | 0.49 | 0.31 |
| `march__lift0.035__gentle` | march | 1.39 | 1.66 | 1.51 | 1.18 |
| `march__lift0.035__normal` | march | 1.39 | 1.52 | 1.37 | 1.34 |
| `side_step__dx0_dy0.03_dth0__gentle` | side_step | 1.75 | 1.59 | 1.37 | 1.75 |
| `sway__amp0.03m__f0.5` | sway | 0.89 | 1.38 | 0.77 | 0.67 |
| `sway__amp0.03m__f1.0` | sway | 1.15 | 2.29 | 1.12 | 0.92 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 1.51 | 1.71 | 1.58 | 1.70 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 1.59 | 1.67 | 1.59 | 1.75 |
| `walk_back__dx-0.02_dy0_dth0__gentle` | walk_back | 0.94 | 1.00 | 0.86 | 0.76 |
| `walk_back__dx-0.02_dy0_dth0__normal` | walk_back | 1.16 | 1.23 | 1.14 | 1.07 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 1.01 | 1.10 | 0.94 | 0.91 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 1.29 | 1.52 | 1.30 | 1.21 |
| `walk_turn__dx0.04_dy0_dth-0.15__gentle` | walk_turn | 1.59 | 1.88 | 1.61 | 1.77 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | 1.72 | 1.84 | 1.77 | 1.74 |
