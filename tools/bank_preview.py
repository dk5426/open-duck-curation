"""Render a grid of get-up start poses from a bank (one row per kind, if the bank has 'kind'), as a PNG.
  cd Open_Duck_Playground && MUJOCO_GL=osmesa .venv/bin/python ../tools/bank_preview.py --bank <bank.npz> --out x.png
"""

import argparse
import os
import sys

import mujoco
import numpy as np
from etils import epath

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import base  # noqa: E402

SCENE = "playground/open_duck_mini_v2/xmls/scene_getup_backlash.xml"
KINDS = ["drop", "limp", "walk", "real"]
CLS = ["upright", "front", "back", "side"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bank", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--per-row", type=int, default=8)
    a = p.parse_args()
    from PIL import Image, ImageDraw, ImageFont

    b = np.load(a.bank)
    kinds = b["kind"] if "kind" in b.files else np.zeros(len(b["qpos"]), int)
    m = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
    d = mujoco.MjData(m)
    r = mujoco.Renderer(m, 220, 240)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    cam.trackbodyid = 1
    cam.distance, cam.elevation, cam.azimuth = 0.75, -25.0, 135.0
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 13)
    rows = sorted(set(kinds.tolist()))
    sheet = Image.new("RGB", (240 * a.per_row, 220 * len(rows)), (0, 0, 0))
    rng = np.random.default_rng(0)
    for ri, k in enumerate(rows):
        idx = rng.choice(np.where(kinds == k)[0], size=min(a.per_row, int(np.sum(kinds == k))), replace=False)
        for ci, i in enumerate(idx):
            d.qpos[:] = b["qpos"][i]
            d.qpos[0:2] = 0  # walk falls end up to ~1 m away; the tracking camera is smoothed and would lag behind
            mujoco.mj_forward(m, d)
            r.update_scene(d, cam)
            img = Image.fromarray(r.render())
            dr = ImageDraw.Draw(img)
            name = KINDS[k] if "kind" in b.files else "bank"
            dr.text((6, 4), f"{name}: {CLS[int(b['cls'][i])]}", fill=(255, 255, 0), font=font)
            sheet.paste(img, (ci * 240, ri * 220))
    sheet.save(a.out)
    print("PNG:", a.out)


if __name__ == "__main__":
    main()
