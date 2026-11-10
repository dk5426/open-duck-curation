# Overnight log, 2026-11-09 → 11-10

Timestamped journal of the overnight work (GPUs 1 and 2 only; GPU 3 stays free).

## Decisions taken (owner, 23:40)

1. Raise the model's knee limit to 1.66 rad (measured on the robot) and regenerate deeper crouches.
2. Dry run of Steps 4–5 on the draft rules is allowed. It is labelled "dry run, not pre-registered", 1 seed per
   condition, reduced size.
3. Re-split so every category has a validation source.
4. Course deadlines: owner will update later.

## Log

- **23:13** Pilot 1 (`track_pilot1_100M`, dataset v1, 13 train clips) started on GPU 1.
- **23:22** Pilot 2 (`track_pilot2_300M`, same, 300M) started on GPU 2, to see how far the learning curve goes.
  Throughput about 94M steps/h.
- **23:40** Starting dataset v2 (decisions 1 and 3).
- **23:30** Dataset v2 → v3 (knee limit 1.66 rad, deeper crouches, every category with a val source; new motions:
  march in place, bow, sway, head nod/shake/look-around/tilt). 60 clips, 12 dropped by the checks.
- **23:35** Reward ledger v3: gaits pay 2.0–2.1× more for perfect tracking than for standing, but the stationary
  categories only 1.03× (crouch), 1.05× (head), 1.11× (sway), 1.25× (bow): standing still collects almost all of
  their reward, so the policy has no reason to follow them.
- **23:38** Fix: **motion-relative tolerances.** Each clip's Gaussian width for the legs, head and keypoint terms is
  0.5 × the clip's rms distance from home, floored (0.02 rad legs, 0.04 rad head, 4 mm keypoints) and capped at the
  old fixed widths. Gaits are unchanged (capped); stationary clips get tight tolerances. Ledger after:
  crouch 1.21×, head 1.18×, sway 1.50×, bow 1.44×; gaits 2.55–2.74×.
- **23:40** Stopped pilot 2 (v1 data, outdated). Started the dry-run scoring policy on v3 (GPU 2).
- **23:45** Found that v3 has **no walk_fwd clip in train** and no test clip for walk_turn or bow: splits were drawn
  before the checks, and the dropped sources emptied a split. Fix (v4): splits drawn after the checks over surviving
  sources; extra sources for the thin categories (walk_fwd 0.03 / 0.05 m, walk_turn at 0.02–0.03 m with 0.10–0.15
  rad, bow 15° / 25°). The v3 scoring run is restarted on v4. New tool `curation/clips/write_dataset_doc.py` writes
  `DATASET.md` from the manifest, so the per-category split table catches this immediately.
- **23:50** Dataset **v4**: 74 clips (train 37 / val 18 / test 19), every category has train, val and test sources
  (`docs/DATASET.md`, generated). Ledger v4 (`results/reward_ledger_v4.json`): gaits 2.55–2.74×, stationary
  1.18–1.50×. GIFs: `results/clips_v4/`.
- **23:50** Why the crouch is only 12 mm even at 1.66 rad: the home stance already bends the knee to about 1.5 rad;
  14 mm needs 1.64, 20 mm needs 1.74, 40 mm needs 2.05. The knee is the binding joint (the hips and ankles have room).
  A deeper crouch needs a different home stance, not a different limit.
- **23:50** Scoring policy for the dry run restarted on v4: `dry_score_v4_150M`, GPU 2. Tracking env changes exported
  as `patches/open_duck_playground/0011-*.patch`.
- **00:30** Pilot 1 evaluated (`results/pilot1_eval_v1.json`, GIF `results/pilot1_rollouts.gif`): 28/28 clips complete,
  0 falls, but it **does not walk**: it stands in a wide stance and shuffles. Leg error 0.25–0.67 rad rms on gaits
  (score 3.2–7.5) vs 0.04 rad on crouches (score 0.8). The score separates categories, not clips within them.
- **00:40** The v4 scoring policy (home-based actions) shows the same standing basin in its reward terms: the legs term
  pays 0.08/step and keypoints 0.05/step out of 1, flat after 60M, while alive / orientation / yaw / velocity keep
  rising; leg error grows during training (15 → 44). Cause: actions are offsets from the **home pose**, so tracking a
  gait needs large coordinated actions while standing needs none.
