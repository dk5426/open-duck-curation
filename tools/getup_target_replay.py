"""Which plant effects make the sim move like the real robot? Open-loop replay of recorded get-ups: start the sim
from the robot's start pose (getup_replay.start_state) and send it the joint targets the robot was sent, step by
step, with no policy in the loop. Then compare sim and robot joint positions and trunk uprightness.

The sim is the get-up model with full self-collision (getup_real_eval.full_selfcollision_model, robot head gains)
and servo overload protection. Knobs, each swept over a grid:
  delay   the targets reach the servos this many 20 ms steps late
  torque  torque limit x this factor (sim 3.23 N m; STS3215 7.4 V published stall ~1.9 N m = x0.59)
  kp      position gain x this factor
  curve   torque falls off with joint speed: limit x max(0, 1 - |qdot| / w0), w0 = no-load speed (rad/s)
A lower error = the sim behaves more like the robot.

  cd Open_Duck_Playground && .venv/bin/python ../tools/getup_target_replay.py --logs ../robot_logs/2026110*_getup.npz
"""

import argparse
import glob
import itertools
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getup_real_eval import full_selfcollision_model  # noqa: E402
from getup_replay import start_state  # noqa: E402
from servo_protection import ServoProtection  # noqa: E402

LEGS = list(range(0, 5)) + list(range(9, 14))


class Plant:
    def __init__(self):
        self.m = full_selfcollision_model()
        self.d = mujoco.MjData(self.m)
        m = self.m
        jids = [m.actuator_trnid[i, 0] for i in range(m.nu)]
        self.qadr = np.array([m.jnt_qposadr[j] for j in jids])
        self.vadr = np.array([m.jnt_dofadr[j] for j in jids])
        self.lo, self.hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
        self.up = m.sensor_adr[m.sensor("upvector").id]
        self.acc = m.sensor_adr[m.sensor("accelerometer").id]
        self.g0, self.b0, self.f0 = m.actuator_gainprm.copy(), m.actuator_biasprm.copy(), m.actuator_forcerange.copy()

    def body(self, mu=None, soft=None, com_dx=0.0, com_dz=0.0, mass=1.0):
        """Floor friction / softness (surface_dr's mapping: 0 hard .. 1 thick carpet) and trunk CoM shift / mass."""
        m = self.m
        if not hasattr(self, "fl0"):
            fl = m.geom("floor").id
            tr = m.body("trunk_assembly").id
            self.fl, self.tr = fl, tr
            self.fl0 = (m.geom_friction[fl].copy(), m.geom_solref[fl].copy(), m.geom_solimp[fl].copy())
            self.tr0 = (m.body_ipos[tr].copy(), m.body_mass[tr])
        m.geom_friction[self.fl], m.geom_solref[self.fl], m.geom_solimp[self.fl] = [x.copy() for x in self.fl0]
        if mu is not None:
            m.geom_friction[self.fl, 0] = mu
        if soft:
            m.geom_solref[self.fl] = [0.02 + 0.06 * soft, 1.0 - 0.2 * soft]
            m.geom_solimp[self.fl, :3] = [0.9 - 0.6 * soft, 0.95, 0.001 + 0.009 * soft]
        m.body_ipos[self.tr] = self.tr0[0] + np.array([com_dx, 0.0, com_dz])
        m.body_mass[self.tr] = self.tr0[1] * mass

    def configure(self, torque, kp):
        m = self.m
        m.actuator_gainprm[:], m.actuator_biasprm[:] = self.g0, self.b0
        m.actuator_gainprm[:, 0] = self.g0[:, 0] * kp
        m.actuator_biasprm[:, 1] = self.b0[:, 1] * kp
        self.fmax = self.f0[:, 1] * torque
        m.actuator_forcerange[:, 0], m.actuator_forcerange[:, 1] = -self.fmax, self.fmax

    def replay(self, log, delay, w0, steps):
        m, d = self.m, self.d
        q0 = start_state(self, log["pos"][0], log["obs"][0, 3:6])
        mujoco.mj_resetData(m, d)
        d.qpos[:] = q0
        mujoco.mj_forward(m, d)
        prot = ServoProtection(m.nu)
        tg = log["targets"]
        cur = np.clip(log["pos"][0], self.lo, self.hi)
        pos, ups = [], []
        kp = m.actuator_gainprm[:, 0].copy()
        for k in range(steps):
            pos.append(d.qpos[self.qadr].copy())
            a = d.sensordata[self.acc: self.acc + 3]
            ups.append((d.sensordata[self.up + 2], a[2] / max(np.linalg.norm(a), 1e-6)))
            if k - delay >= 0:
                cur = tg[k - delay]
            q = d.qpos[self.qadr]
            d.ctrl[:] = prot.limit_targets(cur, q, kp, self.fmax)
            for _ in range(10):
                if w0:
                    lim = self.fmax * np.clip(1 - np.abs(d.qvel[self.vadr]) / w0, 0.05, 1.0)
                    m.actuator_forcerange[:, 0], m.actuator_forcerange[:, 1] = -lim, lim
                mujoco.mj_step(m, d)
            if w0:
                m.actuator_forcerange[:, 0], m.actuator_forcerange[:, 1] = -self.fmax, self.fmax
            prot.update(d.actuator_force, np.abs(kp * (cur - d.qpos[self.qadr])), self.fmax)
        ups = np.array(ups)
        acc_up = np.convolve(ups[:, 1], np.ones(5) / 5, mode="same")  # same measure and smoothing as robot_up
        return np.array(pos), acc_up


