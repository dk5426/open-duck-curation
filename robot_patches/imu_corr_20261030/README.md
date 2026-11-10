# Open Duck: get-up IMU correction + no voltage cutoff during get-up (2026-10-30)

On top of `recorder_20261030` (`1a21db15`). Only `scripts/v2_rl_walk_mujoco.py` changes (`imu_corr_vs_installed.patch`,
sha256 `9615bcbf...`) plus one line in `40-skills.conf`. INSTALLED 2026-10-30 ~14:40 (runtime was stopped; files only).

**IMU correction (get-up only).** The robot's accelerometer at the home pose reads (-0.15, -4.22, 7.94) m/s^2; the
training model's reads (-1.22, -1.95, 9.54): 17.5 deg apart and 8% low (walk log 20261030_135301, 1-5 s standing).
In sim this offset dropped getup_173M's side starts 12/16 -> 7/16 (tools/getup_imu_offset_eval.py), and the runtime's
standing test read 0.883 at home vs 0.972 in sim (threshold 0.85). With `DUCK_IMU_STANDING_ACC=-0.15,-4.22,7.94`
the get-up's gyro and accelerometer are rotated by that 17.5 deg and scaled x1.071 before the policy and the standing
test see them. The walker's observation is not touched (test 3: identical to the installed version, number for
number). Re-measure after any IMU remount: median `acc_raw` over a few seconds standing still at home in a recorder
log. Unset -> no correction. The get-up recording keeps the raw IMU in `gyro_raw`/`acc_raw`; `obs` has the corrected.

**Voltage cutoff (owner request).** During a get-up the 6.5 V cutoff is ignored (logged as `[GETUP] bus voltage ...
ignored`). A get-up start sagged the bus from 7.8 V to 5.6 V within 0.16 s and the cutoff ended the runtime. Optional
hard floor during get-up: `DUCK_GETUP_MIN_VOLTAGE` (unset = none). Walking and paused keep the normal cutoff, and it is
back as soon as a get-up ends.

Tests (Mac and the duck's Python): `test_mock_imu_corr.py` (4), `test_mock_voltage.py` (4), plus getup, reset
button, recorder: all PASS.

Rollback: copy `~/imu_corr_20261030/v2_rl_walk_mujoco.py.recorder_installed` back to `scripts/`, restore
`~/imu_corr_20261030/40-skills.conf.before` to `/etc/systemd/system/open-duck-runtime.service.d/40-skills.conf`,
`sudo systemctl daemon-reload`.
