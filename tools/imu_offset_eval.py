"""Does the IMU difference measured on the robot explain a walker's falls? Rotate (and scale) the simulated
accelerometer and gyro by the offset between the robot's standing accelerometer reading (from a recorder log) and the
sim's, then run the robot loop (robot_loop_eval.RobotLoop: no speed clip, the robot's IMU filter, scale 0.25) for
several walkers, with and without the offset.

  cd Open_Duck_Playground && .venv/bin/python ../tools/imu_offset_eval.py --log <walk.npz> -o a.onnx -o b.onnx
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robot_loop_eval import RobotLoop  # noqa: E402

SIM_STANDING_ACC = np.array([-1.22, -1.95, 9.54])  # robot_log_compare / this model at home, 2026-10-30


def rotation_between(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), np.dot(a, b)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


class OffsetLoop(RobotLoop):
    R, acc_scale = np.eye(3), 1.0

    def get_obs(self, data, command):
        # apply the mount offset to the true sensors, THEN the robot's filter (as on the robot)
        imu = self.imu_filter
        self.imu_filter = False
        obs = super().get_obs(data, command)
        self.imu_filter = imu
        obs[0:3] = self.R @ obs[0:3]
        obs[3:6] = self.acc_scale * (self.R @ obs[3:6])
        if imu:
            gyro, acc = np.clip(obs[0:3], -5, 5), np.clip(obs[3:6], -10, 10)
            if self._good_gyro is not None and np.any(np.abs(gyro - self._good_gyro) > 2.0):
                gyro = self._good_gyro
            else:
                self._good_gyro = gyro.copy()
            if self._good_acc is not None and np.any(np.abs(acc) > 9.8):
                acc = self._good_acc
            else:
                self._good_acc = acc.copy()
            obs[0:3], obs[3:6] = gyro, acc
        return obs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("-o", "--onnx", action="append", required=True)
    p.add_argument("--seeds", type=int, default=6)
    a = p.parse_args()
    log = np.load(a.log)
    t = log["t"] - log["t"][0]
    still = (t > 1) & (t < 5) & np.all(np.abs(log["commands"][:, :3]) < 1e-3, axis=1)
    robot_acc = np.median(log["acc_raw"][still], axis=0)
    R = rotation_between(SIM_STANDING_ACC, robot_acc)
    ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    scale = np.linalg.norm(robot_acc) / np.linalg.norm(SIM_STANDING_ACC)
    print(f"robot standing accel {np.round(robot_acc, 2)} vs sim {SIM_STANDING_ACC}: rotation {ang:.1f} deg, "
          f"magnitude x{scale:.3f}")
    ref = "playground/open_duck_mini_v2/data/polynomial_coefficients.pkl"
    variants = {"sim IMU": (np.eye(3), 1.0), "robot's IMU tilt": (R, 1.0), "robot's IMU tilt + scale": (R, scale)}
    robot_sched = [(1, list(c[:3])) for c in log["commands"]]
    print(f"\n{'walker':36s} {'IMU':26s} {'stand':>6s} {'robot cmds':>11s} {'random 60s':>11s} {'mean tilt':>10s}")
    for onnx in a.onnx:
        r = OffsetLoop(f"playground/open_duck_mini_v2/xmls/scene_flat_terrain_backlash.xml", onnx, ref)
        for name, (Rv, sc) in variants.items():
            r.R, r.acc_scale = Rv, sc
            ok_stand = ok_robot = ok_rand = 0
            tilts = []
            for seed in range(a.seeds):
                rng = np.random.default_rng(seed)
                r.configure(noclip=True, imu=True)
                r.action_scale = 0.25
                ok_stand += r.rollout([(250, [0, 0, 0])], rng)["fell_at"] is None
                up = r.data.site_xmat[r.imu_site_id].reshape(3, 3)[2, 2]
                tilts.append(np.degrees(np.arccos(np.clip(up, -1, 1))))
                r.configure(noclip=True, imu=True)
                r.action_scale = 0.25
                ok_robot += r.rollout(robot_sched, np.random.default_rng(seed))["fell_at"] is None
                sched = [(100, [0, 0, 0])]
                for _ in range(30):
                    c = [rng.uniform(-0.15, 0.15), rng.uniform(-0.2, 0.2), rng.uniform(-1, 1)]
                    sched.append((100, [0.0, 0.0, 0.0] if rng.random() < 0.1 else c))
                r.configure(noclip=True, imu=True)
                r.action_scale = 0.25
                ok_rand += r.rollout(sched, rng)["fell_at"] is None
            n = a.seeds
            print(f"{os.path.basename(onnx):36s} {name:26s} {ok_stand:>4d}/{n} {ok_robot:>9d}/{n} {ok_rand:>9d}/{n} "
                  f"{np.mean(tilts):>8.1f}deg")


if __name__ == "__main__":
    main()
