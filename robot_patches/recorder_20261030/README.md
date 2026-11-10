# Open Duck: step recorder (2026-10-30)

On top of `skills_20261030` (installed 2026-10-30 13:33). Only `scripts/v2_rl_walk_mujoco.py` changes
(`recorder_vs_installed.patch`, sha256 `1a21db15...`). INSTALLED 2026-10-30 14:04 on the duck.

v1 (`47cdb301`, 13:51) built Python lists and converted them every 30 s: the first real walk showed 65 ms and 97 ms
stalls at 30 s and 60 s (3-5 missed control steps). v2 copies each step into preallocated arrays and writes only the
new rows every 30 s (part files, merged at the end of the segment) from a low-priority thread. On the duck's Pi
(test 4, 1500 steps at 50 Hz, 9 part saves): worst step 3.8 ms, loop period max 20.2 ms.

Records every 50 Hz control step of the walker and the get-up to `~/duck_logs/<YYYYmmdd_HHMMSS>_<walk|getup>.npz`, one
file per segment (a segment ends when stepping stops for > 0.5 s: pause, abort, finish). Written by a background thread
at the end of a segment and every 30 s during one. Does not change what the robot does. Off: `DUCK_RECORD=0`.

| field | walk | getup |
|---|---|---|
| `t` (monotonic s) | yes | yes |
| `obs` (exactly what the policy saw) | 101 | 92 |
| `action` (raw policy output) | 14 | 14 |
| `targets` (sent to the servos) | 14, incl. head commands | 14 |
| `gyro_raw`, `acc_raw` (IMU before the walker's filter) | yes | yes (get-up uses raw) |
| `pos`, `vel` (present joints) | in `obs` | yes |
| `commands`, `took` (loop time) | yes | - |
| `meta` | walker / get-up ONNX, action scales, kp, joint order, home pose | same |

Tests (Mac and on the duck's Python): `test_mock_recorder.py` (get-up writes 40x92 obs; a pause splits walker segments;
`DUCK_RECORD=0` writes nothing; worst add() < 10 ms and no late loop step with part saves) plus the four earlier mock tests, all PASS.

Rollback: copy `~/skills_20261030/v2_rl_walk_mujoco.py.skills_installed` back to `scripts/` and restart.
