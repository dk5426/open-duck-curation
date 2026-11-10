"""Render every clip of a library as a kinematic replay (base pose + joints from the clip, no physics), one GIF per
category with the clips side by side, labelled with id, split and check results.

  cd Open_Duck_Playground && MUJOCO_GL=osmesa .venv/bin/python ../open-duck-curation/curation/clips/render_clips.py \
      --lib ../open-duck-curation/data/clips_v1 --out ../open-duck-curation/results/clips_v1
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np
from etils import epath

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import base  # noqa: E402

SCENE = "playground/open_duck_mini_v2/xmls/scene_flat_terrain_backlash.xml"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lib", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--cols", type=int, default=2)
    a = p.parse_args()
    from PIL import Image, ImageDraw, ImageFont

    os.makedirs(a.out, exist_ok=True)
    lib = np.load(os.path.join(a.lib, "library.npz"))
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    m = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
    d = mujoco.MjData(m)
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    W, H = 300, 260
    r = mujoco.Renderer(m, H, W)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance, cam.elevation, cam.azimuth = 0.75, -18.0, 135.0
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
    small = ImageFont.truetype("DejaVuSans.ttf", 11)
    home_z = m.keyframe("home").qpos[2]
    cats = sorted(set(c["category"] for c in man["clips"]))
    for cat in cats:
        clips = [c for c in man["clips"] if c["category"] == cat]
        cols = min(a.cols, len(clips))
        rows = (len(clips) + cols - 1) // cols
        frames = []
        T = max(c["length"] for c in clips)
        for k in range(0, T, 2):
            sheet = Image.new("RGB", (cols * W, rows * H), (0, 0, 0))
            for n, c in enumerate(clips):
                i = c["index"]
                kk = min(k, c["length"] - 1)
                d.qpos[:] = m.keyframe("home").qpos
                d.qpos[0:3] = lib["base_pos"][i, kk]
                d.qpos[3:7] = lib["base_quat"][i, kk]
                d.qpos[qadr] = lib["q"][i, kk]
                mujoco.mj_kinematics(m, d)
                cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.12]
                r.update_scene(d, cam)
                img = Image.fromarray(r.render())
                dr = ImageDraw.Draw(img)
                dr.rectangle([0, 0, W, 34], fill=(0, 0, 0))
                short = c["id"].replace(cat + "__", "")
                dr.text((5, 2), short[:44], fill=(255, 255, 255), font=font)
                ck = c["check"]
                dr.text((5, 18), f"{c['split']} | peak {ck['peak_joint_speed_rad_s']:.1f} rad/s | t {kk / 50:.1f}s",
                        fill=(255, 210, 90) if ck.get("fast_for_servo") else (150, 230, 150), font=small)
                sheet.paste(img, ((n % cols) * W, (n // cols) * H))
            frames.append(sheet.quantize(colors=128))
        path = os.path.join(a.out, f"{cat}.gif")
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
        print("GIF:", path, f"({len(clips)} clips)")


if __name__ == "__main__":
    main()
