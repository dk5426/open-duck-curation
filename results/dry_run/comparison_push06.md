# Dry run (not pre-registered), test clips, push06

19 test clips, 10 categories. Lower e is better.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| full | 1.715 | 0.673 | 6.16 | 0.50 |
| curated | 1.911 | 0.601 | 7.84 | 0.10 |
| random | 1.766 | 0.651 | 6.95 | 0.30 |
| kinematic | 1.699 | 0.656 | 6.79 | 0.40 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.196 [+0.115, +0.292] | +0.19 | +0.08 | +0.08 | +0.48 | +0.19 | +0.53 | +0.01 | +0.08 | +0.22 | +0.09 |
| random | +0.146 [+0.062, +0.257] | +0.17 | -0.07 | -0.01 | +0.24 | +0.13 | +0.61 | +0.06 | +0.06 | +0.17 | +0.09 |
| kinematic | +0.213 [+0.128, +0.308] | +0.21 | +0.15 | +0.03 | +0.41 | +0.10 | +0.61 | +0.06 | +0.08 | +0.28 | +0.15 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.256 (bar: ≥ −0.05): **no**
- **pass: no**

## Per clip (e)

| clip | category | full | curated | random | kinematic |
|---|---|---|---|---|---|
| `bow__pitch20deg__fast` | bow | 0.92 | 1.11 | 1.02 | 0.91 |
| `bow__pitch20deg__slow` | bow | 1.03 | 1.22 | 0.97 | 0.99 |
| `crouch__depth0.40__fast` | crouch | 0.79 | 0.81 | 0.87 | 0.71 |
| `crouch__depth0.40__slow` | crouch | 0.53 | 0.67 | 0.74 | 0.48 |
| `head__nod__fast` | head | 3.08 | 3.21 | 3.19 | 3.17 |
| `head__nod__slow` | head | 3.13 | 3.17 | 3.22 | 3.15 |
| `march__lift0.035__gentle` | march | 1.71 | 2.19 | 1.78 | 1.63 |
| `march__lift0.035__normal` | march | 1.54 | 2.01 | 1.93 | 1.75 |
| `side_step__dx0_dy0.03_dth0__gentle` | side_step | 1.75 | 1.93 | 1.81 | 1.84 |
| `sway__amp0.03m__f0.5` | sway | 1.40 | 1.67 | 1.36 | 1.16 |
| `sway__amp0.03m__f1.0` | sway | 1.47 | 2.27 | 1.36 | 1.57 |
| `turn_in_place__dx0_dy0_dth-0.30__gentle` | turn_in_place | 2.14 | 2.12 | 2.09 | 1.98 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | 2.05 | 2.10 | 2.01 | 2.11 |
| `walk_back__dx-0.02_dy0_dth0__gentle` | walk_back | 1.88 | 2.00 | 1.86 | 1.84 |
| `walk_back__dx-0.02_dy0_dth0__normal` | walk_back | 1.58 | 1.62 | 1.65 | 1.64 |
| `walk_fwd__dx0.03_dy0_dth0__gentle` | walk_fwd | 1.88 | 1.93 | 1.75 | 1.83 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | 1.54 | 1.93 | 1.76 | 1.47 |
| `walk_turn__dx0.04_dy0_dth-0.15__gentle` | walk_turn | 2.06 | 2.08 | 2.05 | 1.99 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | 2.10 | 2.26 | 2.11 | 2.05 |
