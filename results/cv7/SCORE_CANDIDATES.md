# Study cv7: exploratory selection-score candidates

EXPLORATORY (added 2026-11-19 after Phase 1 results; not pre-registered). No training: the scoring policies' evaluations only. 82 train clips: 37 clean, 8 feasible leans, 37 infeasible leans. Scorers: seeds [0, 1, 2]. Early checkpoints: 43M, 107M.

AUC = probability an infeasible lean scores worse than a feasible clip (1 = perfect separation). The top-45 cut (55%) is a plain global cut without the coverage rule. The threshold rule keeps every train clip no worse than the worst clean val clip under the same candidate.

| candidate | AUC feasible vs infeasible | per scorer | AUC clean vs infeasible | top-45: clean dropped / infeasible kept | threshold: value, clips kept, clean dropped, infeasible kept |
|---|---|---|---|---|---|
| 1. typenorm_val | **0.978** | 0.982, 0.972, 0.983 | 0.974 | 2 / 2 | 5.25, 72, 0, 27 |
| 1+2. typenorm_val_x_progress_107M | **0.975** | 0.970, 0.950, 0.982 | 0.972 | 3 / 3 | n/a (no val evaluation) |
| balance | **0.966** | 0.965, 0.956, 0.976 | 0.966 | 4 / 4 | 4.73, 81, 0, 36 |
| tilt | **0.966** | 0.965, 0.956, 0.976 | 0.966 | 4 / 4 | 0.25, 76, 0, 31 |
| 1+2. typenorm_val_x_progress_43M | **0.957** | 0.956, 0.937, 0.969 | 0.951 | 5 / 5 | 8.65, 75, 0, 30 |
| 1. typenorm_train | **0.901** | 0.908, 0.898, 0.904 | 0.881 | 8 / 8 | n/a (no val evaluation) |
| 2. v3_x_progress_107M | **0.863** | 0.862, 0.833, 0.885 | 0.835 | 10 / 10 | n/a (no val evaluation) |
| score_v3 (current) | **0.861** | 0.869, 0.849, 0.869 | 0.831 | 10 / 10 | 3.22, 72, 0, 27 |
| 2. v3_x_progress_43M | **0.859** | 0.862, 0.832, 0.882 | 0.831 | 10 / 10 | 5.38, 75, 0, 30 |
| score (original) | **0.838** | 0.832, 0.835, 0.838 | 0.804 | 12 / 12 | 2.40, 73, 0, 28 |
| 2. progress_43M | **0.600** | 0.602, 0.589, 0.613 | 0.587 | 18 / 21 | 1.66, 82, 0, 37 |
| 2. progress_107M | **0.589** | 0.483, 0.526, 0.719 | 0.586 | 16 / 20 | n/a (no val evaluation) |

Reference: curated (score_v3 ensemble with the coverage rule) at 55% dropped 10 clean clips and kept 10 infeasible leans; stratified curation kept 31 clean and 6 infeasible; the oracle keeps all 37 clean and 0 infeasible.

## Ranks by motion type: `1. typenorm_val` against `score_v3 (current)`

| type | clips | worst rank, current | worst rank, best candidate |
|---|---|---|---|
| bow | 4 | 10 | 21 |
| crouch | 6 | 21 | 39 |
| head | 4 | 25 | 44 |
| march | 2 | 37 | 49 |
| side_step | 4 | 46 | 5 |
| sway | 2 | 26 | 45 |
| turn_in_place | 3 | 60 | 31 |
| walk_back | 2 | 61 | 46 |
| walk_fwd | 3 | 52 | 25 |
| walk_turn | 7 | 57 | 43 |
| feasible lean | 8 | 14 | 29 |
| infeasible lean | 37 | 82 | 82 |

For infeasible leans the best rank (the first one kept) matters more: current 12, best candidate 26.

