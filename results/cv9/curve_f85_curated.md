# cv9 secondary curve (85%, nominal test): curated

69 test clips (69 bootstrap units: sources), 14 categories, metric `score`. Lower e is better. Dropped (every condition falls in >= 0.5 of rollouts): `side_step__dx0_dy0.0275_dth0__gentle`.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| full | 0.363 | 0.989 | 0.43 | 1.00 |
| curated | 0.350 | 0.997 | 0.27 | 1.00 |
| kinematic | 0.343 | 0.999 | 0.06 | 1.00 |
| random | 0.371 | 0.988 | 0.43 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [97.5% CI] | bow | crouch | dance | head | headbang | hop | leg_lift | side_step | sway | turn_in_place | twist | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | -0.014 [-0.039, +0.001] | +0.02 | -0.00 | +0.00 | -0.00 | +0.00 | -0.00 | -0.00 | -0.18 | -0.00 | +0.00 | +0.00 | -0.01 | -0.00 | -0.05 |
| kinematic | +0.006 [-0.005, +0.019] | -0.01 | +0.00 | +0.00 | -0.00 | +0.00 | +0.00 | -0.00 | +0.04 | -0.01 | +0.01 | +0.00 | +0.00 | +0.01 | +0.04 |
| random | -0.021 [-0.050, -0.004] | +0.01 | +0.00 | -0.01 | -0.01 | -0.00 | -0.00 | -0.01 | -0.22 | -0.01 | -0.00 | -0.00 | -0.02 | -0.01 | -0.05 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **yes**
- worst per-category completion drop vs full: +0.000 (bar: ≥ −0.05): **yes**
- **pass: no**

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch12deg__slow, bow__pitch15deg__fast, bow__pitch17deg__slow, bow__pitch22deg__fast, bow__pitch24deg__slow, crouch__depth0.30__slow, crouch__depth0.40__fast, crouch__depth0.60__slow, crouch__depth0.75__fast, crouch__depth0.90__slow, dance__f1.25_a0.55, dance__f1.75_a0.5, dance__f1_a0.75, dance__f2.25_a0.65, dance__f2_a0.45, head__nod_a0.85__slow, head__shake_a0.85__fast, head__tilt_a0.7__fast, headbang__f1.5_a0.35, headbang__f1_a0.4, headbang__f2.5_a0.2, headbang__f2_a0.35, headbang__f3_a0.2, hop__h0.0035_n2, hop__h0.0065_n2, hop__h0.006_n1, hop__h0.0075_n1, hop__h0.0095_n1, kick__r0.045_tau0.5_dy0.045, march__lift0.0175__gentle, march__lift0.03__normal, side_step__dx0_dy-0.0175_dth0__gentle, stomp__lift0.025_period1.2_dy0.045, sway__amp0.0135m__f0.5, sway__amp0.0175m__f1.0, sway__amp0.0225m__f0.5, sway__amp0.0275m__f1.0, tap__reach0.035_period1.4_dy0.045, turn_in_place__dx0_dy0_dth0.175__normal, twist__f0.5_a0.2, twist__f0.75_a0.25, twist__f1.25_a0.15, twist__f1.5_a0.2, twist__f1_a0.3, walk_back__dx-0.0225_dy0_dth0__normal, walk_back__dx-0.0275_dy0_dth0__gentle, walk_back__dx-0.0325_dy0_dth0__normal, walk_back__dx-0.0375_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.0275_dy0_dth0__normal, walk_fwd__dx0.035_dy0_dth0__gentle, walk_turn__dx0.025_dy0_dth0.12__normal

**inside**

| vs | clips | Δe [97.5% CI] |
|---|---|---|
| full | 52 | -0.003 [-0.017, +0.005] |
| kinematic | 52 | +0.002 [-0.004, +0.008] |
| random | 52 | -0.010 [-0.028, -0.000] |

**outside**

| vs | clips | Δe [97.5% CI] |
|---|---|---|
| full | 17 | -0.046 [-0.138, +0.002] |
| kinematic | 17 | +0.021 [-0.020, +0.069] |
| random | 17 | -0.055 [-0.154, -0.002] |


