"""Compare a real-robot walker recording (robot_patches/recorder_20261030, ~/duck_logs/*_walk.npz) with the same
policy in MuJoCo driven by the SAME command sequence, through the robot's loop (robot_loop_eval.RobotLoop: no speed
clip, the robot's IMU filter, the recorded action scale).

Reports, robot vs sim: loop timing, trunk tilt (from the accelerometer), gyro, joint tracking (position at step k+1 vs
the target sent at step k), policy action size and saturation, foot contacts, IMU-filter freezes; and the robot's
balance-loss moments (tilt or gyro spikes) with the command at the time. Writes a PNG of the time series.

  cd Open_Duck_Playground && uv run python ../tools/robot_log_compare.py --log <walk.npz> -o <policy.onnx> --png out.png
"""

import argparse
import ast
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robot_loop_eval import RobotLoop  # noqa: E402

# walker obs layout (101): gyro 3, accel 3, commands 7, joint pos - home 14, 0.05 * joint vel 14, last 3 actions 42,
# motor targets 14, foot contacts 2, phase 2
POS, VEL, CONTACT = slice(13, 27), slice(27, 41), slice(97, 99)
LEGS = list(range(0, 5)) + list(range(9, 14))


def tilt_deg(acc):
    a = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-6)
    return np.degrees(np.arccos(np.clip(a[:, 2], -1, 1)))


def summarize(name, d, home, names):
    out = {}
    acc = d["acc_raw"]
    out["tilt"] = tilt_deg(acc)
    out["gyro"] = d["gyro_raw"]
    pos = d["obs"][:, POS] + home
    out["track"] = np.abs(pos[1:] - d["targets"][:-1])  # where the joint is vs where it was told to be last step
    out["action"] = d["action"]
    out["contacts"] = d["obs"][:, CONTACT] > 0.5
    out["acc_frozen"] = np.mean(np.any(np.abs(np.clip(acc, -10, 10)) > 9.8, axis=1))
    return out


def sim_run(onnx, scene, log, scale):
    ref = "playground/open_duck_mini_v2/data/polynomial_coefficients.pkl"
    r = RobotLoop(f"playground/open_duck_mini_v2/xmls/{scene}", onnx, ref)
    r.configure(noclip=True, imu=True)
    r.action_scale = scale
    r.reset(np.random.default_rng(0), 0.0)
    rec = {k: [] for k in ("obs", "action", "targets", "gyro_raw", "acc_raw", "true_tilt")}
    fell = None
    for k, cmd in enumerate(log["commands"]):
        r.commands = list(cmd)
        raw_obs = super(RobotLoop, r).get_obs(r.data, r.commands)  # unfiltered sensors, before the step
        raw_obs[3] -= 1.3
        r.control_step()
        o = r.get_obs(r.data, r.commands)
        rec["obs"].append(o)
        rec["action"].append(r.last_action.copy())
        rec["targets"].append(r.motor_targets.copy())
        rec["gyro_raw"].append(raw_obs[0:3])
        rec["acc_raw"].append(raw_obs[3:6])
        up = r.data.site_xmat[r.imu_site_id].reshape(3, 3)[2, 2]
        rec["true_tilt"].append(np.degrees(np.arccos(np.clip(up, -1, 1))))
        if fell is None and r.fallen():
            fell = k
            break
    return {k: np.array(v) for k, v in rec.items()}, fell, r


