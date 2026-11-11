"""Ambitious-clip library for the contamination sweep: the clean library plus real motions pushed past what the robot
can likely do, that still pass the library's kinematic checks (the case curation is meant for: valid-looking motion
the body cannot track). Val and test are unchanged.

Candidates:
  gaits       curation/clips/gen_ambitious.sh: faster walking, longer steps, quicker turns, a quicker step style
  stationary  bow 30 / 35 / 40 deg in 0.4 s, full-depth crouch in 0.3 s, 5 cm sway at 1.5 Hz, head nod / shake at 2.5 Hz
Clips failing the kinematic checks are dropped; the passing ones are added in a seeded order, as many as --n.
They take split "train", source "<source>__amb" and "contaminant": "ambitious".

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_ambitious.py \
      --lib ../open-duck-curation/data/clips_v5 --gaits ../open-duck-curation/data/placo_gaits_ambitious \
      --n 16 --out ../open-duck-curation/data/clips_v5amb
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_library as ml  # noqa: E402
from make_contaminated import write_library  # noqa: E402

SEED = 13
ml.BOW_STYLES["vfast"] = (0.4, 0.3)
ml.SWAY_FREQ["f1.5"] = 1.5
ml.HEAD_SPEEDS["vfast"] = 2.5


def candidates(m, d, qadr, gait_dir):
    for (cat, sid), styles in sorted(ml.gait_files(gait_dir).items()):
        for sty, path in sorted(styles.items()):
            q, pos, quat, contacts, prm = ml.gait_clip(m, d, qadr, path, 1.0)
            yield cat, sid, f"__{sty}", (q, pos, quat, contacts), {
                "dx": prm.get("dx"), "dy": prm.get("dy"), "dtheta": prm.get("dtheta"), "style": sty,
                "single_support_s": prm.get("single_support_duration"), "foot_lift_m": prm.get("walk_foot_height")}
    max_drop = ml.max_crouch_drop(m, d, qadr, margin=0.03)
    for b in (30, 35, 40):
        q, pos, quat, contacts, prm = ml.stationary_clip(m, d, qadr, "bow", b, "vfast")
        yield "bow", f"bow__pitch{b}deg", "__vfast", (q, pos, quat, contacts), prm
    q, pos, quat, contacts, prm = ml.crouch_clip(m, d, qadr, 1.0, 0.3, 0.3, max_drop)
    yield "crouch", "crouch__depth1.00", "__vfast", (q, pos, quat, contacts), prm
    q, pos, quat, contacts, prm = ml.stationary_clip(m, d, qadr, "sway", 0.05, "f1.5")
    yield "sway", "sway__amp0.05m", "__f1.5", (q, pos, quat, contacts), prm
    for h in ("nod", "shake"):
        q, pos, quat, contacts, prm = ml.stationary_clip(m, d, qadr, "head", h, "vfast")
        yield "head", f"head__{h}", "__vfast", (q, pos, quat, contacts), prm


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--gaits", required=True, help="output folder of gen_ambitious.sh")
    p.add_argument("--n", type=int, default=16)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    lib = dict(np.load(os.path.join(a.lib, "library.npz")))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    m, d = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    passing = []
    for cat, sid, suffix, (q, pos, quat, contacts), prm in candidates(m, d, qadr, a.gaits):
        qd = np.gradient(q, 1 / ml.FPS, axis=0)
        rep = ml.check_clip(m, d, qadr, q, qd, pos, quat, contacts)
        print(f"  {sid + suffix:50s} {'pass' if rep['pass'] else 'FAIL'}  speed {rep['peak_joint_speed_rad_s']:5.2f}"
              f"  margin {rep['joint_limit_margin_rad']:.3f}")
        if not rep["pass"]:
            continue
        lin, ang = ml.body_velocities(pos, quat)
        arrays = dict(q=q, qd=qd, base_pos=pos, base_quat=quat, lin_vel=lin, ang_vel=ang,
                      contacts=np.asarray(contacts, dtype=np.float32), keypts=ml.keypoints(m, d, qadr, q))
        entry = {"id": f"{sid}{suffix}__amb", "category": cat, "source": f"{sid}__amb", "split": "train",
                 "params": prm, "check": rep, "contaminant": "ambitious", "length": len(q)}
        passing.append((entry, arrays))
    rng = np.random.default_rng(SEED)
    pick = [passing[i] for i in rng.permutation(len(passing))[: a.n]]
    n_train = sum(c["split"] == "train" for c in man["clips"])
    write_library(lib, man, pick, a.out, {"clean_library": os.path.basename(os.path.normpath(a.lib)),
                                          "ambitious_train_clips": len(pick),
                                          "share_of_train": round(len(pick) / (n_train + len(pick)), 3),
                                          "passing_candidates": len(passing), "seed": SEED})
    print(f"{a.out}: {n_train} clean + {len(pick)} ambitious train clips ({len(passing)} candidates passed the checks):")
    for e, _ in pick:
        print("   ", e["id"])


if __name__ == "__main__":
    main()
