# Study cv7: summary (PREREG v2)

Library `clips_v7`: 82 train clips (37 measured infeasible), 56 test clips. Seeds [0, 1, 2]. Lower e is better.

**One primary result:** curated vs full and random at 55%, nominal test, original score (PREREG v2 §7). Everything else is SECONDARY (pre-registered, no pass bar, no multiple-comparison correction) or EXPLORATORY (added after results were seen), and is labelled as such.

## Selection score validation

| candidate | AUC (mean over scorers) | per scorer | Spearman between scorers |
|---|---|---|---|
| score | 0.835 | 0.832, 0.835, 0.838 | 1.00, 1.00, 1.00 |
| score_v2 | 0.762 | 0.763, 0.754, 0.769 | 0.99, 0.99, 0.98 |
| score_v3 | 0.862 | 0.869, 0.849, 0.869 | 0.99, 0.99, 0.99 |
| fall_rate | 0.622 | 0.622, 0.622, 0.622 | 1.00, 1.00, 1.00 |

Selection score: **score_v3** (highest AUC; within 0.02 the original score wins).

Label stability: 1 of 55 held poses are borderline (< 80% of 27 perturbed hold tests agree with the label): `lean__33__dx+0.051`.

| candidate | AUC without the borderline clips (mean over scorers) |
|---|---|
| score | 0.831 |
| score_v2 | 0.756 |
| score_v3 | 0.859 |
| fall_rate | 0.622 |

## Subsets: clean clips, leans and measured-infeasible clips kept

| selector | 40% | 55% | 70% | 85% |
|---|---|---|---|---|
| curated | 33 clips: 22 clean, 11 leans, 3 infeasible, 1 borderline | 45 clips: 27 clean, 18 leans, 10 infeasible, 1 borderline | 57 clips: 35 clean, 22 leans, 14 infeasible, 1 borderline | 70 clips: 37 clean, 33 leans, 25 infeasible, 1 borderline |
| kinematic | 33 clips: 20 clean, 13 leans, 9 infeasible, 0 borderline | 45 clips: 25 clean, 20 leans, 15 infeasible, 1 borderline | 57 clips: 30 clean, 27 leans, 21 infeasible, 1 borderline | 70 clips: 36 clean, 34 leans, 27 infeasible, 1 borderline |
| oracle | 33 clips: 27 clean, 6 leans, 0 infeasible, 1 borderline | 45 clips: 37 clean, 8 leans, 0 infeasible, 1 borderline | 57 clips: 37 clean, 20 leans, 12 infeasible, 1 borderline | 70 clips: 37 clean, 33 leans, 25 infeasible, 1 borderline |
| random (seed 0) | 33 clips: 16 clean, 17 leans, 15 infeasible, 0 borderline | 45 clips: 22 clean, 23 leans, 19 infeasible, 0 borderline | 57 clips: 28 clean, 29 leans, 24 infeasible, 0 borderline | 70 clips: 35 clean, 35 leans, 29 infeasible, 0 borderline |

## The curve: mean test e (nominal), mean over seeds [seed range]

full (all 82 clips): 0.501 [0.494, 0.515]; checked (every kinematic-check pass, natural size): 0.456 [0.430, 0.474]

| selector | 40% | 55% | 70% | 85% |
|---|---|---|---|---|
| curated | 0.580 [0.544, 0.629] | 0.519 [0.483, 0.538] | 0.487 [0.461, 0.506] | 0.462 [0.435, 0.491] |
| kinematic | 0.461 [0.452, 0.477] | 0.461 [0.446, 0.489] | 0.455 [0.452, 0.460] | 0.454 [0.443, 0.475] |
| oracle | 0.442 [0.426, 0.471] | 0.451 [0.418, 0.479] | 0.426 [0.421, 0.433] | 0.435 [0.428, 0.443] |
| random | 0.657 [0.549, 0.747] | 0.624 [0.573, 0.719] | 0.498 [0.493, 0.507] | 0.477 [0.451, 0.512] |

Curated minus each selector (source-level 95% CI; negative = curated better):