def pct(x, q):
    return np.percentile(x, q) if len(x) else float("nan")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--scene", default="scene_flat_terrain_backlash.xml")
    p.add_argument("--png", default=None)
    a = p.parse_args()

    log = np.load(a.log)
    meta = ast.literal_eval(str(log["meta"]))
    names, home = meta["joints"], np.array(meta["init_pos"])
    n = len(log["t"])
    print(f"== {os.path.basename(a.log)}: {n} steps ({log['t'][-1] - log['t'][0]:.1f} s), walker {meta['walker_onnx']}, "
          f"action scale {meta['action_scale']}, kp {meta['kp']}")

    dt = np.diff(log["t"]) * 1000
    took = log["took"] * 1000
    print(f"\nloop: step interval median {np.median(dt):.1f} ms, p99 {pct(dt, 99):.1f}, max {dt.max():.1f}; "
          f"{(dt > 25).sum()} intervals > 25 ms ({100 * np.mean(dt > 25):.1f}%); compute median {np.median(took):.1f} ms")
    late = np.where(dt > 25)[0]
    if len(late):
        gaps = np.diff(log["t"][late + 1])
        print(f"      late steps recur every {np.median(gaps):.2f} s (median gap between them)")

    sim, fell, r = sim_run(a.onnx, a.scene, log, meta["action_scale"])
    sim_names = list(r.actuator_names) if hasattr(r, "actuator_names") else names
    if list(sim_names) != list(names):
        print("WARNING joint order differs:", sim_names)
    ns = len(sim["obs"])
    print(f"sim: same {n} commands -> {'fell at step %d' % fell if fell is not None else 'no fall'} ({ns} steps)")

    R = summarize("robot", {k: log[k] for k in ("obs", "action", "targets", "gyro_raw", "acc_raw")}, home, names)
    S = summarize("sim", sim, home, names)

    print(f"\n{'':28s} {'robot':>14s} {'sim':>14s}")
    def row(label, rv, sv, fmt="{:.2f}"):
        print(f"{label:28s} {fmt.format(rv):>14s} {fmt.format(sv):>14s}")
    row("tilt from accel p50 (deg)", pct(R["tilt"], 50), pct(S["tilt"], 50), "{:.1f}")
    row("tilt from accel p95 (deg)", pct(R["tilt"], 95), pct(S["tilt"], 95), "{:.1f}")
    row("tilt max (deg)", R["tilt"].max(), S["tilt"].max(), "{:.1f}")
    for i, ax in enumerate("xyz"):
        row(f"gyro {ax} rms (rad/s)", np.sqrt(np.mean(R["gyro"][:, i] ** 2)), np.sqrt(np.mean(S["gyro"][:, i] ** 2)))
    row("accel mean x", log["acc_raw"][:, 0].mean(), sim["acc_raw"][:, 0].mean())
    row("accel mean y", log["acc_raw"][:, 1].mean(), sim["acc_raw"][:, 1].mean())
    row("accel mean z", log["acc_raw"][:, 2].mean(), sim["acc_raw"][:, 2].mean())
    row("IMU filter: accel frozen %", 100 * R["acc_frozen"], 100 * S["acc_frozen"], "{:.0f}")
    row("action |a| mean", np.abs(R["action"]).mean(), np.abs(S["action"]).mean())
    row("action |a| p99", pct(np.abs(R["action"]), 99), pct(np.abs(S["action"]), 99))
    row("legs tracking err mean (rad)", R["track"][:, LEGS].mean(), S["track"][:, LEGS].mean(), "{:.3f}")
    row("both feet down %", 100 * np.mean(R["contacts"].all(1)), 100 * np.mean(S["contacts"].all(1)), "{:.0f}")
    row("no foot down %", 100 * np.mean(~R["contacts"].any(1)), 100 * np.mean(~S["contacts"].any(1)), "{:.0f}")

    print(f"\njoint tracking |pos(k+1) - target(k)| mean, rad (robot / sim):")
    for j, nm in enumerate(names):
        rt, st = R["track"][:, j].mean(), S["track"][:, j].mean()
        flag = "  <-- robot > 2x sim" if rt > 2 * st and rt > 0.02 else ""
        print(f"  {nm:16s} {rt:.3f} / {st:.3f}{flag}")
    # static offset: where the joint sits vs target, signed, while standing still (zero command)
    still = np.all(np.abs(log["commands"][:, :3]) < 1e-3, axis=1)
    if still.sum() > 50:
        off = (log["obs"][1:, POS] + home - log["targets"][:-1])[still[1:]].mean(0)
        print("\nrobot standing still: mean (position - target), rad:  " +
              ", ".join(f"{nm} {o:+.3f}" for nm, o in zip(names, off) if abs(o) > 0.02))

    # balance-loss moments on the robot
    ev = np.where((R["tilt"] > 15) | (np.linalg.norm(R["gyro"], axis=1) > 3.0))[0]
    print(f"\nrobot moments with tilt > 15 deg or |gyro| > 3 rad/s: {len(ev)} steps")
    if len(ev):
        starts = ev[np.r_[True, np.diff(ev) > 25]]
        for s in starts[:12]:
            c = log["commands"][s, :3]
            w = slice(max(0, s - 5), min(n, s + 25))
            print(f"  t={log['t'][s] - log['t'][0]:6.2f}s cmd vx {c[0]:+.2f} vy {c[1]:+.2f} wz {c[2]:+.2f}: "
                  f"tilt peak {R['tilt'][w].max():.0f} deg, |gyro| peak {np.linalg.norm(R['gyro'][w], axis=1).max():.1f}")

    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        t = log["t"] - log["t"][0]
        ts = np.arange(ns) * 0.02
        fig, ax = plt.subplots(5, 1, figsize=(13, 13), sharex=True)
        ax[0].plot(t, log["commands"][:, 0], label="vx"); ax[0].plot(t, log["commands"][:, 1], label="vy")
        ax[0].plot(t, log["commands"][:, 2], label="wz"); ax[0].set_ylabel("command"); ax[0].legend(loc="upper right")
        ax[1].plot(t, R["tilt"], label="robot", lw=0.8); ax[1].plot(ts, S["tilt"], label="sim", lw=0.8)
        ax[1].set_ylabel("tilt deg (accel)"); ax[1].legend(loc="upper right")
        ax[2].plot(t, np.linalg.norm(R["gyro"], axis=1), label="robot", lw=0.6)
        ax[2].plot(ts, np.linalg.norm(S["gyro"], axis=1), label="sim", lw=0.6); ax[2].set_ylabel("|gyro| rad/s")
        ax[2].legend(loc="upper right")
        ax[3].plot(t[1:], R["track"][:, LEGS].mean(1), label="robot", lw=0.6)
        ax[3].plot(ts[1:], S["track"][:, LEGS].mean(1), label="sim", lw=0.6); ax[3].set_ylabel("leg track err rad")
        ax[3].legend(loc="upper right")
        ax[4].plot(t[1:], np.diff(log["t"]) * 1000, lw=0.6, color="k"); ax[4].axhline(20, color="r", lw=0.5)
        ax[4].set_ylabel("robot step ms"); ax[4].set_xlabel("s")
        fig.suptitle(f"{os.path.basename(a.log)}: robot vs sim, same commands")
        fig.tight_layout()
        fig.savefig(a.png, dpi=90)
        print("PNG:", a.png)


if __name__ == "__main__":
    main()
