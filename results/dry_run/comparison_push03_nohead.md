# Dry run (not pre-registered), test clips, push03, head excluded

17 test clips, 9 categories (excluded: head). Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| full | 1.251 | 0.906 | 2.53 | 0.89 |
| curated | 1.452 | 0.840 | 4.41 | 0.78 |
| random | 1.274 | 0.887 | 3.24 | 1.00 |
| kinematic | 1.186 | 0.895 | 3.24 | 0.78 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.200 [+0.079, +0.353] | +0.02 | +0.16 | +0.38 | -0.00 | +0.82 | +0.10 | -0.00 | +0.22 | +0.02 |
| random | +0.178 [+0.069, +0.330] | +0.08 | +0.06 | +0.20 | +0.17 | +0.85 | +0.10 | -0.02 | +0.08 | +0.08 |
| kinematic | +0.266 [+0.128, +0.433] | +0.08 | +0.27 | +0.44 | -0.10 | +0.95 | -0.02 | +0.26 | +0.25 | +0.08 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.400 (bar: ≥ −0.05): **no**
- **pass: no**

## Per clip (e)

| clip | category | full | curated | random | kinematic |
|---|---|---|---|---|---|
| `bow__pitch20deg__fast` | bow | 0.78 | 0.81 | 0.75 | 0.72 |
| `bow__pitch20deg__slow` | bow | 0.67 | 0.68 | 0.59 | 0.61 |
| `crouch__depth0.40__fast` | crouch | 0.62 | 0.77 | 0.71 | 0.45 |
| `crouch__depth0.40__slow` | crouch | 0.50 | 0.66 | 0.61 | 0.44 |
| `march__lift0.035__gentle` | march | 1.23 | 1.72 | 1.54 | 1.25 |
| `march__lift0.035__normal` | march | 1.49 | 1.76 | 1.54 | 1.34 |
| `side_step__dx0_dy0.03_dth0__gentle` | side_step | 1.66 | 1.66 | 1.49 | 1.76 |
| `sway__amp0.03m__f0.5` | sway | 1.13 | 1.63 | 1.10 | 1.04 |
| `sway__amp0.03m__f1.0` | sway | 1.15 | 2.30 | 1.13 | 0.99 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 1.65 | 1.89 | 1.74 | 1.75 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 1.82 | 1.77 | 1.70 | 1.95 |
| `walk_back__dx-0.02_dy0_dth0__gentle` | walk_back | 1.15 | 1.16 | 1.28 | 0.77 |
| `walk_back__dx-0.02_dy0_dth0__normal` | walk_back | 1.25 | 1.22 | 1.15 | 1.09 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 1.02 | 1.35 | 1.13 | 1.10 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 1.36 | 1.47 | 1.51 | 1.21 |
| `walk_turn__dx0.04_dy0_dth-0.15__gentle` | walk_turn | 1.96 | 1.86 | 1.80 | 1.81 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | 1.83 | 1.97 | 1.88 | 1.87 |
