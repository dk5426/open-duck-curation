"""Dynamic feasibility label for a clip library (the "physics filter" for dynamic contaminants), from the reference alone.

Three checks, each on the clip as written (kinematic replay, no policy):
  1. speed: a target that moves at most 5.24 rad/s (the env's rate limit) falls more than 0.1 rad (the scoring
     tolerance on joint error) behind the reference
  2. balance: the zero-moment point (cart-table model from the whole-body CoM acceleration, angular momentum ignored)
     outside the support polygon (bottom-face corners of the sole boxes of the feet marked in contact; only the corners
     within 8 mm of the lowest, so a rolled sole supports on its edge) by more than
     5 mm for longer than 0.1 s
  3. take-off: for a flight phase, the vertical take-off speed g * t_flight / 2 is more than the fastest the legs can
     extend at the servo speed limit (sum over both legs' joints of |dz_base / dq| x 5.24 rad/s, halved since the two
     legs push the same base)
infeasible = any of the three. Writes <lib>/dynamic_labels.json: per clip the three measures, the flags and the label.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/dynamic_check.py \
      --lib ../open-duck-curation/data/clips_wild_sweep
"""

import argparse
import itertools
import json
import os
import sys

import mujoco
import numpy as np
from scipy.signal import savgol_filter
from scipy.spatial import ConvexHull

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_library import FPS, load_model  # noqa: E402

V_MAX = 5.24  # rad/s, the tracking env's target rate limit
LAG_MAX = 0.1  # rad: the scoring tolerance on joint error (tau_dof)
G = 9.81
SOLE_GEOMS = ("left_foot_bottom_tpu", "right_foot_bottom_tpu")
LEG_JOINTS = [f"{s}_{j}" for s in ("left", "right") for j in ("hip_yaw", "hip_roll", "hip_pitch", "knee", "ankle")]


def signed_dist(p, pts):
    """Signed distance of 2-D point p to the convex hull of pts (positive inside). Degenerate hulls: distance to the
    segment / point, negative."""
    pts = np.unique(np.round(pts, 5), axis=0)
    if len(pts) >= 3:
        try:
            h = ConvexHull(pts)
            return float(-np.max(h.equations[:, :2] @ p + h.equations[:, 2]))
        except Exception:
            pass
    if len(pts) == 1:
        return -float(np.linalg.norm(p - pts[0]))
    a, b = pts[np.argmax(np.linalg.norm(pts - pts[0], axis=1))], pts[0]
    t = np.clip(np.dot(p - a, b - a) / max(np.dot(b - a, b - a), 1e-12), 0, 1)
    return -float(np.linalg.norm(p - (a + t * (b - a))))


def runs_longer(mask, n):
    """True if mask has a run of more than n consecutive True frames."""
    k = 0
    for v in mask:
        k = k + 1 if v else 0
        if k > n:
            return True
    return False


