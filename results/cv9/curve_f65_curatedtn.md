# cv9 secondary curve (65%, nominal test): curatedtn

69 test clips (69 bootstrap units: sources), 14 categories, metric `score`. Lower e is better. Dropped (every condition falls in >= 0.5 of rollouts): `side_step__dx0_dy0.0275_dth0__gentle`.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| full | 0.363 | 0.989 | 0.43 | 1.00 |
| curated | 0.397 | 0.993 | 0.51 | 1.00 |
| kinematic | 0.348 | 0.999 | 0.07 | 1.00 |
| random | 0.383 | 0.985 | 0.48 | 1.00 |
| curatedtn | 0.352 | 0.999 | 0.09 | 1.00 |

## curatedtn minus each other condition (paired over test clips; negative = curatedtn better)

| vs | Δe overall [97.5% CI] | bow | crouch | dance | head | headbang | hop | leg_lift | side_step | sway | turn_in_place | twist | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | -0.012 [-0.043, +0.010] | +0.03 | -0.01 | -0.00 | +0.00 | +0.07 | -0.00 | +0.02 | -0.23 | +0.00 | -0.02 | +0.00 | -0.00 | -0.01 | -0.07 |
| curated | -0.045 [-0.077, -0.018] | +0.01 | +0.00 | -0.00 | +0.01 | +0.07 | +0.00 | -0.01 | -0.16 | +0.01 | -0.16 | +0.00 | -0.12 | -0.15 | -0.15 |
| kinematic | +0.004 [-0.006, +0.014] | +0.04 | -0.00 | -0.00 | +0.00 | +0.02 | -0.00 | +0.02 | -0.00 | +0.00 | -0.02 | -0.00 | +0.00 | -0.01 | +0.01 |
| random | -0.032 [-0.084, +0.000] | +0.02 | -0.01 | -0.02 | -0.02 | +0.05 | -0.01 | -0.01 | -0.28 | -0.10 | -0.01 | -0.02 | +0.01 | -0.01 | -0.09 |

## P.9 pass bar

- curatedtn beats full with the CI excluding 0: **no**
- curatedtn beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: +0.000 (bar: ≥ −0.05): **yes**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch12deg__slow, bow__pitch15deg__fast, bow__pitch17deg__slow, bow__pitch22deg__fast, bow__pitch24deg__slow, crouch__depth0.30__slow, crouch__depth0.40__fast, crouch__depth0.60__slow, crouch__depth0.75__fast, crouch__depth0.90__slow, dance__f1.25_a0.55, dance__f1.75_a0.5, dance__f1_a0.75, dance__f2.25_a0.65, dance__f2_a0.45, head__nod_a0.85__slow, head__shake_a0.85__fast, head__tilt_a0.7__fast, headbang__f1.5_a0.35, headbang__f1_a0.4, headbang__f2.5_a0.2, headbang__f2_a0.35, headbang__f3_a0.2, hop__h0.0035_n2, hop__h0.0065_n2, hop__h0.006_n1, hop__h0.0075_n1, hop__h0.0095_n1, kick__r0.045_tau0.5_dy0.045, march__lift0.0175__gentle, march__lift0.03__normal, side_step__dx0_dy-0.0175_dth0__gentle, stomp__lift0.025_period1.2_dy0.045, sway__amp0.0135m__f0.5, sway__amp0.0175m__f1.0, sway__amp0.0225m__f0.5, sway__amp0.0275m__f1.0, tap__reach0.035_period1.4_dy0.045, turn_in_place__dx0_dy0_dth0.175__normal, twist__f0.5_a0.2, twist__f0.75_a0.25, twist__f1.25_a0.15, twist__f1.5_a0.2, twist__f1_a0.3, walk_back__dx-0.0225_dy0_dth0__normal, walk_back__dx-0.0275_dy0_dth0__gentle, walk_back__dx-0.0325_dy0_dth0__normal, walk_back__dx-0.0375_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.0275_dy0_dth0__normal, walk_fwd__dx0.035_dy0_dth0__gentle, walk_turn__dx0.025_dy0_dth0.12__normal

**inside**

| vs | clips | Δe [97.5% CI] |
|---|---|---|
| full | 52 | +0.006 [-0.011, +0.020] |
| curated | 52 | -0.018 [-0.048, +0.005] |
| kinematic | 52 | +0.004 [-0.005, +0.016] |
| random | 52 | -0.016 [-0.073, +0.009] |

**outside**

| vs | clips | Δe [97.5% CI] |
|---|---|---|
| full | 17 | -0.065 [-0.177, -0.001] |
| curated | 17 | -0.127 [-0.212, -0.062] |
| kinematic | 17 | +0.001 [-0.019, +0.027] |
| random | 17 | -0.078 [-0.212, -0.002] |


