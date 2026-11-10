"""Headless evaluation of an in-place jump ONNX policy in MuJoCo (CPU), same observation contract as jump.py
(get-up's 92 + [trigger on, seconds since trigger]; no observation noise, no action delay).

Each trial: 4 s from standing, trigger at 1.0 s for 0.5 s. Per trial: longest airborne stretch (both soles off the
floor) in ms, peak base rise above the pre-trigger stance (mm), peak lift of the lower sole (mm), xy drift (mm),
whether it is still standing at the end. --gif renders 3 trials back to back.

  MUJOCO_GL=osmesa uv run python ../tools/jump_eval.py -o <policy.onnx> --out r.json --gif r.gif
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getup_eval import GetupSim  # noqa: E402

WINDOW_STEPS, TRIGGER_STEP, STEPS = 25, 50, 200


class JumpSim(GetupSim):
    def obs(self):
        since = self.i - TRIGGER_STEP
        on = 0.0 <= since < WINDOW_STEPS
        return np.concatenate([super().obs(), [float(on), np.clip(since * 0.02, -1.0, 2.0)]]).astype(np.float32)


def trial(sim, rng, on_frame=None):
    q = sim.m.keyframe("home").qpos.copy()
    q[sim.qadr] += rng.uniform(-0.05, 0.05, len(sim.qadr))
    sim.start(q)
    sole_site = [sim.m.site("left_foot").id, sim.m.site("right_foot").id]
    air, best_air, z_ref, sole_ref, rise, lift = 0, 0, None, None, 0.0, 0.0
    xy0 = sim.d.qpos[0:2].copy()
    for i in range(STEPS):
        sim.i = i
        sim.step()
        z = sim.d.qpos[2]
        soles = [sim.d.site_xpos[s][2] for s in sole_site]
        if i == TRIGGER_STEP - 1:
            z_ref, sole_ref = z, min(soles)
        if i >= TRIGGER_STEP and z_ref is not None:
            rise = max(rise, z - z_ref)
            lift = max(lift, min(soles) - sole_ref)
            up = not any(sim.touching(g) for g in sim.soles)
            air = air + 1 if up else 0
            best_air = max(best_air, air)
        if on_frame:
            on_frame(i)
    return {"air_ms": best_air * 20, "base_rise_mm": 1000 * rise, "sole_lift_mm": 1000 * lift,
            "drift_mm": 1000 * float(np.linalg.norm(sim.d.qpos[0:2] - xy0)), "standing_at_end": bool(sim.standing())}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--out", required=True)
    p.add_argument("--gif", default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--window", type=int, default=25, help="trigger window in control steps (jump: 25, jump2: 30)")
    a = p.parse_args()
    global WINDOW_STEPS
    WINDOW_STEPS = a.window
    sim = JumpSim(a.onnx)
    rows = [trial(sim, np.random.default_rng(s)) for s in range(a.n)]
    keys = ["air_ms", "base_rise_mm", "sole_lift_mm", "drift_mm"]
    print(f"== {os.path.basename(a.onnx)}: {a.n} trials, trigger at 1.0 s")
    for k in keys:
        v = [r[k] for r in rows]
        print(f"  {k:14s} median {np.median(v):6.1f}  max {np.max(v):6.1f}")
    print(f"  standing at end {sum(r['standing_at_end'] for r in rows)}/{a.n};",
          f"trials with any airborne step {sum(r['air_ms'] > 0 for r in rows)}/{a.n}")
    result = {"onnx": os.path.abspath(a.onnx), "rows": rows}
    if a.gif:
        from PIL import Image, ImageDraw, ImageFont

        r = mujoco.Renderer(sim.m, 420, 560)
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        cam.trackbodyid = 1
        cam.distance, cam.elevation, cam.azimuth = 0.9, -5.0, 90.0
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        title = a.title or f"In-place jump {os.path.basename(a.onnx)}"
        frames = []
        for s in range(3):
            def on_frame(i, s=s):
                r.update_scene(sim.d, cam)
                img = Image.fromarray(r.render())
                dr = ImageDraw.Draw(img)
                dr.rectangle([0, 0, 560, 50], fill=(0, 0, 0))
                dr.text((8, 4), title, fill=(255, 255, 255), font=font)
                on = 0 <= i - TRIGGER_STEP < WINDOW_STEPS
                airb = not any(sim.touching(g) for g in sim.soles)
                dr.text((8, 26), f"trial {s + 1}  t={i / 50:4.2f}s  {'JUMP' if on else ''} {'AIRBORNE' if airb else ''}",
                        fill=(255, 120, 120) if airb else (255, 220, 0), font=font)
                frames.append(img.quantize(colors=128))
            trial(sim, np.random.default_rng(100 + s), on_frame)
        # half speed so the hop is visible
        frames[0].save(a.gif, save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
        result["gif"] = os.path.abspath(a.gif)
        print("GIF:", a.gif)
    json.dump(result, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
