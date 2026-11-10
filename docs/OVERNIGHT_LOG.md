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
- **23:50** Found that v3 has **no walk_fwd clip in train** and no test clip for walk_turn or bow: splits were drawn
  before the checks, and the dropped sources emptied a split. Fix (v4): splits drawn after the checks over surviving
  sources; extra sources for the thin categories (walk_fwd 0.03 / 0.05 m, walk_turn at 0.02–0.03 m with 0.10–0.15
  rad, bow 15° / 25°). The v3 scoring run is restarted on v4. New tool `curation/clips/write_dataset_doc.py` writes
  `DATASET.md` from the manifest, so the per-category split table catches this immediately.
- **00:05** Dataset **v4**: 74 clips (train 37 / val 18 / test 19), every category has train, val and test sources
  (`docs/DATASET.md`, generated). Ledger v4 (`results/reward_ledger_v4.json`): gaits 2.55–2.74×, stationary
  1.18–1.50×. GIFs: `results/clips_v4/`.
- **00:05** Why the crouch is only 12 mm even at 1.66 rad: the home stance already bends the knee to about 1.5 rad;
  14 mm needs 1.64, 20 mm needs 1.74, 40 mm needs 2.05. The knee is the binding joint (the hips and ankles have room).
  A deeper crouch needs a different home stance, not a different limit.
- **00:05** Scoring policy for the dry run restarted on v4: `dry_score_v4_150M`, GPU 2. Tracking env changes exported
  as `patches/open_duck_playground/0011-*.patch`.