## Per clip (e)

| clip | category | full | curated | kinematic | random | curatedtn |
|---|---|---|---|---|---|---|
| `bow__pitch12deg__slow` | bow | 0.15 | 0.16 | 0.15 | 0.16 | 0.20 |
| `bow__pitch15deg__fast` | bow | 0.17 | 0.20 | 0.17 | 0.18 | 0.20 |
| `bow__pitch17deg__slow` | bow | 0.17 | 0.19 | 0.17 | 0.18 | 0.21 |
| `bow__pitch22deg__fast` | bow | 0.22 | 0.25 | 0.22 | 0.24 | 0.24 |
| `bow__pitch24deg__slow` | bow | 0.21 | 0.23 | 0.20 | 0.23 | 0.23 |
| `crouch__depth0.30__slow` | crouch | 0.11 | 0.10 | 0.11 | 0.11 | 0.10 |
| `crouch__depth0.40__fast` | crouch | 0.11 | 0.10 | 0.11 | 0.11 | 0.10 |
| `crouch__depth0.60__slow` | crouch | 0.11 | 0.11 | 0.11 | 0.11 | 0.11 |
| `crouch__depth0.75__fast` | crouch | 0.11 | 0.10 | 0.11 | 0.11 | 0.10 |
| `crouch__depth0.90__slow` | crouch | 0.11 | 0.11 | 0.11 | 0.11 | 0.11 |
| `dance__f1.25_a0.55` | dance | 0.11 | 0.11 | 0.12 | 0.13 | 0.11 |
| `dance__f1.75_a0.5` | dance | 0.11 | 0.11 | 0.12 | 0.13 | 0.11 |
| `dance__f1_a0.75` | dance | 0.13 | 0.12 | 0.13 | 0.15 | 0.12 |
| `dance__f2.25_a0.65` | dance | 0.13 | 0.14 | 0.14 | 0.17 | 0.14 |
| `dance__f2_a0.45` | dance | 0.11 | 0.12 | 0.12 | 0.13 | 0.11 |
| `head__look_tilt_a1__fast` | head | 0.14 | 0.12 | 0.14 | 0.17 | 0.16 |
| `head__nod_a0.85__slow` | head | 0.11 | 0.11 | 0.11 | 0.12 | 0.11 |
| `head__nod_tilt_a1__slow` | head | 0.14 | 0.11 | 0.12 | 0.15 | 0.12 |
| `head__shake_a0.85__fast` | head | 0.10 | 0.10 | 0.10 | 0.12 | 0.10 |
| `head__tilt_a0.7__fast` | head | 0.10 | 0.10 | 0.11 | 0.11 | 0.10 |
| `headbang__f1.5_a0.35` | headbang | 0.20 | 0.20 | 0.27 | 0.22 | 0.22 |
| `headbang__f1_a0.4` | headbang | 0.19 | 0.19 | 0.22 | 0.22 | 0.20 |
| `headbang__f2.5_a0.2` | headbang | 0.18 | 0.17 | 0.21 | 0.18 | 0.25 |
| `headbang__f2_a0.35` | headbang | 0.24 | 0.23 | 0.24 | 0.24 | 0.28 |
| `headbang__f3_a0.2` | headbang | 0.19 | 0.18 | 0.30 | 0.19 | 0.36 |
| `hop__h0.0035_n2` | hop | 0.15 | 0.14 | 0.15 | 0.16 | 0.15 |
| `hop__h0.0065_n2` | hop | 0.15 | 0.14 | 0.15 | 0.16 | 0.15 |
| `hop__h0.006_n1` | hop | 0.14 | 0.14 | 0.14 | 0.15 | 0.14 |
| `hop__h0.0075_n1` | hop | 0.14 | 0.14 | 0.14 | 0.15 | 0.14 |
| `hop__h0.0095_n1` | hop | 0.14 | 0.14 | 0.14 | 0.15 | 0.14 |
| `kick__r0.045_tau0.5_dy0.045` | leg_lift | 0.29 | 0.36 | 0.28 | 0.35 | 0.37 |
| `march__lift0.0175__gentle` | leg_lift | 0.38 | 0.38 | 0.38 | 0.39 | 0.37 |
| `march__lift0.03__normal` | leg_lift | 0.69 | 0.73 | 0.70 | 0.67 | 0.66 |
| `stomp__lift0.025_period1.2_dy0.045` | leg_lift | 0.33 | 0.35 | 0.33 | 0.37 | 0.36 |
| `tap__reach0.035_period1.4_dy0.045` | leg_lift | 0.36 | 0.37 | 0.35 | 0.40 | 0.38 |
| `side_step__dx0_dy-0.0175_dth0__gentle` | side_step | 0.99 | 1.07 | 0.76 | 1.10 | 0.80 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 1.71 | 1.27 | 0.99 | 1.83 | 1.03 |
| `side_step__dx0_dy0.0225_dth0__normal` | side_step | 0.71 | 0.76 | 0.73 | 0.70 | 0.69 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.64 | 0.69 | 0.66 | 0.64 | 0.62 |
| `sway__amp0.0135m__f0.5` | sway | 0.13 | 0.13 | 0.13 | 0.14 | 0.14 |
| `sway__amp0.0175m__f1.0` | sway | 0.17 | 0.18 | 0.17 | 0.17 | 0.18 |
| `sway__amp0.0225m__f0.5` | sway | 0.18 | 0.17 | 0.17 | 0.18 | 0.18 |
| `sway__amp0.0275m__f1.0` | sway | 0.26 | 0.27 | 0.27 | 0.79 | 0.28 |
| `sway__amp0.0325m__f0.5` | sway | 0.25 | 0.24 | 0.24 | 0.25 | 0.24 |
| `turn_in_place__dx0_dy0_dth-0.20__normal` | turn_in_place | 0.69 | 1.16 | 0.68 | 0.68 | 0.69 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.51 | 0.69 | 0.52 | 0.50 | 0.50 |
| `turn_in_place__dx0_dy0_dth0.10__gentle` | turn_in_place | 0.38 | 0.37 | 0.38 | 0.39 | 0.37 |
| `turn_in_place__dx0_dy0_dth0.175__normal` | turn_in_place | 0.63 | 0.67 | 0.63 | 0.61 | 0.60 |
| `turn_in_place__dx0_dy0_dth0.25__normal` | turn_in_place | 0.71 | 0.76 | 0.72 | 0.71 | 0.68 |
| `twist__f0.5_a0.2` | twist | 0.13 | 0.12 | 0.14 | 0.15 | 0.13 |
| `twist__f0.75_a0.25` | twist | 0.14 | 0.14 | 0.14 | 0.16 | 0.14 |
| `twist__f1.25_a0.15` | twist | 0.12 | 0.12 | 0.12 | 0.14 | 0.12 |
| `twist__f1.5_a0.2` | twist | 0.14 | 0.14 | 0.14 | 0.16 | 0.14 |
| `twist__f1_a0.3` | twist | 0.16 | 0.16 | 0.16 | 0.18 | 0.17 |
| `walk_back__dx-0.0225_dy0_dth0__normal` | walk_back | 0.62 | 0.74 | 0.62 | 0.61 | 0.61 |
| `walk_back__dx-0.0275_dy0_dth0__gentle` | walk_back | 0.43 | 0.49 | 0.42 | 0.41 | 0.41 |
| `walk_back__dx-0.0325_dy0_dth0__normal` | walk_back | 0.65 | 0.83 | 0.65 | 0.65 | 0.67 |
| `walk_back__dx-0.0375_dy0_dth0__gentle` | walk_back | 0.44 | 0.51 | 0.44 | 0.43 | 0.43 |
| `walk_back__dx-0.045_dy0_dth0__normal` | walk_back | 0.65 | 0.82 | 0.65 | 0.65 | 0.67 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.60 | 0.62 | 0.60 | 0.59 | 0.57 |
| `walk_fwd__dx0.0275_dy0_dth0__normal` | walk_fwd | 0.61 | 0.63 | 0.61 | 0.60 | 0.58 |
| `walk_fwd__dx0.035_dy0_dth0__gentle` | walk_fwd | 0.47 | 0.89 | 0.48 | 0.48 | 0.48 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.79 | 0.88 | 0.79 | 0.80 | 0.80 |
| `walk_fwd__dx0.055_dy0_dth0__gentle` | walk_fwd | 0.72 | 0.88 | 0.72 | 0.72 | 0.73 |
| `walk_turn__dx0.025_dy0_dth-0.18__normal` | walk_turn | 0.80 | 1.00 | 0.80 | 0.80 | 0.79 |
| `walk_turn__dx0.025_dy0_dth0.12__normal` | walk_turn | 0.63 | 0.67 | 0.64 | 0.62 | 0.61 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 1.17 | 1.17 | 0.74 | 1.22 | 0.86 |
| `walk_turn__dx0.035_dy0_dth0.08__gentle` | walk_turn | 0.61 | 0.70 | 0.59 | 0.62 | 0.59 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.81 | 0.86 | 0.85 | 0.82 | 0.80 |
