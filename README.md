# Open Duck motion curation

Course project, Optimal Control and Reinforcement Learning. Team: Dhawal Kabra, Kanad Patel, Neer Patel, Pierrick Rugery.

**Research question:** can selecting reference motions by their trackability (feasibility-aware dataset curation, after
ExBody2) improve motion-imitation accuracy and stability on a small, constrained biped while preserving motion diversity?

The robot is derived from [Open Duck Mini v2](https://github.com/apirrone/Open_Duck_Mini):
- 14 Feetech STS3215 servos (10 leg, 4 neck/head);
- a BNO055 IMU;
- foot-contact switches;
- a Raspberry Pi.

Training uses [Open Duck Playground](https://github.com/apirrone/Open_Duck_Playground) (MuJoCo Playground / MJX, brax
PPO).

## Start here

| Document | What it is |
|---|---|
| [`docs/PLAN.md`](docs/PLAN.md) | The ordered plan. Every task has an id, "done when", cost and risks; includes the pre-registration draft (§4) |
| [`docs/TRACKER.md`](docs/TRACKER.md) | Snapshot of the task tracker. The live tracker is a shared web page; ask Dhawal for access |
| [`docs/AUDIT.md`](docs/AUDIT.md) | What already exists for each project step, what is partial, what is missing; compute budget; literature |
| [`docs/SETUP.md`](docs/SETUP.md) | How the upstream pipeline was reproduced, the upstream bugs found, training cost, walker results |
| [`docs/DATASET.md`](docs/DATASET.md) | Reference-clip dataset v4 (74 clips, 10 categories: 6 gaits, crouch, bow, sway, head), how it is made, checks, splits; GIFs in `results/clips_v4/` (v1 kept for history) |
| [`docs/ROBOT_TESTS.md`](docs/ROBOT_TESTS.md) | Every test that needs the robot, in the order to run them |
| [`docs/PREREG.md`](docs/PREREG.md) | Pre-registration DRAFT: clip splits, score, selection rule, threshold choice, random control, statistics, pass bar. Needs the team's sign-off before Step 4 |

## What is in this repository

| Folder | Contents |
|---|---|
| `docs/` | Plan, tracker snapshot, audit, setup notes |
| `patches/open_duck_playground/` | Our changes to Open Duck Playground as a patch series (11 commits on top of upstream `b9be205`): pinned dependencies, get-up and jump tasks, floor-surface randomization, walker v2, name-based randomization ids, and the **reference-clip tracking environment** (`tracking.py`; 0011 adds motion-relative tolerances and the 1.66 rad knee) |
| `patches/reference_motion_generator/` | Dependency pin for the reference-motion generator (on top of upstream `3d7bc6f`) |
| `patches/locks/` | `uv.lock` files that resolve the exact versions we trained with |
| `tools/` | Evaluation and analysis scripts: walker evaluation and tracking score, robot-log vs sim comparison, IMU plots, servo response, get-up evaluation and replay, start-pose banks, GPU-safe launch and queue scripts |
| `policies/` | Trained ONNX policies (walker and get-up), with the robot's 50 Hz contract |
| `robot_logs/` | Real-robot recordings (50 Hz: observation, action, targets, joint positions, raw IMU, commands, loop timing), 2026-10-30 to 2026-11-02 |
| `robot_patches/` | Changes installed on the robot's runtime, each as a diff with its README and off-robot tests |
| `curation/` | Project code: clip generation and checks (`clips/`), reward ledger (`env/`), per-clip evaluator and rollout GIFs (`eval/`), subset selection (`select/`), robot test scripts (`robot/`), log analyses (`analysis/`) |
| `data/clips_v4/` (current), `data/clips_v1/` | The clip library (`library.npz`, `manifest.json`, `splits.json`) and the gait generator presets |
| `results/` | Analysis results and GIFs |

## Setup

Clone the upstream repositories next to this one, then apply our patches.

```bash
git clone https://github.com/apirrone/Open_Duck_Playground.git
cd Open_Duck_Playground
git checkout -b local/setup b9be205
git am ../open-duck-curation/patches/open_duck_playground/*.patch
cp ../open-duck-curation/patches/locks/playground.uv.lock uv.lock
uv sync                        # on a Linux GPU machine; see docs/SETUP.md for the Mac viewer setup
cd ..

git clone https://github.com/apirrone/Open_Duck_reference_motion_generator.git
cd Open_Duck_reference_motion_generator
git checkout 3d7bc6f
git apply ../open-duck-curation/patches/reference_motion_generator/pin_dependencies.patch
cp ../open-duck-curation/patches/locks/motion_generator.uv.lock uv.lock
git lfs pull                   # the robot meshes are Git LFS files
```

The tools are run from inside `Open_Duck_Playground`. For example, evaluating our walker on CPU:

```bash
cd Open_Duck_Playground
MUJOCO_GL=osmesa JAX_PLATFORMS=cpu uv run python ../open-duck-curation/tools/duck_eval.py \
  -o ../open-duck-curation/policies/ours_walker_full300M_258M.onnx --out walker.json
```

**Before any GPU training on the shared cluster:**
- Read the cluster rules in `docs/SETUP.md`: check `nvidia-smi`, pin `CUDA_VISIBLE_DEVICES`, use `tools/launch_train.sh`
  (it takes a GPU lock).
- Set `OPENDUCK_ROOT` to your working directory and `OPENDUCK_LOCKS` to the shared lock folder.

**Two start-pose banks used by the get-up tasks are not in the patches.** Regenerate them with
`tools/make_sitting_bank.py` and `tools/make_getup_bank_v2.py`.

## Policies

| File | What it does | Notes |
|---|---|---|
| `ours_walker_full300M_258M.onnx` | Velocity-command walker | Tracks commands 26% better than upstream's `BEST_WALK_ONNX_2` in sim; runs on the robot (101 inputs, 14 outputs, action scale 0.25) |
| `getup_real2_80M.onnx` | Get-up from any fall | 40/40 sim starts, 21/21 recorded robot starts at 60–100% servo strength; head-vs-body collision and weak-servo training (92 inputs) |
| `getup_real_41M.onnx`, `getup_real_29M.onnx`, `getup_back2_101M.onnx`, `getup_173M.onnx` | Earlier get-up versions | See `docs/SETUP.md` |
| `jump_101M.onnx` | In-place jump attempt | Does not leave the ground; kept for reference |

## Credits and licence

- Open Duck Mini, Open Duck Playground and the reference-motion generator are by Antoine Pirrone (apirrone); the patches
  here modify those projects.
- Our own code and documents are under the Apache License 2.0 (`LICENSE`).
