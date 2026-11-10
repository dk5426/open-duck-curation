"""Feasibility GIFs for the next task (recovery + flips), no learning involved.

  Upstream's model lets ONLY the two foot soles touch the floor (every other geom has contype=conaffinity=0), so a
  fallen duck sinks through the ground. Here every mesh geom is made to collide with the floor (not with itself),
  which is what a recovery task needs.

  drop: the robot is dropped from random orientations with its joints held at the home pose; shows (and counts over
        many seeds) the resting poses a recovery policy must start from.
  jump: open-loop maximum-effort jump: crouch, then command fully extended legs at once. Run twice: with the 5.24 rad/s
        motor speed clip used in training, and with only the 3.23 Nm torque limit. Reports base rise, air time and
        the rotation a flip would need in that air time. The base is held upright on a vertical rail (orientation and
        xy reset every physics step), an optimistic upper bound that stops a topple from spoiling the measurement.

  MUJOCO_GL=osmesa uv run python ../tools/feasibility_gifs.py --outdir ../results
"""

import argparse
import os
import sys

import mujoco
import numpy as np
from etils import epath
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import base  # noqa: E402

LEG = [0, 1, 2, 3, 4, 9, 10, 11, 12, 13]  # actuator indices of the legs
PITCH_LEG = [2, 3, 4, 11, 12, 13]  # hip_pitch, knee, ankle on both sides


class Sim:
    def __init__(self):
        # Separate collision bit for the body: floor contype 1 -> 3, body meshes conaffinity 2 / contype 0, so the body
        # touches the floor only and never itself; the foot soles keep contype 1 / conaffinity 1. MuJoCo also keeps
        # per-body OR-ed masks (body_contype/body_conaffinity) for its broadphase; they must be updated too, or the
        # new geom masks are silently filtered out.
        self.m = mujoco.MjModel.from_xml_string(
            epath.Path("playground/open_duck_mini_v2/xmls/scene_flat_terrain.xml").read_text(), assets=base.get_assets())
        m = self.m
        m.geom_contype[m.geom("floor").id] = 3
        body_mesh = (m.geom_type == mujoco.mjtGeom.mjGEOM_MESH) & (m.geom_contype == 0) & (m.geom_conaffinity == 0)
        m.geom_conaffinity[body_mesh] = 2
        for b in range(m.nbody):
            gs = m.geom_bodyid == b
            if gs.any():
                m.body_contype[b] = np.bitwise_or.reduce(m.geom_contype[gs])
                m.body_conaffinity[b] = np.bitwise_or.reduce(m.geom_conaffinity[gs])
        self.d = mujoco.MjData(self.m)
        self.home_q = self.m.keyframe("home").qpos.copy()
        self.home_u = self.m.keyframe("home").ctrl.copy()
        self.r = mujoco.Renderer(self.m, height=420, width=560)
        self.cam = mujoco.MjvCamera()
        self.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        self.cam.trackbodyid = 1
        self.cam.distance, self.cam.elevation, self.cam.azimuth = 1.2, -12.0, 120.0
        self.font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        self.foot_bodies = {self.m.body("foot_assembly").id, self.m.body("foot_assembly_2").id}
        self.floor = self.m.geom("floor").id

    def frame(self, title, line, color=(255, 220, 0)):
        self.r.update_scene(self.d, self.cam)
        img = Image.fromarray(self.r.render())
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, 560, 50], fill=(0, 0, 0))
        dr.text((8, 4), title, fill=(255, 255, 255), font=self.font)
        dr.text((8, 26), line, fill=color, font=self.font)
        return img.quantize(colors=128)

    def any_contact_except_feet(self):
        for c in self.d.contact[: self.d.ncon]:
            g = c.geom2 if c.geom1 == self.floor else c.geom1 if c.geom2 == self.floor else None
            if g is not None and self.m.geom_bodyid[g] not in self.foot_bodies:
                return True
        return False

    def airborne(self):
        return not any(c.geom1 == self.floor or c.geom2 == self.floor for c in self.d.contact[: self.d.ncon])

    def up_axis(self):
        return self.d.xmat[1].reshape(3, 3)[:, 2]  # body z in world

    def fwd_axis(self):
        return self.d.xmat[1].reshape(3, 3)[:, 0]


def classify(s):
    up, fw = s.up_axis(), s.fwd_axis()
    if up[2] > 0.7:
        return "upright"
    if fw[2] < -0.6:
        return "on front"
    if fw[2] > 0.6:
        return "on back"
    return "on side"


