# Study cv9, Phase 2: other learners at 65%

SECONDARY (pre-registered, no pass bar, no correction for multiple comparisons). Same subsets, test clips and evaluator as Phase 1; only the learner changes. Lower e is better.

## Mean test e (nominal), mean over seeds [seed range]

| learner | curatedtn |
|---|---|
| PPO (Phase 1) | 0.356 [0.356, 0.356] |
| PPO without feed-forward | 2.436 [2.436, 2.436] |
| SAC | 2.262 [2.262, 2.262] |
| DAgger (student of the Phase 1 PPO) | 0.350 [0.350, 0.350] |
| ARS | 2.578 [2.578, 2.578] |
| FastTD3 | 1.347 [1.347, 1.347] |

## Completion and falls per clip

| learner | curatedtn |
|---|---|
| PPO (Phase 1) | 0.997 / 0.23 |
| PPO without feed-forward | 1.000 / 0.00 |
| SAC | 0.530 / 8.66 |
| DAgger (student of the Phase 1 PPO) | 0.999 / 0.13 |
| ARS | 0.442 / 8.96 |
| FastTD3 | 0.948 / 1.79 |

## Paired differences (source-level 95% CI; negative = the first condition better)

| learner |  |
|---|
| PPO (Phase 1) |  |
| PPO without feed-forward |  |
| SAC |  |
| DAgger (student of the Phase 1 PPO) |  |
| ARS |  |
| FastTD3 |  |

## P4 / P5: does a learner gain more from curation (curatedtn) than PPO?

Difference of gaps: (full − curatedtn) for the learner minus (full − curatedtn) for PPO, per test clip (seed means), sources resampled. Positive = the learner gains more. P4 predicts positive for SAC and FastTD3 (and PPO without feed-forward).

| learner | difference of gaps [95% CI] |
|---|---|
