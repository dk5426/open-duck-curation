# Open Duck startup hardening + reset-to-home button (2026-10-29)

Prepared and tested off the robot only (mock servo bus and stubbed hardware); **nothing here has run on the robot**.
Built against the files currently deployed on the duck (hashes below match the robot's own shutdown-update
manifest of 2026-10-13).

## What changes

| Problem on the robot | Change |
|---|---|
| The duck sometimes doesn't reach its start pose | `turn_on()` now: switches torque on explicitly; writes kp with re-tries over several rounds and treats a servo that never takes it as an error (before, a kp write that failed inside `turn_on` only printed a warning and left that joint at the soft start-up kp 2); reads every joint back and re-sends goal + kp to any joint more than 0.15 rad off the pose, then names it (`turn on : pose reached (worst ...)` or `[WARN] pose check ...`). A servo that failed an earlier write but recovered is no longer counted as dead. |
| Restart after `./run_duck.sh stop` leaves the legs soft | `stop` switches torque off and start-up never switched it back on; it is now switched on explicitly (new rustypot API: `sync_write_torque_enable`; the old `rustypot.feetech` API is used only if it has `enable_torque`). |
| A crash after standing up gives a sag / re-pose loop | IMU, foot switches, controller and gait reference are now set up **before** any motor moves; eyes / projector / speaker / ears that fail to start are disabled with a warning instead of crashing the runtime. |
| Controller "connected" but the script crashes | `run_duck.sh` only waits for `/dev/input/js0`; the controller class now also waits (default 30 s, `DUCK_PYGAME_JOYSTICK_TIMEOUT`) until pygame sees a joystick. |
| No way to recover without a restart | **Reset button (RB):** hold RB -> the walker pauses and the duck goes soft (kp 2) holding the home pose, so you can stand it up by hand; release RB -> it stiffens into the home pose, re-checks every joint, and the policy's memory (last actions, gait phase, motor targets) is cleared like a fresh start; it stays paused. Press **A** to walk again. A is ignored while RB is held. Button index via `DUCK_RESET_BUTTON_INDEX` (default 7 = RB in this pad's mapping, same table as A=0, B=1, X=3, Y=4, LB=6). |

Not changed: walking itself, gains (kp 22 / head 8), action scale, the IMU filter, the shutdown button, sounds,
ears. Files: `patched/` (full files), `original/` (what is on the robot now), `startup_hardening.patch` (diff).

## Tests run (on a Mac, no hardware)

```
python test_mock_startup.py        # fake STS3215 bus with injected faults, original vs patched HWI
python test_mock_init_order.py     # RLWalk.__init__ with every hardware module stubbed
python test_mock_reset_button.py   # hold / release RB, then A
```
| Case | original | patched |
|---|---|---|
| healthy bus | starts | starts, `pose reached` |
| torque left off by `run_duck.sh stop` | starts with **every joint limp** | starts, pose reached |
| flaky left_knee (fails its first 4 writes) | aborts | recovers on re-try, starts |
| dead right_ankle | aborts | aborts (loud, names the servo) |
| left_ankle stuck 0.3 rad short | starts silently off-pose | starts, warns `left_ankle -0.30` after 3 re-write rounds |
| IMU fails to start | **motors move**, then crash | crash before any motor moves |
| controller fails to start | **motors move**, then crash | crash before any motor moves |
| eyes fail to start | motors move, then crash | eyes disabled, duck starts |
| reset button (fake bus) | - | hold: all kp 2, torque on; release: every joint back at home; policy state cleared; paused |

What the mocks cannot tell: real servo timing, whether your servo firmware already re-enables torque on a goal write
(upstream relies on that), and whether 0.15 rad is the right pose tolerance under the duck's own weight (it only
warns, never aborts, on pose error).

## Install on the duck (robot side; keep the duck on a stand or hold it for the first start)

```bash
cd /home/duck/open_duck_mini_runtime
sudo systemctl stop open-duck-runtime

# 1. the files must be exactly the ones this patch was built against
sha256sum scripts/v2_rl_walk_mujoco.py \
          mini_bdx_runtime/mini_bdx_runtime/rustypot_position_hwi.py \
          mini_bdx_runtime/mini_bdx_runtime/xbox_controller.py
#   80ec9148de57ed5fd92fc4251028c60afd6980ccb1b3354aca0354842663fdff  scripts/v2_rl_walk_mujoco.py
#   c1d338132e73010f0531c940fadfe1dcf4fc8af28b51e57acaddb2bc3ef9671e  .../rustypot_position_hwi.py
#   fbcdd315dc726059db62e800301a3efd6b491da17487fcd9df109197991a4556  .../xbox_controller.py
#   (any mismatch: stop, the robot copy changed since 2026-10-13)

# 2. backup
B=~/startup_hardening_backup_$(date +%Y%m%d_%H%M%S); mkdir -p $B
cp -a scripts/v2_rl_walk_mujoco.py mini_bdx_runtime/mini_bdx_runtime/rustypot_position_hwi.py \
      mini_bdx_runtime/mini_bdx_runtime/xbox_controller.py $B/

# 3. copy the three files from patched/ (scp them over first), then
sudo systemctl start open-duck-runtime
journalctl -u open-duck-runtime -f
```
Expected log on a good start: `[START] sensors and controller ready; moving to the start pose`, `turn on : low KPS
set`, `turn on : init pos set`, `turn on : high kps`, `turn on : pose reached (worst <joint> <error> rad)`, then the
usual sounds and `Done instantiating RLWalk`. Then try: A (walk) -> A (pause) -> hold RB, set it upright, release ->
`[RESET] at the home pose, paused; press A to start the policy` -> A.

**Rollback:** `sudo systemctl stop open-duck-runtime`, copy the three files back from `$B`, start again.

Patched file hashes (check after copying):
```
43638f4241e2917678f26ddf833ed67207a63cc124b41501f0ab5742864e7297  scripts/v2_rl_walk_mujoco.py
81cc764dd36f3d1767164f80b5eff121743426f0f69301b4f17e9e0207e56e60  mini_bdx_runtime/mini_bdx_runtime/rustypot_position_hwi.py
c3836819651cac5a9f1f88f865752869e995a32f98382aed572290927e4bca0b  mini_bdx_runtime/mini_bdx_runtime/xbox_controller.py  (CRLF kept, as on the robot)
```
