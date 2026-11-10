"""Start-state bank v2 for the get-up task (2026-11-02, owner: more variation in the fallen starts). Four kinds,
all on the get-up model (body collision boxes) and settled before they are stored:

  drop  40%  as make_getup_bank.worker but wider: joints at random targets over the FULL range (70% of samples) or
             home, dropped from 0.15-0.5 m with a random spin (|w| up to 6 rad/s), settled 1.0-2.0 s
  limp  25%  dropped the same way with the servos nearly soft (kp x 0.08), so the joints flop as when torque cuts out
  walk  25%  the walker (ours_walker_full300M_258M) walking random commands in the get-up scene, kicked (base velocity
             0.6-1.6 m/s, spin up to 5 rad/s) every 1-2 s until it falls; the walker keeps running 0.5-2 s after the
             fall (on the robot it runs until someone presses the get-up button), then the joints hold and it settles
  real  10%  the recorded robot get-up starts (joint angles + IMU tilt, getup_replay.start_state), joints +-0.15 rad,
             settled

Samples that end standing are dropped. Writes playground/open_duck_mini_v2/data/getup_init_bank_v2.npz (qpos, cls,
kind) and prints the mix. Run from Open_Duck_Playground:
  MUJOCO_GL=osmesa .venv/bin/python ../tools/make_getup_bank_v2.py --n 4096 --procs 32 --walker <walker.onnx> \
      --robot-logs ../robot_logs/2026103015*_getup.npz
"""

import argparse
import glob
import os
import sys
from multiprocessing import Pool

import mujoco
import numpy as np
from etils import epath

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_getup_bank import classify  # noqa: E402
from playground.open_duck_mini_v2 import base  # noqa: E402

SCENE = "playground/open_duck_mini_v2/xmls/scene_getup_backlash.xml"
OUT = "playground/open_duck_mini_v2/data/getup_init_bank_v2.npz"
KINDS = ["drop", "limp", "walk", "real"]
MIX = [0.40, 0.25, 0.25, 0.10]
G = {}


def model():
    if "m" not in G:
        G["m"] = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
    return G["m"]


def joint_adr(m):
    return np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])


def standing(m, d):
    return classify(d) == 0 and d.qpos[2] > 0.12


def settle(m, d, seconds):
    for _ in range(int(seconds / m.opt.timestep)):
        mujoco.mj_step(m, d)


def drop(rng, limp):
    m = model()
    d = mujoco.MjData(m)
    gain0, bias0 = m.actuator_gainprm.copy(), m.actuator_biasprm.copy()
    lo, hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
    jadr = joint_adr(m)
    try:
        if limp:
            m.actuator_gainprm[:, 0] *= 0.08
            m.actuator_biasprm[:, 1] *= 0.08
        for _ in range(200):
            mujoco.mj_resetDataKeyframe(m, d, 0)
            tgt = m.keyframe("home").ctrl.copy() if rng.random() < 0.3 else rng.uniform(lo, hi)
            d.qpos[jadr] = tgt
            q = rng.normal(size=4)
            d.qpos[3:7] = q / np.linalg.norm(q)
            d.qpos[2] = rng.uniform(0.15, 0.5)
            d.qvel[3:6] = rng.uniform(-6, 6, 3)
            d.ctrl[:] = tgt
            mujoco.mj_forward(m, d)
            settle(m, d, rng.uniform(1.0, 2.0))
            if not np.isnan(d.qpos).any() and not standing(m, d):
                return d.qpos.copy()
        raise RuntimeError("200 drops all landed standing")
    finally:
        m.actuator_gainprm[:], m.actuator_biasprm[:] = gain0, bias0


