# Overnight report, 2026-11-09 → 11-10

What was done overnight without the robot, how to check each result, and what needs a team decision. The full
timestamped journal is `docs/OVERNIGHT_LOG.md`. Everything here ran in simulation on GPUs 1 and 2. The robot was not
touched, and robot tests are listed for Wednesday in `docs/ROBOT_TESTS.md`.

**Short version**

1. The dataset grew from 6 to 10 motion categories: march, bow, sway and head moves were added, for 74 clips in all. Every category now has train, val and test clips (dataset v4).
2. The tracking env did not track gaits: every policy learned to stand and shuffle. **Reference feed-forward**
   actions fixed it: leg error dropped from 0.27 to 0.06 rad at 50M steps.
3. A full **dry run** of Steps 4–5 ran end to end. It is labelled "dry run, not pre-registered": 1 seed, 100M steps, dataset v4. The run covered:
   - the scoring policy;
   - per-clip scores;
   - 4 τ fine-tunes;
   - τ choice;
   - curated, random, kinematic and full conditions;
   - test evaluation with pushes and low friction;
   - the P.9 comparison.
4. **Dry-run result:** curated came out worst (Δe +0.19 vs full, +0.20 vs random). Random and kinematic matched full.
   But curated is just as far behind on clips it trained on identically, and its training curve lagged from the
   start. This is a slow run, not evidence about curation. With one seed the noise is as large as the effect, so the
   real study's 3 seeds are a minimum. Details in [Dry-run result](#dry-run-result).
5. **Five bugs and design problems** were found and fixed before the real study, listed under [Failures and surprises](#failures-and-surprises).

The private gallery page has every GIF inline (link in the morning message). The GIFs are also in the repo under
`results/`.

## Results

Each result has its claim, numbers, file, commit and a command to reproduce it. Commands run from `Open_Duck_Playground/` unless stated, with
`R=../open-duck-curation`.

### 1. Dataset v4: 74 clips, 10 categories, every split populated

- **Claim:** gaits (walk forward/back, side step, turn in place, walk-turn, march) plus stationary moves (crouch, bow,
  sway, head nod/shake/look-around/tilt), all passing the kinematic checks, split per source after the checks.
- **Numbers:** 74 clips, train 37 / val 18 / test 19. Knee limit raised to 1.66 rad (owner decision 1).
- **Files:** `data/clips_v4/`, `docs/DATASET.md` (generated), GIFs `results/clips_v4/*.gif`.
- **Commit:** 92c9abc.
- **Reproduce:** `bash curation/clips/gen_gaits.sh && python3 curation/clips/make_library.py --out data/clips_v4`, then
  `python3 curation/clips/write_dataset_doc.py --lib data/clips_v4 --out docs/DATASET.md`.

### 2. Motion-relative reward tolerances

- **Claim:** with fixed Gaussian widths, standing still earned 80–97% of a stationary clip's reward, so the policy had
  no reason to crouch or bow. Widths now scale with each clip's motion (0.5 × rms distance from home, floored, capped
  at the old widths).
- **Numbers (reward ledger, perfect tracking ÷ standing still):**

  | category | before | after |
  |---|---|---|
  | crouch | 1.03× | 1.21× |
  | head | 1.05× | 1.18× |
  | sway | 1.11× | 1.50× |
  | bow | 1.25× | 1.44× |
  | gaits | 2.0–2.1× | 2.55–2.74× |
- **Files:** `results/reward_ledger_v3.json`, `results/reward_ledger_v4.json`; env patch
  `patches/open_duck_playground/0011-*.patch`.
- **Commit:** 92c9abc.
- **Reproduce:** `.venv/bin/python $R/curation/env/reward_ledger.py`.

### 3. Reference feed-forward fixes the standing basin

- **Claim:** with actions as offsets from the home pose, every policy settled into standing and shuffling. Pilot 1
  completed 28/28 clips with 0 falls, but its gait leg error was 0.25–0.67 rad. With the joint target set to reference
  pose + 0.25 × action, a zero action replays the clip, and the policy tracks.
- **Numbers (at 50M steps):**

  | run | leg error | legs term / step | keypoints term / step |
  |---|---|---|---|
  | home-based | 0.267 rad | 0.08 | 0.05 |
  | feed-forward | **0.058 rad** | 0.70 | 0.58 |
- **Files:**
  - `results/pilot1_rollouts.gif`, `results/pilot1_eval_v1.json` (before);
  - `results/dry_run/ab_ff_50M_rollouts.gif` (after);
  - `results/dry_run/score_home_v4_all.json`;
  - env patch `patches/open_duck_playground/0012-*.patch`.