| vs | 40% | 55% | 70% | 85% |
|---|---|---|---|---|
| full | +0.079 [-0.055, +0.207] | +0.018 [-0.075, +0.085] | -0.014 [-0.056, +0.007] | -0.039 [-0.136, +0.003] |
| kinematic | +0.118 [+0.020, +0.247] | +0.058 [-0.004, +0.163] | +0.032 [-0.023, +0.157] | +0.008 [-0.039, +0.085] |
| oracle | +0.138 [+0.040, +0.262] | +0.068 [-0.007, +0.145] | +0.061 [+0.002, +0.197] | +0.027 [-0.008, +0.115] |
| random | -0.077 [-0.269, +0.065] | -0.105 [-0.290, +0.023] | -0.011 [-0.049, +0.033] | -0.015 [-0.080, +0.041] |

## PRIMARY: 55% keep-fraction, test nominal, score

| condition | mean e | completion | falls / clip | coverage |
| curated | 0.519 | 0.976 | 0.72 | 1.00 |
| full | 0.501 | 0.976 | 0.38 | 1.00 |
| kinematic | 0.461 | 0.994 | 0.13 | 1.00 |
| oracle | 0.451 | 0.986 | 0.24 | 1.00 |
| random | 0.624 | 0.940 | 1.14 | 1.00 |
| checked | 0.456 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 0.492 | 0.988 | 0.36 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| full | +0.018 [-0.075, +0.085] | +0.01 | +0.01 | -0.29 | +0.01 | +0.29 | +0.00 | +0.08 | +0.01 | +0.00 | +0.22 |
| kinematic | +0.058 [-0.004, +0.163] | -0.02 | -0.00 | +0.25 | -0.01 | +0.21 | -0.01 | +0.09 | -0.02 | -0.03 | +0.21 |
| oracle | +0.068 [-0.006, +0.144] | -0.00 | +0.00 | -0.01 | +0.02 | +0.32 | -0.00 | +0.15 | +0.06 | +0.04 | +0.26 |
| random | -0.105 [-0.286, +0.023] | +0.01 | -0.00 | -1.12 | +0.02 | +0.03 | -0.00 | +0.03 | +0.04 | -0.01 | +0.08 |
| checked | +0.064 [+0.003, +0.142] | -0.01 | -0.00 | +0.08 | +0.01 | +0.29 | -0.01 | +0.12 | +0.03 | +0.02 | +0.24 |
| curatedscore_f55 | +0.027 [-0.040, +0.118] | +0.00 | +0.00 | +0.14 | -0.03 | +0.24 | +0.00 | -0.01 | -0.03 | -0.06 | +0.11 |
- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.062 (bar: ≥ −0.05): **no**
- **pass: no**
## Leave-one-clip-out: curated minus each condition with each test clip dropped
| vs | Δe range | CI upper bound range | drops that flip the CI past 0 |
| full | +0.006 .. +0.037 | +0.064 .. +0.090 | none |
| kinematic | +0.038 .. +0.061 | +0.108 .. +0.168 | none |
| oracle | +0.057 .. +0.072 | +0.127 .. +0.149 | none |
| random | -0.111 .. -0.071 | +0.018 .. +0.029 | none |
| checked | +0.051 .. +0.067 | +0.112 .. +0.149 | none |
| curatedscore_f55 | +0.016 .. +0.030 | +0.087 .. +0.124 | none |

## SECONDARY: 55% keep-fraction, test nominal, score_v2

Secondary: reported without a pass bar and without correction for multiple comparisons; read as supporting evidence only.

