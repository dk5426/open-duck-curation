"""Side-by-side GIF of a real robot get-up and the same policy in sim from the same start.

Left, ROBOT: kinematic replay of the recording. Joints = the recorded present positions (`pos`), trunk orientation =
a complementary filter of the recorded IMU (the corrected gyro/accel the policy saw: gyro integrated, pulled 2% per
step toward the accelerometer's gravity direction, so impact spikes do not jerk it), heading from the gyro. The body
is lowered until its lowest point touches the floor (no physics: this is what the sensors say happened).
Right, SIM: getup_replay.start_state + the policy, physics on.

  cd Open_Duck_Playground && MUJOCO_GL=osmesa .venv/bin/python ../tools/getup_side_by_side.py --log <getup.npz> \
      -o <getup.onnx> --gif out.gif
"""

import argparse
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getup_eval import GetupSim  # noqa: E402
from getup_replay import quat_from_matrix, rotation_between, start_state  # noqa: E402


def so3_exp(v):
    th = np.linalg.norm(v)
    if th < 1e-12:
        return np.eye(3)
    k = v / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def robot_orientations(gyro, acc, dt, alpha=0.98):
    """World-from-IMU rotations: integrate the gyro, nudge toward the accelerometer's up direction each step."""
    R = rotation_between(acc[0], np.array([0, 0, 1.0]))  # R @ a_hat = e_z
    out = [R.copy()]
    for k in range(1, len(gyro)):
        R = R @ so3_exp(gyro[k - 1] * dt[k - 1])
        a = acc[k]
        n = np.linalg.norm(a)
        if 4.0 < n < 16.0:  # skip impact spikes
            up_meas = R @ (a / n)  # where the accel says "up" is, in world
            corr = rotation_between(up_meas, np.array([0, 0, 1.0]))
            ang = np.arccos(np.clip(np.trace(corr) / 2 - 0.5, -1, 1))
            if ang > 1e-6:
                axis = np.array([corr[2, 1] - corr[1, 2], corr[0, 2] - corr[2, 0], corr[1, 0] - corr[0, 1]])
                axis /= np.linalg.norm(axis)
                R = so3_exp(axis * ang * (1 - alpha)) @ R
        out.append(R.copy())
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--gif", required=True)
    p.add_argument("--seconds", type=float, default=None, help="default: the recording's length")
    a = p.parse_args()
    from PIL import Image, ImageDraw, ImageFont

    log = np.load(a.log)
    t = log["t"] - log["t"][0]
    n = len(t) if a.seconds is None else min(len(t), int(a.seconds * 50))
    gyro, acc, pos = log["obs"][:, 0:3], log["obs"][:, 3:6], log["pos"]
    R_wi = robot_orientations(gyro, acc, np.diff(t))

    # robot replay model (kinematics only) and the sim (physics)
    sim = GetupSim(a.onnx)
    rm = sim.m
    rd = mujoco.MjData(rm)
    mujoco.mj_resetDataKeyframe(rm, rd, rm.keyframe("home").id)
    mujoco.mj_forward(rm, rd)
    imu = rm.site("imu").id
    R_bi = rd.xmat[1].reshape(3, 3).T @ rd.site_xmat[imu].reshape(3, 3)
    body_geoms = [g for g in range(rm.ngeom) if rm.geom_bodyid[g] > 0 and rm.geom_contype[g] | rm.geom_conaffinity[g]]

    corners = np.array([[i, j, k] for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)], dtype=float)

    def lowest_point(g):
        c, Rg = rd.geom_xpos[g], rd.geom_xmat[g].reshape(3, 3)
        if rm.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX:
            return float(np.min((corners * rm.geom_size[g]) @ Rg.T, axis=0)[2] + c[2])
        if rm.geom_type[g] == mujoco.mjtGeom.mjGEOM_SPHERE:
            return c[2] - rm.geom_size[g][0]
        return c[2] - rm.geom_rbound[g]

    def robot_pose(k):
        rd.qpos[:] = rm.keyframe("home").qpos
        rd.qpos[sim.qadr] = pos[k]
        rd.qpos[3:7] = quat_from_matrix(R_wi[k] @ R_bi.T)
        rd.qpos[0:3] = [0, 0, 0.3]
        mujoco.mj_kinematics(rm, rd)
        mujoco.mj_forward(rm, rd)
        rd.qpos[2] -= min(lowest_point(g) for g in body_geoms)
        mujoco.mj_forward(rm, rd)

    qpos0 = start_state(sim, pos[0], acc[0])
    sim.start(qpos0)

    W, H = 480, 400
    r = mujoco.Renderer(rm, H, W)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    cam.trackbodyid = 1
    cam.distance, cam.elevation, cam.azimuth = 1.0, -15.0, 135.0
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
    small = ImageFont.truetype("DejaVuSans.ttf", 13)
    frames = []
    for k in range(n):
        if k:
            sim.step()
        if k % 2:
            continue
        robot_pose(k)
        r.update_scene(rd, cam)
        left = Image.fromarray(r.render())
        r.update_scene(sim.d, cam)
        right = Image.fromarray(r.render())
        img = Image.new("RGB", (2 * W, H + 56), (0, 0, 0))
        img.paste(left, (0, 56))
        img.paste(right, (W, 56))
        dr = ImageDraw.Draw(img)
        up_r = (R_wi[k] @ R_bi.T)[2, 2]
        up_s = sim.sensor(sim.up)[2]
        dr.text((8, 4), f"ROBOT (recorded joints + IMU)  up {up_r:+.2f}", fill=(255, 255, 255), font=font)
        dr.text((W + 8, 4), f"SIM, same policy & start  up {up_s:+.2f}" + ("  STANDING" if sim.standing() else ""),
                fill=(120, 255, 120) if sim.standing() else (255, 255, 255), font=font)
        dr.text((8, 30), f"{os.path.basename(a.log)}   t = {t[k]:4.2f} s", fill=(255, 220, 0), font=small)
        dr.text((W + 8, 30), os.path.basename(a.onnx)[:40], fill=(255, 220, 0), font=small)
        dr.line([(W, 0), (W, H + 56)], fill=(255, 255, 255), width=2)
        frames.append(img.quantize(colors=160))
    frames[0].save(a.gif, save_all=True, append_images=frames[1:], duration=60, loop=0, optimize=True)
    print(f"GIF: {a.gif} ({len(frames)} frames, played at 0.67x speed)")


if __name__ == "__main__":
    main()