- **Commit:** a970e05.
- **Reproduce:** `.venv/bin/python $R/curation/analysis/compare_runs.py --runs <home run> <ff run> --at 25 50`.

### 4. Dataset v5: train clips cover every joint a category moves

- **Claim:** `head__nod` fell within 0.2 s, and the cause is not physics. No v4 training clip moves head_pitch, so its observation
  channels have a normaliser std of exactly 0, and a 0.4 rad nod reaches the network as about 10⁵. In v5 the held-out
  sources are re-drawn until the train sources move every joint the category moves.
- **Numbers:** val `head__look_around` (head_pitch) falls 10/10 under the v4 scoring policy, while trained head moves
  score 0.41–0.45, the best of any clip.
- **Files:** `data/clips_v5/`, `results/dry_run/scores_val_scoring.json`.
- **Commit:** 7be2a9d.
- **Reproduce:** `python3 curation/clips/make_library.py --out data/clips_v5`.

### 5. Dry-run pipeline (Steps 4–5), end to end

- **Claim:** every step of the PREREG procedure runs, with scripts.
- **Steps:**
  - scoring policy `dry_score_ff_100M`;
  - per-clip train scores (0.41–1.74; scores separate clips within gait categories);
  - τ candidates p40 / p55 / p70 / p85 (21 / 23 / 27 / 32 clips), each fine-tuned for 50M and scored on val;
  - τ* = p85;
  - curated (32 clips), random seed 0 (29), kinematic (32) and full (37), each trained for 100M from scratch;
  - test evaluation, nominal plus push 0.3 and 0.6 m/s and friction × 0.6.
- **Files:**
  - `results/dry_run/` (`scores_*.json`, `subsets/`, `tau_choice.json`, `test/`, `comparison*.md`, `gifs/`);
  - runbook `docs/DRY_RUN.md`.
- **Commits:** f6f2778, 2601110, 80abb6f, b25ae8e, plus the results commit.
- **Reproduce:** `docs/DRY_RUN.md`, step by step.

### Dry-run result

**Curated came out worst; random and kinematic matched full. The curated deficit does not come from the clips
curation removed, so with one seed this says nothing yet about curation.** Dry run, not pre-registered: 1 seed, 100M
steps, v4 data, 19 test clips × 10 rollouts.

| condition (train clips) | mean e nominal | falls / clip | push 0.3 m/s | push 0.6 m/s | friction × 0.6 |
|---|---|---|---|---|---|
| full (37) | 1.342 | 1.89 | 1.447 | 1.715 | 1.329 |
| curated, τ = p85 (32) | 1.528 | 3.79 | 1.635 | 1.911 | 1.499 |
| random, seed 0 (29) | 1.333 | 2.37 | 1.476 | 1.766 | 1.328 |
| kinematic (32) | 1.301 | 3.00 | 1.394 | 1.699 | 1.298 |

Curated minus each other condition (Δe, nominal; negative = curated better):

| vs | all clips | head excluded |
|---|---|---|
| full | +0.19 [+0.09, +0.31] | +0.20 [+0.09, +0.35] |
| random | +0.20 [+0.10, +0.33] | +0.22 [+0.12, +0.37] |
| kinematic | +0.23 [+0.10, +0.39] | +0.25 [+0.11, +0.43] |

The pass bar (P.9) fails in every setting: nominal, both pushes, low friction, with and without head. Three checks show
the deficit is a property of the curated **run**, not of curated **data**:

1. **It is the same where the training clips were identical.** Curated dropped only 5 fast walk_fwd / walk_turn clips. On test categories
   where curated trained on exactly the same clips as full, it is worse by +0.21. On the two categories it cut, it is
   worse by +0.18. Random and kinematic differ from full by less than 0.07 on both groups.
2. **Its training curve lagged.** At 50M steps curated's episode length was 97 against 145–149 for the other three, and at 100M it was still 129
   against 148–154. It lagged on a clip set that should be easier.
3. **The largest gap is sway** (+0.81 vs full), where all four conditions trained on the same two sway clips.

The data cannot separate two explanations:

- **A slow seed.** This is the simplest reading, since nothing about the selection predicts it.
- **Hard clips teach balance recovery that other categories use.** This would be the opposite of the ExBody2 premise.

Testing either needs seeds: the real study's 3 seeds per condition, or a cheap check with one more seed each of
curated and full (about 45 min each on one GPU). The noise floor this sets is useful in itself. With one seed, two
runs on identical data can differ by 0.8 on a clip and 0.2 on the test mean.

