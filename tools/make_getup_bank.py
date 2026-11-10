"""Start-state bank for the get-up task: settled drops onto the floor, on the get-up model (body collision boxes).

Each sample: random base orientation, dropped from 0.2-0.4 m with the joints held (PD, home kp) at either the home pose
(half the samples) or random targets inside 70% of each joint's range, then simulated 1.5 s so it comes to rest.
Samples that land upright and standing are dropped (the env adds standing starts itself).

Run from Open_Duck_Playground:  uv run python ../tools/make_getup_bank.py --n 4096
Writes playground/open_duck_mini_v2/data/getup_init_bank.npz (qpos, cls).
"""

import argparse
from multiprocessing import Pool

import mujoco
import numpy as np
from etils import epath

from playground.open_duck_mini_v2 import base

SCENE = "playground/open_duck_mini_v2/xmls/scene_getup_backlash.xml"
OUT = "playground/open_duck_mini_v2/data/getup_init_bank.npz"


def classify(d):
    R = d.xmat[1].reshape(3, 3)
    up, fw = R[:, 2], R[:, 0]
    if up[2] > 0.7:
        return 0  # upright-ish (sitting/kneeling counts here when low)
    if fw[2] < -0.6:
        return 1  # on front
    if fw[2] > 0.6:
        return 2  # on back
    return 3  # on side


def worker(seed):
    m = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
    d = mujoco.MjData(m)
    rng = np.random.default_rng(seed)
    home = m.keyframe("home")
    lo, hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
    jadr = [m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)]
    while True:
        mujoco.mj_resetDataKeyframe(m, d, 0)
        if rng.random() < 0.5:
            tgt = home.ctrl.copy()
        else:
            c, r = (lo + hi) / 2, (hi - lo) / 2
            tgt = c + rng.uniform(-0.7, 0.7, m.nu) * r
        d.qpos[jadr] = tgt
        q = rng.normal(size=4)
        d.qpos[3:7] = q / np.linalg.norm(q)
        d.qpos[2] = rng.uniform(0.2, 0.4)
        d.ctrl[:] = tgt
        mujoco.mj_forward(m, d)
        for _ in range(750):
            mujoco.mj_step(m, d)
        if np.isnan(d.qpos).any():
            continue
        cls = classify(d)
        if cls == 0 and d.qpos[2] > 0.12:
            continue  # landed standing: not a get-up start
        return d.qpos.copy(), cls


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=4096)
    p.add_argument("--procs", type=int, default=16)
    a = p.parse_args()
    with Pool(a.procs) as pool:
        res = pool.map(worker, range(a.n), chunksize=16)
    qpos = np.stack([r[0] for r in res])
    cls = np.array([r[1] for r in res])
    np.savez(OUT, qpos=qpos, cls=cls)
    names = ["low upright/sitting", "front", "back", "side"]
    print(f"wrote {OUT} {qpos.shape}; " + ", ".join(f"{names[k]} {np.sum(cls == k)}" for k in range(4)),
          f"; base z range {qpos[:, 2].min():.3f}-{qpos[:, 2].max():.3f}")
