"""Sim half of robot test R4: the same step + chirp profile as joint_step_test.py, one joint at a time, on the
training model with the base fixed in the air (as on the stand), commanded at 50 Hz. Reports per joint, for the
+0.3 rad step: dead time (first motion > 2% of the step), t63 / t90 (s), peak speed (rad/s), overshoot; for the chirp:
gain and phase lag at 1, 2 and 4 Hz. With --robot <step_test.npz> the same numbers are computed from the robot's log
and printed side by side.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/robot/joint_step_sim.py \
      --joints left_knee left_hip_pitch left_ankle --out joint_step_sim.json [--robot step_test.npz]
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np
from etils import epath

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joint_step_test import DT, profile  # noqa: E402

from playground.open_duck_mini_v2 import base  # noqa: E402

SCENE = "playground/open_duck_mini_v2/xmls/scene_flat_terrain_backlash.xml"


def simulate(m, d, joint, offs):
    qadr = [m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)]
    names = [m.actuator(i).name for i in range(m.nu)]
    home = m.keyframe("home").ctrl.copy()
    mujoco.mj_resetDataKeyframe(m, d, m.keyframe("home").id)
    d.qpos[2] = 0.4  # hanging: feet clear of the floor
    i = names.index(joint)
    lo, hi = m.actuator_ctrlrange[i]
    nsub = int(round(DT / m.opt.timestep))
    t, tgt, pos = [], [], []
    for k, o in enumerate(offs):
        ctrl = home.copy()
        ctrl[i] = np.clip(home[i] + o, lo + 0.05, hi - 0.05)
        d.ctrl[:] = ctrl
        pos.append(d.qpos[qadr[i]])  # read before the step, like the robot script
        tgt.append(ctrl[i])
        t.append(k * DT)
        for _ in range(nsub):
            d.qpos[0:3] = [0, 0, 0.4]   # base held fixed (on the stand)
            d.qpos[3:7] = [1, 0, 0, 0]
            d.qvel[0:6] = 0
            mujoco.mj_step(m, d)
    return np.array(t), np.array(tgt), np.array(pos)


def metrics(t, tgt, pos):
    """Step response for the +0.3 rad step and chirp gain / phase."""
    dtg = np.diff(tgt)
    k0 = int(np.argmax(dtg > 0.25)) + 1  # the +0.3 step edge
    base, step = pos[k0 - 1], tgt[k0] - tgt[k0 - 1]
    resp = (pos[k0: k0 + int(1.5 / DT)] - base) / step
    tt = np.arange(len(resp)) * DT
    first = lambda thr: float(tt[np.argmax(resp >= thr)]) if np.any(resp >= thr) else float("nan")  # noqa: E731
    out = {"dead_time_s": first(0.02), "t63_s": first(0.63), "t90_s": first(0.90),
           "overshoot": float(max(resp.max() - 1, 0)),
           "peak_speed_rad_s": float(np.nanmax(np.abs(np.diff(pos[k0: k0 + int(1.5 / DT)]))) / DT)}
    n_chirp = int(10.0 / DT)
    c0 = len(t) - int(1.0 / DT) - n_chirp
    u, y = tgt[c0: c0 + n_chirp] - tgt[c0 - 1], pos[c0: c0 + n_chirp] - pos[c0 - 1]
    tc = np.arange(n_chirp) * DT
    f_inst = 0.5 + 4.5 * tc / 10.0
    for f in (1.0, 2.0, 4.0):
        w = np.abs(f_inst - f) < 0.25
        U = np.sum(u[w] * np.exp(-2j * np.pi * f * tc[w]))
        Y = np.sum(y[w] * np.exp(-2j * np.pi * f * tc[w]))
        out[f"gain_{f:g}Hz"] = float(np.abs(Y / U)) if abs(U) > 0 else float("nan")
        out[f"lag_{f:g}Hz_ms"] = float(-np.angle(Y / U) / (2 * np.pi * f) * 1000) if abs(U) > 0 else float("nan")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--joints", nargs="+", default=["left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "head_pitch"])
    p.add_argument("--out", required=True)
    p.add_argument("--robot", default=None)
    a = p.parse_args()
    m = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
    d = mujoco.MjData(m)
    res = {}
    rob = np.load(a.robot) if a.robot else None
    keys = ["dead_time_s", "t63_s", "t90_s", "overshoot", "peak_speed_rad_s", "gain_1Hz", "lag_1Hz_ms", "gain_2Hz",
            "lag_2Hz_ms", "gain_4Hz", "lag_4Hz_ms"]
    print(f"{'joint':16s} " + " ".join(f"{k:>16s}" for k in keys))
    for j in a.joints:
        t, tgt, pos = simulate(m, d, j, profile(0.0))
        res[j] = {"sim": metrics(t, tgt, pos)}
        print(f"{j + ' sim':16s} " + " ".join(f"{res[j]['sim'][k]:16.3f}" for k in keys))
        if rob is not None and f"{j}__t" in rob.files:
            res[j]["robot"] = metrics(rob[f"{j}__t"], rob[f"{j}__target"], rob[f"{j}__pos"])
            print(f"{j + ' robot':16s} " + " ".join(f"{res[j]['robot'][k]:16.3f}" for k in keys))
    json.dump(res, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
