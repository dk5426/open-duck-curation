# Contamination sweep (planned 2026-11-11, not pre-registered)

**Question.** Does trackability-based curation help more when the training set contains clips the robot cannot
track?

**Why.** In study st7, every clean v5 training clip was achievable: 0 falls in 370 scoring rollouts, worst clip
e 0.87. The library builder had already removed infeasible clips, so curation could only drop useful data, and curated
came out slightly behind full. ExBody2's setting is retargeted motion capture, where a share of the clips is
physically wrong. This sweep recreates that setting.

## Data

`curation/clips/make_contaminated.py` builds the sweep libraries.

- It makes one corrupted copy of each of the 37 v5 training clips, in a seeded order, cycling through four
  corruptions:
  - `fast`: played at 2× speed;
  - `jitter`: 8 Hz leg-joint noise, 0.12 rad;
  - `slide`: base translation ×3 against unchanged legs (or a 0.15 m/s drift for stationary clips);
  - `exaggerate`: leg deviation from home ×1.8, clipped to the joint range.
- 17 of the 37 copies still pass the builder's kinematic check: all `fast` and `slide` copies, plus a few
  `exaggerate` ones. A kinematic filter alone would keep those.
- The libraries are nested, and val and test are the v5 ones, unchanged:

| Library | Corrupted clips added | Share of the training set |
|---|---|---|
| `data/clips_v5c15` | 7 | 16% |
| `data/clips_v5c30` | 16 | 30% |
| `data/clips_v5c50` | 37 | 50% |

## Runs

Each level is one `run_study.py` study, `--conds full curated --seeds 0 1`:

- a scoring policy (300M);
- 4 τ fine-tunes, with τ* picked on val;
- full and curated, each at 200M with 2 seeds;
- test evaluation: nominal, two pushes, low friction.

Study st7 (3 seeds) is the 0% point.

`curation/study/run_sweep.sh` chains the levels:

1. wait for st7;
2. smoke test (`cs30smoke`);
3. `cs30`, then `cs50`, then `cs15`.

It stops at the first failure. Each level takes about 5 h on two A4000s, about 15 h in total.

## Read-out

- Curated minus full (Δe on the test clips, paired bootstrap 95% CI) for each contamination level.
- The share of corrupted clips that curation removed, against the clean clips it kept (from `tau_choice.json`).
- **Prediction:** Δe is about 0 at 0% and becomes negative (curated better) as contamination grows. If it stays at
  about 0 even at 50%, PPO is robust to this kind of contamination, and that is the finding.
