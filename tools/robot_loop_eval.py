"""Reproduce the real robot's walk loop (duck/Open_Duck_Mini_Runtime/scripts/v2_rl_walk_mujoco.py) in MuJoCo and switch
its differences from training on one at a time, to find which one makes the walker fall.

Robot differences from the training/eval loop (duck_eval.Runner):
  scale    action_scale 0.2 (run_duck.sh) instead of 0.25
  noclip   no 5.24 rad/s motor-target speed clip (commented out on the robot)
  imu      the robot's IMU filter: accel clipped to +-10 and replaced by the last accepted sample whenever any axis
           exceeds 9.8 m/s^2; gyro clipped to +-5 and replaced by the last accepted sample when it jumps > 2 rad/s
Test: 2 s stand, 4 s forward at full stick, release for 6 s; plus 6 random-command 60 s runs.

  uv run python ../tools/robot_loop_eval.py -o <policy.onnx> [--gif-config all --gif out.gif]
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from duck_eval import SEGMENTS, Runner, render_gif  # noqa: E402


class RobotLoop(Runner):
    def configure(self, scale=False, noclip=False, imu=False):
        self.action_scale = 0.2 if scale else 0.25
        self.noclip, self.imu_filter = noclip, imu
        self._good_gyro = self._good_acc = None
        self.acc_frozen = self.gyro_frozen = self.samples = 0

    def get_obs(self, data, command):
        obs = super().get_obs(data, command)
        # Upstream's MjInfer adds +1.3 to accel x; training never does (a JAX no-op) and the robot doesn't either
        # (its tare_x is commented out), so undo it here for every configuration.
        obs[3] -= 1.3
        if self.imu_filter:
            gyro, acc = np.clip(obs[0:3], -5, 5), np.clip(obs[3:6], -10, 10)
            self.samples += 1
            if self._good_gyro is not None and np.any(np.abs(gyro - self._good_gyro) > 2.0):
                gyro = self._good_gyro
                self.gyro_frozen += 1
            else:
                self._good_gyro = gyro.copy()
            if self._good_acc is not None and np.any(np.abs(acc) > 9.8):
                acc = self._good_acc
                self.acc_frozen += 1
            else:
                self._good_acc = acc.copy()
            obs[0:3], obs[3:6] = gyro, acc
        return obs

    def control_step(self):
        if not self.noclip:
            return super().control_step()
        saved = self.max_motor_velocity
        self.max_motor_velocity = 1e6
        try:
            return super().control_step()
        finally:
            self.max_motor_velocity = saved


CONFIGS = {
    "training loop": {},
    "+ scale 0.2": {"scale": True},
    "+ no speed clip": {"noclip": True},
    "+ IMU filter": {"imu": True},
    "robot (all three)": {"scale": True, "noclip": True, "imu": True},
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--onnx", action="append", required=True)
    p.add_argument("--scene", default="scene_flat_terrain_backlash.xml")
    p.add_argument("--gif", default=None)
    p.add_argument("--gif-config", default="robot (all three)")
    a = p.parse_args()
    ref = "playground/open_duck_mini_v2/data/polynomial_coefficients.pkl"
    for onnx in a.onnx:
        r = RobotLoop(f"playground/open_duck_mini_v2/xmls/{a.scene}", onnx, ref)
        print(f"\n== {os.path.basename(onnx)}")
        print(f"{'loop':20s} {'stand 2s':>9s} {'walk+release':>13s} {'random 60s':>11s} {'acc frozen':>11s} {'gyro frozen':>12s}")
        for name, cfg in CONFIGS.items():
            stand_ok = walk_ok = rand_ok = 0
            acc_f = gyro_f = n = 0
            for seed in range(3):
                r.configure(**cfg)
                stand_ok += r.rollout([(100, [0, 0, 0])], np.random.default_rng(seed))["fell_at"] is None
                r.configure(**cfg)
                log = r.rollout([(100, [0, 0, 0]), (200, SEGMENTS["fwd"]), (300, [0, 0, 0])], np.random.default_rng(seed))
                walk_ok += log["fell_at"] is None
                acc_f += r.acc_frozen
                gyro_f += r.gyro_frozen
                n += r.samples
            for seed in range(6):
                rng = np.random.default_rng(100 + seed)
                sched = [(100, [0, 0, 0])]
                for _ in range(30):
                    c = [rng.uniform(-0.15, 0.15), rng.uniform(-0.2, 0.2), rng.uniform(-1, 1)]
                    sched.append((100, [0.0, 0.0, 0.0] if rng.random() < 0.1 else c))
                r.configure(**cfg)
                rand_ok += r.rollout(sched, rng)["fell_at"] is None
            fa = f"{100 * acc_f / n:.0f}%" if n else "-"
            fg = f"{100 * gyro_f / n:.0f}%" if n else "-"
            print(f"{name:20s} {stand_ok:>7d}/3 {walk_ok:>11d}/3 {rand_ok:>9d}/6 {fa:>11s} {fg:>12s}")
        if a.gif and onnx == a.onnx[0]:
            r.configure(**CONFIGS[a.gif_config])
            fell = render_gif(r, a.gif, f"{os.path.basename(onnx)}: {a.gif_config}")
            print("GIF:", a.gif, "fell at", fell)


if __name__ == "__main__":
    main()
