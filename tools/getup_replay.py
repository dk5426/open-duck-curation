"""Rebuild a real robot get-up start in MuJoCo and run a get-up policy from it, to see whether the robot's failure
reproduces in sim. Start pose = the recorded joint positions at the Menu press + a trunk orientation that makes the
sim IMU read the same gravity direction as the policy saw on the robot (obs[0, 3:6], i.e. after the runtime's IMU
correction; heading is arbitrary). The body is dropped from 5 cm and settled for 1 s holding those joints, then the
policy runs for --seconds. Variants model the robot's slower servos by scaling actuator stiffness (kp) and damping.

Prints the uprightness trace (sim vs robot) and whether / when the sim stands; --gif renders the variants.

  cd Open_Duck_Playground && MUJOCO_GL=osmesa .venv/bin/python ../tools/getup_replay.py --log <getup.npz> \
      -o <getup.onnx> [--kp 1.0 0.5 0.3] [--gif out.gif]
"""

import argparse
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getup_eval import GetupSim  # noqa: E402


def quat_from_matrix(R):
    q = np.empty(4)
    mujoco.mju_mat2Quat(q, R.reshape(-1))
    return q


def rotation_between(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), np.dot(a, b)
    if c < -0.999999:  # opposite: any perpendicular axis
        p = np.cross(a, [1, 0, 0] if abs(a[0]) < 0.9 else [0, 1, 0])
        p /= np.linalg.norm(p)
        return 2 * np.outer(p, p) - np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def start_state(sim, joints, acc_seen):
    m, d = sim.m, sim.d
    mujoco.mj_resetDataKeyframe(m, d, m.keyframe("home").id)
    mujoco.mj_forward(m, d)
    imu = m.site("imu").id
    R_wb = d.xmat[1].reshape(3, 3)
    R_bi = R_wb.T @ d.site_xmat[imu].reshape(3, 3)  # imu site in the base frame (fixed)
    # want the imu's "up" (accel direction) to be acc_seen: R_wi^T e_z = a_hat  ->  R_wi = rotation taking a_hat to e_z
    R_wi = rotation_between(acc_seen, np.array([0, 0, 1.0]))
    R_wb_new = R_wi @ R_bi.T
    q = d.qpos.copy()
    q[3:7] = quat_from_matrix(R_wb_new)
    q[sim.qadr] = joints
    d.qpos[:] = q
    d.qvel[:] = 0
    mujoco.mj_forward(m, d)
    # lift so the lowest geom clears the floor by 5 cm, then settle holding the recorded joints
    lowest = min(d.geom_xpos[g][2] - m.geom_rbound[g] for g in range(m.ngeom) if m.geom_bodyid[g] > 0)
    d.qpos[2] += 0.05 - lowest
    d.ctrl[:] = np.clip(joints, sim.lo, sim.hi)
    for _ in range(500):
        mujoco.mj_step(m, d)
    return d.qpos.copy()


