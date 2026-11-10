"""Walker switch (View, button 10) in the patched v2_rl_walk_mujoco.py, no robot: switches only while paused, clears
the walker's memory, toggles back, is ignored while walking, held down switches once, and is disabled without a
second walker file.
  python test_mock_walker_switch.py
"""

import os
import sys

import numpy as np

import test_mock_getup as T


def press(w, idx, steps=1):
    w.command_controller.buttons[idx] = True
    for _ in range(steps):
        w._check_walker_button()
    w.command_controller.buttons[idx] = False
    w._check_walker_button()


def main():
    mod = T.load()
    mod.time.sleep = lambda s: None
    mod.time.monotonic = lambda: T.Clock.t
    ok = True
    os.environ["DUCK_ALT_ONNX_MODEL"] = os.path.abspath(T.__file__)  # any existing file: FakePolicy ignores it
    w = T.make(mod)
    first = w.policy
    w.paused = True
    w.last_action = np.ones(14)
    w.imitation_i = 7
    press(w, 10, steps=5)  # held for 5 samples: one switch
    case1 = (len(w.walkers) == 2 and w.policy is w.walkers[1][1] and w.policy is not first
             and not w.last_action.any() and w.imitation_i == 0 and w.rec.meta["walker_onnx"] == w.walkers[1][0])
    print(f"1. paused + View (held) -> one switch to {w.walkers[1][0]}, memory cleared: {'PASS' if case1 else 'FAIL'}")
    ok &= case1

    press(w, 10)
    case2 = w.policy is first and w.rec.meta["walker_onnx"] == w.walkers[0][0]
    print(f"2. View again -> back to {w.walkers[0][0]}: {'PASS' if case2 else 'FAIL'}")
    ok &= case2

    w.paused = False
    w.last_action = np.ones(14)
    press(w, 10)
    case3 = w.policy is first and w.last_action.all()
    print(f"3. walking + View -> ignored, nothing reset: {'PASS' if case3 else 'FAIL'}")
    ok &= case3

    w.paused = True
    T.World.accel, T.World.pos = np.array([9.8, 0, 0]), np.array(T.HOME) + 0.6
    T.press(w, 11)  # get-up running
    press(w, 10)
    case4 = w.getup_active and w.policy is first
    print(f"4. during a get-up + View -> ignored: {'PASS' if case4 else 'FAIL'}")
    ok &= case4

    os.environ["DUCK_ALT_ONNX_MODEL"] = "/nonexistent.onnx"
    w = T.make(mod)
    w.paused = True
    first = w.policy
    press(w, 10)
    case5 = len(w.walkers) == 1 and w.policy is first
    print(f"5. no second walker file -> switch disabled: {'PASS' if case5 else 'FAIL'}")
    ok &= case5
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
