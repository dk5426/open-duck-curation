"""Bank of the poses a get-up policy gets stuck in: roll the policy out from fresh back drops (seeds neither the
training bank nor getup_eval uses) and keep the states at 2, 3 and 4 s where a sole is on the floor and the base is
off the floor (> 8 cm) but the robot is not standing (getup_back@108M: on its feet, trunk pitched back ~90 deg). getup_back2 starts part of its episodes from these.
Writes playground/open_duck_mini_v2/data/getup_sit_bank.npz (qpos).

  cd Open_Duck_Playground && MUJOCO_GL=osmesa .venv/bin/python ../tools/make_sitting_bank.py -o <getup.onnx> --n 600
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getup_eval import GetupSim  # noqa: E402
from make_getup_bank import worker  # noqa: E402

OUT = "playground/open_duck_mini_v2/data/getup_sit_bank.npz"
KEEP_STEPS = (100, 150, 200)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--n", type=int, default=600, help="drops to try (about a third land on the back)")
    a = p.parse_args()
    sim = GetupSim(a.onnx)
    out, n_back, n_stuck = [], 0, 0
    for k in range(a.n):
        q, cls = worker(300000 + k)
        if cls != 2:
            continue
        n_back += 1
        sim.start(q)
        stuck = False
        for i in range(1, max(KEEP_STEPS) + 1):
            sim.step()
            if (i in KEEP_STEPS and not sim.standing() and sim.d.qpos[2] > 0.08
                    and any(sim.touching(g) for g in sim.soles)):
                out.append(sim.d.qpos.copy())
                stuck = True
        n_stuck += stuck
    qpos = np.array(out)
    np.savez(OUT, qpos=qpos)
    print(f"back drops {n_back}, stuck on its feet in {n_stuck}; wrote {OUT} {qpos.shape}; "
          f"base height median {np.median(qpos[:, 2]):.3f} m")


if __name__ == "__main__":
    main()