def robot_up(log):
    oa = log["obs"][:, 3:6]
    up = oa[:, 2] / np.linalg.norm(oa, axis=1)
    return np.convolve(up, np.ones(5) / 5, mode="same")


WINDOWS = [(0, 25), (25, 50), (50, 75), (75, 125)]  # 0-0.5 s (soft start), 0.5-1, 1-1.5, 1.5-2.5 s


def score(plant, logs, steps):
    jerr, uerr, win = [], [], []
    for log in logs:
        pos, ups = plant.replay(log, 0, 0.0, steps)
        e = np.abs(ups - robot_up(log)[:steps])
        jerr.append(np.abs(pos[:, LEGS] - log["pos"][:steps, LEGS]).mean())
        uerr.append(e.mean())
        win.append([e[a:b].mean() for a, b in WINDOWS])
    return np.mean(jerr), np.mean(uerr), np.mean(win, axis=0)


def matched_starts(plant, logs, steps, tol=0.1):
    """Keep the logs whose rebuilt start matches the robot: uprightness within tol over the first 0.2 s."""
    plant.configure(1.0, 1.0)
    plant.body()
    keep = []
    for log in logs:
        _, ups = plant.replay(log, 0, 0.0, 10)
        if np.abs(ups[:10] - robot_up(log)[:10]).mean() < tol:
            keep.append(log)
    print(f"  starts that match the robot at t=0 (uprightness within {tol}): {len(keep)}/{len(logs)}")
    return keep


def self_divergence(plant, logs, steps):
    """How far apart do two sims drift on the same targets when one is nudged (joint start +-0.01 rad, floor mu x0.95)?
    This is the replay test's noise floor: robot-vs-sim errors at or below it identify nothing."""
    plant.configure(1.0, 1.0)
    out = []
    for log in logs:
        plant.body()
        _, a = plant.replay(log, 0, 0.0, steps)
        nudged = dict(log)
        rng = np.random.default_rng(0)
        nudged["pos"] = log["pos"].copy()
        nudged["pos"][0] = log["pos"][0] + rng.uniform(-0.01, 0.01, 14)
        plant.body(mu=0.95 * float(plant.fl0[0][0]) if hasattr(plant, "fl0") else 0.95)
        _, b = plant.replay(nudged, 0, 0.0, steps)
        e = np.abs(a - b)
        out.append([e[x:y].mean() for x, y in WINDOWS])
    plant.body()
    print("  SIM vs NUDGED SIM (noise floor)            by window " + " ".join(f"{x:.2f}" for x in np.mean(out, 0)))