def walk_fall(rng, walker_onnx):
    from duck_eval import Runner

    if "walker" not in G:
        G["walker"] = Runner(SCENE, walker_onnx, "playground/open_duck_mini_v2/data/polynomial_coefficients.pkl")
    r = G["walker"]
    m, d = r.model, r.data
    for _ in range(20):  # a walker that never falls within 30 s is retried; then fall back to a drop
        r.reset(rng, 0.02)
        fell_at, k = None, 0
        next_kick = int(rng.uniform(50, 100))
        after = int(rng.uniform(25, 100))
        while k < 1500:
            if k % 100 == 0:
                r.commands = [rng.uniform(-0.15, 0.15), rng.uniform(-0.2, 0.2), rng.uniform(-1, 1), 0, 0, 0, 0]
            if k == next_kick:
                v = rng.uniform(0.6, 1.6) * np.array([np.cos(a := rng.uniform(0, 2 * np.pi)), np.sin(a)])
                d.qvel[0:2] += v
                d.qvel[3:6] += rng.uniform(-5, 5, 3)
                next_kick += int(rng.uniform(50, 100))
            r.control_step()
            k += 1
            if fell_at is None and r.fallen():
                fell_at = k
            if fell_at is not None and k - fell_at >= after:
                break
        if fell_at is None or np.isnan(d.qpos).any():
            continue
        d.ctrl[:] = d.qpos[joint_adr(m)]  # hold where the joints are, like the paused runtime
        settle(m, d, 1.0)
        if not np.isnan(d.qpos).any() and not standing(m, d):
            return d.qpos.copy()
    return drop(rng, limp=False)


def real_start(rng, logs):
    from getup_eval import GetupSim
    from getup_replay import start_state

    if "real" not in G:
        G["real"] = [np.load(p) for p in logs]
    m = model()

    class Shim:  # what start_state needs from a GetupSim, without loading a policy
        pass

    s = Shim()
    s.m, s.d = m, mujoco.MjData(m)
    s.qadr = joint_adr(m)
    s.lo, s.hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
    for _ in range(50):  # new log and new noise each try: a start that settles standing would otherwise repeat forever
        log = G["real"][rng.integers(len(G["real"]))]
        joints = np.clip(log["pos"][0] + rng.uniform(-0.15, 0.15, m.nu), s.lo, s.hi)
        q = start_state(s, joints, log["obs"][0, 3:6])
        if not np.isnan(q).any() and not standing(m, s.d):
            return q
    return drop(rng, limp=False)  # every recorded start settled standing: fall back to a drop


def worker(args):
    seed, kind, walker_onnx, logs = args
    rng = np.random.default_rng(500000 + seed)
    if kind == "drop":
        q = drop(rng, limp=False)
    elif kind == "limp":
        q = drop(rng, limp=True)
    elif kind == "walk":
        q = walk_fall(rng, walker_onnx)
    else:
        q = real_start(rng, logs)
    d = mujoco.MjData(model())
    d.qpos[:] = q
    mujoco.mj_forward(model(), d)
    return q, classify(d), KINDS.index(kind)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=4096)
    p.add_argument("--procs", type=int, default=32)
    p.add_argument("--walker", required=True)
    p.add_argument("--robot-logs", nargs="+", required=True)
    a = p.parse_args()
    logs = sorted(set(sum([glob.glob(x) for x in a.robot_logs], [])))
    counts = np.round(np.array(MIX) * a.n).astype(int)
    counts[0] += a.n - counts.sum()
    jobs = []
    for kind, c in zip(KINDS, counts):
        jobs += [(len(jobs) + i, kind, os.path.abspath(a.walker), logs) for i in range(c)]
    with Pool(a.procs) as pool:
        res = pool.map(worker, jobs, chunksize=4)
    qpos = np.stack([r[0] for r in res])
    cls = np.array([r[1] for r in res])
    kind = np.array([r[2] for r in res])
    assert qpos.shape[1] == model().nq
    np.savez(OUT, qpos=qpos, cls=cls, kind=kind)
    names = ["low upright/sitting", "front", "back", "side"]
    print(f"wrote {OUT} {qpos.shape} from {len(logs)} robot logs")
    for k, kn in enumerate(KINDS):
        sel = kind == k
        print(f"  {kn:5s} {sel.sum():5d}: " + ", ".join(f"{names[c]} {np.sum(cls[sel] == c)}" for c in range(4))
              + f"; base z {np.median(qpos[sel, 2]):.3f} median")


if __name__ == "__main__":
    main()
