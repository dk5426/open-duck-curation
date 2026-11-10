# Dry run of Steps 4–5 (not pre-registered)

**Status: dry run, not pre-registered.** The owner allowed (2026-11-09) a reduced run of the study on the draft
rules in `PREREG.md`, to test the pipeline end to end and to see the effect size before the team signs off.
Nothing here counts as the study's result: the rules can still change, there is 1 seed per condition, and the
budgets are halved.

| | Pre-registered (draft) | Dry run |
|---|---|---|
| Dataset | `clips_v4` | same |
| Env | `tracking.py` default | reference feed-forward (patch 0012); the first attempt with home-based actions (`dry_score_v4_150M`, `dry_full_v4_100M`) learned to stand and was abandoned (`OVERNIGHT_LOG.md` 00:30–01:20) |
| Scoring policy | 300M on all train clips | 100M (`dry_score_ff_100M`) |
| τ selection fine-tunes | 50M each, 4 candidates | 50M each, 4 candidates |
| Final runs | 200M × 3 seeds, from scratch | 100M × 1 seed (seed 0), from scratch |
| Conditions | full, curated, random, (kinematic) | full, curated, random, kinematic |

## Steps and commands (cluster, from `Open_Duck_Playground/`)

1. Scoring policy: `tools/launch_train.sh 1 dry_score_ff_100M 100000000 --env tracking`.
2. Score train and val clips (P.2), 10 rollouts:
   `.venv/bin/python ../open-duck-curation/curation/eval/eval_clips.py --ckpt <final ckpt> --clips train --rollouts 10 --out scores_train.json`
   (and `--clips val`).
3. Subsets: `python curation/select/select_subsets.py --scores scores_train.json --manifest data/clips_v4/manifest.json --out subsets/`.
4. τ fine-tunes: for each `curated_pXX.json`,
   `CURATION_CLIPS=<path to curated_pXX.json> tools/launch_train.sh <gpu> dry_tau_pXX 50000000 --env tracking --restore_checkpoint_path <scoring ckpt>`,
   then score the val clips; τ* = lowest mean val score.
5. Random and kinematic subsets matched to `curated_<τ*>.json` (`--match`, seed 0).
6. Final runs, 100M, from scratch: full (`dry_full_ff_100M`), curated, random, kinematic.
7. Test metrics (P.7) on the test clips, plus rollout GIFs.

Results go to `results/dry_run/` and the log in `OVERNIGHT_LOG.md`.

**Outcome (2026-11-10 04:58):** all steps ran. Curated (τ = p85) came out worst on test; random and kinematic matched
full. The deficit is the same on clips curated trained on identically, so it reflects that one run, not curation.
Tables and checks: `OVERNIGHT_REPORT.md`, section "Dry-run result"; `results/dry_run/comparison_*.md`.