| condition | mean e | completion | falls / clip | coverage |
| curated | 1.035 | 0.976 | 0.72 | 1.00 |
| full | 1.015 | 0.976 | 0.38 | 1.00 |
| kinematic | 1.037 | 0.994 | 0.13 | 1.00 |
| oracle | 0.885 | 0.986 | 0.24 | 1.00 |
| random | 1.084 | 0.940 | 1.14 | 1.00 |
| checked | 0.917 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 1.126 | 0.988 | 0.36 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| full | +0.020 [-0.092, +0.124] | +0.01 | +0.00 | -0.27 | -0.09 | +0.34 | -0.00 | +0.23 | +0.01 | -0.14 | +0.30 |
| kinematic | -0.002 [-0.139, +0.161] | -0.01 | -0.00 | +0.27 | -0.05 | +0.31 | -0.01 | +0.32 | -0.59 | -0.46 | +0.44 |
| oracle | +0.149 [+0.045, +0.265] | -0.01 | +0.01 | -0.02 | +0.05 | +0.43 | +0.00 | +0.43 | +0.24 | +0.06 | +0.54 |
| random | -0.049 [-0.256, +0.117] | +0.00 | +0.00 | -1.17 | -0.09 | +0.20 | -0.01 | +0.30 | +0.36 | -0.12 | +0.20 |
| checked | +0.118 [+0.030, +0.223] | -0.02 | +0.00 | +0.08 | -0.02 | +0.36 | +0.00 | +0.30 | +0.12 | +0.01 | +0.57 |
| curatedscore_f55 | -0.091 [-0.204, +0.033] | +0.01 | +0.00 | +0.13 | -0.08 | +0.19 | -0.00 | +0.04 | -0.55 | -0.41 | -0.16 |
- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.062 (bar: ≥ −0.05): **no**
- **pass: no**

## SECONDARY: 55% keep-fraction, test nominal, score_v3

Secondary: reported without a pass bar and without correction for multiple comparisons; read as supporting evidence only.

| condition | mean e | completion | falls / clip | coverage |
| curated | 1.375 | 0.976 | 0.72 | 1.00 |
| full | 1.306 | 0.976 | 0.38 | 1.00 |
| kinematic | 1.329 | 0.994 | 0.13 | 1.00 |
| oracle | 1.174 | 0.986 | 0.24 | 1.00 |
| random | 1.414 | 0.940 | 1.14 | 1.00 |
| checked | 1.198 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 1.477 | 0.988 | 0.36 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| full | +0.069 [-0.053, +0.199] | +0.01 | -0.04 | -0.21 | -0.05 | +0.56 | -0.05 | +0.31 | +0.04 | -0.11 | +0.55 |
| kinematic | +0.046 [-0.111, +0.242] | +0.03 | -0.01 | +0.40 | -0.06 | +0.48 | +0.01 | +0.36 | -0.56 | -0.47 | +0.64 |
| oracle | +0.201 [+0.074, +0.348] | -0.00 | +0.00 | -0.06 | +0.05 | +0.66 | +0.00 | +0.58 | +0.24 | +0.10 | +0.79 |
| random | -0.039 [-0.260, +0.141] | +0.01 | +0.02 | -1.22 | -0.04 | +0.19 | -0.01 | +0.31 | +0.40 | -0.12 | +0.23 |
| checked | +0.177 [+0.067, +0.313] | +0.02 | +0.01 | +0.12 | -0.01 | +0.57 | +0.02 | +0.39 | +0.15 | +0.02 | +0.82 |
| curatedscore_f55 | -0.102 [-0.226, +0.040] | +0.02 | +0.00 | +0.11 | -0.12 | +0.26 | -0.01 | -0.04 | -0.57 | -0.45 | -0.10 |
- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.062 (bar: ≥ −0.05): **no**
- **pass: no**

## SECONDARY: 55% keep-fraction, test nominal, tilt_err

Secondary: reported without a pass bar and without correction for multiple comparisons; read as supporting evidence only.

| condition | mean e | completion | falls / clip | coverage |
| curated | 0.039 | 0.976 | 0.72 | 1.00 |
| full | 0.035 | 0.976 | 0.38 | 1.00 |
| kinematic | 0.030 | 0.994 | 0.13 | 1.00 |
| oracle | 0.032 | 0.986 | 0.24 | 1.00 |
| random | 0.048 | 0.940 | 1.14 | 1.00 |
| checked | 0.030 | 0.992 | 0.15 | 1.00 |
| curatedscore_f55 | 0.038 | 0.988 | 0.36 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| full | +0.004 [-0.003, +0.011] | +0.00 | -0.00 | -0.01 | +0.00 | +0.03 | -0.00 | +0.01 | +0.00 | +0.00 | +0.03 |
| kinematic | +0.009 [+0.001, +0.021] | +0.00 | -0.00 | +0.04 | -0.00 | +0.02 | +0.00 | +0.01 | +0.00 | -0.00 | +0.03 |
| oracle | +0.007 [-0.001, +0.015] | +0.00 | -0.00 | -0.00 | +0.00 | +0.03 | +0.00 | +0.02 | +0.00 | +0.00 | +0.03 |
| random | -0.009 [-0.026, +0.003] | +0.00 | +0.00 | -0.10 | +0.01 | -0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| checked | +0.009 [+0.003, +0.019] | +0.00 | +0.00 | +0.02 | +0.00 | +0.03 | +0.00 | +0.01 | +0.00 | +0.00 | +0.03 |
| curatedscore_f55 | +0.001 [-0.006, +0.010] | +0.00 | -0.00 | +0.01 | -0.00 | +0.01 | -0.00 | -0.01 | -0.00 | -0.00 | +0.01 |
- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.062 (bar: ≥ −0.05): **no**
- **pass: no**

