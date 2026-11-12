"""Infeasible-pool library (ExBody2's setting): the clean library plus clips our kinematic checks reject or that this
body cannot perform, kept the way a raw motion-capture pipeline would keep them (joint targets clipped to the range,
nothing else repaired). Val and test are unchanged.

Three groups ("contaminant" in the manifest):
  rejected_ambitious  every make_ambitious.py candidate that FAILS the checks (mostly joint-limit violations: faster
                      walks, wider side-steps, 0.6 rad/s turns, fast deep bows), q clipped to the range, base height
                      re-grounded
  rejected_corrupted  the corrupted copies in clips_v5c50 that fail the checks (sinking / floating soles, joints pinned
                      at the limit); cs50 already trained on these, so they repeat a tested case
  impossible          new motions this body cannot do with its feet planted and servo speeds:
                        lean_fwd              base held 6 / 8 cm forward of the feet (CoM outside the support)
                        bow_unbalanced        45 / 60 deg trunk pitch without moving the CoM back
                        one_leg               a foot lifted by the full crouch depth and held, base not shifted over
                                              the other foot
                        jump                  crouch, then base 3 cm above home with both feet in the air, twice
                        crouch_snap           full crouch and back in 0.12 s (beyond the servo speed)
                        sway_whip             5 cm sway at 3 Hz; head_whip  nod / shake at 4 Hz
The check report is kept in each entry ("check"), so which rule each clip breaks is on record.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_infeasible.py \
      --lib ../open-duck-curation/data/clips_v5 --c50 ../open-duck-curation/data/clips_v5c50 \
      --gaits ../open-duck-curation/data/placo_gaits_ambitious --out ../open-duck-curation/data/clips_v5inf
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_ambitious as ma  # noqa: E402  (also registers the vfast styles)
import make_library as ml  # noqa: E402
from make_contaminated import write_library  # noqa: E402

T = int(ml.CLIP_S * ml.FPS)
ml.SWAY_FREQ["f3"] = 3.0
ml.HEAD_SPEEDS["f4"] = 4.0


def arrays(m, d, qadr, q, pos, quat, contacts):
    qd = np.gradient(q, 1 / ml.FPS, axis=0)
    lin, ang = ml.body_velocities(pos, quat)
    return dict(q=q, qd=qd, base_pos=pos, base_quat=quat, lin_vel=lin, ang_vel=ang,
                contacts=np.asarray(contacts, dtype=np.float32), keypts=ml.keypoints(m, d, qadr, q))


def held(t, t_in=0.4, t_move=0.6, t_hold=2.2):
    """0 -> 1 -> held -> 0 profile (min-jerk ramps)."""
    return ml.minjerk((t - t_in) / t_move) - ml.minjerk((t - t_in - t_move - t_hold) / t_move)


def impossible(m, d, qadr):
    t = np.arange(T) / ml.FPS
    home = m.keyframe("home").qpos
    hc = m.keyframe("home").ctrl
    ones = np.ones((T, 2), dtype=np.float32)
    out = []

    def pose_clip(fn, frac):
        q, pos, quat, cache = np.zeros((T, 14)), np.zeros((T, 3)), np.zeros((T, 4)), {}
        for k in range(T):
            key = round(float(frac[k]), 4)
            if key not in cache:
                cache[key] = fn(key)
            q[k], pos[k], quat[k] = cache[key][0], cache[key][1][0:3], cache[key][1][3:7]
        return q, pos, quat

    for dx in (0.06, 0.08):  # forward lean: base moved, soles fixed, CoM not kept over the feet
        q, pos, quat = pose_clip(lambda f: ml.solve_legs_pose(m, d, qadr, f * dx, 0.0, 0.0), held(t))
        out.append(("lean_fwd", f"lean_fwd__dx{dx:.2f}", (q, pos, quat, ones), {"dx_m": dx}))
    for b in (45, 60):
        q, pos, quat = pose_clip(lambda f: ml.solve_legs_pose(m, d, qadr, 0.0, 0.0, f * np.radians(b)), held(t))
        out.append(("bow_unbalanced", f"bow_unbalanced__pitch{b}deg", (q, pos, quat, ones), {"pitch_deg": b}))
    # one leg: that leg takes the full-crouch joint deltas (its foot rises by the crouch depth), the other stays at home
    max_drop = ml.max_crouch_drop(m, d, qadr, margin=0.03)
    qc_full = ml.solve_crouch_legs(m, d, qadr, max_drop)[0]
    for side, s_ in (("left", 0), ("right", 1)):
        f = held(t)
        idx = [ml.names_index(f"{side}_{j}") for j in ("hip_pitch", "knee", "ankle")]
        q = np.tile(hc, (T, 1)).astype(float)
        q[:, idx] += f[:, None] * (qc_full - hc)[idx]
        quat = np.tile(home[3:7], (T, 1))
        c = ones.copy()
        c[f > 0.05, s_] = 0
        pos = np.tile(home[0:3], (T, 1))
        pos[:, 2] = ml.grounded_height(m, d, qadr, q, quat, c)
        out.append(("one_leg", f"one_leg__{side}", (q, pos, quat, c), {"foot": side, "lift_m": max_drop}))
    # jump: 0.3 s crouch, 0.15 s push to legs at home with the base 3 cm up and both feet off, land, twice
    drop = 0.6 * ml.max_crouch_drop(m, d, qadr, margin=0.03)
    qc = ml.solve_crouch_legs(m, d, qadr, drop)[0]
    q, pos, c = np.tile(hc, (T, 1)).astype(float), np.tile(home[0:3], (T, 1)), ones.copy()
    for t0 in (0.5, 2.2):
        dn = ml.minjerk((t - t0) / 0.3) - ml.minjerk((t - t0 - 0.3) / 0.1)
        up = ml.minjerk((t - t0 - 0.3) / 0.1) - ml.minjerk((t - t0 - 0.5) / 0.15)
        q = q + dn[:, None] * (qc - hc)
        pos[:, 2] += -dn * drop + up * 0.03
        c[up > 0.05] = 0
    out.append(("jump", "jump__h0.03", (q, pos, np.tile(home[3:7], (T, 1)), c), {"height_m": 0.03, "crouch_m": drop}))
    q, pos, quat, c, prm = ml.crouch_clip(m, d, qadr, 1.0, 0.12, 0.3, max_drop)
    out.append(("crouch_snap", "crouch_snap__0.12s", (q, pos, quat, c), prm))
    q, pos, quat, c, prm = ml.stationary_clip(m, d, qadr, "sway", 0.05, "f3")
    out.append(("sway_whip", "sway_whip__amp0.05_f3", (q, pos, quat, c), prm))
    for h in ("nod", "shake"):
        q, pos, quat, c, prm = ml.stationary_clip(m, d, qadr, "head", h, "f4")
        out.append(("head_whip", f"head_whip__{h}_f4", (q, pos, quat, c), prm))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--c50", required=True, help="corrupted library whose failing copies are added")
    p.add_argument("--gaits", required=True, help="output folder of gen_ambitious.sh")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    lib = dict(np.load(os.path.join(a.lib, "library.npz")))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    m, d = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
    extra = []

    def add(group, cat, cid, source, prm, arr, rep):
        extra.append(({"id": cid, "category": cat, "source": source, "split": "train", "params": prm, "check": rep,
                       "contaminant": group, "length": len(arr["q"])}, arr))

    for cat, sid, suffix, (q, pos, quat, contacts), prm in ma.candidates(m, d, qadr, a.gaits):
        rep = ml.check_clip(m, d, qadr, q, np.gradient(q, 1 / ml.FPS, axis=0), pos, quat, contacts)
        if rep["pass"]:
            continue
        q = np.clip(q, lo, hi)
        pos = pos.copy()
        pos[:, 2] = ml.grounded_height(m, d, qadr, q, quat, contacts)
        arr = arrays(m, d, qadr, q, pos, quat, contacts)
        add("rejected_ambitious", cat, f"{sid}{suffix}__rej", f"{sid}__rej", prm, arr, rep)
    n_amb = len(extra)

    c50 = dict(np.load(os.path.join(a.c50, "library.npz")))
    for c in json.load(open(os.path.join(a.c50, "manifest.json")))["clips"]:
        if c.get("contaminant") and not c["check"]["pass"]:
            n = c["length"]
            arr = {k: c50[k][c["index"]][:n] for k in ("q", "qd", "base_pos", "base_quat", "lin_vel", "ang_vel",
                                                         "contacts", "keypts")}
            add("rejected_corrupted", c["category"], c["id"], c["source"], c["params"] | {"corruption": c["contaminant"]},
                arr, c["check"])
    n_cor = len(extra) - n_amb

    for cat, cid, (q, pos, quat, contacts), prm in impossible(m, d, qadr):
        q = np.clip(q, lo, hi)
        rep = ml.check_clip(m, d, qadr, q, np.gradient(q, 1 / ml.FPS, axis=0), pos, quat, contacts)
        add("impossible", cat, cid, cid, prm, arrays(m, d, qadr, q, pos, quat, contacts), rep)
    n_imp = len(extra) - n_amb - n_cor

    n_train = sum(c["split"] == "train" for c in man["clips"])
    write_library(lib, man, extra, a.out, {"clean_library": os.path.basename(os.path.normpath(a.lib)),
                                           "rejected_ambitious": n_amb, "rejected_corrupted": n_cor,
                                           "impossible": n_imp, "infeasible_train_clips": len(extra),
                                           "share_of_train": round(len(extra) / (n_train + len(extra)), 3)})
    print(f"{a.out}: {n_train} clean + {len(extra)} infeasible train clips "
          f"({n_amb} rejected ambitious, {n_cor} rejected corrupted, {n_imp} impossible)")
    for e, _ in extra:
        k = e["check"]
        print(f"  {e['contaminant']:18s} {e['id'][:58]:58s} pass {k['pass']!s:5s} margin {k['joint_limit_margin_rad']:+.3f} "
              f"speed/servo {k['speed_vs_servo']:.2f} sole spread {k['stance_sole_z_spread_mm']}mm")


if __name__ == "__main__":
    main()
