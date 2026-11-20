"""Keyframed "wild" clips in the library format: families hop, kick, stomp, tap, dance, headbang, twist, each swept from
gentle to beyond the servos (`--demo`: the five gallery demos), plus HELDOUT gentle variants for val / test (used by
make_v8.py). Clips are at most 4 s, the library's length.

No split and no feasibility label yet. Each clip is a few keyframes of base offset and foot targets,
eased with min-jerk and solved by inverse kinematics (both legs, all five joints, damped least squares) with the base
pose given. Feet in contact stay where they are at home, free to roll (the leg has no ankle roll joint, so a sideways
weight shift rolls the sole onto an edge); the hop has a flight phase with both feet off the floor.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_wild.py \
      --out ../open-duck-curation/data/clips_wild
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_library import (FPS, KEYPOINT_NAMES, body_velocities, check_clip, keypoints, load_model,  # noqa: E402
                          mat_log, minjerk)

W = np.array([0.0, 0.3, 0.3])  # weights of the sole orientation error about x (roll), y, z
LEGS = {0: ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle"],
        1: ["right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]}
SOLES = ("left_foot", "right_foot")


def rot(roll=0.0, pitch=0.0, yaw=0.0):
    """wxyz quaternion from roll, pitch, yaw (rad), applied yaw-pitch-roll."""
    cr, sr, cp, sp, cy, sy = (np.cos(roll / 2), np.sin(roll / 2), np.cos(pitch / 2), np.sin(pitch / 2),
                              np.cos(yaw / 2), np.sin(yaw / 2))
    return np.array([cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy,
                     cr * cp * sy - sr * sp * cy])


class Solver:
    def __init__(self, m, d, qadr):
        self.m, self.d, self.qadr = m, d, qadr
        self.home = m.keyframe("home").qpos.copy()
        d.qpos[:] = self.home
        mujoco.mj_kinematics(m, d)
        self.sites = [m.site(n).id for n in SOLES]
        self.foot_p = [d.site_xpos[s].copy() for s in self.sites]
        self.foot_R = [d.site_xmat[s].reshape(3, 3).copy() for s in self.sites]
        self.q = self.home.copy()

    def solve(self, base_off, quat, foot_off, foot_pitch=(0.0, 0.0), iters=100):
        """Leg joints for the base at home + base_off with orientation quat, each sole at its home pose + foot_off[leg]
        (pitched by foot_pitch[leg] rad). Warm-starts from the previous frame."""
        m, d = self.m, self.d
        q = self.q.copy()
        q[0:3] = self.home[0:3] + base_off
        q[3:7] = quat
        tgt = []
        for leg in (0, 1):
            Rp = np.array([[np.cos(foot_pitch[leg]), 0, np.sin(foot_pitch[leg])], [0, 1, 0],
                           [-np.sin(foot_pitch[leg]), 0, np.cos(foot_pitch[leg])]])
            tgt.append((self.foot_p[leg] + foot_off[leg], Rp @ self.foot_R[leg]))
        err = 0.0
        for _ in range(iters):
            d.qpos[:] = q
            mujoco.mj_kinematics(m, d)
            mujoco.mj_comPos(m, d)
            err = 0.0
            for leg, s in enumerate(self.sites):
                dofs = [m.jnt_dofadr[m.joint(n).id] for n in LEGS[leg]]
                qa = [m.jnt_qposadr[m.joint(n).id] for n in LEGS[leg]]
                # no ankle roll joint: a sideways weight shift has to roll the sole, so roll (about x) is left free
                e = np.concatenate([tgt[leg][0] - d.site_xpos[s], W * mat_log(tgt[leg][1] @ d.site_xmat[s].reshape(3, 3).T)])
                err = max(err, float(np.linalg.norm(e[:3])))
                jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
                mujoco.mj_jacSite(m, d, jp, jr, s)
                J = np.vstack([jp, W[:, None] * jr])[:, dofs]
                q[qa] += np.linalg.solve(J.T @ J + 1e-4 * np.eye(5), J.T @ e)
            if err < 1e-5:
                break
        lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
        q[self.qadr] = np.clip(q[self.qadr], lo, hi)
        self.q = q
        return q[self.qadr].copy(), q[0:3].copy(), err


def track(t, keys):
    """Piecewise min-jerk interpolation of keyframes [(time, value array), ...] at times t."""
    times = [k[0] for k in keys]
    vals = [np.asarray(k[1], float) for k in keys]
    out = np.zeros((len(t),) + vals[0].shape)
    for n, tt in enumerate(t):
        j = np.searchsorted(times, tt, side="right") - 1
        if j < 0:
            out[n] = vals[0]
        elif j >= len(keys) - 1:
            out[n] = vals[-1]
        else:
            s = minjerk((tt - times[j]) / (times[j + 1] - times[j]))
            out[n] = vals[j] + s * (vals[j + 1] - vals[j])
    return out


G = 9.81


def build(m, d, qadr, fam, prm):
    """One clip of family `fam` with parameters `prm`. Per-frame base offset, base rpy, foot offsets, foot pitches,
    head joints and contacts, then IK. Returns q, base_pos, base_quat, contacts, worst IK sole error (m)."""
    Z = [0, 0, 0]
    if fam == "hop":  # n hops; flight time is ballistic for the flight height h (feet clear the floor by h)
        h, n = prm["h"], prm["n"]
        tf = 2 * np.sqrt(2 * h / G)
        seq, tt = [(0.3, Z)], 0.3
        for _ in range(n):
            seq += [(tt + 0.4, [0, 0, -0.01]), (tt + 0.55, [0, 0, 0.012]), (tt + 0.55 + tf / 2, [0, 0, 0.012 + h]),
                    (tt + 0.55 + tf, [0, 0, 0.012]), (tt + 0.7 + tf, [0, 0, -0.01])]
            tt += 0.7 + tf
        seq.append((tt + 0.5, Z))
        dur = tt + 0.8
    elif fam == "kick":
        dur = 3.2
    elif fam in ("stomp", "tap"):  # as many alternating steps as fit in the library's 4 s, at least two
        n_steps = max(2, min(4, int(3.4 / prm["period"]) // 2 * 2))
        dur = 0.6 + n_steps * prm["period"]
    else:
        dur = 4.0
    T = int(dur * FPS)
    t = np.arange(T) / FPS
    head_home = m.keyframe("home").ctrl[5:9]
    base = np.zeros((T, 3)); rpy = np.zeros((T, 3)); fl = np.zeros((T, 3)); fr = np.zeros((T, 3))
    fp = np.zeros((T, 2)); head = np.tile(head_home, (T, 1)); con = np.ones((T, 2))
    env = minjerk(t / 0.5) * minjerk((dur - t) / 0.5)
    if fam == "hop":
        base = track(t, seq)
        lift = np.clip(base[:, 2] - 0.012, 0, None)  # feet leave the floor once the legs are extended
        fl[:, 2] = fr[:, 2] = lift
        con[lift > 5e-4] = 0
        head[:, 1] += 0.2 * np.sin(2 * np.pi * t / (0.7 + 2 * np.sqrt(2 * prm["h"] / G))) * env
    elif fam == "kick":  # shift onto the left foot, chamber, snap the right foot forward by r in time tau, recover
        r, tau = prm["r"], prm["tau"]
        dy = prm.get("dy", 0.045)
        base = track(t, [(0.3, Z), (0.9, [0, dy, 0.01]), (2.3, [0, dy, 0.01]), (2.9, Z)])
        fr = track(t, [(0.9, Z), (1.2, [0.0, 0, 0.03]), (1.2 + tau, [r, 0, 0.035]), (1.2 + 2 * tau, [0.0, 0, 0.03]),
                       (1.55 + 2 * tau, Z)])
        fp[:, 1] = track(t, [(1.2, [0]), (1.2 + tau, [-0.4]), (1.2 + 2 * tau, [0])])[:, 0]
        rpy[:, 0] = track(t, [(0.3, [0]), (0.9, [-0.06]), (2.3, [-0.06]), (2.9, [0])])[:, 0]
        con[(t > 0.93) & (t < 1.52 + 2 * tau), 1] = 0
    elif fam in ("stomp", "tap"):  # alternate legs: weight over the stance foot, swing foot lifts (stomp) or taps out (tap)
        P = prm["period"]
        dy = prm.get("dy", 0.04)
        keys_b, keys_l, keys_r = [(0.2, Z)], [(0.2, Z)], [(0.2, Z)]
        tt = 0.2
        for side in [+1, -1] * (n_steps // 2):
            keys_b += [(tt + 0.35 * P, [0, side * dy, 0.01]), (tt + P, [0, side * dy, 0.01])]
            sw = keys_r if side > 0 else keys_l
            up = [0.01, 0, prm["lift"]] if fam == "stomp" else [prm["reach"], -side * 0.5 * prm["reach"], 0.012]
            sw += [(tt + 0.4 * P, Z), (tt + 0.6 * P, up), (tt + 0.8 * P, Z)]
            con[(t > tt + 0.42 * P) & (t < tt + 0.78 * P), 1 if side > 0 else 0] = 0
            tt += P
        keys_b.append((tt + 0.4, Z))
        base, fl, fr = track(t, keys_b), track(t, keys_l), track(t, keys_r)
        head[:, 1] += 0.15 * np.sin(2 * np.pi * t / P) * env
    elif fam == "dance":  # bounce at f, sway and trunk twist at f / 2, head grooves; a scales every amplitude
        f, a = prm["f"], prm["a"]
        base[:, 2] = -0.004 * a * (1 - np.cos(2 * np.pi * f * t)) * env
        base[:, 1] = 0.02 * a * np.sin(np.pi * f * t) * env
        rpy[:, 2] = 0.2 * a * np.sin(np.pi * f * t + np.pi / 2) * env
        rpy[:, 0] = -0.05 * a * np.sin(np.pi * f * t) * env
        head[:, 2] += 0.4 * a * np.sin(np.pi * f * t + np.pi) * env
        head[:, 3] += 0.25 * a * np.sin(2 * np.pi * f * t) * env
        head[:, 1] += 0.2 * a * np.sin(2 * np.pi * f * t) * env
    elif fam == "headbang":  # nods at f with neck and head, amplitude a (rad on head_pitch), small knee bounce
        f, a = prm["f"], prm["a"]
        head[:, 0] += 0.6 * a * np.sin(2 * np.pi * f * t) * env
        head[:, 1] += a * np.sin(2 * np.pi * f * t) * env
        base[:, 2] = -0.003 * (1 - np.cos(2 * np.pi * f * t)) * env
    elif fam == "twist":  # trunk yaw about the planted feet at f, amplitude a (rad), head counter-rotates
        f, a = prm["f"], prm["a"]
        rpy[:, 2] = a * np.sin(2 * np.pi * f * t) * env
        head[:, 2] -= 0.8 * a * np.sin(2 * np.pi * f * t) * env
    sol = Solver(m, d, qadr)
    q, pos, quat, worst = np.zeros((T, 14)), np.zeros((T, 3)), np.zeros((T, 4)), 0.0
    for k in range(T):
        quat[k] = rot(*rpy[k])
        q[k], pos[k], err = sol.solve(base[k], quat[k], (fl[k], fr[k]), fp[k])
        q[k, 5:9] = np.clip(head[k], m.jnt_range[m.actuator_trnid[5:9, 0], 0], m.jnt_range[m.actuator_trnid[5:9, 0], 1])
        worst = max(worst, err)
    return q, pos, quat, con.astype(np.float32), worst


def grid(only_demo=False):
    """(family, params, id) for the clip family sweep, spanning gentle to beyond the servos."""
    out = []
    def add(fam, prm):
        out.append((fam, prm, clip_id(fam, prm)))
    if only_demo:
        for fam, prm in (("hop", dict(h=0.02, n=1)), ("kick", dict(r=0.06, tau=0.2)), ("stomp", dict(lift=0.035, period=0.95)),
                         ("dance", dict(f=2.0, a=1.0)), ("headbang", dict(f=3.0, a=0.5))):
            add(fam, prm)
        return out
    for h in (0.005, 0.01, 0.02, 0.03, 0.04):
        add("hop", dict(h=h, n=1 if h >= 0.02 else 2))
    for dy in (0.045, 0.025):  # sideways weight shift (m); the CoM cannot reach the stance foot without ankle roll
        for r in (0.03, 0.06):
            for tau in (0.4, 0.2):
                add("kick", dict(r=r, tau=tau, dy=dy))
        for lift in (0.015, 0.03):
            for period in (1.6, 0.8):
                add("stomp", dict(lift=lift, period=period, dy=dy))
        for reach in (0.03, 0.05):
            add("tap", dict(reach=reach, period=1.2, dy=dy))
    for f in (1.0, 1.5, 2.0, 2.5):
        for a in (0.6, 1.2):
            add("dance", dict(f=f, a=a))
    for f in (1.0, 2.0, 3.0, 4.0):
        for a in (0.25, 0.5):
            add("headbang", dict(f=f, a=a))
    for f in (0.5, 1.5):
        for a in (0.15, 0.3):
            add("twist", dict(f=f, a=a))
    return out


HELDOUT = {  # gentle variants at parameters no train clip has: val 1, test 2 per family (weight shift 4.5 cm)
    "val": [("hop", dict(h=0.0075, n=2)), ("kick", dict(r=0.045, tau=0.4, dy=0.045)),
            ("stomp", dict(lift=0.02, period=1.4, dy=0.045)), ("tap", dict(reach=0.035, period=1.4, dy=0.045)),
            ("dance", dict(f=1.25, a=0.6)), ("headbang", dict(f=1.5, a=0.25)), ("twist", dict(f=1.0, a=0.2))],
    "test": [("hop", dict(h=0.005, n=1)), ("hop", dict(h=0.008, n=1)),
             ("kick", dict(r=0.04, tau=0.5, dy=0.045)), ("kick", dict(r=0.05, tau=0.35, dy=0.045)),
             ("stomp", dict(lift=0.02, period=1.6, dy=0.045)), ("stomp", dict(lift=0.025, period=1.2, dy=0.045)),
             ("tap", dict(reach=0.03, period=1.6, dy=0.045)), ("tap", dict(reach=0.04, period=1.4, dy=0.045)),
             ("dance", dict(f=1.25, a=0.8)), ("dance", dict(f=1.75, a=0.5)),
             ("headbang", dict(f=1.5, a=0.35)), ("headbang", dict(f=1.0, a=0.4)),
             ("twist", dict(f=0.75, a=0.25)), ("twist", dict(f=1.25, a=0.15))]}


def clip_id(fam, prm):
    return f"{fam}__" + "_".join(f"{k}{v:g}" for k, v in prm.items())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--demo", action="store_true", help="only the five gallery demos")
    a = p.parse_args()
    m, d = load_model()
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    data, man = {k: [] for k in ("q", "qd", "base_pos", "base_quat", "lin_vel", "ang_vel", "contacts", "keypts")}, []
    for n, (fam, prm, cid) in enumerate(grid(a.demo)):
        q, pos, quat, con, err = build(m, d, qadr, fam, prm)
        qd = np.gradient(q, 1 / FPS, axis=0)
        lin, ang = body_velocities(pos, quat)
        for k, v in (("q", q), ("qd", qd), ("base_pos", pos), ("base_quat", quat), ("lin_vel", lin), ("ang_vel", ang),
                     ("contacts", con), ("keypts", keypoints(m, d, qadr, q))):
            data[k].append(v)
        chk = check_clip(m, d, qadr, q, qd, pos, quat, con)
        man.append({"id": cid, "category": fam, "source": cid, "split": "demo", "params": dict(prm, ik_foot_err_mm=round(1000 * err, 2)),
                    "check": chk, "length": len(q), "index": n})
        print(f"{cid:28s} T {len(q):3d} ik {1000 * err:5.2f} mm  peak {chk['peak_joint_speed_rad_s']:5.2f} rad/s  "
              f"x{chk['speed_vs_servo']:.2f}  margin {chk['joint_limit_margin_rad']:.3f}  pass {chk['pass']}")
    L = max(len(x) for x in data["q"])
    pad = {k: np.stack([np.concatenate([x, np.repeat(x[-1:], L - len(x), 0)]) for x in v]) for k, v in data.items()}
    os.makedirs(a.out, exist_ok=True)
    np.savez_compressed(os.path.join(a.out, "library.npz"), length=np.array([c["length"] for c in man]), **pad)
    json.dump({"keypoints": KEYPOINT_NAMES, "fps": FPS, "clips": man}, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