## SECONDARY: 55% keep-fraction, test push03, score

Secondary: reported without a pass bar and without correction for multiple comparisons; read as supporting evidence only.

| condition | mean e | completion | falls / clip | coverage |
| curated | 0.729 | 0.900 | 2.48 | 1.00 |
| full | 0.693 | 0.909 | 1.92 | 1.00 |
| kinematic | 0.665 | 0.922 | 1.85 | 1.00 |
| oracle | 0.665 | 0.912 | 2.01 | 1.00 |
| random | 0.820 | 0.870 | 2.76 | 1.00 |
| checked | 0.647 | 0.926 | 1.71 | 1.00 |
| curatedscore_f55 | 0.711 | 0.910 | 2.20 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| full | +0.036 [-0.059, +0.108] | +0.02 | -0.01 | -0.24 | +0.00 | +0.27 | +0.00 | +0.16 | +0.06 | +0.03 | +0.20 |
| kinematic | +0.064 [-0.002, +0.165] | -0.01 | -0.02 | +0.26 | -0.04 | +0.20 | +0.02 | +0.17 | -0.04 | -0.02 | +0.20 |
| oracle | +0.064 [-0.011, +0.141] | -0.01 | -0.01 | -0.00 | +0.03 | +0.31 | +0.01 | +0.17 | -0.01 | +0.05 | +0.23 |
| random | -0.091 [-0.254, +0.029] | +0.01 | +0.00 | -1.01 | +0.04 | +0.01 | -0.02 | +0.07 | +0.01 | -0.01 | +0.06 |
| checked | +0.082 [+0.021, +0.158] | -0.00 | -0.02 | +0.09 | +0.06 | +0.25 | +0.02 | +0.21 | +0.04 | +0.04 | +0.25 |
| curatedscore_f55 | +0.018 [-0.050, +0.106] | +0.00 | -0.01 | +0.13 | -0.09 | +0.16 | +0.02 | +0.03 | -0.02 | -0.05 | +0.07 |
- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.070 (bar: ≥ −0.05): **no**
- **pass: no**

## SECONDARY: 55% keep-fraction, test push06, score

Secondary: reported without a pass bar and without correction for multiple comparisons; read as supporting evidence only.

| condition | mean e | completion | falls / clip | coverage |
| curated | 1.268 | 0.681 | 6.73 | 0.40 |
| full | 1.265 | 0.681 | 6.55 | 0.40 |
| kinematic | 1.232 | 0.696 | 6.35 | 0.40 |
| oracle | 1.232 | 0.690 | 6.42 | 0.40 |
| random | 1.355 | 0.655 | 6.93 | 0.30 |
| checked | 1.240 | 0.691 | 6.49 | 0.50 |
| curatedscore_f55 | 1.262 | 0.686 | 6.60 | 0.40 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| full | +0.003 [-0.065, +0.046] | -0.00 | +0.03 | -0.21 | +0.03 | +0.14 | -0.01 | +0.01 | +0.02 | +0.02 | +0.07 |
| kinematic | +0.036 [-0.007, +0.101] | -0.03 | +0.04 | +0.12 | +0.04 | +0.16 | -0.00 | +0.02 | -0.01 | +0.00 | +0.08 |
| oracle | +0.037 [-0.015, +0.086] | -0.01 | +0.02 | -0.00 | +0.05 | +0.16 | +0.00 | +0.03 | +0.03 | +0.05 | +0.11 |
| random | -0.087 [-0.226, +0.013] | -0.02 | +0.00 | -0.86 | +0.06 | +0.06 | -0.02 | -0.02 | -0.00 | -0.01 | +0.04 |
| checked | +0.029 [-0.015, +0.077] | -0.01 | +0.03 | +0.01 | +0.05 | +0.13 | -0.01 | +0.04 | -0.01 | +0.01 | +0.11 |
| curatedscore_f55 | +0.006 [-0.043, +0.058] | -0.01 | +0.03 | +0.04 | -0.03 | +0.11 | -0.01 | -0.02 | -0.03 | -0.01 | +0.02 |
- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.039 (bar: ≥ −0.05): **yes**
- **pass: no**

