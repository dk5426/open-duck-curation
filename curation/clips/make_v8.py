"""Dataset v8 (exploratory wild-clip study, 2026-11-19): v7 without the leans, plus keyframed wild clips.

  train  v7's 37 clean train clips + the 45-clip wild sweep (make_wild.grid: hop, kick, stomp, tap, dance, headbang,
         twist, each swept from gentle to beyond the robot) = 82, like v7
  val    v7's 19 clean val clips + 1 gentle held-out variant per wild family (make_wild.HELDOUT)
  test   v7's 56 clean test clips + 2 gentle held-out variants per wild family

No feasibility labels for the wild clips (no oracle in this study): "feasibility.infeasible" is False and
"feasibility.labelled" is False. The reference-only measures of dynamic_check.py are attached as "dynamic" for
description only (that check also marks every v7 walking gait infeasible).

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_v8.py \
      --lib ../open-duck-curation/data/clips_v7 --out ../open-duck-curation/data/clips_v8
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_library as ml  # noqa: E402
from dynamic_check import check as dyn_check  # noqa: E402
from make_contaminated import write_library  # noqa: E402
from make_infeasible import arrays  # noqa: E402
from make_wild import HELDOUT, build, clip_id, grid  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    lib = dict(np.load(os.path.join(a.lib, "library.npz")))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    keep = [c for c in man["clips"] if c["category"] != "lean"]
    idx = np.array([c["index"] for c in keep])
    base = {k: v[idx] for k, v in lib.items()}
    man = dict(man, clips=[dict(c, index=j) for j, c in enumerate(keep)])
    for c in man["clips"]:
        if c["split"] == "train":
            c["feasibility"] = dict(c.get("feasibility", {}), labelled=True)
    m, d = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    T = base["q"].shape[1]

    jobs = [("train", fam, prm, cid) for fam, prm, cid in grid()]
    jobs += [(split, fam, prm, clip_id(fam, prm)) for split, items in HELDOUT.items() for fam, prm in items]
    seen = {cid for *_, cid in jobs}
    assert len(seen) == len(jobs), "duplicate wild clip id"
    extra = []
    for split, fam, prm, cid in jobs:
        q, pos, quat, con, err = build(m, d, qadr, fam, prm)
        assert len(q) <= T, f"{cid}: {len(q)} frames > library length {T}"
        qd = np.gradient(q, 1 / ml.FPS, axis=0)
        rep = ml.check_clip(m, d, qadr, q, qd, pos, quat, con)
        dyn = dyn_check(m, d, qadr, q, pos, quat, con)
        e = {"id": cid, "category": fam, "source": cid, "split": split, "params": dict(prm, ik_foot_err_mm=round(1000 * err, 2)),
             "check": rep, "length": len(q), "contaminant": "wild", "dynamic": dyn, "new_in": "v8"}
        if split == "train":
            e["feasibility"] = {"kinematic": rep["pass"], "infeasible": False, "labelled": False}
        extra.append((e, arrays(m, d, qadr, q, pos, quat, con)))
        print(f"  {split:5s} {cid:34s} T {len(q):3d}  kinematic {rep['pass']!s:5s}  x{rep['speed_vs_servo']:.2f}  "
              f"lag {dyn['rate_lag_rad']:.2f}  zmp {dyn['zmp_min_margin_mm']}")
    meta = {"version": "v8", "base_library": os.path.basename(os.path.normpath(a.lib)), "leans": 0,
            "wild_train": sum(s == "train" for s, *_ in jobs), "wild_val": len(HELDOUT["val"]), "wild_test": len(HELDOUT["test"]),
            "labels": "none for wild clips (no oracle)"}
    write_library(base, man, extra, a.out, meta)
    n = {s: sum(c["split"] == s for c in json.load(open(os.path.join(a.out, "manifest.json")))["clips"]) for s in ("train", "val", "test")}
    print(f"{a.out}: {n}")


if __name__ == "__main__":
    main()
