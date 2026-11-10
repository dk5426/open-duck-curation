"""Get-up IMU correction in the patched v2_rl_walk_mujoco.py, no robot:
1. DUCK_IMU_STANDING_ACC set and the duck standing at home -> the get-up sees the model's standing reading (uprightness
   0.972, not 0.883), and the runtime standing test agrees;
2. unset -> the get-up sees the raw reading, unchanged;
3. the walker's observation is identical, number for number, to the installed version's (same fake sensors);
4. the get-up recording keeps the raw IMU.
  python test_mock_imu_corr.py
"""

import glob
import importlib.util
import os
import sys
import tempfile
import threading

import numpy as np

import test_mock_getup as T

HERE = os.path.dirname(os.path.abspath(__file__))
ROBOT_STANDING = np.array([-0.15, -4.22, 7.94])
SIM_STANDING = np.array([-1.22, -1.95, 9.54])
os.environ["DUCK_RECORD_DIR"] = tempfile.mkdtemp()


def load_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    mod = T.load()  # patched, with every hardware module stubbed
    mod.time.sleep = lambda s: None
    mod.time.monotonic = lambda: T.Clock.t
    ok = True
    T.World.pos = np.array(T.HOME)
    T.World.accel = ROBOT_STANDING.copy()

    # 1. correction on
    os.environ["DUCK_IMU_STANDING_ACC"] = ",".join(str(x) for x in ROBOT_STANDING)
    w = T.make(mod)
    T.press(w, 11)
    pos, vel = w._read_joints()
    obs, acc = w._getup_obs(pos, vel)
    up = acc[2] / np.linalg.norm(acc)
    case1 = np.allclose(obs[3:6], SIM_STANDING, atol=1e-6) and abs(up - 0.972) < 0.001
    print(f"1. correction on: get-up sees accel {np.round(obs[3:6], 3)} (model {SIM_STANDING}), uprightness "
          f"{up:.3f}: {'PASS' if case1 else 'FAIL'}")
    ok &= case1

    # 2. correction off
    os.environ.pop("DUCK_IMU_STANDING_ACC")
    w2 = T.make(mod)
    T.press(w2, 11)
    obs2, acc2 = w2._getup_obs(pos, vel)
    case2 = np.allclose(obs2[3:6], ROBOT_STANDING) and abs(acc2[2] / np.linalg.norm(acc2) - 0.883) < 0.001
    print(f"2. correction off: get-up sees raw accel {np.round(obs2[3:6], 3)}: {'PASS' if case2 else 'FAIL'}")
    ok &= case2

    # 3. walker observation identical to the installed version, correction set
    os.environ["DUCK_IMU_STANDING_ACC"] = ",".join(str(x) for x in ROBOT_STANDING)
    # the real HWI returns numpy arrays (the walker subtracts the home pose from them)
    T.FakeHWI.get_present_positions = lambda self, ignore=None: np.array(T.World.pos)
    T.FakeHWI.get_present_velocities = lambda self, ignore=None: np.zeros(14)
    orig = load_file(os.path.join(HERE, "original_installed/scripts/v2_rl_walk_mujoco.py"), "walk_installed")
    orig.time.sleep = lambda s: None
    same = True
    rng = np.random.default_rng(0)
    wa, wb = T.make(mod), T.make(orig)
    for k in range(50):
        T.World.accel = ROBOT_STANDING + rng.normal(0, 1.0, 3)
        T.World.pos = np.array(T.HOME) + rng.normal(0, 0.05, 14)
        for w_ in (wa, wb):
            w_.last_commands = [0.1, 0.0, 0.2, 0, 0, 0, 0]
            w_.imitation_phase = np.array([np.cos(k / 10), np.sin(k / 10)])
        oa, ob = wa.get_obs(), wb.get_obs()
        same &= oa is not None and ob is not None and np.array_equal(oa, ob)
    print(f"3. walker observation identical to the installed version over 50 steps: {'PASS' if same else 'FAIL'}")
    ok &= same

    # 4. get-up recording: obs carries the corrected IMU, gyro_raw / acc_raw the raw one
    T.World.accel, T.World.pos = ROBOT_STANDING.copy(), np.array(T.HOME) + 0.3
    w = T.make(mod)
    T.press(w, 11)
    for _ in range(5):
        w._getup_step()
        T.Clock.t += 0.02
    w.rec.close()
    for th in threading.enumerate():
        if th is not threading.current_thread() and th.daemon:
            th.join(timeout=5)
    f = sorted(glob.glob(os.path.join(os.environ["DUCK_RECORD_DIR"], "*_getup.npz")))[-1]
    d = np.load(f)
    case4 = np.allclose(d["acc_raw"][0], ROBOT_STANDING, atol=1e-4) and np.allclose(d["obs"][0, 3:6], SIM_STANDING,
                                                                                   atol=1e-3)
    print(f"4. get-up log: raw {np.round(d['acc_raw'][0], 2)}, policy saw {np.round(d['obs'][0, 3:6], 2)}: "
          f"{'PASS' if case4 else 'FAIL'}")
    ok &= case4
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