- **00:55** Fix under test: **reference feed-forward**, joint target = reference pose + 0.25 × action (zero action
  replays the clip; `ref_feedforward`, now the default). A/B at 50M: `ab_ff_50M` (GPU 1, current widths) and
  `ab_ff_wide_50M` (GPU 2, leg width 0.3 rad, keypoints 5 cm). `TRACKING_OVERRIDES` (JSON of flattened config keys)
  added for ablations. Home-based baselines that finished: `dry_score_v4_150M`, `dry_full_v4_100M`.
- **01:20** **A/B result: reference feed-forward fixes the standing basin.** At 50M (`curation/analysis/compare_runs.py`):

  | run | leg error (rad) | episode length | legs term / step | keypoints term / step |
  |---|---|---|---|---|
  | home-based (`dry_score_v4_150M` at 54M) | 0.267 | 139 | 0.08 | 0.05 |
  | feed-forward (`ab_ff_50M`) | **0.058** | 160 | 0.70 | 0.58 |
  | feed-forward + wide widths (`ab_ff_wide_50M`, at 36M) | 0.064 | 155 | 0.66 | 0.48 |

  Wider reward widths add nothing at matched steps (0.068 vs 0.068 at 25M), so the widths stay. Feed-forward is the
  default from patch 0012. Home-based checkpoints must be evaluated with `TRACKING_OVERRIDES='{"ref_feedforward": false}'`.
- **01:20** Home-based scoring policy per clip (`results/dry_run/score_home_v4_all.json`): all gaits complete but
  untracked (leg error 0.25–0.69 rad). **Unseen head moves fall 4/4** (nod, look-around; val/test), while the trained
  head moves (tilt, shake) score best of all: a generalization failure within a category.
- **01:22** Dry run restarted on the feed-forward env: scoring policy `dry_score_ff_100M` (GPU 1).
- **01:40** Feed-forward rollouts (`results/dry_run/ab_ff_50M_rollouts.gif`): the walk now follows the reference (leg
  error 0.04–0.09 rad, keypoints < 1 cm); the bow tracks. **`head__nod` falls within 0.2 s.** Open-loop in MuJoCo,
  head_pitch ±0.4 rad tilts the base only 1–1.5°, so it is not physics. Cause: **no training clip moves head_pitch**
  (v4's train head sources are shake and tilt), so its reference channels have normaliser std exactly 0 (8 channels
  in all), and a 0.4 rad nod arrives at the network as ~10⁵. The unseen-head falls under the home-based policy have the
  same cause.
- **01:45** Fix for the real study (`make_library.py`, dataset **v5**, `data/clips_v5`): held-out sources are re-drawn
  until the train sources move every joint the category moves. v5 head: look-around + tilt train, nod val, shake test.
  The dry run stays on v4: the failure hits every condition equally on the same val/test clips (noise, not bias), and
  restarting would cost 30 min. Head clips are reported separately in the dry-run results.
- **02:09** Feed-forward scoring policy `dry_score_ff_100M` and full condition `dry_full_ff_100M` finished (≈130M
  steps/h, faster than the 94M/h first estimate).
- **02:15** Train + val scored (10 rollouts, on GPU: 2 min for 37 clips). `results/dry_run/scores_train.json`:
  scores 0.41–1.74; now they separate clips **within** gait categories too (e.g. walk_fwd 0.04–0.05 m/s gentle falls
  3–4/10, walk_turn 0.04 m/s 0.15 rad/s gentle 8/10). Stationary clips are the easiest (0.41–0.69). Val head
  look-around falls 10/10 (zero-variance head_pitch, see 01:40).
- **02:16** τ candidates (`results/dry_run/subsets/`): p40 0.61 → 21 clips, p55 1.10 → 23, p70 1.23 → 27, p85 1.38 →
  32 (each includes the per-category coverage clips). Fine-tunes p40 / p55 started (GPU 1 / 2, 50M, warm start from
  the scoring policy); p70 / p85 follow. First launch failed in seconds: `CURATION_CLIPS` is a file path (runbook fixed).
