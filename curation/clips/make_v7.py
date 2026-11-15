"""Dataset v7 (PREREG v2): the final library of the confirmatory study.

  train  v5's 37 clean train clips + 45 leans sampled continuously across the feasible / infeasible boundary
  val    v5's 18 clean val clips (unchanged)
  test   v5's 18 clean test clips + two NEW sources per category (each in its 2 variants), every parameter inside the
         category's training range: gaits from gen_test_gaits.sh, crouch 0.3 / 0.7, bow 12 / 22 deg, sway 1.5 / 2.5 cm,
         head nod_tilt / look_tilt (combinations of training head moves)

Leans (category "lean", contaminant "lean"): signed base shift dx ~ U(+1, +16) cm forward or U(-10, -1) cm back (the
side drawn in proportion to the range lengths), both soles fixed, trunk upright; ramp-in 0.4 s, move ~ U(0.4, 1.0) s,
hold ~ U(1.0, 3.4 - 2 move) s, ramp back. Joint targets clipped to the range (as a raw pipeline would keep them).

Every train clip carries "feasibility", measured, never assumed:
  kinematic  passes check_clip (joint limits, foot gap, stance soles)
  static     hold_test.py on its most extreme held pose: "holds", "fails" (with why) or "dynamic" (no held stretch)
  infeasible True only if the static test fails. This is the label the oracle / physics filter uses.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_v7.py \
      --lib ../open-duck-curation/data/clips_v5 --test-gaits ../open-duck-curation/data/placo_gaits_test7 \
      --out ../open-duck-curation/data/clips_v7
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

SEED, N_LEANS = 7, 45
FWD, BACK = (0.01, 0.16), (-0.10, -0.01)  # boundary measured in the first draw: fwd ~5 cm, back ~2.5-3 cm
NEW_STATIONARY = [("crouch", 0.3), ("crouch", 0.7), ("bow", 12), ("bow", 22), ("sway", 0.015), ("sway", 0.025),
                  ("head", "nod_tilt"), ("head", "look_tilt")]
# v5's variants; importing make_infeasible / make_ambitious registers faster ones (vfast, f1.5, f3, f4) that v5 never had
V5_VARIANTS = {"bow": ("fast", "slow"), "sway": ("f0.5", "f1.0"), "head": ("slow", "fast")}


def test_clips(m, d, qadr, gait_dir, max_drop):
    """(category, source, suffix, (q, pos, quat, contacts), params) for every new test clip."""
    for (cat, sid), styles in sorted(ml.gait_files(gait_dir).items()):
        for sty, path in sorted(styles.items()):
            q, pos, quat, contacts, prm = ml.gait_clip(m, d, qadr, path, 1.0)
            lin, ang = ml.body_velocities(pos, quat)
            prm = {"dx": prm.get("dx"), "dy": prm.get("dy"), "dtheta": prm.get("dtheta"), "style": sty,
                   "single_support_s": prm.get("single_support_duration"), "foot_lift_m": prm.get("walk_foot_height"),
                   "mean_vx": round(float(lin[:, 0].mean()), 4), "mean_vy": round(float(lin[:, 1].mean()), 4),
                   "mean_yaw_rate": round(float(ang[:, 2].mean()), 4)}
            yield cat, sid, f"__{sty}", (q, pos, quat, contacts), prm
    for cat, src in NEW_STATIONARY:
        if cat == "crouch":
            sid = f"crouch__depth{src:.2f}"
            for sty, (tm, th) in ml.CROUCH_STYLES.items():
                q, pos, quat, c, prm = ml.crouch_clip(m, d, qadr, src, tm, th, max_drop)
                yield cat, sid, f"__{sty}", (q, pos, quat, c), prm
            continue
        sid = f"bow__pitch{src}deg" if cat == "bow" else f"sway__amp{src:.3f}m" if cat == "sway" else f"head__{src}"
        for v in V5_VARIANTS[cat]:
            q, pos, quat, c, prm = ml.stationary_clip(m, d, qadr, cat, src, v)
            yield cat, sid, f"__{v}", (q, pos, quat, c), prm


def leans(m, d, qadr, rng):
    t = np.arange(T) / ml.FPS
    ones = np.ones((T, 2), dtype=np.float32)
    w_fwd = (FWD[1] - FWD[0]) / ((FWD[1] - FWD[0]) + (BACK[1] - BACK[0]))
    for j in range(N_LEANS):
        dx = rng.uniform(*FWD) if rng.random() < w_fwd else rng.uniform(*BACK)
        tm = rng.uniform(0.4, 1.0)
        th = rng.uniform(1.0, 3.4 - 2 * tm)
        f = held(t, 0.4, tm, th)
        q, pos, quat, cache = np.zeros((T, 14)), np.zeros((T, 3)), np.zeros((T, 4)), {}
        for k in range(T):
            key = round(float(f[k]), 4)
            if key not in cache:
                cache[key] = ml.solve_legs_pose(m, d, qadr, key * dx, 0.0, 0.0)
            q[k], pos[k], quat[k] = cache[key][0], cache[key][1][0:3], cache[key][1][3:7]
        yield f"lean__{j:02d}__dx{dx:+.3f}", (q, pos, quat, ones), {"dx_m": round(float(dx), 4),
                                                                     "move_s": round(tm, 3), "hold_s": round(th, 3)}


def static_label(m, d, qadr, q, pos, quat, contacts, qd):
    quiet = np.convolve(np.abs(qd).max(axis=1) < ht.STILL, np.ones(ht.STILL_FRAMES), "same") >= ht.STILL_FRAMES
    still = np.where(quiet)[0]
    if not len(still):
        return {"static": "dynamic"}
    k = int(still[np.argmax(np.abs(q[still] - m.keyframe("home").ctrl).sum(axis=1))])
    h = ht.hold(m, d, qadr, q[k], pos[k], quat[k], contacts[k])
    return {"static": "holds" if h["held"] else "fails", "hold": h | {"frame": k}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--test-gaits", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    lib = dict(np.load(os.path.join(a.lib, "library.npz")))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    m, d = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
    max_drop = man.get("max_crouch_drop_m") or ml.max_crouch_drop(m, d, qadr, margin=0.03)
    have = {c["source"] for c in man["clips"]}

    # feasibility of the existing clean train clips
    man = dict(man)
    for c in man["clips"]:
        if c["split"] == "train":
            i, n = c["index"], c["length"]
            lab = static_label(m, d, qadr, lib["q"][i][:n], lib["base_pos"][i][:n], lib["base_quat"][i][:n],
                               lib["contacts"][i][:n], lib["qd"][i][:n])
            c["feasibility"] = {"kinematic": c["check"]["pass"], **lab, "infeasible": lab["static"] == "fails"}

    extra, dropped = [], []
    for cat, sid, suffix, (q, pos, quat, contacts), prm in test_clips(m, d, qadr, a.test_gaits, max_drop):
        assert sid not in have, f"{sid} already in {a.lib}"
        rep = ml.check_clip(m, d, qadr, q, np.gradient(q, 1 / ml.FPS, axis=0), pos, quat, contacts)
        if not rep["pass"]:
            dropped.append(sid + suffix)
            continue
        extra.append(({"id": sid + suffix, "category": cat, "source": sid, "split": "test", "params": prm,
                       "check": rep, "length": len(q), "new_in": "v7"}, arrays(m, d, qadr, q, pos, quat, contacts)))
        print(f"  test {sid + suffix}")

    rng = np.random.default_rng(SEED)
    n_inf = 0
    for cid, (q, pos, quat, contacts), prm in leans(m, d, qadr, rng):
        q = np.clip(q, lo, hi)
        qd = np.gradient(q, 1 / ml.FPS, axis=0)
        rep = ml.check_clip(m, d, qadr, q, qd, pos, quat, contacts)
        lab = static_label(m, d, qadr, q, pos, quat, contacts, qd)
        feas = {"kinematic": rep["pass"], **lab, "infeasible": lab["static"] == "fails"}
        n_inf += feas["infeasible"]
        extra.append(({"id": cid, "category": "lean", "source": cid, "split": "train", "params": prm, "check": rep,
                       "contaminant": "lean", "feasibility": feas, "length": T},
                      arrays(m, d, qadr, q, pos, quat, contacts)))
        print(f"  {cid:28s} kinematic {rep['pass']!s:5s} static {lab['static']:7s}"
              + (f" ({lab['hold']['why']} at {lab['hold']['t_fail_s']} s)" if lab["static"] == "fails" else ""))
    n_test = sum(e["split"] == "test" for e, _ in extra)
    write_library(lib, man, extra, a.out, {"version": "v7", "clean_library": os.path.basename(os.path.normpath(a.lib)),
                                           "leans": N_LEANS, "leans_infeasible": n_inf, "lean_seed": SEED,
                                           "new_test_clips": n_test, "test_dropped_by_checks": dropped})
    print(f"{a.out}: +{n_test} test clips (dropped {dropped}), +{N_LEANS} leans ({n_inf} infeasible by the hold test)")


if __name__ == "__main__":
    main()
