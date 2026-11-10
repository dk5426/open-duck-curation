"""Headless evaluation of a get-up ONNX policy in MuJoCo (CPU), with the same observation contract as getup.py
(no observation noise, no action delay).

Starts are fresh drops generated with seeds the training bank never used (make_getup_bank.worker), plus standing and
pushed starts. Each episode runs --seconds. Success = trunk up (> 0.85) and base above 0.8 x standing height for the
whole final second. Reports success rate per start class, time to first stand, and the fraction of time the head
touches the floor. Optionally renders a GIF of a few starts.

  MUJOCO_GL=osmesa uv run python ../tools/getup_eval.py -o <policy.onnx> --out r.json --gif r.gif
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np
import onnxruntime
from etils import epath

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_getup_bank import classify, worker  # noqa: E402
from playground.open_duck_mini_v2 import base  # noqa: E402

SCENE = "playground/open_duck_mini_v2/xmls/scene_getup_backlash.xml"
STAND_HEIGHT, ACTION_SCALE, VMAX = 0.155, 1.0, 5.24
CLASS_NAMES = {1: "front", 2: "back", 3: "side", 0: "sitting", 9: "standing", 8: "pushed"}


class GetupSim:
    def __init__(self, onnx_path):
        self.m = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
        self.d = mujoco.MjData(self.m)
        self.sess = onnxruntime.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        m = self.m
        self.home_u = m.keyframe("home").ctrl.copy()
        self.lo, self.hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
        jids = [m.actuator_trnid[i, 0] for i in range(m.nu)]
        self.qadr = np.array([m.jnt_qposadr[j] for j in jids])
        self.vadr = np.array([m.jnt_dofadr[j] for j in jids])
        self.bl_adr = np.array([m.jnt_qposadr[m.joint(m.actuator(i).name + "_backlash").id]
                                if m.actuator(i).name + "_backlash" in [m.joint(k).name for k in range(m.njnt)] else -1
                                for i in range(m.nu)])
        sens = lambda n: (m.sensor_adr[m.sensor(n).id], m.sensor_dim[m.sensor(n).id])  # noqa: E731
        self.gyro, self.acc, self.up = sens("gyro"), sens("accelerometer"), sens("upvector")
        self.floor = m.geom("floor").id
        self.soles = [m.geom(n).id for n in ["left_foot_bottom_tpu", "right_foot_bottom_tpu"]]
        self.head = [m.geom(n).id for n in ["col_head_assembly", "col_neck_yaw_assembly"]]

    def touching(self, g):
        for c in self.d.contact[: self.d.ncon]:
            if {c.geom1, c.geom2} == {g, self.floor}:
                return True
        return False

    def sensor(self, s):
        return self.d.sensordata[s[0]: s[0] + s[1]].copy()

    def obs(self):
        q = self.d.qpos[self.qadr].copy()
        q += np.where(self.bl_adr >= 0, self.d.qpos[np.maximum(self.bl_adr, 0)], 0.0)
        return np.concatenate([
            self.sensor(self.gyro), self.sensor(self.acc), q - self.home_u, self.d.qvel[self.vadr] * 0.05,
            self.a1, self.a2, self.a3, self.targets, [float(self.touching(g)) for g in self.soles],
        ]).astype(np.float32)

    def start(self, qpos, qvel=None):
        mujoco.mj_resetData(self.m, self.d)
        self.d.qpos[:] = qpos
        if qvel is not None:
            self.d.qvel[:6] = qvel
        self.targets = np.clip(self.d.qpos[self.qadr], self.lo, self.hi)
        self.d.ctrl[:] = self.targets
        self.a1 = self.a2 = self.a3 = np.zeros(self.m.nu)
        mujoco.mj_forward(self.m, self.d)

    def step(self):
        a = self.sess.run(None, {"obs": [self.obs()]})[0][0]
        self.a3, self.a2, self.a1 = self.a2, self.a1, a
        t = np.clip(self.home_u + ACTION_SCALE * a, self.lo, self.hi)
        self.targets = np.clip(t, self.targets - VMAX * 0.02, self.targets + VMAX * 0.02)
        self.d.ctrl[:] = self.targets
        for _ in range(10):
            mujoco.mj_step(self.m, self.d)

    def standing(self):
        return self.sensor(self.up)[2] > 0.85 and self.d.qpos[2] > 0.8 * STAND_HEIGHT


def episode(sim, qpos, qvel, seconds, on_frame=None):
    sim.start(qpos, qvel)
    n = int(seconds * 50)
    stand, head = [], []
    for i in range(n):
        sim.step()
        stand.append(sim.standing())
        head.append(any(sim.touching(g) for g in sim.head))
        if on_frame:
            on_frame(i, stand[-1])
    last = stand[-50:]
    first = next((i / 50 for i, s in enumerate(stand) if s), None)
    return {"success": bool(all(last)), "t_first_stand": first, "head_contact_frac": float(np.mean(head)),
            "nan": bool(np.isnan(sim.d.qpos).any())}


def starts(n_fallen, seed0=100000):
    home = None
    out = []
    for k in range(n_fallen):
        q, c = worker(seed0 + k)
        out.append((c, q, None))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--seconds", type=float, default=10.0)
    p.add_argument("--out", required=True)
    p.add_argument("--gif", default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--gif-classes", default="front,back,side,pushed",
                   help="start classes to render, in order; a repeated name renders its next start (e.g. back,back,back)")
    a = p.parse_args()

    sim = GetupSim(a.onnx)
    home_q = sim.m.keyframe("home").qpos.copy()
    rng = np.random.default_rng(7)
    cases = starts(a.n)
    cases += [(9, home_q, None)] * 4
    cases += [(8, home_q, np.r_[rng.uniform(-1, 1, 2), 0, rng.uniform(-4, 4, 3)]) for _ in range(8)]
    rows = []
    for c, q, v in cases:
        r = episode(sim, q, v, a.seconds)
        r["class"] = CLASS_NAMES[c]
        rows.append(r)
    summary = {}
    for name in ["front", "back", "side", "sitting", "standing", "pushed"]:
        rs = [r for r in rows if r["class"] == name]
        if rs:
            ts = [r["t_first_stand"] for r in rs if r["t_first_stand"] is not None]
            summary[name] = {"n": len(rs), "success": sum(r["success"] for r in rs),
                             "median_t_first_stand": float(np.median(ts)) if ts else None,
                             "head_contact_frac": float(np.mean([r["head_contact_frac"] for r in rs]))}
    print(f"== {os.path.basename(a.onnx)}  ({a.seconds:.0f} s episodes)")
    print(f"{'start':9s} {'success':>9s} {'t_stand':>8s} {'head':>6s}")
    for k, s in summary.items():
        t = "-" if s["median_t_first_stand"] is None else f"{s['median_t_first_stand']:.1f}s"
        print(f"{k:9s} {s['success']:>4d}/{s['n']:<4d} {t:>8s} {s['head_contact_frac']:6.2f}")
    tot = [r for r in rows if r["class"] in ("front", "back", "side", "sitting")]
    print(f"all fallen starts: {sum(r['success'] for r in tot)}/{len(tot)}")
    result = {"onnx": os.path.abspath(a.onnx), "summary": summary, "rows": rows}

    if a.gif:
        from PIL import Image, ImageDraw, ImageFont

        r = mujoco.Renderer(sim.m, 420, 560)
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        cam.trackbodyid = 1
        cam.distance, cam.elevation, cam.azimuth = 1.1, -18.0, 135.0
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        title = a.title or f"Get-up policy {os.path.basename(a.onnx)}"
        frames = []
        picks = {}
        for c, q, v in cases:
            picks.setdefault(CLASS_NAMES[c], []).append((q, v))
        for name in a.gif_classes.split(","):
            if not picks.get(name):
                continue
            q, v = picks[name].pop(0)

            def on_frame(i, st, name=name):
                if i % 2:
                    return
                r.update_scene(sim.d, cam)
                img = Image.fromarray(r.render())
                dr = ImageDraw.Draw(img)
                dr.rectangle([0, 0, 560, 50], fill=(0, 0, 0))
                dr.text((8, 4), title, fill=(255, 255, 255), font=font)
                dr.text((8, 26), f"start: {name}   t={i / 50:4.1f}s   {'STANDING' if st else ''}",
                        fill=(120, 255, 120) if st else (255, 220, 0), font=font)
                frames.append(img.quantize(colors=128))

            episode(sim, q, v, 6.0, on_frame)
        frames[0].save(a.gif, save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
        result["gif"] = os.path.abspath(a.gif)
        print("GIF:", a.gif)
    json.dump(result, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
