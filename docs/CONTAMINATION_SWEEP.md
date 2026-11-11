# Contamination sweep (planned 2026-11-11, not pre-registered)

**Question.** Does trackability-based curation help more when the training set contains clips the robot cannot
track?

**Why.** In study st7, every clean v5 training clip was achievable: 0 falls in 370 scoring rollouts, worst clip
e 0.87. The library builder had already removed infeasible clips, so curation could only drop useful data. ExBody2's
setting is retargeted motion capture, where part of the data is motion the robot cannot perform. This sweep
recreates that setting in two ways.

## Data

### Ambitious clips (main): `data/clips_v5amb`

These are real motions, pushed beyond the dataset's range, that still pass the kinematic checks. This is the case
curation is meant for: motion that looks valid but that this body probably cannot track.

They are built by `curation/clips/gen_ambitious.sh` and `curation/clips/make_ambitious.py`. The gaits come from the
same generator and settings as the dataset, plus a quicker step style (single support 0.22 s, foot lift 3.5 cm).

- **Candidates (37):**
  - walk_fwd 0.07 / 0.08 m/s;
  - walk_back −0.06 / −0.08 m/s;
  - side_step ±0.04 / ±0.05 m/s;
  - turn_in_place ±0.45 / ±0.6 rad/s;
  - walk_turn 0.05 m/s at ±0.3 rad/s and 0.06 m/s at ±0.4 rad/s;
  - a 30 / 35 / 40° bow in 0.4 s;
  - a full-depth crouch in 0.3 s;
  - a 5 cm sway at 1.5 Hz;
  - head nod and shake at 2.5 Hz.
- **11 pass the kinematic checks**, and all 11 go into the library:
  - walk_back ×4 (−0.08 comes out nearly identical to −0.06: the generator seems to cap backward speed);
  - turn_in_place 0.45 ×2;
  - walk_turn 0.05 / 0.3 (quick);
  - the fast crouch, the fast sway, and the fast head nod and shake.
- **Every faster forward walk and side-step, every 0.6 rad/s turn and every fast bow breaks a joint limit.** For this
  robot, "beyond the range but still valid" is a narrow band.
- **Share:** 11 / 48 = 23% of the training set. This is not padded to 30%.

### Corrupted copies (secondary): `data/clips_v5c{15,30,50}`

These are artificial retargeting artifacts, built by `curation/clips/make_contaminated.py`.

- It makes one corrupted copy of each of the 37 v5 training clips, in a seeded order, cycling through four
  corruptions:
  - `fast`: played at 2× speed;
  - `jitter`: 8 Hz leg-joint noise, 0.12 rad;
  - `slide`: base translation ×3 against unchanged legs (or a 0.15 m/s drift for stationary clips);
  - `exaggerate`: leg deviation from home ×1.8, clipped to the joint range.
- 17 of the 37 copies still pass the kinematic check.
- **Weaknesses:**
  - Each copy has a clean twin in the training set, which may make it easier to tolerate and easier to spot.
  - Jitter and slide are crude imitations of real artifacts.
- The libraries are nested:

| Library | Corrupted clips added | Share of the training set |
|---|---|---|
| `data/clips_v5c15` | 7 | 16% |
| `data/clips_v5c30` | 16 | 30% |
| `data/clips_v5c50` | 37 | 50% |

Val and test are the v5 ones in every library.

## Runs

Each library gets one `run_study.py` study, `--conds full curated --seeds 0 1`:

- a scoring policy (300M);
- 4 τ fine-tunes, with τ* picked on val;
- full and curated, each at 200M with 2 seeds;
- test evaluation: nominal, two pushes, low friction.

Study st7 (3 seeds) is the clean point.

`curation/study/run_sweep.sh` runs the queue, which stops at the first failure:

1. smoke test `cs30smoke` (done first, separately);
2. `cs30` (corrupted 30%);
3. `camb` (ambitious 23%);
4. `cs50` (corrupted 50%).

Each study takes about 5 h on two A4000s, about 15 h in total. `cs15` was dropped to make room for `camb`.

## Read-out

- Curated minus full (Δe on the test clips, paired bootstrap 95% CI) for each library.
- The share of contaminating clips that curation removed, against the clean clips it kept (from `tau_choice.json`
  and the study log).
- **Prediction:** Δe is about 0 on the clean pool and becomes negative (curated better) with contamination,
  especially for the ambitious clips. If it stays at about 0, PPO tolerates this kind of contamination, and that is
  the finding.
