# Open Duck: walker switch on the View button (2026-10-30)

On top of `imu_corr_20261030` (`9615bcbf`). Only `scripts/v2_rl_walk_mujoco.py` changes
(`walker_switch_vs_installed.patch`, sha256 `d92b82e1...`). INSTALLED 2026-10-30 ~15:00 (runtime was stopped; file only).

Both walkers are loaded at start: the main one (`DUCK_ONNX_MODEL`, now ours_walker_full300M_258M) and a second one
(`DUCK_ALT_ONNX_MODEL`, default `BEST_WALK_ONNX_2.onnx` in the runtime folder). **While paused**, View (⧉,
`DUCK_WALKER_SWITCH_BUTTON_INDEX`, default 10) swaps them and clears the walker's memory like a fresh start; the log
says `[WALKER] switched to <name>; press A to walk`. While walking, during a get-up or during an RB reset the button
is ignored (`[WALKER] pause first`). Every restart begins on the main walker. The recorder's `meta` names the active
walker in each file.

Index 10 is inferred (Menu measured as 11 on this pad; View sits next to it) and not yet measured: if the log shows
no `[WALKER]` line on View, run `button_probe.py` and set `DUCK_WALKER_SWITCH_BUTTON_INDEX` in `40-skills.conf`.
Unused today besides View: D-pad left/right (a hat, not a button index).

Tests (Mac and the duck's Python): `test_mock_walker_switch.py` (5 cases) plus get-up, reset, IMU correction,
voltage, init order: all PASS.

Rollback: copy `~/walker_switch_20261030/v2_rl_walk_mujoco.py.imu_corr_installed` back to `scripts/`.