def run(sim, qpos, seconds, on_frame=None):
    sim.start(qpos)
    ups, stand, pos, tgt = [], [], [], []
    for i in range(int(seconds * 50)):
        sim.step()
        ups.append(sim.sensor(sim.up)[2])
        stand.append(sim.standing())
        pos.append(sim.d.qpos[sim.qadr].copy())
        tgt.append(sim.targets.copy())
        if on_frame:
            on_frame(i, ups[-1], stand[-1])
    run.last = (np.array(pos), np.array(tgt))
    return np.array(ups), np.array(stand)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--kp", type=float, nargs="+", default=[1.0, 0.5, 0.3])
    p.add_argument("--seconds", type=float, default=6.0)
    p.add_argument("--gif", default=None)
    p.add_argument("--png", default=None, help="robot vs sim plot: uprightness, hip pitch, knee, neck/head pitch")
    a = p.parse_args()
    log = np.load(a.log)
    joints, acc_seen = log["pos"][0], log["obs"][0, 3:6]
    t = log["t"] - log["t"][0]
    oa = log["obs"][:, 3:6]
    robot_up = oa[:, 2] / np.linalg.norm(oa, axis=1)

    sim = GetupSim(a.onnx)
    gain0, bias0, damp0 = sim.m.actuator_gainprm.copy(), sim.m.actuator_biasprm.copy(), sim.m.dof_damping.copy()
    qpos = start_state(sim, joints, acc_seen)
    sim.start(qpos)
    s_acc = sim.sensor(sim.acc)
    print(f"== {os.path.basename(a.log)} with {os.path.basename(a.onnx)}")
    print(f"robot start: accel seen {np.round(acc_seen, 2)} (uprightness {acc_seen[2] / np.linalg.norm(acc_seen):+.2f}); "
          f"sim after settling: accel {np.round(s_acc, 2)} (uprightness {s_acc[2] / np.linalg.norm(s_acc):+.2f})")
    print(f"robot: never stood; uprightness at 1/2/3 s: "
          + " ".join(f"{robot_up[min(len(t) - 1, int(s * 50))]:+.2f}" for s in (1, 2, 3)))
    results = {}
    for kp in a.kp:
        m = sim.m
        m.actuator_gainprm[:] = gain0
        m.actuator_biasprm[:] = bias0
        m.actuator_gainprm[:, 0] = gain0[:, 0] * kp
        m.actuator_biasprm[:, 1] = bias0[:, 1] * kp
        ups, stand = run(sim, qpos, a.seconds)
        first = np.argmax(stand) / 50 if stand.any() else None
        held = stand[-50:].all()
        results[kp] = (ups, stand) + run.last
        print(f"sim kp x{kp:<4}: stands {'at %.1f s' % first if first is not None else 'never'}; standing at the end: "
              f"{held}; uprightness at 1/2/3 s: " + " ".join(f"{ups[min(len(ups) - 1, s * 50)]:+.2f}" for s in (1, 2, 3)))
    m.actuator_gainprm[:], m.actuator_biasprm[:], m.dof_damping[:] = gain0, bias0, damp0

    if a.png:
        import ast

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        names = ast.literal_eval(str(log["meta"]))["joints"]
        ts = np.arange(int(a.seconds * 50)) * 0.02
        fig, ax = plt.subplots(4, 1, figsize=(13, 13), sharex=True)
        ax[0].plot(t, robot_up, color="k", lw=1.4, label="ROBOT")
        for kp, (ups, stand, _, _) in results.items():
            ax[0].plot(ts, ups, lw=1, label=f"sim kp x{kp}")
        ax[0].axhline(0.85, color="r", ls="--", lw=0.6)
        ax[0].set_ylabel("uprightness"); ax[0].set_ylim(-1.05, 1.05); ax[0].legend(loc="lower right")
        pos1, tgt1 = results[a.kp[0]][2], results[a.kp[0]][3]
        for k, (js, lab) in enumerate([(["left_hip_pitch", "right_hip_pitch"], "hip pitch"),
                                       (["left_knee", "right_knee"], "knee"),
                                       (["neck_pitch", "head_pitch"], "neck / head pitch")], start=1):
            for j, col in zip(js, ["tab:blue", "tab:orange"]):
                i = names.index(j)
                ax[k].plot(t, log["pos"][:, i], color=col, lw=1.6, label=f"{j} ROBOT")
                ax[k].plot(ts, pos1[:, i], color=col, lw=1, ls="--", label=f"{j} sim kp x{a.kp[0]}")
            ax[k].set_ylabel(f"{lab} (rad)"); ax[k].legend(loc="upper right", fontsize=7)
        ax[-1].set_xlabel("s since the get-up started")
        fig.suptitle(f"{os.path.basename(a.log)}: robot vs sim from the same start, {os.path.basename(a.onnx)}")
        fig.tight_layout()
        fig.savefig(a.png, dpi=85)
        print("PNG:", a.png)

    if a.gif:
        from PIL import Image, ImageDraw, ImageFont

        r = mujoco.Renderer(sim.m, 420, 560)
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        cam.trackbodyid = 1
        cam.distance, cam.elevation, cam.azimuth = 1.1, -18.0, 135.0
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        frames = []
        for kp in a.kp:
            sim.m.actuator_gainprm[:, 0] = gain0[:, 0] * kp
            sim.m.actuator_biasprm[:, 1] = bias0[:, 1] * kp

            def on_frame(i, up, st, kp=kp):
                if i % 2:
                    return
                r.update_scene(sim.d, cam)
                img = Image.fromarray(r.render())
                dr = ImageDraw.Draw(img)
                dr.rectangle([0, 0, 560, 50], fill=(0, 0, 0))
                dr.text((8, 4), f"robot start {os.path.basename(a.log)[:15]}, servo kp x{kp}", fill=(255, 255, 255),
                        font=font)
                dr.text((8, 26), f"t={i / 50:4.1f}s  up {up:+.2f}  {'STANDING' if st else ''}",
                        fill=(120, 255, 120) if st else (255, 220, 0), font=font)
                frames.append(img.quantize(colors=128))

            run(sim, qpos, a.seconds, on_frame)
        sim.m.actuator_gainprm[:], sim.m.actuator_biasprm[:] = gain0, bias0
        frames[0].save(a.gif, save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
        print("GIF:", a.gif)


if __name__ == "__main__":
    main()
