"""S1.3: are the robot's foot switches right? No ground truth exists in the logs, so the reference is kinematic: while
walking, the foot whose sole sits lower in the trunk frame (forward kinematics of the recorded joint angles) carries
the weight. A foot is called "down" when its sole is within --margin of the lowest sole.

Reports, per foot, how often the switch agrees with the kinematic stance call, the switch's duty cycle, and the
timing offset (in 20 ms steps) that best lines the switch up with the kinematic signal.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/analysis/foot_switch_check.py \
      --logs ../robot_logs/*_walk.npz --png switch_check.png
"""

import argparse
import ast
import glob
import os
import sys

import mujoco
import numpy as np
from etils import epath

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import base  # noqa: E402

SCENE = "playground/open_duck_mini_v2/xmls/scene_flat_terrain_backlash.xml"
POS, CONTACT, CMD = slice(13, 27), slice(97, 99), slice(6, 9)


ROBOT_STANDING_ACC = np.array([-0.15, -4.22, 7.94])  # robot accelerometer at the home pose (2026-10-30 log)


def rot_between(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), np.dot(a, b)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def sole_heights(m, d, qadr, q, acc=None):
    """Sole heights for each row of joint angles. Without acc: in the trunk frame (base upright). With acc (robot raw
    accelerometer, smoothed): along the measured "up" direction, after rotating the robot's IMU reading into the
    model's IMU frame (mounting offset measured from the standing pose)."""
    out = np.zeros((len(q), 2))
    ids = [m.site("left_foot").id, m.site("right_foot").id]
    imu = m.site("imu").id
    d.qpos[:] = m.keyframe("home").qpos
    mujoco.mj_kinematics(m, d)
    sim_standing = d.site_xmat[imu].reshape(3, 3).T @ np.array([0, 0, 9.81])  # model IMU reading at home
    R_corr = rot_between(ROBOT_STANDING_ACC, sim_standing)
    for k, qk in enumerate(q):
        d.qpos[:] = m.keyframe("home").qpos
        d.qpos[qadr] = qk
        mujoco.mj_kinematics(m, d)
        p = np.array([d.site_xpos[i] for i in ids])
        if acc is None:
            out[k] = p[:, 2]
        else:
            up_imu = R_corr @ acc[k]
            up_world_frame = d.site_xmat[imu].reshape(3, 3) @ (up_imu / np.linalg.norm(up_imu))  # trunk-model frame
            out[k] = p @ up_world_frame
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", nargs="+", required=True)
    p.add_argument("--margin", type=float, default=0.004, help="m: a sole this close to the lowest one counts as down")
    p.add_argument("--png", default=None)
    p.add_argument("--tilt", action="store_true", help="measure heights along the IMU's up direction")
    a = p.parse_args()
    m = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
    d = mujoco.MjData(m)
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    files = sorted(set(sum([glob.glob(x) for x in a.logs], [])))
    sw_all, kin_all, ex = [], [], None
    for f in files:
        try:
            log = np.load(f)
        except Exception:
            continue
        meta = ast.literal_eval(str(log["meta"]))
        moving = np.any(np.abs(log["commands"][:, :3]) > 1e-3, axis=1)
        if moving.sum() < 100:
            continue
        q = log["obs"][:, POS] + np.array(meta["init_pos"])
        acc = log["acc_raw"].copy()
        bad = (np.linalg.norm(acc, axis=1) < 4) | (np.linalg.norm(acc, axis=1) > 16)
        acc[bad] = np.nan
        for i in range(3):  # 0.2 s centred moving average, glitches ignored
            col = acc[:, i]; ok = ~np.isnan(col)
            acc[:, i] = np.interp(np.arange(len(col)), np.where(ok)[0], col[ok])
            acc[:, i] = np.convolve(acc[:, i], np.ones(11) / 11, mode="same")
        h = sole_heights(m, d, qadr, q, acc if a.tilt else None)
        low = h.min(1, keepdims=True)
        kin = (h - low) < a.margin                      # kinematic "down"
        sw = log["obs"][:, CONTACT] > 0.5
        sw_all.append(sw[moving]); kin_all.append(kin[moving])
        if ex is None or moving.sum() > ex[3].sum():
            ex = (os.path.basename(f), h, sw, moving)
    sw, kin = np.concatenate(sw_all), np.concatenate(kin_all)
    print(f"{len(sw_all)} walk logs, {len(sw)} moving steps; heights {'along measured up (IMU tilt)' if a.tilt else 'in the trunk frame'}")
    for name, alt in [("as read", sw), ("inverted", ~sw), ("left/right swapped", sw[:, ::-1]), ("swapped + inverted", ~sw[:, ::-1])]:
        print(f"  hypothesis {name:20s}: agreement L {100 * np.mean(alt[:, 0] == kin[:, 0]):.0f}%  R {100 * np.mean(alt[:, 1] == kin[:, 1]):.0f}%")
    for j, side in enumerate(["left", "right"]):
        agree = np.mean(sw[:, j] == kin[:, j])
        # best lag: switch shifted by L steps vs kinematic
        best = max(range(-5, 6), key=lambda L: np.mean(np.roll(sw[:, j], -L) == kin[:, j]))
        print(f"  {side:5s}: switch down {100 * sw[:, j].mean():.0f}% of steps, kinematic down {100 * kin[:, j].mean():.0f}%; "
              f"agree {100 * agree:.0f}%; best alignment at switch shift {best:+d} steps "
              f"({100 * np.mean(np.roll(sw[:, j], -best) == kin[:, j]):.0f}%)")
        tp = np.mean(sw[kin[:, j], j]); tn = np.mean(~sw[~kin[:, j], j])
        print(f"         when the foot is kinematically down the switch reads down {100 * tp:.0f}%; when up it reads up {100 * tn:.0f}%")
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        name, h, swe, mov = ex
        k0 = np.argmax(mov) + 100
        sl = slice(k0, k0 + 200)
        t = np.arange(200) * 0.02
        fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
        for j, side in enumerate(["left", "right"]):
            ax[j].plot(t, 1000 * (h[sl, j] - h[sl].min(1)), label="sole height above the lower sole (mm, FK)")
            ax[j].fill_between(t, 0, 25 * swe[sl, j], step="mid", alpha=0.3, color="tab:green", label="switch reads down")
            ax[j].axhline(1000 * a.margin, color="k", lw=0.5, ls="--")
            ax[j].set_ylabel(f"{side} (mm)"); ax[j].legend(loc="upper right", fontsize=8)
        ax[1].set_xlabel("s"); fig.suptitle(f"Foot switches vs kinematic stance, {name}")
        fig.tight_layout(); fig.savefig(a.png, dpi=90)
        print("PNG:", a.png)


if __name__ == "__main__":
    main()
