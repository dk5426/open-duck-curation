"""Static-hold test: can the robot hold a clip's most extreme still pose under its own servos?

For each clip, the test pose is the frame farthest from home inside a held stretch (reference joint speed < 0.2 rad/s
for at least 0.5 s; a turning point of a sway is not a held pose). The robot is placed in that pose at rest, the servos
hold the reference joint targets, and the sim runs for 2 s (CPU MuJoCo, the training scene and actuators). A pose whose
centre of mass is outside its support, or that needs more torque than the servos have, tips over or sags, and a foot
the reference holds in the air comes down; a feasible pose stays put. Clips with no held stretch (gaits, whips) are
reported as dynamic: this test says nothing about them.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/hold_test.py \
      --lib ../open-duck-curation/data/clips_v5inf [--ids a b ...] [--out hold.json]
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_library as ml  # noqa: E402

HOLD_S, STILL, STILL_FRAMES = 2.0, 0.2, 25
TILT_DEG, DROP_M, SLIDE_M = 20.0, 0.03, 0.05  # fail = trunk rotated 20 deg from the pose, base 3 cm low, or 5 cm moved
SOLES = ("left_foot_bottom_tpu", "right_foot_bottom_tpu")


def hold(m, d, qadr, q, pos, quat, contacts, hold_s=HOLD_S):
    soles = [m.geom(n).id for n in SOLES]
    floor = m.geom("floor").id
    mujoco.mj_resetData(m, d)
    d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos, quat, q
    d.ctrl[:] = q
    mujoco.mj_forward(m, d)
    p0, R0 = d.qpos[0:3].copy(), d.xmat[1].reshape(3, 3).copy()
    for k in range(int(hold_s / m.opt.timestep)):
        mujoco.mj_step(m, d)
        tilt = np.degrees(np.arccos(np.clip((R0[:, 2] @ d.xmat[1].reshape(3, 3)[:, 2]), -1, 1)))
        drop, slide = p0[2] - d.qpos[2], np.linalg.norm(d.qpos[0:2] - p0[0:2])
        touched = {s for j in range(d.ncon) for s, g in enumerate(soles)
                   if {d.contact[j].geom1, d.contact[j].geom2} == {g, floor}}
        down = any(contacts[s] < 0.5 for s in touched)
        if tilt > TILT_DEG or drop > DROP_M or slide > SLIDE_M or down:
            why = "tipped" if tilt > TILT_DEG else "sagged" if drop > DROP_M else "moved" if slide > SLIDE_M \
                else "lifted foot came down"
            return {"held": False, "t_fail_s": round(k * m.opt.timestep, 3), "why": why}
    return {"held": True, "tilt_deg": round(float(tilt), 1), "drop_mm": round(1000 * float(drop), 1),
            "slide_mm": round(1000 * float(slide), 1)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--ids", nargs="*", default=None)
    p.add_argument("--groups", nargs="*", default=None, help="contaminant groups (clean = train clips without one)")
    p.add_argument("--out", default=None)
    a = p.parse_args()
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    lib = np.load(os.path.join(a.lib, "library.npz"))
    m, d = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    home = m.keyframe("home").ctrl
    out = {}
    for c in man["clips"]:
        grp = c.get("contaminant") or "clean"
        if (a.ids and c["id"] not in a.ids) or (a.groups and grp not in a.groups) or (not a.ids and c["split"] != "train"):
            continue
        i, n = c["index"], c["length"]
        q, qd = lib["q"][i][:n], lib["qd"][i][:n]
        quiet = np.convolve(np.abs(qd).max(axis=1) < STILL, np.ones(STILL_FRAMES), "same") >= STILL_FRAMES
        still = np.where(quiet)[0]
        if not len(still):
            out[c["id"]] = {"group": grp, "dynamic": True}
        else:
            k = int(still[np.argmax(np.abs(q[still] - home).sum(axis=1))])
            out[c["id"]] = {"group": grp, "frame": k, **hold(m, d, qadr, q[k], lib["base_pos"][i][k], lib["base_quat"][i][k],
                                                         lib["contacts"][i][k])}
        r = out[c["id"]]
        res = "dynamic" if r.get("dynamic") else ("HOLDS" if r["held"] else f"FAILS {r['why']} at {r['t_fail_s']} s")
        print(f"{grp:18s} {c['id'][:44]:44s} {res}", flush=True)
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