def drop(s, rng, quat=None):
    mujoco.mj_resetDataKeyframe(s.m, s.d, 0)
    s.d.qpos[2] = 0.35
    if quat is None:
        quat = rng.normal(size=4)
    s.d.qpos[3:7] = quat / np.linalg.norm(quat)
    s.d.ctrl[:] = s.home_u
    mujoco.mj_forward(s.m, s.d)


def run_drop(s, outdir, n_stats):
    rng = np.random.default_rng(0)
    counts = {}
    for _ in range(n_stats):
        drop(s, rng)
        for _ in range(1500):
            mujoco.mj_step(s.m, s.d)
        k = classify(s)
        counts[k] = counts.get(k, 0) + 1
    print("drop rest poses over", n_stats, "random orientations:", counts)

    def q(axis, ang):
        a = np.asarray(axis, float)
        return np.r_[np.cos(ang / 2), np.sin(ang / 2) * a / np.linalg.norm(a)]

    cases = [("pitched forward 90deg", q([0, 1, 0], np.pi / 2)), ("pitched back 90deg", q([0, 1, 0], -np.pi / 2)),
             ("rolled left 90deg", q([1, 0, 0], np.pi / 2)), ("upside down", q([1, 0, 0], np.pi)),
             ("random", None), ("random", None)]
    frames = []
    for name, quat in cases:
        drop(s, rng, quat)
        for i in range(1250):
            mujoco.mj_step(s.m, s.d)
            if i % 25 == 0:
                frames.append(s.frame("Recovery start states: drop, joints held at home",
                                      f"start: {name}  ->  t={i * 0.002:.1f}s  {classify(s)}"))
    path = os.path.join(outdir, "feasibility_fall_poses.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)
    print("wrote", path, len(frames))
    return counts


def run_jump(s, outdir):
    crouch = s.home_u.copy()
    crouch[PITCH_LEG] = np.clip(s.home_u[PITCH_LEG] * 2.0, s.m.actuator_ctrlrange[PITCH_LEG, 0],
                                s.m.actuator_ctrlrange[PITCH_LEG, 1])
    extend = s.home_u.copy()
    extend[PITCH_LEG] = 0.0
    results, frames = {}, []
    for label, vmax in [("speed clip 5.24 rad/s (as trained)", 5.24), ("torque limit only (3.23 Nm)", None)]:
        mujoco.mj_resetDataKeyframe(s.m, s.d, 0)
        mujoco.mj_forward(s.m, s.d)
        z0 = s.d.qpos[2]
        target = s.home_u.copy()
        air, best_air, cur_air, zmax, wmax = 0, 0, 0, z0, 0.0
        for i in range(1500):
            goal = crouch if i < 500 else extend
            if i % 10 == 0:  # 50 Hz targets like the policy
                if vmax is None:
                    target = goal.copy()
                else:
                    step = vmax * 0.02
                    target = np.clip(goal, target - step, target + step)
                s.d.ctrl[:] = target
            mujoco.mj_step(s.m, s.d)
            s.d.qpos[0:2] = 0.0
            s.d.qpos[3:7] = [1, 0, 0, 0]
            s.d.qvel[[0, 1, 3, 4, 5]] = 0.0
            if i >= 500:
                zmax = max(zmax, s.d.qpos[2])
                wmax = max(wmax, s.d.qvel[2])  # peak upward base speed
                if s.airborne():
                    cur_air += 1
                    best_air = max(best_air, cur_air)
                else:
                    cur_air = 0
            if i % 10 == 0:
                frames.append(s.frame("Max-effort jump (base on a vertical rail): crouch, extend",
                                      f"{label}  t={i * 0.002:.2f}s  rise={1000 * (zmax - z0):.0f} mm"))
        air_s = best_air * 0.002
        results[label] = {"rise_mm": 1000 * (zmax - z0), "air_s": air_s, "peak_up_speed": wmax,
                          "flip_needs_rad_s": 2 * np.pi / air_s if air_s > 0 else float("inf")}
        print(label, {k: round(v, 3) for k, v in results[label].items()})
    path = os.path.join(outdir, "feasibility_jump.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)
    print("wrote", path, len(frames))
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", required=True)
    p.add_argument("--n_stats", type=int, default=200)
    a = p.parse_args()
    s = Sim()
    run_drop(s, a.outdir, a.n_stats)
    run_jump(s, a.outdir)