- **02:45** τ fine-tunes p40 / p55 done and scored on val (`results/dry_run/scores_val_p40.json`, `_p55.json`); p70 / p85
  running. A driver (`after_tau.sh` on the cluster, steps in `DRY_RUN.md`) picks τ* by the P.4 rule, builds the
  matched random (seed 0) and kinematic subsets, and launches curated, random and kinematic at 100M from scratch.
- **02:55** `eval_clips.py` gained `--push` (lateral kick at t = 1.5 s, alternating ±y) and `--friction` (P.7). Smoke
  test: walk_fwd completion 1.00 → 0.75 (0.6 m/s) → 0.44 (1.5 m/s). New `curation/analysis/compare_conditions.py`
  (P.7–P.9: per condition, paired Δe with bootstrap CI, per category, pass bar). Full condition test-scored:
  `results/dry_run/test/full_{nominal,push03,push06,fric06}.json`.
- **03:14** τ chosen (`results/dry_run/tau_choice.json`). Val means: p40 1.006 (21 clips), p55 0.986 (23), p70 0.962
  (27), p85 0.962 (32). **τ* = p85**, but the result carries little information: all four candidates lie within 0.044 of
  each other, inside the 0.05 tie band, so the P.4 rule ("ties go to the larger subset") would pick p85 regardless.
  The only val clip that separates them is `turn_in_place 0.30 gentle` (1.19–1.50). For the PREREG: either shrink the
  tie band or score τ on more val rollouts / seeds. Curated (32 clips) and random seed 0 launched at 100M (GPU 1 / 2).
- **04:02** Curated finished; kinematic (32 clips) launched on GPU 1. **Matching bug found:** P.5's random draw stopped
  at 90% of the curated duration, and since every clip is 200 frames, random always got about 10% less data (29 clips,
  5,800 frames vs 6,400). Fixed in `select_subsets.py` (stop at the total closest to the target; seed 0 now gives 32).
  The dry-run random run keeps its 29 clips, which slightly favours curated. This is a caveat on the dry-run result
  only. Random also happens to draw no march clip.
- **04:03** Test evaluation chained on the cluster (`tools_dry/eval_finals.sh`): curated now, random and kinematic as
  their training ends.
- **04:06** First test result, curated vs full (nominal, 19 test clips): **curated is worse**, Δe +0.19 [95% CI +0.09,
  +0.31], falls 3.8 vs 1.9 per clip. Curated (p85) dropped 5 train clips, all fast walk_fwd / walk_turn. But the
  biggest losses are in categories where curated and full trained on **identical** clips: sway +0.81 (sway 0.03 m at
  1 Hz: 1.15 → 2.29), crouch +0.18. With one seed per condition, run-to-run noise is at least as large as the effect
  being measured. This is the main lesson of the dry run so far: the 3 seeds per condition in PREREG P.6 are needed,
  not optional. `compare_conditions.py` now resamples seeds within each drawn clip, as P.8 states (it previously
  averaged them first, which would have made the CI too narrow).
- **04:07** Test rollouts, full vs curated, on the clips where they differ most (sway 0.03 m at 1 Hz, crouch 0.40, walk_fwd
  0.03 normal, walk_turn 0.04 / −0.15 gentle): `results/dry_run/gifs/test_full.gif`, `test_curated.gif` (curated is
  shorter, 346 vs 400 frames, because it falls).
- **04:58** All test evaluations done (`results/dry_run/test/`, `comparison_*.md`). Nominal mean e: full 1.342, curated
  1.528, random 1.333, kinematic 1.301. Curated is worse than every other condition with the CI excluding 0, under every
  perturbation and with or without head; P.9 fails. Random and kinematic sit within 0.04 of full.
- **05:00** Why curated lost. Its deficit is the same on test categories where it trained on exactly the same clips as
  full (+0.21) as on the two it cut (+0.18), and its training episode length lagged from the start (97 vs 145–149 at
  50M, 129 vs 148–154 at 100M). This reads as a slow run (seed), not a curation effect. The alternative, that hard
  clips teach balance recovery that transfers, cannot be separated without seeds. Write-up: `OVERNIGHT_REPORT.md`.
