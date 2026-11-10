# Get-up soft start (2026-11-02)

On top of `walker_switch_20261030`. Only `scripts/v2_rl_walk_mujoco.py` changes (`soft_start_vs_installed.patch`).

For the first `DUCK_GETUP_SOFT_S` seconds of a get-up (default 0.5 s) the joint-speed limit is multiplied by
`DUCK_GETUP_SOFT_FACTOR` (default 1/3). All 14 servos starting at full speed pulled about 10 A and once browned out the
Raspberry Pi. In simulation (`tools/getup_real_eval.py --soft 0.5`) it cuts the start-up torque peak from 39 to
25 N·m and still stands from 13/13 recorded robot starts at full servo strength.

Test (no robot): `python test_mock_soft_start.py`; the other `test_mock_*.py` cover the earlier changes on the same file.
