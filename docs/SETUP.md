# Open Duck Mini v2: simulation training setup (reproduction of the upstream pipeline)

Simulation only. Nothing here commands a robot. All upstream repos are apirrone's (Apache-2.0);
our changes live only on the local branch `local/setup` and are never pushed.

| Where | Path |
|---|---|
| Mac | `~/Desktop/OpenDuck` |
| Training cluster (one A4000 GPU used) | `$OPENDUCK_ROOT` |
| Our tools | `tools/` (`duck_eval.py`, `ref_gif.py`, `probe_deadzone.py`, `launch_train.sh`) |
| Results + GIFs | `results/` (Mac copies; cluster copies in the same relative path) |
| Training runs | cluster `runs/<run>/` (checkpoints, per-checkpoint ONNX, tensorboard events, `train.log`, `launch.txt`) |
| Exact lockfiles | `locks/playground.uv.lock`, `locks/motion_generator.uv.lock`, `locks/playground_local_setup.patch` |

## Status

| Step | State |
|---|---|
| 1a clone | done, Mac + cluster |
| 1b install + JAX on GPU | done (versions below) |
| 1c play BEST_WALK_ONNX_2 | done: walks, 6/6 random 60 s runs survive on both scenes. `results/best2.gif` |
| 1d reference motions | done: 240 gaits, numerically identical to the shipped pkl. `results/ref_generated.gif` |
| 1e smoke run | done: 7M steps in 9 min, reward 14 -> 98, exports work. `results/smoke_7M.gif` (stands only, as expected) |
| 1e full 300M run | done: 2026-10-29 17:20 -> 22:00 EDT (4 h 40 min), exit 0, `runs/full_300M` |
| 1f export + compare | done: **our 258M checkpoint tracks commands 26% better than BEST_WALK_ONNX_2** and survives every test; `policies/ours_walker_full300M_258M.onnx`, `results/final/walker_side_by_side.gif` |

## Versions (cluster, what actually works)

