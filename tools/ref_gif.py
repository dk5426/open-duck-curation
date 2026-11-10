"""Kinematic GIF of the polynomial reference gaits: joints from the reference (16 minus the two antennas -> the 14
actuated joints, as in ref_motion_viewer.py), base moved by integrating the reference's own base linear velocity
(dims 34:37) and yaw rate (dim 39). The reference stores base velocities, not base positions.

  MUJOCO_GL=osmesa uv run python ../tools/ref_gif.py --pkl <polynomial_coefficients.pkl> --gif ref.gif
"""

import argparse
import os
import sys

import mujoco
import numpy as np
from etils import epath
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.getcwd())
from playground.common.poly_reference_motion_numpy import PolyReferenceMotion  # noqa: E402
from playground.open_duck_mini_v2 import base  # noqa: E402

CMDS = [("fwd", [0.15, 0, 0]), ("back", [-0.15, 0, 0]), ("left", [0, 0.2, 0]), ("right", [0, -0.2, 0]),
        ("yaw_l", [0, 0, 1.0]), ("yaw_r", [0, 0, -1.0])]

p = argparse.ArgumentParser()
p.add_argument("--pkl", required=True)
p.add_argument("--gif", required=True)
p.add_argument("--title", default="Reference gaits (placo -> polynomial), kinematic")
p.add_argument("--pinned", action="store_true", help="keep the base fixed (old behaviour)")
args = p.parse_args()

model = mujoco.MjModel.from_xml_string(
    epath.Path("playground/open_duck_mini_v2/xmls/scene_flat_terrain.xml").read_text(), assets=base.get_assets())
data = mujoco.MjData(model)
prm = PolyReferenceMotion(args.pkl)
home = np.array(model.keyframe("home").qpos)
renderer = mujoco.Renderer(model, height=420, width=560)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
cam.trackbodyid = 1
cam.distance, cam.elevation, cam.azimuth = 1.15, -15.0, 135.0
font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
frames = []
for name, cmd in CMDS:
    pos, yaw = home[0:3].copy(), 0.0
    for i in range(3 * 50):
        ref = np.array(prm.get_reference_motion(*cmd, i))
        j = ref[0:16]
        q = home.copy()
        q[7:21] = np.concatenate([j[:9], j[11:]])
        if not args.pinned:
            pos[:2] += ref[34:36] * 0.02
            yaw += ref[39] * 0.02
            q[0:3] = pos
            yq = np.array([np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)])
            res = np.zeros(4)
            mujoco.mju_mulQuat(res, yq, home[3:7])
            q[3:7] = res
        data.qpos[:] = q
        mujoco.mj_forward(model, data)
        if i % 2:
            continue
        renderer.update_scene(data, cam)
        img = Image.fromarray(renderer.render())
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 560, 50], fill=(0, 0, 0))
        d.text((8, 4), args.title, fill=(255, 255, 255), font=font)
        d.text((8, 26), f"{name}: vx={cmd[0]:+.2f} vy={cmd[1]:+.2f} wz={cmd[2]:+.2f}  (base pinned)" if args.pinned else f"{name}: vx={cmd[0]:+.2f} vy={cmd[1]:+.2f} wz={cmd[2]:+.2f}  (base from ref velocity)",
               fill=(255, 220, 0), font=font)
        frames.append(img.quantize(colors=128))
frames[0].save(args.gif, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)
print("wrote", args.gif, len(frames))
