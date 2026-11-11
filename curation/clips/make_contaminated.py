"""Contaminated libraries for the contamination sweep: the clean library plus corrupted copies of its TRAIN clips, the
kind of artifacts retargeted motion capture carries (the setting curation is meant for). Val and test are unchanged.

One corrupted copy per train clip, in a seeded order, the corruption cycling through:
  fast        played at 2x speed (joint speeds and base velocities double; the clip lasts half as long)
  jitter      8 Hz sinusoidal noise of 0.12 rad on every leg joint (random phase per joint): retargeting jitter
  slide       base translation x3 against unchanged legs, or a 0.15 m/s drift for stationary clips: foot sliding
  exaggerate  leg-joint deviation from home x1.8, clipped to the joint range: wrong scale, sinking / floating soles
Libraries are nested: c15 holds the first 7 copies, c30 the first 16, c50 all 37 (share of the final train set).
Corrupted clips keep their source's category, take split "train", source "<source>__x" and "contaminant": <kind>.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_contaminated.py \
      --lib ../open-duck-curation/data/clips_v5 --out ../open-duck-curation/data/clips_v5c
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_library as ml  # noqa: E402

KINDS = ("fast", "jitter", "slide", "exaggerate")
LEVELS = {"c15": 7, "c30": 16, "c50": 37}
SEED = 11
LEGS = [i for i, n in enumerate(ml.ACT) if n.startswith(("left_", "right_"))]


def corrupt(kind, q, pos, quat, home, lo, hi, stationary, rng):
    n = len(q)
    if kind == "fast":
        m = n // 2
        return (ml.resample(q, 2.0, m), ml.resample(pos, 2.0, m),
                np.array([x / np.linalg.norm(x) for x in ml.resample(quat, 2.0, m)]))
    q, pos = q.copy(), pos.copy()
    if kind == "jitter":
        t = np.arange(n) / ml.FPS
        ph = rng.uniform(0, 2 * np.pi, len(LEGS))
        q[:, LEGS] += 0.12 * np.sin(2 * np.pi * 8.0 * t[:, None] + ph)
    elif kind == "slide":
        if stationary:
            pos[:, 0] += 0.15 * np.arange(n) / ml.FPS
        else:
            pos[:, :2] = pos[0, :2] + 3.0 * (pos[:, :2] - pos[0, :2])
    elif kind == "exaggerate":
        q[:, LEGS] = home[LEGS] + 1.8 * (q[:, LEGS] - home[LEGS])
    return np.clip(q, lo, hi), pos, quat


def write_library(lib, man, extra, out, meta):
    """The clean library plus `extra` [(manifest entry, arrays)] appended as clips, padded to the library's length."""
    os.makedirs(out, exist_ok=True)
    T = lib["q"].shape[1]
    new = dict(lib)
    for key in [x for x in lib if x != "length"]:
        add = np.zeros((len(extra), T) + lib[key].shape[2:], dtype=np.float32)
        for j, (_, arr) in enumerate(extra):
            x = arr[key]
            add[j, : len(x)] = x
            add[j, len(x):] = x[-1]
        new[key] = np.concatenate([lib[key], add])
    new["length"] = np.concatenate([lib["length"], [e["length"] for e, _ in extra]]).astype(np.int32)
    m2 = dict(man)
    n0 = len(man["clips"])
    m2["clips"] = man["clips"] + [e | {"index": n0 + j} for j, (e, _) in enumerate(extra)]
    m2["contamination"] = meta
    np.savez_compressed(os.path.join(out, "library.npz"), **new)
    json.dump(m2, open(os.path.join(out, "manifest.json"), "w"), indent=1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--out", required=True, help="prefix: writes <out>15, <out>30, <out>50")
    a = p.parse_args()
    lib = dict(np.load(os.path.join(a.lib, "library.npz")))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    m, d = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    home = m.keyframe("home").ctrl.copy()
    lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
    rng = np.random.default_rng(SEED)
    train = [c for c in man["clips"] if c["split"] == "train"]
    order = [train[i] for i in rng.permutation(len(train))]
    extra = []
    for k, c in enumerate(order):
        kind = KINDS[k % len(KINDS)]
        i, n = c["index"], c["length"]
        stationary = c["category"] in ("crouch", "bow", "sway", "head")
        q, pos, quat = corrupt(kind, lib["q"][i, :n], lib["base_pos"][i, :n], lib["base_quat"][i, :n], home, lo, hi,
                               stationary, rng)
        L = len(q)
        contacts = lib["contacts"][i, :n]
        contacts = ml.resample(contacts, 2.0, L).round() if kind == "fast" else contacts
        qd = np.gradient(q, 1 / ml.FPS, axis=0)
        lin, ang = ml.body_velocities(pos, quat)
        arrays = dict(q=q, qd=qd, base_pos=pos, base_quat=quat, lin_vel=lin, ang_vel=ang, contacts=contacts,
                      keypts=ml.keypoints(m, d, qadr, q))
        rep = ml.check_clip(m, d, qadr, q, qd, pos, quat, contacts)
        entry = {k2: c[k2] for k2 in ("category", "params")} | {
            "id": f"{c['id']}__x{kind}", "source": c["source"] + "__x", "split": "train", "contaminant": kind,
            "corrupted_from": c["id"], "check": rep, "length": L}
        extra.append((entry, arrays))
        print(f"  {entry['id']:55s} check {'pass' if rep['pass'] else 'FAIL'}  speed {rep['peak_joint_speed_rad_s']:.2f}")
    for name, k in LEVELS.items():
        write_library(lib, man, extra[:k], a.out + name[1:],
                      {"clean_library": os.path.basename(os.path.normpath(a.lib)), "corrupted_train_clips": k,
                       "share_of_train": round(k / (len(train) + k), 3), "kinds": KINDS, "seed": SEED})
        print(f"{a.out + name[1:]}: {len(train)} clean + {k} corrupted train clips ({100 * k / (len(train) + k):.0f}%)")

if __name__ == "__main__":
    main()
