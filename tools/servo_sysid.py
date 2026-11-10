"""Measure how the real servos follow their targets, from recorder logs, and the same numbers for the sim replaying
the same get-up starts (getup_real_eval.ProtectedGetupSim, full self-collision, protection, soft start).

Per joint group (hips, knees, ankles, head):
  delay    the shift (in 20 ms control steps) that best lines up the target's motion with the joint's motion
           (cross-correlation of the per-step changes)
  v99      99th percentile joint speed reached (rad/s): how fast the joint actually moves when asked
  lag      mean |target(k) - position(k+1)| (rad)
  slope    least-squares gain of position change vs target change at the best delay (1 = follows fully)

  cd Open_Duck_Playground && .venv/bin/python ../tools/servo_sysid.py --logs ../robot_logs/20261102_18*_getup.npz \
      -o <getup.onnx> [--sim-torque 1.0]
"""

import argparse
import ast
import glob
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GROUPS = {"hips": ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "right_hip_yaw", "right_hip_roll",
                   "right_hip_pitch"],
          "knees": ["left_knee", "right_knee"], "ankles": ["left_ankle", "right_ankle"],
          "head": ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]}


def measure(targets, pos, names, max_delay=8):
    """targets[k] = target sent at step k, pos[k] = position read at step k (before that step's target)."""
    out = {}
    dt_t = np.diff(targets, axis=0)
    dp = np.diff(pos, axis=0)
    for g, js in GROUPS.items():
        idx = [names.index(j) for j in js]
        best, scores = 0, []
        for dly in range(0, max_delay + 1):
            a = dt_t[: len(dt_t) - dly, idx].ravel()
            b = dp[dly:, idx].ravel()
            scores.append(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
        best = int(np.argmax(scores))
        a = dt_t[: len(dt_t) - best, idx].ravel()
        b = dp[best:, idx].ravel()
        slope = float(np.dot(a, b) / (np.dot(a, a) + 1e-9))
        v = np.abs(dp[:, idx]) / 0.02
        lag = np.abs(targets[:-1, idx] - pos[1:, idx]).mean()
        out[g] = dict(delay=best, corr=float(scores[best]), v99=float(np.percentile(v, 99)), lag=float(lag),
                      slope=slope)
    return out


def summarize(label, rows):
    print(f"\n{label}")
    print(f"  {'group':7s} {'delay (steps)':>13s} {'corr':>5s} {'v99 rad/s':>9s} {'lag rad':>8s} {'slope':>6s}")
    for g in GROUPS:
        r = [x[g] for x in rows]
        print(f"  {g:7s} {np.median([x['delay'] for x in r]):13.1f} {np.median([x['corr'] for x in r]):5.2f} "
              f"{np.median([x['v99'] for x in r]):9.2f} {np.median([x['lag'] for x in r]):8.3f} "
              f"{np.median([x['slope'] for x in r]):6.2f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", nargs="+", required=True)
    p.add_argument("-o", "--onnx", default=None, help="also replay each start in sim with this policy")
    p.add_argument("--sim-torque", type=float, default=1.0)
    p.add_argument("--seconds", type=float, default=4.0)
    a = p.parse_args()
    logs = []
    for x in a.logs:
        for f in sorted(glob.glob(x)):
            try:
                d = np.load(f)
                if "pos" in d.files and len(d["t"]) > 60:
                    logs.append((f, d))
            except Exception:
                pass
    print(f"{len(logs)} robot get-up logs")
    names = ast.literal_eval(str(logs[0][1]["meta"]))["joints"]
    n = int(a.seconds * 50)
    summarize("ROBOT (recorded)", [measure(d["targets"][:n], d["pos"][:n], names) for _, d in logs])
    if a.onnx:
        from getup_real_eval import ProtectedGetupSim, full_selfcollision_model
        from getup_replay import start_state

        rows = []
        for _, d in logs:
            sim = ProtectedGetupSim(a.onnx)
            sim.m = full_selfcollision_model()
            sim.d = mujoco.MjData(sim.m)
            sim.m.actuator_forcerange[:] *= a.sim_torque
            sim.protect, sim.soft_s, sim.soft_factor = True, 0.5, 1 / 3
            q = start_state(sim, d["pos"][0], d["obs"][0, 3:6])
            sim.start(q)
            tg, ps = [], []
            for _ in range(n):
                ps.append(sim.d.qpos[sim.qadr].copy())
                sim.step()
                tg.append(sim.targets.copy())
            rows.append(measure(np.array(tg), np.array(ps), names))
        summarize(f"SIM (same starts, torque x{a.sim_torque})", rows)


if __name__ == "__main__":
    main()