## SECONDARY: 55% keep-fraction, test fric06, score

Secondary: reported without a pass bar and without correction for multiple comparisons; read as supporting evidence only.

| condition | mean e | completion | falls / clip | coverage |
| curated | 0.512 | 0.979 | 0.65 | 1.00 |
| full | 0.500 | 0.976 | 0.37 | 1.00 |
| kinematic | 0.459 | 0.995 | 0.12 | 1.00 |
| oracle | 0.448 | 0.988 | 0.21 | 1.00 |
| random | 0.618 | 0.941 | 1.07 | 1.00 |
| checked | 0.456 | 0.992 | 0.17 | 1.00 |
| curatedscore_f55 | 0.485 | 0.990 | 0.23 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| full | +0.012 [-0.083, +0.079] | +0.01 | +0.00 | -0.31 | +0.01 | +0.29 | +0.00 | +0.07 | +0.00 | +0.00 | +0.20 |
| kinematic | +0.053 [-0.005, +0.152] | -0.02 | -0.00 | +0.23 | -0.00 | +0.20 | -0.01 | +0.07 | -0.02 | -0.03 | +0.20 |
| oracle | +0.064 [-0.008, +0.137] | -0.00 | +0.00 | -0.00 | +0.02 | +0.31 | -0.00 | +0.13 | +0.05 | +0.04 | +0.24 |
| random | -0.106 [-0.286, +0.021] | +0.01 | -0.00 | -1.12 | +0.02 | +0.02 | -0.00 | +0.03 | +0.03 | -0.01 | +0.09 |
| checked | +0.056 [-0.002, +0.130] | -0.01 | -0.00 | +0.05 | +0.01 | +0.28 | -0.01 | +0.10 | +0.03 | +0.02 | +0.22 |
| curatedscore_f55 | +0.027 [-0.040, +0.118] | +0.00 | +0.00 | +0.14 | -0.03 | +0.25 | +0.00 | -0.01 | -0.03 | -0.06 | +0.11 |
- curated beats full with the CI excluding 0: **no**
- curated beats random with the CI excluding 0: **no**
- worst per-category completion drop vs full: -0.057 (bar: ≥ −0.05): **no**
- **pass: no**

## f*: curated's best keep-fraction on validation (amendment 11-16)

| fraction | curated val e per seed | mean |
|---|---|---|
| 40% | 0.693, 0.502, 0.622 | 0.606 |
| 55% | 0.417, 0.611, 0.602 | 0.543 |
| 70% | 0.611, 0.613, 0.451 | 0.558 |
| 85% | 0.608, 0.470, 0.418 | 0.499 |

f* = **85%** (lowest mean 85%; the main fraction is kept within 0.01). Phases 2 and 3 run at f*.

## EXPLORATORY: stratified curation at 55% (added 11-17 after interim results, not pre-registered)

`curatedstrat_f55`: 45 clips, 31 clean, 6 measured infeasible. Negative = stratified better.