Resolved by `uv` with `exclude-newer = 2025-08-06` (the Playground repo's last commit was 2025-08-05):

| Package | Version |
|---|---|
| python | 3.12 (uv-managed) |
| jax / jaxlib / jax-cuda12-plugin | 0.7.0 |
| mujoco / mujoco-mjx | 3.3.4 |
| playground (mujoco_playground) | 0.0.5 |
| brax | 0.12.4 |
| flax | 0.11.0 |
| orbax-checkpoint | 0.11.20 |
| tensorflow / tf2onnx / onnx / onnxruntime | 2.19.0 / 1.16.1 / 1.17.0 / 1.22.1 |
| numpy | 2.1.3 |
| motion generator: python / placo / numpy | 3.10.12 / 0.6.3 / 1.26.4 (`exclude-newer = 2025-04-04`) |
| uv | 0.13.6 |
| GPU / driver / CUDA | RTX A4000 16 GB / 570.211.01 / 12.8 |

Upstream commits: Open_Duck_Mini `b23317a` (v2), Open_Duck_Playground `b9be205` (main),
Open_Duck_reference_motion_generator `3d7bc6f` (main), Open_Duck_Mini_Runtime `376de65` (v2).

## Exact commands

```bash
# --- install (cluster) ---
curl -LsSf https://astral.sh/uv/install.sh | sh            # -> ~/.local/bin/uv
# git-lfs is not installed system-wide and needs no sudo this way:
curl -sL https://github.com/git-lfs/git-lfs/releases/download/v3.6.1/git-lfs-linux-amd64-v3.6.1.tar.gz | tar xz -C /tmp \
  && cp /tmp/git-lfs-3.6.1/git-lfs ~/.local/bin/
cd $OPENDUCK_ROOT
for r in Open_Duck_Mini Open_Duck_Playground Open_Duck_reference_motion_generator Open_Duck_Mini_Runtime; do
  git clone https://github.com/apirrone/$r.git; done

cd Open_Duck_Playground && git checkout -b local/setup
printf '\n[tool.uv]\nexclude-newer = "2025-08-06T00:00:00Z"\n' >> pyproject.toml
uv sync
# + one line in playground/common/export_onnx.py (see "What broke", #2). Both are in locks/playground_local_setup.patch

# --- reference motions (CPU, ~3 min with -j16) ---
cd ../Open_Duck_reference_motion_generator && git lfs install --local && git lfs pull   # STLs are LFS
git checkout -b local/setup && printf '\n[tool.uv]\nexclude-newer = "2025-04-04T00:00:00Z"\n' >> pyproject.toml
uv sync
uv run scripts/auto_waddle.py -j16 --duck open_duck_mini_v2 --sweep --output_dir recordings
uv run scripts/fit_poly.py --ref_motion recordings/
cp polynomial_coefficients.pkl ../Open_Duck_Playground/playground/open_duck_mini_v2/data/
# USE_IMITATION_REWARD is already True in joystick.py at b9be205

# --- training (GPU; wrapper does nvidia-smi + lock + trap + env vars) ---
cd $OPENDUCK_ROOT
ALLOW_BUSY_GPU=1 setsid nohup tools/launch_train.sh 0 smoke_5M_b 5000000   > /dev/null 2>&1 &   # smoke
ALLOW_BUSY_GPU=1 setsid nohup tools/launch_train.sh 0 full_300M 300000000  > /dev/null 2>&1 &   # the "current win"
#   which runs, inside Open_Duck_Playground:
#   CUDA_VISIBLE_DEVICES=0 XLA_PYTHON_CLIENT_PREALLOCATE=false XLA_PYTHON_CLIENT_MEM_FRACTION=0.75 \
#     uv run playground/open_duck_mini_v2/runner.py --task flat_terrain_backlash --num_timesteps 300000000 --output_dir <runs/...>
uv run tensorboard --logdir ../runs                   # from Open_Duck_Playground

# --- headless evaluation + GIF (CPU, OSMesa; never touches a GPU) ---
cd Open_Duck_Playground
MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES= \
  uv run python ../tools/duck_eval.py -o ../Open_Duck_Mini/BEST_WALK_ONNX_2.onnx \
  --scenes scene_flat_terrain_backlash.xml,scene_flat_terrain.xml --out ../results/best2.json --gif ../results/best2.gif
MUJOCO_GL=osmesa uv run python ../tools/ref_gif.py --pkl playground/open_duck_mini_v2/data/polynomial_coefficients.pkl \
  --gif ../results/ref_generated.gif

# --- interactive viewer on the Mac (keyboard: arrows = vx/vy, a/e = yaw, h = head mode) ---
cd ~/Desktop/OpenDuck/Open_Duck_Playground
PYTHONPATH=. ../.venv-mac/bin/mjpython playground/open_duck_mini_v2/mujoco_infer.py -o ../Open_Duck_Mini/BEST_WALK_ONNX_2.onnx
#   .venv-mac = uv venv --python 3.12 + jax==0.7.0 mujoco==3.3.4 mujoco-mjx==3.3.4 playground==0.0.5 onnxruntime etils
#   ml-collections pillow (CPU jax; jax[cuda12] has no macOS wheels, so the repo's own `uv sync` cannot run on a Mac)
```

## What broke and how it was fixed

1. **Unpinned dependencies break the code.** The repo has no lockfile and asks for `playground>=0.0.3`, `jax>=0.5`.
   In Oct 2026 that resolves to jax 0.12 / mujoco 3.17 / playground 0.2.0, and `joystick.py` fails on import:
   `ModuleNotFoundError: mujoco_playground._src.collision`. Fix: `[tool.uv] exclude-newer` at the repo's commit
   date, so everything resolves as it did when the code was written. No code changes needed for this.
2. **OOM at the first checkpoint.** `runner.py` exports ONNX at every eval through TensorFlow. TF initialises the GPU
   on first use and reserves ~11.9 GB of it next to JAX, so the next PPO update dies with
   `RESOURCE_EXHAUSTED: Out of memory while trying to allocate 788445576 bytes`. Fix (one line, `export_onnx.py`):
   `tf.config.set_visible_devices([], "GPU")`; export now runs on CPU. On a 24 GB+ GPU upstream may never see this.
3. **Motion generator meshes are Git LFS** and neither machine had git-lfs: on the Mac the clone checkout fails, on the
   cluster the STLs are 130-byte pointer files. Fix: user-local git-lfs binary + `git lfs pull` (cluster); the Mac
   clone uses `GIT_LFS_SKIP_SMUDGE=1` (generation runs on the cluster only).
4. Harmless noise you will see: `ERROR:tf2onnx.tfonnx: rewriter rewrite_constant_fold ... np.cast was removed` on
   every export (NumPy 2; that optimisation is skipped, the ONNX is correct); `RuntimeWarning: overflow encountered
   in cast`; a `TypeError: 'NoneType' object is not callable` from the OSMesa context at interpreter exit after a GIF
   is written; `Polyfit may be poorly conditioned` from `fit_poly.py`.
5. `train.log` shows no `STEP:` lines until the run ends (Python buffers stdout to a file). Watch tensorboard instead.

## Findings about the upstream pipeline (verified in sim, not changed)

- **Our reference motions reproduce theirs exactly**: same 240-key grid, every evaluated polynomial identical
  (max abs diff 0.0); the pickle bytes differ only by serialisation.
- **The pretrained policy will not start walking from rest for small or rightward commands.** After 2 s of zero
  command it stays still for |vx| <= 0.075, all |vy| except +0.2 (vy = -0.2 never starts), and |wz| = 0.25.
  Training never starts an episode at rest (every episode starts with a sampled command; only 10% of commands are
  zero), so walk initiation from standing is under-trained. Probe: `tools/probe_deadzone.py`. Confirmed: with the
  command applied from t = 0 (no standing phase) it does walk right (vy -0.111) and every other command except
  vx = 0.075, which stays still either way.
- **The reference stores base velocities, not base positions.** Each 40-dim frame = 16 joint pos, 16 joint vel,
  2 foot contacts, 3 base linear vel, 3 base angular vel (all world frame). Training is free-floating; the base moves
  only through foot contact, rewarded by command tracking (vx/vy 2.5, yaw 6.0) and imitation (1.0). Our first
  reference GIF pinned the base (as upstream's `ref_motion_viewer.py` does); `results/ref_generated_moving.gif`
  integrates the reference's own base velocity instead.
- **Upstream bug: the reference yaw rate is ~40x too small.** `gait_generator.py:compute_angular_velocity` multiplies
  `as_rotvec()` (already angle-scaled) by `angle / dt` again, so it records w * (w * dt) instead of w. The recorded
  base orientations turn correctly: gait `-0.074_0.037_0.963` turns at 1.012 rad/s by its quaternions but records
  wz = 0.025; `-1.111` -> -1.090 vs -0.029; `0.444` -> 0.486 vs 0.006. So the imitation term's yaw-rate part (weight
  0.5) rewards *not* turning while `tracking_ang_vel` (weight 6.0) rewards turning; tracking wins (BEST_WALK_ONNX_2
  turns at 0.94 rad/s). The roll/pitch rates are shrunk the same way. Not fixed, to keep the reproduction faithful.
  This also makes the turning segments of `ref_generated_moving.gif` barely rotate.
- **Imitation compares world-frame velocities under random spawn yaw.** `reward_imitation` matches the robot's
  world-frame base velocity (`qvel[:3]`) to the reference's world-frame velocity, but `reset()` spawns every robot at
  a random yaw in +-3.14 rad, so that part of the term only lines up when the robot happens to face +x. It also
  computes a torso-orientation term from reference dims 3:7, which are joint angles (no quaternion is stored); that
  term is never added to the sum, so it has no effect.
- **The reference covers less than the command range.** Commands are clamped to the nearest gait on the grid; the
  reference's own mean speeds are vx +0.155 / -0.116 for commanded +-0.15 and vy +-0.115 for commanded +-0.2.
- **Accelerometer offset mismatch.** `joystick.py` calls `accelerometer.at[0].set(accelerometer[0] + 1.3)` and drops
  the result (JAX arrays are immutable), so training never adds +1.3 to accel-x; `mujoco_infer.py` does add it. The
  robot runtime instead subtracts a calibrated `x_offset`. Not changed, so our training matches theirs.
- **Default viewer scene has no backlash.** `mujoco_infer.py` defaults to `scene_flat_terrain.xml`; training uses the
  backlash scene. We evaluate on both.
- **Deploy contract (Open_Duck_Mini_Runtime `v2_rl_walk_mujoco.py`)**: 50 Hz; `target = init_pos + 0.25 * action`;
  leg kp 30, head kp 8; obs = gyro, accel, 7 commands, joint pos - default, 0.05 * joint vel, last 3 actions, motor
  targets, 2 foot contacts, 2 phase (101 dims, same as training). Differences from sim: the motor speed clip is
  commented out on the robot, the phase speed is 1.0 (1.3 while LB is held) plus a d-pad offset in 0.05 steps
  (`get_phase_frequency_factor`, which would scale 1.0 -> 1.2 with |vx|, is defined but never called), and head
  commands are added on top of the policy's head targets. The Playground README of 2025-04 to 2025-06 says the real
  robot ran this walk at kp 22, not the script's default 30.

- **Only the two foot soles can touch the floor.** Every other geom has contype = conaffinity = 0, so a fallen duck
  sinks through the ground. Fine for walking (a fall ends the episode), unusable for recovery. Note: setting masks on
  a compiled MuJoCo model is not enough; `body_contype`/`body_conaffinity` must be updated too, or the broadphase
  silently drops the pairs (cost three wrong renders before it was found).
- **Domain randomization hits the wrong ids.** `randomize.py` hardcodes `FLOOR_GEOM_ID = 0` (a trunk mesh; the floor
  is geom 46), so floor friction is never randomized, and `TORSO_BODY_ID = 1` (`base`, 0.0 kg; the trunk is
  `trunk_assembly`, 0.70 kg), so the CoM shift does nothing and the +-0.1 kg torso offset gives about half the envs a
  negative point mass. Left as is for the walker reproduction; the get-up/jump tasks look both ids up by name.

## Next tasks (owner's order, 2026-10-29): recovery, then a simple in-place jump

Queued on GPU 0 behind the walker (`tools/queue_runs.sh`, queue file `tools/queue_after_walker.txt`, log
`queue.log`): getup smoke 5M -> getup 200M -> jump smoke 5M -> jump 100M -> walker v2 300M (`--env joystick_sdr`:
upstream walker + fixed DR ids + floor-surface DR, action scale 0.25; added at the owner's request). Each launch goes through
`launch_train.sh`; a refused launch retries every 5 min, a failed run stops the queue. Local commit `f9b63e9` on
`local/setup` (cluster).

**Feasibility first** (`tools/feasibility_gifs.py`, GIFs `results/feasibility_fall_poses.gif`,
`results/feasibility_jump.gif`):
- Max-effort open-loop jump (deep crouch, then full extension, base on a vertical rail, an optimistic bound): the soles
  leave the floor for 8-10 ms at a peak upward speed of 0.25 m/s, with the 5.24 rad/s speed clip or with only the
  3.23 Nm torque limit. An airborne flip in that time needs ~600 rad/s of body rotation, ~100x out of reach, so
  "flips" were redefined with the owner as roll-overs inside recovery. The jump task targets a hop of a few mm.
- Random drops (100, with body collisions): 44 land on a side, 30 on the back, 25 on the front, 1 upright.

**Get-up task** (`playground/open_duck_mini_v2/getup.py`):
- Model: `tools/make_getup_model.py` adds one collision box per body (13, fitted to the visual mesh vertices, shrunk
  10%, zero density so mass/inertia are unchanged; separate collision bit so boxes touch only the floor). Standing at
  home, only the soles touch the floor, so walking contact is unchanged. Picture: `results/getup_model_boxes.png`.
- Starts: 60% from a 4096-state bank of settled drops (`tools/make_getup_bank.py`; front 1355, back 1172, side
  1566, sitting 3), random heading; 20% mid-fall (standing + up to 1 m/s push and 4 rad/s spin); 20% standing.
- Obs 92 (robot-available: gyro, accel, joint pos/vel, last 3 actions, motor targets, foot contacts); critic adds
  gravity, height, velocities, forces, head contact. Actions: home + 1.0 x action (the walker's 0.25 cannot reach
  get-up poses), same 5.24 rad/s clip, 0-2 step action delay, same noise and DR (with the ids fixed).
- Reward: upright 4, height 4, home pose 3 and stillness 1 (both only once up), head touching the floor -2, base spin,
  joint speed, torque and action-rate costs. No termination; 10 s episodes.
- Eval: `tools/getup_eval.py` (fresh drops from seeds the bank never used + standing + pushed starts; success = up
  and at height for the whole final second; time to stand; head-contact fraction; GIF).
- Runtime use would be a switch: walker -> get-up on a detected fall -> walker when stable.

**Jump task** (`playground/open_duck_mini_v2/jump.py`): 4 s episodes from standing; a trigger turns on at a random
time in 0.5-2 s for 0.5 s (obs 94 = get-up's 92 + trigger + time since trigger). Paid inside the window for upward
speed, both soles off the floor and base height; outside it for standing still at home; penalised for lifting a foot
outside the window, drift and spin; falls end the episode (reward clipped at 0 per step, as upstream's walker does).
Eval: `tools/jump_eval.py` (air time, base rise, sole lift, drift, standing at the end; GIF).

**Floor-surface randomization** (`playground/open_duck_mini_v2/surface_dr.py`, owner request 2026-10-29), used by
get-up and jump: per env, floor friction U[0.25, 1.0] and softness from MuJoCo's hard default to "thick carpet"
(standing sink 0.2 -> 6.9 mm). The floor has contact priority 1, so its values alone set every foot contact.
Sensitivity check first (`tools/surface_eval.py`, tile / wood / default / rubber mat / carpet / thick carpet):
neither BEST_WALK_ONNX_2 nor our walker at 193M falls on any of them (6/6 random 60 s runs each); slippery tile
mostly costs backward speed (pretrained -0.051 vs -0.077 m/s; ours -0.025 vs -0.084) and ours turns left better on
soft floors. GIFs `results/surface_best2_tile.gif`, `results/surface_best2_thick_carpet.gif`. The carpet model is a
uniform soft contact, not measured carpet: treat carpet verdicts as provisional.

**Results of the queued runs (2026-10-29/30, all exit 0; queue done 04:29):**

| run | wall time | result (fresh tests, CPU MuJoCo, `results/overnight/`) |
|---|---|---|
| getup_200M | 22:11 -> 00:43 | **stands up from the front 15-16/16 and from a side 8-12/16, never from the back (0/8)**; holds standing starts 4/4 and pushed starts 7/8. Best checkpoint is 173M (27/40 fallen starts; final 202M: 24/40). From the back it reaches a stable sitting pose (head up, legs forward) and stays there. Training was still improving (steps standing per episode 20 at 43M -> 279/500 at 202M). GIF `results/overnight/getup_final.gif` |
| jump_100M | 00:53 -> 02:10 | **no jump**: on the trigger it extends the legs and raises the base ~19 mm, but the soles never leave the floor (0 ms airborne in 10/10 trials; open-loop bound was 8-10 ms); stays standing 10/10, drift ~9 mm. GIF `results/overnight/jump_final.gif` |
| walker_sdr_300M | 02:10 -> 04:29 | **worse than the first walker**: tracking score 0.72-0.83 (first walker 0.30, pretrained 0.41); walks forward (~0.10 m/s) but backward, side-steps and turning are near zero on every floor and from rest or a direct start. Most likely cause: fixing upstream's torso-id bug switched on its +-5 cm CoM shift (and +-0.1 kg) on the real trunk, a disturbance upstream never actually trained with; surfaces down to friction 0.25 add to it. Not separated yet. |

Both pipelines were tested end to end on CPU (64 envs, 0.1M steps: build, train, export ONNX, evaluate, GIF):
`results/getup_cpu_test.gif`, `results/jump_cpu_test.gif` (untrained policies, they fall, as expected).

## Training cost

| Run | Steps | Wall time | Throughput | GPU memory (incl. 1.25 GB of another user's job) |
|---|---|---|---|---|
| smoke_5M_b | 6.9M | 9 min (1 min compile) | ~14.5k steps/s | ~2.6 GB in use |
| full_300M | 300M | 4 h 40 min (17:20 -> 22:00) | ~23.8k steps/s for the first hour, ~18k/s later (shared box) | 6.6 GB on the GPU in total, ~5.4 GB ours |

PPO config is mujoco_playground's `BerkeleyHumanoidJoystickFlatTerrain` (8192 envs, unroll 20, 32 minibatches,
4 updates/batch, 15 evals -> a checkpoint + ONNX every ~20M steps on the full run).

## Our policy vs BEST_WALK_ONNX_2

Same evaluator (`tools/duck_eval.py`), same schedules, both scenes, 3 seeds. Each command starts from a 2 s
standstill. Metrics: survival; mean body-frame vx, vy, yaw rate over the last 70% of a 10 s window; per-swing foot
clearance; and 6 random-command 60 s runs. Checkpoints were chosen by behaviour, not by training reward (the reward
at 300M had dipped; the last checkpoint is not the best).

**Tracking score** = mean over 7 commands of |achieved - commanded| / |commanded| (`tools/score_tracking.py`;
lower is better, 1.0 = does not move). Every policy below survived every test (6/6 random 60 s on both scenes).

| policy | no-backlash scene | backlash scene | mean |
|---|---|---|---|
| BEST_WALK_ONNX_2 (pretrained) | 0.478 | 0.344 | 0.411 |
| ours 172M | 0.588 | 0.474 | 0.531 |
| ours 193M | 0.580 | 0.437 | 0.509 |
| **ours 258M (chosen)** | **0.374** | **0.234** | **0.304** |
| ours 279M | 0.393 | 0.263 | 0.328 |
| ours 300M | 0.420 | 0.259 | 0.340 |

Backlash scene, from a standstill (pretrained -> ours 258M): forward 0.133 -> 0.123; back -0.078 -> -0.078;
left 0.096 -> 0.143; right 0.000 -> -0.105 (the pretrained policy never starts side-stepping right); turn left
+0.94 -> +0.96; turn right -0.88 -> -0.96; forward+turn 0.50 -> 0.58 rad/s; foot clearance forward 19/17 ->
17/20 mm. Both still ignore half-stick forward (0.075) from a standstill.

Robot-loop test (`tools/robot_loop_eval.py`: action scale 0.2, no speed clip, the robot's IMU filter, raw accel
without upstream's +1.3): both policies stand, walk, stop and survive 6/6 random runs in every combination; the IMU
filter freezes the accelerometer on 16-36% of steps. Surfaces (`tools/surface_eval.py`): both survive tile ->
thick carpet 6/6; ours is slower forward on carpet (0.09 vs 0.13 m/s on thick carpet) and turns better everywhere.
GIFs: `results/final/walker_side_by_side.gif` (same command schedule, pretrained left, ours right),
`results/final/ours258M.gif`. ONNX: `policies/ours_walker_full300M_258M.onnx` (sha256 31328ec8...), the same
101-in / 14-out contract as BEST_WALK_ONNX_2, so it is a drop-in on the robot.

BEST_WALK_ONNX_2 detail (backlash scene, 3 seeds):

| segment | cmd (vx, vy, wz) | survived | vx | vy | wz | clearance L/R mm | air |
|---|---|---|---|---|---|---|---|
| stand | 0, 0, 0 | 3/3 | 0.000 | 0.000 | 0.000 | 0 / 0 | 0.00 |
| fwd | 0.15, 0, 0 | 3/3 | 0.133 | 0.019 | 0.001 | 18.6 / 16.9 | 0.65 |
| back | -0.15, 0, 0 | 3/3 | -0.078 | -0.018 | 0.028 | 6.9 / 9.9 | 0.47 |
| left | 0, 0.2, 0 | 3/3 | 0.001 | 0.096 | -0.005 | 12.3 / 3.7 | 0.41 |
| right | 0, -0.2, 0 | 3/3 | 0.000 | 0.000 | 0.000 | 0 / 0 | 0.00 |
| yaw_l | 0, 0, 1 | 3/3 | -0.015 | 0.054 | 0.936 | 14.0 / 10.3 | 0.47 |
| yaw_r | 0, 0, -1 | 3/3 | -0.017 | -0.054 | -0.876 | 8.4 / 9.4 | 0.39 |
| fwd_yaw | 0.15, 0, 0.5 | 3/3 | 0.118 | 0.046 | 0.501 | 15.4 / 16.5 | 0.61 |
| half_fwd | 0.075, 0, 0 | 3/3 | 0.000 | 0.000 | 0.001 | 0 / 0 | 0.00 |
| random 60 s | | 6/6 | | | | | |

## GPU / cluster rules followed

The cluster is shared. The owner allowed GPU 0 for this work (2026-10-29); it also runs another
user's xarm job (~1.25 GB), so the wrapper needs `ALLOW_BUSY_GPU=1` there and JAX is capped at 75% of memory.
`launch_train.sh` refuses to start if `$OPENDUCK_LOCKS/walker_waiting` exists, takes
`$OPENDUCK_LOCKS/gpuN` with an atomic mkdir, writes `openduck <run> pid <PID>` into `gpuN/info`, and an EXIT trap removes
the lock only if it still holds our tag. All evaluation and rendering run on CPU.

## Next-step options

Already queued at the owner's request (see "Next tasks" above): get-up/recovery, in-place jump, walker v2 with
floor-surface randomization and the two DR fixes. Not started:

1. **Match the robot's action scale.** The robot runs 0.2; every policy was trained at 0.25, and in sim 0.2 cuts the
   pretrained walk to ~1/6 of its speed. Either deploy at 0.25 (robot side) or train a walker at 0.2.
2. **Joint-offset calibration on the robot.** All 14 offsets in the robot's duck_config.json are 0.0; upstream's
   `find_soft_offsets.py` measures them. A record-and-compare tool (robot `--save_obs` log vs sim at the same pose)
   would show offsets, IMU axis signs and foot-switch polarity directly.
3. **Start-from-rest and half-stick commands.** Both walkers ignore |vx| < ~0.1 from a standstill. Train with
   episodes that start at rest and with zero/small commands more often than 10%.
4. **Upstream reward bugs:** reference yaw rate ~40x too small (gait_generator double-counts the angle), imitation
   in world frame under random spawn yaw, unused orientation term, `accelerometer.at[0].set` no-op. Each is a small
   fix; train an A/B against the current recipe.
5. **Rough terrain:** upstream ships `scene_rough_terrain_backlash.xml` (1 cm height field); train/evaluate on it.
6. **Latency and motor-model randomisation:** Open_Duck_Mini's `docs/sim2real.md` / BAM actuator identification
   for the STS3215; randomise the 0-3 step action delay more widely and add the robot's measured control-loop
   overruns (0.6-0.85 s stalls right after unpause in the robot journal).
7. **Head commands while walking:** the robot's head range (yaw +-0.5, pitch -0.78..0.3) is narrower than training's
   (yaw +-1.5); evaluate and, if needed, match the training range to the robot.
8. **Runtime skill switching** for get-up and jump on the robot (fall detection -> get-up -> walker; RB/other
   button -> jump), after both policies pass their sim gates.
