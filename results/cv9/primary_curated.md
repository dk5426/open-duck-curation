# cv9 primary (55%, nominal test, original score): curated

69 test clips (69 bootstrap units: sources), 14 categories, metric `score`. Lower e is better. Dropped (every condition falls in >= 0.5 of rollouts): `side_step__dx0_dy-0.025_dth0__gentle`.

## Per condition

| condition | mean e | completion | falls / clip | coverage |
|---|---|---|---|---|
| full | 0.356 | 0.993 | 0.43 | 1.00 |
| curatedtn | 0.355 | 0.998 | 0.14 | 1.00 |
| curated | 0.401 | 0.995 | 0.50 | 1.00 |
| kinematic | 0.353 | 0.999 | 0.21 | 1.00 |
| random | 0.359 | 0.993 | 0.36 | 1.00 |

## curated minus each other condition (paired over test clips; negative = curated better)

| vs | Δe overall [97.5% CI] | bow | crouch | dance | head | headbang | hop | leg_lift | side_step | sway | turn_in_place | twist | walk_back | walk_fwd | walk_turn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | +0.045 [+0.014, +0.081] | +0.04 | -0.00 | +0.00 | -0.01 | -0.01 | -0.00 | +0.04 | -0.05 | -0.01 | +0.18 | -0.00 | +0.09 | +0.24 | +0.12 |
| curatedtn | +0.046 [+0.009, +0.085] | +0.01 | -0.00 | -0.01 | -0.01 | -0.17 | +0.00 | +0.02 | +0.12 | -0.02 | +0.21 | -0.01 | +0.09 | +0.24 | +0.18 |
| kinematic | +0.048 [+0.017, +0.086] | +0.01 | -0.00 | +0.00 | -0.01 | -0.04 | -0.00 | -0.02 | +0.08 | -0.01 | +0.18 | -0.00 | +0.09 | +0.24 | +0.17 |
| random | +0.042 [+0.001, +0.083] | +0.05 | -0.00 | -0.03 | -0.02 | -0.02 | -0.00 | +0.02 | -0.02 | -0.07 | +0.20 | -0.03 | +0.10 | +0.24 | +0.15 |

## P.9 pass bar

- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.029 (bar: ≥ −0.05): **yes**
- **pass: no**

## Leave-one-clip-out: curated minus each condition with each test clip dropped

| vs | Δe range | CI upper bound range | drops that flip the CI past 0 |
|---|---|---|---|
| full | +0.037 .. +0.050 | +0.068 .. +0.086 | none |
| curatedtn | +0.037 .. +0.050 | +0.070 .. +0.089 | none |
| kinematic | +0.040 .. +0.051 | +0.072 .. +0.088 | none |
| random | +0.034 .. +0.047 | +0.070 .. +0.086 | none |

## Secondary: test clips inside vs outside the training parameter range

Inside: bow__pitch12deg__slow, bow__pitch15deg__fast, bow__pitch17deg__slow, bow__pitch22deg__fast, bow__pitch24deg__slow, crouch__depth0.30__slow, crouch__depth0.40__fast, crouch__depth0.60__slow, crouch__depth0.75__fast, crouch__depth0.90__slow, dance__f1.25_a0.55, dance__f1.75_a0.5, dance__f1_a0.75, dance__f2.25_a0.65, dance__f2_a0.45, head__nod_a0.85__slow, head__shake_a0.85__fast, head__tilt_a0.7__fast, headbang__f1.5_a0.35, headbang__f1_a0.4, headbang__f2.5_a0.2, headbang__f2_a0.35, headbang__f3_a0.2, hop__h0.0035_n2, hop__h0.0065_n2, hop__h0.006_n1, hop__h0.0075_n1, hop__h0.0095_n1, kick__r0.045_tau0.5_dy0.045, march__lift0.0175__gentle, march__lift0.03__normal, side_step__dx0_dy-0.0175_dth0__gentle, stomp__lift0.025_period1.2_dy0.045, sway__amp0.0135m__f0.5, sway__amp0.0175m__f1.0, sway__amp0.0225m__f0.5, sway__amp0.0275m__f1.0, tap__reach0.035_period1.4_dy0.045, turn_in_place__dx0_dy0_dth0.175__normal, twist__f0.5_a0.2, twist__f0.75_a0.25, twist__f1.25_a0.15, twist__f1.5_a0.2, twist__f1_a0.3, walk_back__dx-0.0225_dy0_dth0__normal, walk_back__dx-0.0275_dy0_dth0__gentle, walk_back__dx-0.0325_dy0_dth0__normal, walk_back__dx-0.0375_dy0_dth0__gentle, walk_fwd__dx0.025_dy0_dth0__normal, walk_fwd__dx0.0275_dy0_dth0__normal, walk_fwd__dx0.035_dy0_dth0__gentle, walk_turn__dx0.025_dy0_dth0.12__normal

**inside**

