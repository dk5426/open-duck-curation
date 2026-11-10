"""Does the robot's measured IMU offset (imu_offset_eval: 17.5 deg rotation, 0.916 x magnitude, from a recorder log)
break a get-up policy? Runs getup_eval's starts with the simulated gyro and accelerometer rotated (and scaled) by the
offset, vs the plain sim IMU. Also reports the robot runtime's standing test (acc_z / |acc| > 0.85) as the robot would
compute it from the offset reading when the duck really stands at home.

  cd Open_Duck_Playground && .venv/bin/python ../tools/getup_imu_offset_eval.py --log <walk.npz> -o getup.onnx [-o ...]
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getup_eval import CLASS_NAMES, GetupSim, episode, starts  # noqa: E402
from imu_offset_eval import SIM_STANDING_ACC, rotation_between  # noqa: E402


class OffsetGetupSim(GetupSim):
    R, acc_scale = np.eye(3), 1.0

    def obs(self):
        o = super().obs()
        o[0:3] = self.R @ o[0:3]
        o[3:6] = self.acc_scale * (self.R @ o[3:6])
        return o


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("-o", "--onnx", action="append", required=True)
    p.add_argument("--n", type=int, default=40)
    a = p.parse_args()
    log = np.load(a.log)
    t = log["t"] - log["t"][0]
    still = (t > 1) & (t < 5) & np.all(np.abs(log["commands"][:, :3]) < 1e-3, axis=1)
    robot_acc = np.median(log["acc_raw"][still], axis=0)
    R = rotation_between(SIM_STANDING_ACC, robot_acc)
    scale = np.linalg.norm(robot_acc) / np.linalg.norm(SIM_STANDING_ACC)
    print(f"offset: rotation {np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))):.1f} deg, "
          f"magnitude x{scale:.3f}")
    print(f"runtime standing test at home: sim reading {SIM_STANDING_ACC[2] / np.linalg.norm(SIM_STANDING_ACC):.3f}, "
          f"robot reading {robot_acc[2] / np.linalg.norm(robot_acc):.3f} (threshold 0.85)")

    variants = {"sim IMU": (np.eye(3), 1.0), "robot IMU offset": (R, scale)}
    for onnx in a.onnx:
        sim = OffsetGetupSim(onnx)
        home_q = sim.m.keyframe("home").qpos.copy()
        rng = np.random.default_rng(7)
        cases = starts(a.n)
        cases += [(9, home_q, None)] * 4
        cases += [(8, home_q, np.r_[rng.uniform(-1, 1, 2), 0, rng.uniform(-4, 4, 3)]) for _ in range(8)]
        print(f"\n== {os.path.basename(onnx)}")
        print(f"{'IMU':18s} " + " ".join(f"{c:>9s}" for c in ["front", "back", "side", "standing", "pushed"]))
        for name, (Rv, sc) in variants.items():
            sim.R, sim.acc_scale = Rv, sc
            res = {}
            for c, q, v in cases:
                res.setdefault(CLASS_NAMES[c], []).append(episode(sim, q, v, 10.0)["success"])
            print(f"{name:18s} " + " ".join(f"{sum(res.get(c, [])):>4d}/{len(res.get(c, [])):<4d}"
                                           for c in ["front", "back", "side", "standing", "pushed"]))


if __name__ == "__main__":
    main()