def body_sweep(plant, logs, steps):
    logs = matched_starts(plant, logs, steps)
    self_divergence(plant, logs, steps)
    plant.configure(1.0, 1.0)
    print("  uprightness windows: 0-0.5 s | 0.5-1 s | 1-1.5 s | 1.5-2.5 s")
    cases = [("as trained (hard floor, mu 1)", {})]
    cases += [(f"floor friction {mu}", {"mu": mu}) for mu in (0.3, 0.5, 0.7, 1.5)]
    cases += [(f"floor softness {s} (1 = thick carpet)", {"soft": s}) for s in (0.3, 0.6, 1.0)]
    cases += [(f"soft 1.0 + friction {mu}", {"soft": 1.0, "mu": mu}) for mu in (0.5, 1.5)]
    cases += [(f"trunk CoM x {dx:+.2f} m", {"com_dx": dx}) for dx in (-0.03, 0.03)]
    cases += [(f"trunk CoM z {dz:+.2f} m", {"com_dz": dz}) for dz in (-0.03, 0.03)]
    cases += [(f"trunk mass x{mm}", {"mass": mm}) for mm in (0.8, 1.2)]
    for name, kw in cases:
        plant.body(**kw)
        j, u, w = score(plant, logs, steps)
        print(f"  {name:38s} leg joints sim-robot {j:.3f} rad  uprightness (accel, both) {u:.3f}  by window "
              + " ".join(f"{x:.2f}" for x in w), flush=True)
    plant.body()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", nargs="+", required=True)
    p.add_argument("--seconds", type=float, default=2.5)
    p.add_argument("--delays", type=int, nargs="+", default=[0, 1, 2, 3])
    p.add_argument("--torques", type=float, nargs="+", default=[1.0, 0.8, 0.6, 0.45])
    p.add_argument("--kps", type=float, nargs="+", default=[1.0, 0.6])
    p.add_argument("--w0s", type=float, nargs="+", default=[0.0, 5.0])
    p.add_argument("--body", action="store_true",
                   help="instead of the servo grid: as-trained servos, sweep floor friction / softness and trunk CoM / mass")
    a = p.parse_args()
    logs = []
    for x in a.logs:
        for f in sorted(glob.glob(x)):
            try:
                d = np.load(f)
                if "pos" in d.files and len(d["t"]) >= int(a.seconds * 50):
                    logs.append(d)
            except Exception:
                pass
    steps = int(a.seconds * 50)
    print(f"{len(logs)} robot get-ups, first {a.seconds:g} s of each, open-loop target replay")
    plant = Plant()
    if a.body:
        return body_sweep(plant, logs, steps)
    rows = []
    for delay, torque, kp, w0 in itertools.product(a.delays, a.torques, a.kps, a.w0s):
        plant.configure(torque, kp)
        jerr, uerr, lag_s, lag_r = [], [], [], []
        for log in logs:
            pos, ups = plant.replay(log, delay, w0, steps)
            rp = log["pos"][:steps]
            jerr.append(np.abs(pos[:, LEGS] - rp[:, LEGS]).mean())
            uerr.append(np.abs(ups - robot_up(log)[:steps]).mean())
            lag_s.append(np.abs(log["targets"][: steps - 1, LEGS] - pos[1:, LEGS]).mean())
            lag_r.append(np.abs(log["targets"][: steps - 1, LEGS] - rp[1:, LEGS]).mean())
        rows.append((delay, torque, kp, w0, np.mean(jerr), np.mean(uerr), np.mean(lag_s), np.mean(lag_r)))
        print(f"  delay {delay}  torque x{torque:<4}  kp x{kp:<4}  speed curve {'w0=%g' % w0 if w0 else 'off':8s} "
              f"leg joints sim-robot {rows[-1][4]:.3f} rad  uprightness {rows[-1][5]:.3f}  "
              f"leg lag sim {rows[-1][6]:.3f} / robot {rows[-1][7]:.3f}", flush=True)
    rows.sort(key=lambda r: r[4])
    print("\nbest 6 by leg-joint match:")
    for r in rows[:6]:
        print(f"  delay {r[0]}  torque x{r[1]}  kp x{r[2]}  curve {'w0=%g' % r[3] if r[3] else 'off'}: joints {r[4]:.3f}, "
              f"uprightness {r[5]:.3f}")
    base = [r for r in rows if r[0] == 0 and r[1] == 1.0 and r[2] == 1.0 and r[3] == 0.0]
    if base:
        print(f"as trained (delay 0, torque x1, kp x1, no curve): joints {base[0][4]:.3f}, uprightness {base[0][5]:.3f}")


if __name__ == "__main__":
    main()
