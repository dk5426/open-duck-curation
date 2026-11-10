"""Get-up soft start in the patched v2_rl_walk_mujoco.py, no robot: for the first 0.5 s a target moves at most
5.24 / 3 rad/s (0.035 rad per 20 ms step), afterwards at the full 5.24 rad/s (0.105 rad per step).
The fake policy alternates +1 / -1 so every step hits the speed limit.
  python test_mock_soft_start.py
"""

import sys

import numpy as np

import test_mock_getup as T


class Push:  # asks for home +1 / -1 rad on alternate steps, so the speed limit binds and no joint reaches its range end
    def __init__(self, *a, **k):
        self.k = 0

    def infer(self, obs):
        self.k += 1
        return np.ones(14) * (1 if self.k % 2 else -1)


def main():
    mod = T.load()
    mod.time.sleep = lambda s: None
    mod.time.monotonic = lambda: T.Clock.t
    T.World.accel, T.World.pos = np.array([9.8, 0, 0]), np.array(T.HOME)
    w = T.make(mod)
    T.press(w, 11)
    w.getup_policy = Push()
    steps = []
    prev = w.g_targets.copy()
    for k in range(40):
        w._getup_step()
        steps.append(np.max(np.abs(w.g_targets - prev)))
        prev = w.g_targets.copy()
        T.Clock.t += 0.02
    steps = np.array(steps)
    soft, full = steps[:25], steps[26:30]
    ok = np.allclose(soft, 5.24 / 50 / 3, atol=1e-9) and np.allclose(full, 5.24 / 50, atol=1e-9)
    print(f"1. per-step target change: first 0.5 s {soft.max():.4f} rad (want {5.24 / 150:.4f}), "
          f"after {full.max():.4f} rad (want {5.24 / 50:.4f}): {'PASS' if ok else 'FAIL'}")
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
