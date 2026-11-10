# Dry run (not pre-registered), test clips, fric06, head excluded

17 test clips, 9 categories (excluded: head). Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| full | 1.122 | 0.982 | 0.65 | 1.00 |
| curated | 1.300 | 0.926 | 2.47 | 1.00 |
| random | 1.104 | 0.973 | 1.35 | 1.00 |
| kinematic | 1.080 | 0.949 | 2.12 | 0.89 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.178 [+0.085, +0.309] | +0.01 | +0.19 | +0.19 | -0.08 | +0.63 | +0.13 | +0.06 | +0.12 | +0.23 |
| random | +0.197 [+0.092, +0.346] | +0.09 | +0.07 | +0.16 | +0.12 | +0.76 | +0.13 | +0.11 | +0.15 | +0.14 |
| kinematic | +0.220 [+0.090, +0.384] | +0.09 | +0.25 | +0.31 | -0.23 | +0.87 | -0.02 | +0.19 | +0.20 | +0.11 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.303 (bar: ≥ −0.05): **no**
- **pass: no**

## Per clip (e)

| clip | category | full | curated | random | kinematic |
|---|---|---|---|---|---|
| `bow__pitch20deg__fast` | bow | 0.57 | 0.60 | 0.51 | 0.50 |
| `bow__pitch20deg__slow` | bow | 0.59 | 0.59 | 0.49 | 0.50 |
| `crouch__depth0.40__fast` | crouch | 0.38 | 0.57 | 0.49 | 0.32 |
| `crouch__depth0.40__slow` | crouch | 0.38 | 0.56 | 0.50 | 0.32 |
| `march__lift0.035__gentle` | march | 1.38 | 1.70 | 1.26 | 1.18 |
| `march__lift0.035__normal` | march | 1.35 | 1.42 | 1.55 | 1.33 |
| `side_step__dx0_dy0.03_dth0__gentle` | side_step | 1.54 | 1.46 | 1.35 | 1.69 |
| `sway__amp0.03m__f0.5` | sway | 0.90 | 1.12 | 0.78 | 0.67 |
| `sway__amp0.03m__f1.0` | sway | 1.16 | 2.19 | 1.01 | 0.92 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 1.50 | 1.73 | 1.55 | 1.70 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 1.64 | 1.66 | 1.59 | 1.74 |
| `walk_back__dx-0.02_dy0_dth0__gentle` | walk_back | 0.94 | 1.01 | 0.86 | 0.76 |
| `walk_back__dx-0.02_dy0_dth0__normal` | walk_back | 1.14 | 1.21 | 1.14 | 1.06 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 1.02 | 1.10 | 0.94 | 0.92 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 1.28 | 1.43 | 1.29 | 1.21 |
| `walk_turn__dx0.04_dy0_dth-0.15__gentle` | walk_turn | 1.56 | 1.88 | 1.67 | 1.77 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | 1.73 | 1.87 | 1.80 | 1.77 |
