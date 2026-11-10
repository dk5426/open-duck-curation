# Open Duck: new walker + button-triggered get-up (2026-10-30)

On top of `startup_hardening_20261029` (installed 2026-10-29). Only `scripts/v2_rl_walk_mujoco.py` changes (+130 lines,
`skills_vs_installed.patch`), plus two policy files and one service config file. Tested off the robot only.

## What it adds

**New walker** `ours_walker_full300M_258M.onnx`: same inputs/outputs as BEST_WALK_ONNX_2 (101 -> 14), so it is chosen
by `DUCK_ONNX_MODEL` in `40-skills.conf`; no code change. In sim it tracks commands 26% better than BEST_WALK_ONNX_2,
side-steps right (the old one never starts), and passed the robot's exact loop (scale 0.2, no speed clip, IMU filter).
Back to the old walker: delete the `DUCK_ONNX_MODEL` line and restart.

**Get-up on a button** (`DUCK_GETUP_BUTTON_INDEX`, default 11 = Menu on this pad; measure it with `button_probe.py`):
1. The duck has fallen; press the button. The walker stops, the get-up policy (`getup_173M.onnx`) takes the motors with a
   fresh history, starting from the current joint positions.
2. Get-up runs at 50 Hz with exactly its training contract: 92 inputs (gyro, accelerometer, joint pos - home,
   0.05 x joint vel, last 3 actions, motor targets, foot contacts), action scale 1.0, joint limits and the 5.24 rad/s
   speed limit of the training model. It does **not** use the walker's IMU filter (that filter freezes the
   accelerometer whenever an axis reads > 9.8 m/s^2, i.e. most of the time on the floor).
3. Upright (accelerometer z / |a| > 0.85 and every leg joint within 0.35 rad of home) for 1 s -> blends to the home
   pose over 0.5 s -> paused with a fresh walker state. Press **A** to walk.
4. Not upright after 10 s -> stops and holds still, paused. Press the button again to retry, or hold RB to reset by hand.
5. **A** during a get-up aborts it (holds still, paused). **RB** cancels it and starts the soft reset. The low-battery
   cutoff and the shutdown button work in every mode. No get-up policy file -> the button does nothing.

In sim the 173M get-up policy stands up from the front 15/16, from a side 12/16, never from the back (0/8; a back
roll-over policy is training), holds standing 4/4 and recovers pushes 7/8.

## Tests (Mac, no hardware): `python test_mock_getup.py`, plus the three earlier tests on this combined file
| case | result |
|---|---|
| fallen -> button (held 5 samples: starts once) -> upright -> 1 s -> settle -> paused, walker memory cleared, joints at home, policy saw 92 inputs | PASS |
| never upright -> stops at 10.04 s, paused | PASS |
| RB during get-up -> cancelled, soft reset | PASS |
| no get-up policy file -> button ignored | PASS |
| startup hardening / init order / RB reset tests (from 2026-10-29) | PASS |

Not covered: real servo behaviour of the get-up (the duck pushes against the floor with its whole body; kp is 22 on
the legs and 8 on the head here, the training model used one gain for all joints), and the real button index.

## Install (robot side; duck on a stand or held for the first get-up, battery charged)
```bash
# 0. measure the button (read-only, safe while the runtime runs): press Menu, note the index
/home/duck/.venv/bin/python ~/skills_20261030/button_probe.py 20
# 1. files
cd /home/duck/open_duck_mini_runtime
sha256sum scripts/v2_rl_walk_mujoco.py   # must start 43638f42 (the startup-hardening version)
cp scripts/v2_rl_walk_mujoco.py ~/startup_hardening_backup_20261029/v2_rl_walk_mujoco.py.hardened
cp ~/skills_20261030/patched/scripts/v2_rl_walk_mujoco.py scripts/      # sha256 0b5117e1...
cp ~/skills_20261030/ours_walker_full300M_258M.onnx ~/skills_20261030/getup_173M.onnx .
sudo cp ~/skills_20261030/40-skills.conf /etc/systemd/system/open-duck-runtime.service.d/   # fix the index first
sudo systemctl daemon-reload && sudo systemctl restart open-duck-runtime
journalctl -u open-duck-runtime -f    # expect "[GETUP] policy loaded: ... button index N"
```
**Rollback:** `sudo rm /etc/systemd/system/open-duck-runtime.service.d/40-skills.conf`, copy
`v2_rl_walk_mujoco.py.hardened` back, `sudo systemctl daemon-reload && sudo systemctl restart open-duck-runtime`.
