"""Low-voltage cutoff in the patched v2_rl_walk_mujoco.py, no robot: ignored during a get-up (owner 2026-10-30),
unchanged while walking, and an optional get-up floor (DUCK_GETUP_MIN_VOLTAGE) still cuts.
  python test_mock_voltage.py
"""

import os
import sys

import numpy as np

import test_mock_getup as T


def main():
    mod = T.load()
    mod.time.sleep = lambda s: None
    mod.time.monotonic = lambda: T.Clock.t
    state = {"v": 7.8, "off": 0}
    T.FakeHWI.get_present_voltages = lambda self: [state["v"]] * 14
    T.FakeHWI.get_present_currents = lambda self: [0.5] * 14
    T.FakeHWI.joint_names = T.NAMES
    T.FakeHWI.turn_off = lambda self: state.__setitem__("off", state["off"] + 1)
    ok = True

    def check(w, v):
        state["v"], state["off"] = v, 0
        return w.check_motor_voltage(log_power=True), state["off"]

    w = T.make(mod)
    w.min_motor_voltage = 6.5
    r = [check(w, 7.8), check(w, 5.6)]
    case1 = r == [(True, 0), (False, 1)]
    print(f"1. walking: 7.8 V keeps going, 5.6 V cuts torque and stops: {'PASS' if case1 else 'FAIL'} {r}")
    ok &= case1

    os.environ.pop("DUCK_GETUP_MIN_VOLTAGE", None)
    T.World.accel, T.World.pos = np.array([9.8, 0, 0]), np.array(T.HOME) + 0.6
    w = T.make(mod)
    w.min_motor_voltage = 6.5
    T.press(w, 11)
    r = [check(w, 5.6), check(w, 4.0)]
    case2 = w.getup_active and r == [(True, 0), (True, 0)]
    print(f"2. during get-up, no floor: 5.6 V and 4.0 V both ignored: {'PASS' if case2 else 'FAIL'} {r}")
    ok &= case2

    os.environ["DUCK_GETUP_MIN_VOLTAGE"] = "5.0"
    r = [check(w, 5.6), check(w, 4.8)]
    case3 = r == [(True, 0), (False, 1)]
    print(f"3. during get-up, floor 5.0 V: 5.6 V ignored, 4.8 V cuts: {'PASS' if case3 else 'FAIL'} {r}")
    ok &= case3
    os.environ.pop("DUCK_GETUP_MIN_VOLTAGE")

    w._getup_finish("test", success=False)
    r = [check(w, 5.6)]
    case4 = r == [(False, 1)]
    print(f"4. after the get-up ends, the normal cutoff is back: {'PASS' if case4 else 'FAIL'} {r}")
    ok &= case4
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