## Per clip (e)

| clip | category | full | curated | kinematic | random |
|---|---|---|---|---|---|
| `bow__pitch12deg__slow` | bow | 0.15 | 0.15 | 0.17 | 0.16 |
| `bow__pitch15deg__fast` | bow | 0.17 | 0.19 | 0.20 | 0.18 |
| `bow__pitch17deg__slow` | bow | 0.17 | 0.18 | 0.20 | 0.18 |
| `bow__pitch22deg__fast` | bow | 0.22 | 0.25 | 0.26 | 0.23 |
| `bow__pitch24deg__slow` | bow | 0.21 | 0.23 | 0.24 | 0.22 |
| `crouch__depth0.30__slow` | crouch | 0.11 | 0.11 | 0.10 | 0.11 |
| `crouch__depth0.40__fast` | crouch | 0.11 | 0.11 | 0.10 | 0.11 |
| `crouch__depth0.60__slow` | crouch | 0.11 | 0.11 | 0.10 | 0.11 |
| `crouch__depth0.75__fast` | crouch | 0.11 | 0.11 | 0.10 | 0.11 |
| `crouch__depth0.90__slow` | crouch | 0.11 | 0.11 | 0.11 | 0.11 |
| `dance__f1.25_a0.55` | dance | 0.11 | 0.11 | 0.11 | 0.12 |
| `dance__f1.75_a0.5` | dance | 0.11 | 0.12 | 0.12 | 0.12 |
| `dance__f1_a0.75` | dance | 0.13 | 0.13 | 0.12 | 0.14 |
| `dance__f2.25_a0.65` | dance | 0.13 | 0.14 | 0.14 | 0.14 |
| `dance__f2_a0.45` | dance | 0.11 | 0.12 | 0.12 | 0.12 |
| `head__look_tilt_a1__fast` | head | 0.14 | 0.14 | 0.14 | 0.16 |
| `head__nod_a0.85__slow` | head | 0.11 | 0.11 | 0.11 | 0.11 |
| `head__nod_tilt_a1__slow` | head | 0.14 | 0.12 | 0.12 | 0.13 |
| `head__shake_a0.85__fast` | head | 0.10 | 0.11 | 0.10 | 0.11 |
| `head__tilt_a0.7__fast` | head | 0.10 | 0.10 | 0.10 | 0.11 |
| `headbang__f1.5_a0.35` | headbang | 0.20 | 0.21 | 0.20 | 0.21 |
| `headbang__f1_a0.4` | headbang | 0.19 | 0.20 | 0.20 | 0.20 |
| `headbang__f2.5_a0.2` | headbang | 0.18 | 0.18 | 0.17 | 0.18 |
| `headbang__f2_a0.35` | headbang | 0.24 | 0.23 | 0.23 | 0.24 |
| `headbang__f3_a0.2` | headbang | 0.19 | 0.19 | 0.18 | 0.20 |
| `hop__h0.0035_n2` | hop | 0.15 | 0.15 | 0.15 | 0.15 |
| `hop__h0.0065_n2` | hop | 0.15 | 0.15 | 0.15 | 0.15 |
| `hop__h0.006_n1` | hop | 0.14 | 0.14 | 0.14 | 0.14 |
| `hop__h0.0075_n1` | hop | 0.14 | 0.14 | 0.14 | 0.14 |
| `hop__h0.0095_n1` | hop | 0.14 | 0.14 | 0.14 | 0.14 |
| `kick__r0.045_tau0.5_dy0.045` | leg_lift | 0.29 | 0.28 | 0.30 | 0.31 |
| `march__lift0.0175__gentle` | leg_lift | 0.38 | 0.37 | 0.37 | 0.40 |
| `march__lift0.03__normal` | leg_lift | 0.69 | 0.68 | 0.68 | 0.70 |
| `stomp__lift0.025_period1.2_dy0.045` | leg_lift | 0.33 | 0.34 | 0.35 | 0.34 |
| `tap__reach0.035_period1.4_dy0.045` | leg_lift | 0.36 | 0.37 | 0.37 | 0.37 |
| `side_step__dx0_dy-0.0175_dth0__gentle` | side_step | 0.99 | 0.76 | 0.70 | 1.07 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | 1.71 | 1.19 | 1.10 | 1.77 |
| `side_step__dx0_dy0.0225_dth0__normal` | side_step | 0.71 | 0.71 | 0.70 | 0.71 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.64 | 0.65 | 0.64 | 0.65 |
| `sway__amp0.0135m__f0.5` | sway | 0.13 | 0.13 | 0.14 | 0.14 |
| `sway__amp0.0175m__f1.0` | sway | 0.17 | 0.17 | 0.18 | 0.17 |
| `sway__amp0.0225m__f0.5` | sway | 0.18 | 0.17 | 0.18 | 0.18 |
| `sway__amp0.0275m__f1.0` | sway | 0.26 | 0.26 | 0.28 | 0.26 |
| `sway__amp0.0325m__f0.5` | sway | 0.25 | 0.24 | 0.25 | 0.25 |
| `turn_in_place__dx0_dy0_dth-0.20__normal` | turn_in_place | 0.69 | 0.69 | 0.67 | 0.69 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.51 | 0.50 | 0.50 | 0.51 |
| `turn_in_place__dx0_dy0_dth0.10__gentle` | turn_in_place | 0.38 | 0.37 | 0.38 | 0.40 |
| `turn_in_place__dx0_dy0_dth0.175__normal` | turn_in_place | 0.63 | 0.64 | 0.62 | 0.63 |
| `turn_in_place__dx0_dy0_dth0.25__normal` | turn_in_place | 0.71 | 0.73 | 0.70 | 0.71 |
| `twist__f0.5_a0.2` | twist | 0.13 | 0.13 | 0.13 | 0.13 |
| `twist__f0.75_a0.25` | twist | 0.14 | 0.15 | 0.14 | 0.14 |
| `twist__f1.25_a0.15` | twist | 0.12 | 0.12 | 0.12 | 0.13 |
| `twist__f1.5_a0.2` | twist | 0.14 | 0.13 | 0.14 | 0.14 |
| `twist__f1_a0.3` | twist | 0.16 | 0.17 | 0.16 | 0.16 |
| `walk_back__dx-0.0225_dy0_dth0__normal` | walk_back | 0.62 | 0.61 | 0.61 | 0.62 |
| `walk_back__dx-0.0275_dy0_dth0__gentle` | walk_back | 0.43 | 0.41 | 0.41 | 0.44 |
| `walk_back__dx-0.0325_dy0_dth0__normal` | walk_back | 0.65 | 0.65 | 0.64 | 0.66 |
| `walk_back__dx-0.0375_dy0_dth0__gentle` | walk_back | 0.44 | 0.43 | 0.43 | 0.46 |
| `walk_back__dx-0.045_dy0_dth0__normal` | walk_back | 0.65 | 0.65 | 0.65 | 0.66 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.60 | 0.59 | 0.58 | 0.60 |
| `walk_fwd__dx0.0275_dy0_dth0__normal` | walk_fwd | 0.61 | 0.60 | 0.59 | 0.61 |
| `walk_fwd__dx0.035_dy0_dth0__gentle` | walk_fwd | 0.47 | 0.48 | 0.48 | 0.48 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.79 | 0.79 | 0.78 | 0.80 |
| `walk_fwd__dx0.055_dy0_dth0__gentle` | walk_fwd | 0.72 | 0.71 | 0.70 | 0.72 |
| `walk_turn__dx0.025_dy0_dth-0.18__normal` | walk_turn | 0.80 | 0.80 | 0.79 | 0.80 |
| `walk_turn__dx0.025_dy0_dth0.12__normal` | walk_turn | 0.63 | 0.63 | 0.62 | 0.64 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 1.17 | 0.96 | 0.77 | 1.17 |
| `walk_turn__dx0.035_dy0_dth0.08__gentle` | walk_turn | 0.61 | 0.58 | 0.59 | 0.62 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.81 | 0.81 | 0.80 | 0.82 |