| vs | clips | Δe [97.5% CI] |
|---|---|---|
| full | 52 | +0.027 [+0.006, +0.060] |
| curatedtn | 52 | +0.013 [-0.022, +0.051] |
| kinematic | 52 | +0.021 [-0.006, +0.056] |
| random | 52 | +0.018 [-0.025, +0.057] |

**outside**

| vs | clips | Δe [97.5% CI] |
|---|---|---|
| full | 17 | +0.102 [+0.004, +0.206] |
| curatedtn | 17 | +0.145 [+0.071, +0.240] |
| kinematic | 17 | +0.131 [+0.058, +0.228] |
| random | 17 | +0.117 [+0.021, +0.224] |


## Per clip (e)

| clip | category | full | curatedtn | curated | kinematic | random |
|---|---|---|---|---|---|---|
| `bow__pitch12deg__slow` | bow | 0.15 | 0.19 | 0.17 | 0.17 | 0.15 |
| `bow__pitch15deg__fast` | bow | 0.17 | 0.19 | 0.24 | 0.20 | 0.17 |
| `bow__pitch17deg__slow` | bow | 0.17 | 0.20 | 0.20 | 0.19 | 0.16 |
| `bow__pitch22deg__fast` | bow | 0.22 | 0.23 | 0.27 | 0.25 | 0.20 |
| `bow__pitch24deg__slow` | bow | 0.21 | 0.22 | 0.23 | 0.23 | 0.19 |
| `crouch__depth0.30__slow` | crouch | 0.11 | 0.11 | 0.11 | 0.11 | 0.11 |
| `crouch__depth0.40__fast` | crouch | 0.11 | 0.11 | 0.10 | 0.11 | 0.11 |
| `crouch__depth0.60__slow` | crouch | 0.11 | 0.11 | 0.11 | 0.11 | 0.11 |
| `crouch__depth0.75__fast` | crouch | 0.11 | 0.11 | 0.11 | 0.11 | 0.11 |
| `crouch__depth0.90__slow` | crouch | 0.11 | 0.11 | 0.11 | 0.11 | 0.11 |
| `dance__f1.25_a0.55` | dance | 0.11 | 0.12 | 0.11 | 0.11 | 0.13 |
| `dance__f1.75_a0.5` | dance | 0.11 | 0.12 | 0.12 | 0.12 | 0.14 |
| `dance__f1_a0.75` | dance | 0.13 | 0.13 | 0.13 | 0.12 | 0.15 |
| `dance__f2.25_a0.65` | dance | 0.13 | 0.15 | 0.13 | 0.14 | 0.17 |
| `dance__f2_a0.45` | dance | 0.11 | 0.12 | 0.12 | 0.12 | 0.14 |
| `head__look_tilt_a1__fast` | head | 0.14 | 0.14 | 0.12 | 0.15 | 0.15 |
| `head__nod_a0.85__slow` | head | 0.11 | 0.11 | 0.11 | 0.11 | 0.12 |
| `head__nod_tilt_a1__slow` | head | 0.14 | 0.13 | 0.12 | 0.12 | 0.15 |
| `head__shake_a0.85__fast` | head | 0.10 | 0.11 | 0.10 | 0.10 | 0.12 |
| `head__tilt_a0.7__fast` | head | 0.10 | 0.11 | 0.10 | 0.10 | 0.11 |
| `headbang__f1.5_a0.35` | headbang | 0.20 | 0.38 | 0.19 | 0.21 | 0.21 |
| `headbang__f1_a0.4` | headbang | 0.19 | 0.24 | 0.19 | 0.21 | 0.22 |
| `headbang__f2.5_a0.2` | headbang | 0.18 | 0.28 | 0.17 | 0.22 | 0.18 |
| `headbang__f2_a0.35` | headbang | 0.24 | 0.46 | 0.23 | 0.24 | 0.23 |
| `headbang__f3_a0.2` | headbang | 0.19 | 0.43 | 0.18 | 0.29 | 0.19 |
| `hop__h0.0035_n2` | hop | 0.15 | 0.14 | 0.15 | 0.15 | 0.15 |
| `hop__h0.0065_n2` | hop | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 |
| `hop__h0.006_n1` | hop | 0.14 | 0.14 | 0.14 | 0.15 | 0.14 |
| `hop__h0.0075_n1` | hop | 0.14 | 0.14 | 0.14 | 0.15 | 0.14 |
| `hop__h0.0095_n1` | hop | 0.14 | 0.14 | 0.14 | 0.15 | 0.14 |
| `kick__r0.045_tau0.5_dy0.045` | leg_lift | 0.29 | 0.39 | 0.39 | 0.28 | 0.33 |
| `march__lift0.0175__gentle` | leg_lift | 0.38 | 0.36 | 0.38 | 0.39 | 0.39 |
| `march__lift0.03__normal` | leg_lift | 0.69 | 0.68 | 0.73 | 0.66 | 0.65 |
| `stomp__lift0.025_period1.2_dy0.045` | leg_lift | 0.33 | 0.36 | 0.37 | 0.49 | 0.37 |
| `tap__reach0.035_period1.4_dy0.045` | leg_lift | 0.36 | 0.37 | 0.38 | 0.53 | 0.38 |
| `side_step__dx0_dy-0.0175_dth0__gentle` | side_step | 0.99 | 0.70 | 0.91 | 0.71 | 0.95 |
| `side_step__dx0_dy0.0225_dth0__normal` | side_step | 0.71 | 0.69 | 0.79 | 0.73 | 0.70 |
| `side_step__dx0_dy0.0275_dth0__gentle` | side_step | 1.17 | 0.80 | 0.88 | 0.89 | 1.09 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | 0.64 | 0.63 | 0.71 | 0.66 | 0.63 |
| `sway__amp0.0135m__f0.5` | sway | 0.13 | 0.14 | 0.12 | 0.14 | 0.13 |
| `sway__amp0.0175m__f1.0` | sway | 0.17 | 0.18 | 0.17 | 0.18 | 0.16 |
| `sway__amp0.0225m__f0.5` | sway | 0.18 | 0.18 | 0.16 | 0.18 | 0.17 |
| `sway__amp0.0275m__f1.0` | sway | 0.26 | 0.30 | 0.27 | 0.27 | 0.59 |
| `sway__amp0.0325m__f0.5` | sway | 0.25 | 0.25 | 0.24 | 0.25 | 0.24 |
| `turn_in_place__dx0_dy0_dth-0.20__normal` | turn_in_place | 0.69 | 0.66 | 1.28 | 0.67 | 0.67 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | 0.51 | 0.49 | 0.72 | 0.51 | 0.50 |
| `turn_in_place__dx0_dy0_dth0.10__gentle` | turn_in_place | 0.38 | 0.36 | 0.38 | 0.37 | 0.38 |
| `turn_in_place__dx0_dy0_dth0.175__normal` | turn_in_place | 0.63 | 0.60 | 0.68 | 0.64 | 0.61 |
| `turn_in_place__dx0_dy0_dth0.25__normal` | turn_in_place | 0.71 | 0.68 | 0.79 | 0.73 | 0.70 |
| `twist__f0.5_a0.2` | twist | 0.13 | 0.14 | 0.12 | 0.13 | 0.17 |
| `twist__f0.75_a0.25` | twist | 0.14 | 0.15 | 0.14 | 0.14 | 0.18 |
| `twist__f1.25_a0.15` | twist | 0.12 | 0.12 | 0.12 | 0.12 | 0.14 |
| `twist__f1.5_a0.2` | twist | 0.14 | 0.13 | 0.13 | 0.13 | 0.15 |
| `twist__f1_a0.3` | twist | 0.16 | 0.16 | 0.16 | 0.15 | 0.18 |
| `walk_back__dx-0.0225_dy0_dth0__normal` | walk_back | 0.62 | 0.62 | 0.71 | 0.62 | 0.60 |
| `walk_back__dx-0.0275_dy0_dth0__gentle` | walk_back | 0.43 | 0.40 | 0.46 | 0.42 | 0.41 |
| `walk_back__dx-0.0325_dy0_dth0__normal` | walk_back | 0.65 | 0.67 | 0.78 | 0.66 | 0.63 |
| `walk_back__dx-0.0375_dy0_dth0__gentle` | walk_back | 0.44 | 0.42 | 0.49 | 0.43 | 0.43 |
| `walk_back__dx-0.045_dy0_dth0__normal` | walk_back | 0.65 | 0.67 | 0.79 | 0.67 | 0.64 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | 0.60 | 0.58 | 0.68 | 0.59 | 0.58 |
| `walk_fwd__dx0.0275_dy0_dth0__normal` | walk_fwd | 0.61 | 0.59 | 0.71 | 0.60 | 0.59 |
| `walk_fwd__dx0.035_dy0_dth0__gentle` | walk_fwd | 0.47 | 0.48 | 1.04 | 0.47 | 0.48 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | 0.79 | 0.81 | 1.01 | 0.79 | 0.81 |
| `walk_fwd__dx0.055_dy0_dth0__gentle` | walk_fwd | 0.72 | 0.74 | 0.93 | 0.75 | 0.74 |
| `walk_turn__dx0.025_dy0_dth-0.18__normal` | walk_turn | 0.80 | 0.80 | 1.07 | 0.80 | 0.79 |
| `walk_turn__dx0.025_dy0_dth0.12__normal` | walk_turn | 0.63 | 0.61 | 0.74 | 0.64 | 0.62 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | 1.17 | 0.92 | 1.14 | 0.89 | 1.03 |
| `walk_turn__dx0.035_dy0_dth0.08__gentle` | walk_turn | 0.61 | 0.61 | 0.72 | 0.59 | 0.61 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | 0.81 | 0.79 | 0.95 | 0.84 | 0.81 |
