"""How stable is each train clip's hold-test label? (PREREG v2 amendment, 2026-11-15, before any v7 result)

The feasibility label (manifest `feasibility.infeasible`) comes from one 2 s hold of one pose with nominal servo gains
and friction. Near the balance boundary small details decide it. This re-runs the hold test on every train clip that
has a held pose, over 27 perturbations:
  friction x {0.8, 1.0, 1.2}  x  servo gains (kp) x {0.9, 1.0, 1.1}  x  test frame {k - 5, k, k + 5} (k = the labelled
  frame, clamped to the clip), each held for 3 s instead of 2.
A clip is **borderline** when fewer than 80% of the 27 tests agree with its label. The dataset is not changed; the
result goes to <lib>/label_stability.json and the curve analysis reports AUCs and kept counts with and without the
borderline clips.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/label_stability.py \
      --lib ../open-duck-curation/data/clips_v7
"""

import argparse
import itertools
import json
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hold_test as ht  # noqa: E402
import make_library as ml  # noqa: E402

FRICTION, KP, DFRAME, HOLD_S, AGREE = (0.8, 1.0, 1.2), (0.9, 1.0, 1.1), (-5, 0, 5), 3.0, 0.8


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    a = p.parse_args()
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    lib = dict(np.load(os.path.join(a.lib, "library.npz")))
    m0, _ = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))
    qadr = np.array([m0.jnt_qposadr[m0.actuator_trnid[i, 0]] for i in range(m0.nu)])
    models = {}
    for fr, kp in itertools.product(FRICTION, KP):
        m = ml.load_model(man.get("knee_limit_rad", ml.KNEE_LIMIT))[0]
        m.geom_friction[:, 0] *= fr
        m.actuator_gainprm[:, 0] *= kp
        m.actuator_biasprm[:, 1] *= kp
        models[(fr, kp)] = (m, mujoco.MjData(m))
    out = {}
    for c in man["clips"]:
        f = c.get("feasibility")
        if c["split"] != "train" or not f or "hold" not in f:
            continue
        i, n, k0 = c["index"], c["length"], f["hold"]["frame"]
        fails = []
        for (fr, kp), dk in itertools.product(models, DFRAME):
            m, d = models[(fr, kp)]
            k = int(np.clip(k0 + dk, 0, n - 1))
            h = ht.hold(m, d, qadr, lib["q"][i][k], lib["base_pos"][i][k], lib["base_quat"][i][k], lib["contacts"][i][k],
                        hold_s=HOLD_S)
            fails.append(not h["held"])
        p_fail = float(np.mean(fails))
        agree = p_fail if f["infeasible"] else 1 - p_fail
        out[c["id"]] = {"infeasible": f["infeasible"], "fail_rate": round(p_fail, 3), "agreement": round(agree, 3),
                        "borderline": agree < AGREE, "dx_m": c["params"].get("dx_m")}
        print(f"{c['id']:34s} label {'infeasible' if f['infeasible'] else 'feasible  '} perturbed fail rate {p_fail:.2f}"
              f"{'  BORDERLINE' if agree < AGREE else ''}", flush=True)
    json.dump({"perturbations": {"friction": FRICTION, "kp": KP, "dframe": DFRAME, "hold_s": HOLD_S},
               "agree_threshold": AGREE, "clips": out}, open(os.path.join(a.lib, "label_stability.json"), "w"), indent=1)
    b = [k for k, v in out.items() if v["borderline"]]
    print(f"{len(out)} clips with a held pose; borderline: {len(b)} {b}")


if __name__ == "__main__":
    main()
