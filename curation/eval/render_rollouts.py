"""GIF of a tracking policy on chosen clips: the policy in sim (left) next to the reference clip played kinematically
(right), one clip after another, with the clip id, split and live leg / keypoint errors.

  cd Open_Duck_Playground && MUJOCO_GL=osmesa .venv/bin/python ../open-duck-curation/curation/eval/render_rollouts.py \
      --ckpt <checkpoint dir> --clips <id> [<id> ...] --gif out.gif [--title "..."]
"""

import argparse
import os
import sys

import jax
import jax.numpy as jp
import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_clips import load_policy  # noqa: E402

from playground.open_duck_mini_v2 import tracking  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", required=True)
    p.add_argument("--clips", nargs="+", required=True)
    p.add_argument("--gif", required=True)
    p.add_argument("--title", default="")
    a = p.parse_args()
    from PIL import Image, ImageDraw, ImageFont

    env = tracking.Tracking(clip_ids=a.clips)
    policy = load_policy(a.ckpt, env)
    _, man = tracking.load_library()
    split = {c["id"]: c["split"] for c in man["clips"]}
    m = env._mj_model
    d = mujoco.MjData(m)
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    reset = jax.jit(lambda k, c: env.reset_to(k, c, 0))
    step = jax.jit(env.step)
    pol = jax.jit(policy)
    W, H = 360, 300
    r = mujoco.Renderer(m, H, W)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance, cam.elevation, cam.azimuth = 0.8, -15.0, 135.0
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 13)
    small = ImageFont.truetype("DejaVuSans.ttf", 12)
    frames = []
    for ci, cid in enumerate(a.clips):
        st = reset(jax.random.PRNGKey(ci), ci)
        L = int(env._ref_len[ci])
        key = jax.random.PRNGKey(100 + ci)
        fell_at = None
        for k in range(L - 1):
            key, kp = jax.random.split(key)
            act, _ = pol(st.obs, kp)
            st = step(st, act)
            if fell_at is None and float(st.done) > 0.5 and k < L - 3:
                fell_at = k
            if k % 2:
                continue
            ref = env._ref(ci, k + 1)
            # left: policy (sim state); right: reference (kinematic), both looked at from the same relative angle
            d.qpos[:] = np.asarray(st.data.qpos)
            mujoco.mj_kinematics(m, d)
            cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.12]
            r.update_scene(d, cam)
            left = Image.fromarray(r.render())
            d.qpos[:] = m.keyframe("home").qpos
            d.qpos[0:3] = np.asarray(ref["pos"])
            d.qpos[3:7] = np.asarray(ref["quat"])
            d.qpos[qadr] = np.asarray(ref["q"])
            mujoco.mj_kinematics(m, d)
            cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.12]
            r.update_scene(d, cam)
            right = Image.fromarray(r.render())
            img = Image.new("RGB", (2 * W, H + 52), (0, 0, 0))
            img.paste(left, (0, 52))
            img.paste(right, (W, 52))
            dr = ImageDraw.Draw(img)
            dr.text((6, 3), f"{a.title}  {cid}  [{split.get(cid, '?')}]"[:90], fill=(255, 255, 255), font=font)
            legs = float(st.metrics["err/legs_rms"])
            kpe = 100 * float(st.metrics["err/keypoints"])
            status = f"FELL at {fell_at / 50:.1f}s" if fell_at is not None else ""
            dr.text((6, 26), f"POLICY (sim)  t={k / 50:4.1f}s  legs {legs:.2f} rad  keypoints {kpe:.1f} cm  {status}",
                    fill=(255, 120, 120) if fell_at is not None else (255, 220, 0), font=small)
            dr.text((W + 6, 26), "REFERENCE (kinematic)", fill=(150, 230, 150), font=small)
            frames.append(img.quantize(colors=128))
            if fell_at is not None and k > fell_at + 25:
                break
    frames[0].save(a.gif, save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
    print("GIF:", a.gif, len(frames), "frames")


if __name__ == "__main__":
    main()