| condition | mean e | completion | falls / clip | coverage |
| curatedstrat | 0.461 | 0.986 | 0.38 | 1.00 |
| curated | 0.519 | 0.976 | 0.72 | 1.00 |
| full | 0.501 | 0.976 | 0.38 | 1.00 |
| oracle | 0.451 | 0.986 | 0.24 | 1.00 |
| kinematic | 0.461 | 0.994 | 0.13 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| curated | -0.059 [-0.127, -0.003] | -0.02 | -0.01 | -0.07 | -0.01 | -0.27 | -0.01 | -0.10 | -0.06 | -0.02 | -0.13 |
| full | -0.041 [-0.127, +0.007] | -0.01 | -0.00 | -0.35 | +0.00 | +0.03 | -0.01 | -0.02 | -0.05 | -0.02 | +0.09 |
| oracle | +0.009 [-0.053, +0.059] | -0.02 | -0.01 | -0.08 | +0.02 | +0.05 | -0.01 | +0.05 | -0.00 | +0.02 | +0.13 |
| kinematic | -0.000 [-0.046, +0.075] | -0.03 | -0.01 | +0.19 | -0.01 | -0.05 | -0.02 | -0.01 | -0.08 | -0.04 | +0.08 |

## EXPLORATORY: stratified curation at 85% (added 11-17 after interim results, not pre-registered)

`curatedstrat_f85`: 70 clips, 37 clean, 25 measured infeasible. Negative = stratified better.

| condition | mean e | completion | falls / clip | coverage |
| curatedstrat | 0.458 | 0.990 | 0.13 | 1.00 |
| curated | 0.462 | 0.989 | 0.18 | 1.00 |
| full | 0.501 | 0.976 | 0.38 | 1.00 |
| oracle | 0.435 | 1.000 | 0.02 | 1.00 |
| kinematic | 0.454 | 0.997 | 0.08 | 1.00 |
| vs | Δe overall [95% CI] | bow | crouch | head | march | side_step | sway | turn_in_place | walk_back | walk_fwd | walk_turn |
| curated | -0.004 [-0.074, +0.069] | -0.00 | -0.00 | -0.01 | +0.00 | +0.00 | -0.00 | -0.02 | +0.00 | +0.00 | -0.01 |
| full | -0.043 [-0.150, +0.006] | +0.02 | +0.01 | -0.34 | +0.00 | -0.00 | +0.01 | -0.05 | -0.02 | -0.02 | -0.02 |
| oracle | +0.023 [-0.008, +0.106] | +0.01 | -0.00 | +0.23 | +0.00 | -0.01 | -0.00 | -0.01 | +0.01 | -0.00 | -0.01 |
| kinematic | +0.004 [-0.039, +0.078] | -0.00 | -0.01 | +0.13 | -0.00 | -0.02 | -0.01 | -0.02 | -0.01 | -0.01 | -0.02 |

## Training cost (55% keep-fraction and full)

Threshold: validation e ≤ 0.512 (1.1 × the best final validation e). Headline cost: M steps to threshold. Wall-clock is secondary: evaluations share the GPU with training and launches wait for them.

| condition | M steps to threshold (per seed) | val e at 25 / 50 / 75 / 100% | h to threshold | wall-clock h | M steps / h |
|---|---|---|---|---|---|
| full | 101, 101, 43 | 0.586 / 0.501 / 0.561 / 0.617 | 0.76, 0.75, 0.33 | 1.51 | 133 |
| curated | 202, —, — | 0.569 / 0.587 / 0.600 / 0.553 | 1.55, —, — | 1.53 | 132 |
| kinematic | 43, 43, 43 | 0.463 / 0.491 / 0.477 / 0.465 | 0.32, 0.33, 0.33 | 1.53 | 132 |
| oracle | 43, 101, 43 | 0.482 / 0.444 / 0.516 / 0.497 | 0.34, 0.79, 0.33 | 1.57 | 129 |
| random | 43, —, — | 0.612 / 0.654 / 0.645 / 0.645 | 0.33, —, — | 1.51 | 134 |
| checked | —, 144, 43 | 0.544 / 0.536 / 0.485 / 0.505 | —, 1.08, 0.32 | 1.52 | 133 |
| curatedscore_f55 | 43, 144, 43 | 0.536 / 0.566 / 0.503 / 0.536 | 0.33, 1.10, 0.33 | 1.53 | 132 |

**Selection overhead** (paid once, before any final policy trains):

- curated: 3 scoring policies, 6.7 GPU-h of training (2.26, 2.22, 2.24 h), plus scoring every train clip with each (3 evaluations)
- kinematic: the kinematic check, seconds of CPU
- oracle (physics filter): the hold test, about a second of CPU per clip
- random, full: none

Total GPU-h per condition at this fraction = 3 seeds × wall-clock above, plus the overhead for curated.
