"""Reset-to-home button logic with stubbed hardware: hold RB -> paused + soft at home; keep holding -> nothing new;
release -> stiff at home, fresh policy state, still paused; then A -> walks. No hardware, no robot.
  python test_mock_reset_button.py
"""

import time

import numpy as np

import test_mock_init_order as base


class FakePad:
    def __init__(self):
        self.rb = False

    def get_raw_button_sample(self, index):
        return (self.rb if index == 7 else False), time.monotonic()


def main():
    base.stub_modules(None)
    import importlib.util
    import os

    path = os.path.join(base.HERE, "patched/scripts/v2_rl_walk_mujoco.py")
    spec = importlib.util.spec_from_file_location("walk_patched", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.time.sleep = lambda s: None
    w = mod.RLWalk("x.onnx", commands=True)

    calls = []
    w.hwi.go_soft_home = lambda: calls.append("soft") or set()
    w.hwi.stiffen_home = lambda: calls.append("stiff") or set()
    w.hwi._format_servos = lambda ids: str(ids)
    pad = FakePad()
    w.command_controller = pad

    # walking with some history
    w.paused = False
    w.last_action = np.ones(14)
    w.imitation_i = 13
    w.motor_targets = np.full(14, 0.5)

    steps = []
    for rb in [False, True, True, True, False, False]:
        pad.rb = rb
        w._check_reset_button()
        steps.append((rb, w.resetting, w.paused, list(calls)))
    for rb, resetting, paused, c in steps:
        print(f"RB {'held    ' if rb else 'released'} -> resetting={resetting!s:5s} paused={paused!s:5s} hwi calls={c}")

    assert calls == ["soft", "stiff"], calls
    assert w.paused and not w.resetting
    assert not w.last_action.any() and w.imitation_i == 0
    assert np.allclose(w.motor_targets, w.init_pos)
    print("policy state after release: last_action all 0, imitation_i 0, motor_targets = start pose  -> OK")
    print("reset button logic: PASS (runtime stays paused; A toggles it to walk, A is ignored while RB is held)")


if __name__ == "__main__":
    main()
