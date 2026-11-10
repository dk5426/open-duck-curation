"""Per-axis IMU plot: the robot's raw gyro and accelerometer from a recorder log vs the simulated IMU of the same
policy driven by the same command sequence through the robot loop (robot_log_compare.sim_run). Sim and robot are both
closed loop, so their gait phases drift apart: compare levels, ranges and rhythm, not individual peaks.

Writes <out>_full.png (whole run) and <out>_zoom.png (--zoom seconds, default a walking stretch), with single-sample
IMU glitches marked, and prints per-axis mean / std for standing and walking.

  cd Open_Duck_Playground && .venv/bin/python ../tools/imu_plot.py --log <walk.npz> -o <policy.onnx> --out <prefix>
"""

import argparse
import ast
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robot_log_compare import sim_run  # noqa: E402


def glitches(gyro, acc):
    g = np.linalg.norm(gyro, axis=1) > 10
    a = np.linalg.norm(acc, axis=1)
    return g | (a < 4) | (a > 25)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--scene", default="scene_flat_terrain_backlash.xml")
    p.add_argument("--out", required=True)
    p.add_argument("--zoom", type=float, nargs=2, default=None, help="start end, seconds")
    a = p.parse_args()

    log = np.load(a.log)
    meta = ast.literal_eval(str(log["meta"]))
    sim, fell, _ = sim_run(a.onnx, a.scene, log, meta["action_scale"])
    t = log["t"] - log["t"][0]
    ts = np.arange(len(sim["obs"])) * 0.02
    rg, ra = log["gyro_raw"], log["acc_raw"]
    sg, sa = sim["gyro_raw"], sim["acc_raw"]
    bad = glitches(rg, ra)
    moving = np.any(np.abs(log["commands"][:, :3]) > 1e-3, axis=1)
    smoving = moving[: len(ts)]

    print(f"{os.path.basename(a.log)}: {len(t)} robot steps, {bad.sum()} IMU glitch samples excluded from stats; "
          f"sim {'fell at %d' % fell if fell is not None else 'no fall'}")
    print(f"{'':16s} {'standing: robot':>22s} {'sim':>16s}   {'walking: robot':>22s} {'sim':>16s}")
    for name, R, S in [("gyro", rg, sg), ("accel", ra, sa)]:
        for i, ax in enumerate("xyz"):
            cells = []
            for sel_r, sel_s in [(~moving & ~bad, ~smoving), (moving & ~bad, smoving)]:
                r, s = R[sel_r, i], S[sel_s, i]
                cells += [f"{r.mean():+6.2f} ± {r.std():4.2f}", f"{s.mean():+6.2f} ± {s.std():4.2f}"]
            print(f"{name + ' ' + ax:16s} {cells[0]:>22s} {cells[1]:>16s}   {cells[2]:>22s} {cells[3]:>16s}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if a.zoom is None:  # first 8 s stretch of forward walking
        fw = np.where(log["commands"][:, 0] > 0.1)[0]
        z0 = t[fw[0]] + 1.0 if len(fw) else 10.0
        a.zoom = (z0, z0 + 6.0)

    def figure(x0, x1, path, lw):
        fig, ax = plt.subplots(7, 1, figsize=(14, 17), sharex=True)
        ax[0].plot(t, log["commands"][:, 0], label="vx"); ax[0].plot(t, log["commands"][:, 1], label="vy")
        ax[0].plot(t, log["commands"][:, 2], label="wz"); ax[0].set_ylabel("command"); ax[0].legend(loc="upper right")
        rows = [("gyro x (rad/s)", rg[:, 0], sg[:, 0]), ("gyro y (rad/s)", rg[:, 1], sg[:, 1]),
                ("gyro z (rad/s)", rg[:, 2], sg[:, 2]), ("accel x (m/s²)", ra[:, 0], sa[:, 0]),
                ("accel y (m/s²)", ra[:, 1], sa[:, 1]), ("accel z (m/s²)", ra[:, 2], sa[:, 2])]
        for k, (lab, r, s) in enumerate(rows, start=1):
            ax[k].plot(ts, s, color="tab:orange", lw=lw, label="sim (same commands)")
            ax[k].plot(t, np.where(bad, np.nan, r), color="tab:blue", lw=lw, label="robot")
            if bad.any():
                ax[k].plot(t[bad], np.clip(r[bad], *ylim(r[~bad], s)), "rx", ms=4, label="robot glitch (clipped)")
            ax[k].set_ylim(*ylim(r[~bad], s))
            ax[k].set_ylabel(lab)
            ax[k].axhline(0, color="k", lw=0.3)
            if k == 1:
                ax[k].legend(loc="upper right", ncol=3)
        ax[-1].set_xlabel("s")
        ax[-1].set_xlim(x0, x1)
        fig.suptitle(f"{os.path.basename(a.log)} ({meta['walker_onnx']}, scale {meta['action_scale']}): raw IMU, "
                     f"robot vs sim, per axis")
        fig.tight_layout()
        fig.savefig(path, dpi=85)
        print("PNG:", path)

    def ylim(r, s):
        v = np.concatenate([r, s])
        lo, hi = np.percentile(v, 0.5), np.percentile(v, 99.5)
        pad = 0.15 * (hi - lo + 1e-3)
        return lo - pad, hi + pad

    figure(0, t[-1], a.out + "_full.png", 0.5)
    figure(a.zoom[0], a.zoom[1], a.out + "_zoom.png", 1.0)


if __name__ == "__main__":
    main()