Files:
- `results/dry_run/comparison_{nominal,push03,push06,fric06}.md`;
- `results/dry_run/comparison_*_nohead.md`;
- per-clip JSON in `results/dry_run/test/`;
- GIFs `results/dry_run/gifs/test_full.gif`, `test_curated.gif`.

Reproduce:
`python3 curation/analysis/compare_conditions.py --manifest data/clips_v4/manifest.json --cond full=results/dry_run/test/full_nominal.json curated=results/dry_run/test/curated_nominal.json random=results/dry_run/test/random_nominal.json kinematic=results/dry_run/test/kinematic_nominal.json --out /tmp/c.md`
(add `--exclude-category head` for the head-excluded table). The training curves come from
`curation/analysis/compare_runs.py --runs <four run dirs> --at 50 100 --terms legs keypoints alive`.

## Failures and surprises

1. **Standing basin.** Home-based actions made every policy stand (result 3). Pilot 1's 0 falls hid it; only the leg
   error showed it.
2. **Zero-variance observation channels.** A joint that no training clip moves makes the observation normaliser
   divide by ~0, and the policy falls the moment a test clip moves it (result 4). brax's normaliser does not clip.
3. **v3 split hole.** Splits were drawn before the kinematic checks, so dropped sources emptied splits: v3 had no
   walk_fwd train clip. Splits are now drawn after the checks, and `write_dataset_doc.py` prints the per-category split
   table so a hole is visible.
4. **Crouch depth is set by the home stance, not the limit.** The home knee is already at about 1.5 rad, so even at 1.66
   rad the crouch is 12–14 mm (20 mm needs 1.74 rad, 40 mm needs 2.05).
5. **Random control had 10% less data.** P.5's draw stopped at 90% of the curated duration; with 200-frame clips
   that always meant fewer clips. Fixed (80abb6f); the dry-run random run keeps its 29 clips.
6. **The τ rule did not choose.** All four τ candidates scored within 0.044 on val, inside the 0.05 tie band, so the
   rule picks the largest subset regardless.
7. **One seed is not enough.** Curated and full trained on identical sway clips, yet differ by 0.8 on the sway test
   clip. The bootstrap now resamples seeds within clips, as P.8 says (it had averaged them first).
8. **Smaller.**
   - `CURATION_CLIPS` takes a file path, not JSON; the first τ launch failed in seconds.
   - An eval JSON carried a private path; eval now stores only the run and checkpoint name.
   - Some early journal times are out of order; I used the cluster clock after midnight.

## Open decisions for the team

1. **Adopt reference feed-forward** for the real study (PREREG proposal 4). Recommended: yes, since without it nothing
   tracks.
2. **Adopt dataset v5** (PREREG proposal 3). Recommended: yes.
3. **Stationary categories** (crouch, bow, sway, head) score lowest, so curation always keeps them. Keep them in the
   main comparison, or report them separately?
4. **Crouch depth:** accept 12–14 mm, or lower the home stance (a new walker home pose, a bigger change).
5. **τ tie band:** shrink it from 0.05, or score τ with more val rollouts and seeds.
6. **Seeds:** the dry run supports PREREG's 3 seeds per condition as a minimum.
7. **Deadlines** (owner).
8. **Robot tests R1–R7** for Wednesday (`docs/ROBOT_TESTS.md`). R1, the foot-switch L/R swap, matters most.

## Commits overnight

Oldest first, all on `main` of the public repo:

- `dc4c26f` Add result GIFs: walker comparison, get-up versions, jump, robot-vs-sim replays
- `fab7294` Tracking env, reward ledger, per-clip evaluator, subset selection, PREREG draft, robot test scripts
- `8757b64` MODEL_MATCH.md, sim half of the joint step test
- `92c9abc` Dataset v4 (74 clips, 10 categories incl. march, bow, sway, head), splits after checks, motion-relative reward tolerances, overnight log
- `f6f2778` Dry-run runbook (not pre-registered); eval JSON stores run/checkpoint name only
- `a970e05` Tracking env: reference feed-forward (patch 0012); run comparison tool; home-based scoring results; overnight log
- `7be2a9d` Dataset v5: splits keep every moved joint in train (head_pitch zero-variance finding); PREREG proposals
- `2601110` Dry run: scores, tau candidates, perturbation evaluation, condition comparison script
- `7fb224b` Ignore dry-run driver logs
- `80abb6f` Dry run: tau choice and val scores for p70/p85; random subset now matches curated duration
- `b25ae8e` Dry run: curated test evaluation, full vs curated rollouts; bootstrap resamples seeds within clips (P.8)
- (next) this report, the four-condition comparison and the README patch count
