"""Unbalanced-pool library: the clean library plus held poses the simulator itself cannot perform, each verified by the
static-hold test (hold_test.py). Unlike clips_v5inf, whose clips mostly break limits only the real servos have, every
clip here breaks balance, which the simulator models. Val and test are unchanged.

Sources (contaminant "unbalanced"): lean_fwd / lean_back, the base moved forward 10-16 cm / back 5-12 cm with both
soles fixed and the trunk upright, in three timings (move 0.4 s + hold 2.6 s, 0.6 + 2.2, 1.0 + 1.5). These are the
leans the cinf scoring policy fell on 5/5 (forward >= 11 cm, back >= 6 cm) plus the next sizes up. Unbalanced bows and
one-leg stances also fail the hold test, but the policy shrugs them off by tipping its whole body (score 0.1-0.6, no
falls), so they are off by default (--bows, --one-leg).
A clip is kept only if its held pose FAILS the hold test (tips, sags, moves, or the raised foot comes down); a
candidate the robot can hold is dropped and listed. The hold report is kept in each entry ("hold").

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_unbalanced.py \
      --lib ../open-duck-curation/data/clips_v5 --out ../open-duck-curation/data/clips_v5unb
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hold_test as ht  # noqa: E402
import make_library as ml  # noqa: E402
from make_contaminated import write_library  # noqa: E402
from make_infeasible import T, arrays, held  # noqa: E402

LEAN_FWD = (0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16)
LEAN_BACK = (-0.05, -0.06, -0.07, -0.08, -0.09, -0.10, -0.11, -0.12)
BOW_DEG = (35, 40, 45, 50, 55, 60)
ONE_LEG_SCALE = (0.6, 1.0)
TIMINGS = {"m0.4h2.6": (0.4, 2.6), "m0.6h2.2": (0.6, 2.2), "m1.0h1.5": (1.0, 1.5)}


def candidates(m, d, qadr, bows=False, one_leg=False):
    t = np.arange(T) / ml.FPS
    home, hc = m.keyframe("home").qpos, m.keyframe("home").ctrl
    ones = np.ones((T, 2), dtype=np.float32)
    max_drop = ml.max_crouch_drop(m, d, qadr, margin=0.03)
    qc_full = ml.solve_crouch_legs(m, d, qadr, max_drop)[0]

    def pose_clip(fn, frac):
        q, pos, quat, cache = np.zeros((T, 14)), np.zeros((T, 3)), np.zeros((T, 4)), {}
        for k in range(T):
            key = round(float(frac[k]), 4)
            if key not in cache:
                cache[key] = fn(key)
            q[k], pos[k], quat[k] = cache[key][0], cache[key][1][0:3], cache[key][1][3:7]
        return q, pos, quat, ones

    for tn, (tm, th) in TIMINGS.items():
        f = held(t, 0.4, tm, th)
        for dx in LEAN_FWD + LEAN_BACK:
            cat = "lean_fwd" if dx > 0 else "lean_back"
            yield cat, f"{cat}__dx{dx:+.2f}__{tn}", pose_clip(
                lambda s, dx=dx: ml.solve_legs_pose(m, d, qadr, s * dx, 0.0, 0.0), f), {"dx_m": dx}
        for b in BOW_DEG if bows else ():
            yield "bow_unbalanced", f"bow_unbalanced__pitch{b}deg__{tn}", pose_clip(
                lambda s, b=b: ml.solve_legs_pose(m, d, qadr, 0.0, 0.0, s * np.radians(b)), f), {"pitch_deg": b}
        for side, s_ in (("left", 0), ("right", 1)):
            for sc in ONE_LEG_SCALE if one_leg else ():
                idx = [ml.names_index(f"{side}_{j}") for j in ("hip_pitch", "knee", "ankle")]
                q = np.tile(hc, (T, 1)).astype(float)
                q[:, idx] += (sc * f)[:, None] * (qc_full - hc)[idx]
                quat = np.tile(home[3:7], (T, 1))
                c = ones.copy()
                c[f > 0.05, s_] = 0
                pos = np.tile(home[0:3], (T, 1))
                pos[:, 2] = ml.grounded_height(m, d, qadr, q, quat, c)
                yield "one_leg", f"one_leg__{side}__s{sc:.1f}__{tn}", (q, pos, quat, c), \
                    {"foot": side, "lift_m": sc * max_drop}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--bows", action="store_true")
    p.add_argument("--one-leg", action="store_true")
    a = p.parse_args()
    lib = dict(np.load(os.path.join(a.lib, "library.npz")))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    m, d = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
    extra, dropped = [], []
    for cat, cid, (q, pos, quat, contacts), prm in candidates(m, d, qadr, a.bows, a.one_leg):
        q = np.clip(q, lo, hi)
        k = int(np.argmax(np.abs(q - m.keyframe("home").ctrl).sum(axis=1)))
        h = ht.hold(m, d, qadr, q[k], pos[k], quat[k], contacts[k])
        if h["held"]:
            dropped.append(cid)
            continue
        rep = ml.check_clip(m, d, qadr, q, np.gradient(q, 1 / ml.FPS, axis=0), pos, quat, contacts)
        extra.append(({"id": cid, "category": cat, "source": cid.rsplit("__", 1)[0], "split": "train", "params": prm,
                       "check": rep, "hold": h | {"frame": k}, "contaminant": "unbalanced", "length": T},
                      arrays(m, d, qadr, q, pos, quat, contacts)))
        print(f"  keep {cid:44s} fails hold: {h['why']} at {h['t_fail_s']} s; kinematic check pass {rep['pass']}; "
              f"joint-limit margin {rep['joint_limit_margin_rad']:+.3f}")
    n_train = sum(c["split"] == "train" for c in man["clips"])
    write_library(lib, man, extra, a.out, {"clean_library": os.path.basename(os.path.normpath(a.lib)),
                                           "unbalanced": len(extra), "dropped_holdable": dropped,
                                           "share_of_train": round(len(extra) / (n_train + len(extra)), 3)})
    print(f"{a.out}: {n_train} clean + {len(extra)} unbalanced train clips; dropped (robot can hold them): {dropped}")


if __name__ == "__main__":
    main()