def check(m, d, qadr, q, pos, quat, con):
    T = len(q)
    home = m.keyframe("home").qpos
    sole = [m.geom(n).id for n in SOLE_GEOMS]
    corners = [m.geom_aabb[g, :3] + np.array(list(itertools.product((-1, 1), repeat=3))) * m.geom_aabb[g, 3:] for g in sole]
    com, sup = np.zeros((T, 3)), []
    for k in range(T):
        d.qpos[:] = home
        d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos[k], quat[k], q[k]
        mujoco.mj_kinematics(m, d)
        mujoco.mj_comPos(m, d)
        com[k] = d.subtree_com[m.body("base").id]
        pts = []
        for leg, g in enumerate(sole):
            if con[k, leg] > 0.5:
                w = corners[leg] @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]
                w = w[np.argsort(w[:, 2])[:4]]  # the sole's bottom face (it sits ~3 deg toe-down at home)
                pts.append(w[w[:, 2] <= w[0, 2] + 0.008, :2])  # an edge only, when the sole is rolled or pitched further
        sup.append(np.concatenate(pts) if pts else None)
    acc = savgol_filter(com, 9, 3, deriv=2, delta=1 / FPS, axis=0)
    margin = np.full(T, np.nan)
    for k in range(T):
        if sup[k] is not None:
            zmp = com[k, :2] - com[k, 2] / max(G + acc[k, 2], 1e-3) * acc[k, :2]
            margin[k] = signed_dist(zmp, sup[k])
    n01 = int(0.1 * FPS)
    qd = np.gradient(q, 1 / FPS, axis=0)
    legs = [m.actuator(n).id for n in LEG_JOINTS]
    # a servo whose target moves at most V_MAX: how far it falls behind the reference
    f = q[0].copy()
    lag = np.zeros(T)
    for k in range(1, T):
        f += np.clip(q[k] - f, -V_MAX / FPS, V_MAX / FPS)
        lag[k] = np.max(np.abs(q[k] - f))
    fast = bool(lag.max() > LAG_MAX)
    zmp_out = runs_longer(np.nan_to_num(margin, nan=0.0) < -0.005, n01)
    # take-off: each flight phase (both feet off) against the legs' fastest extension at the last stance frame
    flight = (con[:, 0] < 0.5) & (con[:, 1] < 0.5)
    takeoff_fail, need, can = False, 0.0, None
    k = 0
    while k < T:
        if flight[k]:
            j = k
            while j < T and flight[j]:
                j += 1
            tf = (j - k + 1) / FPS
            v_need = G * tf / 2
            kk = max(k - 1, 0)
            d.qpos[:] = home
            d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos[kk], quat[kk], q[kk]
            mujoco.mj_kinematics(m, d)
            mujoco.mj_comPos(m, d)
            v_can = 0.0
            for leg, site in enumerate(("left_foot", "right_foot")):
                jp = np.zeros((3, m.nv))
                mujoco.mj_jacSite(m, d, jp, None, m.site(site).id)
                dofs = [m.jnt_dofadr[m.actuator_trnid[a, 0]] for a in legs[5 * leg:5 * leg + 5]]
                v_can += 0.5 * float(np.sum(np.abs(jp[2, dofs]))) * V_MAX  # sole moving down = base moving up
            need, can = max(need, v_need), v_can if can is None else min(can, v_can)
            takeoff_fail |= v_need > v_can
            k = j
        else:
            k += 1
    return {"peak_joint_speed": round(float(np.max(np.abs(qd))), 3), "rate_lag_rad": round(float(lag.max()), 3),
            "fast": bool(fast),
            "zmp_min_margin_mm": round(1000 * float(np.nanmin(margin)), 1) if np.isfinite(margin).any() else None,
            "zmp_out": bool(zmp_out), "flight_s": round(float(flight.sum()) / FPS, 3),
            "takeoff_need_m_s": round(need, 3), "takeoff_can_m_s": None if can is None else round(can, 3),
            "takeoff_fail": bool(takeoff_fail), "infeasible": bool(fast or zmp_out or takeoff_fail)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    a = p.parse_args()
    m, d = load_model()
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    lib = np.load(os.path.join(a.lib, "library.npz"))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    out = {}
    for c in man["clips"]:
        i, L = c["index"], c["length"]
        r = check(m, d, qadr, lib["q"][i, :L], lib["base_pos"][i, :L], lib["base_quat"][i, :L], lib["contacts"][i, :L])
        out[c["id"]] = r
        flags = ",".join(f for f in ("fast", "zmp_out", "takeoff_fail") if r[f]) or "-"
        print(f"{c['id']:30s} peak {r['peak_joint_speed']:5.2f}  lag {r['rate_lag_rad']:.2f}  zmp {r['zmp_min_margin_mm']!s:>7} mm  "
              f"takeoff {r['takeoff_need_m_s']:.2f}/{r['takeoff_can_m_s']}  -> {'INFEASIBLE' if r['infeasible'] else 'ok'} {flags}")
    json.dump(out, open(os.path.join(a.lib, "dynamic_labels.json"), "w"), indent=1)
    print(f"{sum(r['infeasible'] for r in out.values())} of {len(out)} infeasible")


if __name__ == "__main__":
    main()
