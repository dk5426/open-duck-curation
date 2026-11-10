"""Headless evaluation of an Open Duck Mini v2 ONNX walking policy in MuJoCo.

Reuses the Playground's own MjInfer (obs builder, action scaling, motor speed limit, phase clock) so the policy sees
exactly what mujoco_infer.py feeds it; only the viewer loop is replaced by fixed joystick schedules.

Run from the Open_Duck_Playground checkout:
  uv run python ../tools/duck_eval.py -o ../Open_Duck_Mini/BEST_WALK_ONNX_2.onnx --out best2.json

Per command segment (fresh start from the home keyframe, 2 s of zero command, then the command for --seg_s seconds):
  survived      no fall (torso up-axis z < 0.5, or base below 0.08 m)
  vx, vy        mean base velocity in the yaw-aligned body frame over the last 70% of the command window (m/s)
  wz            mean world yaw rate over the same window (rad/s)
  clearance_mm  mean per-swing peak of the foot site above its stance height (mm), both feet
  air_frac      fraction of control steps with at least one foot off the floor
A 'random' stress test changes the command every 2 s for --random_s seconds, over several seeds.
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2.mujoco_infer import MjInfer  # noqa: E402

SEGMENTS = {
    "stand": [0.0, 0.0, 0.0],
    "fwd": [0.15, 0.0, 0.0],
    "back": [-0.15, 0.0, 0.0],
    "left": [0.0, 0.2, 0.0],
    "right": [0.0, -0.2, 0.0],
    "yaw_l": [0.0, 0.0, 1.0],
    "yaw_r": [0.0, 0.0, -1.0],
    "fwd_yaw": [0.15, 0.0, 0.5],
    "half_fwd": [0.075, 0.0, 0.0],
}


class Runner(MjInfer):
    def __init__(self, scene, onnx_path, ref):
        super().__init__(scene, ref, onnx_path, standing=False)
        self.left_site = self.model.site("left_foot").id
        self.right_site = self.model.site("right_foot").id

    def reset(self, rng, joint_noise):
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.key("home").id)
        if joint_noise > 0:
            addr = self.get_actuator_joints_addr()
            self.data.qpos[addr] += rng.uniform(-joint_noise, joint_noise, len(addr))
        mujoco.mj_forward(self.model, self.data)
        self.data.ctrl[:] = self.default_actuator
        self.motor_targets = self.default_actuator.copy()
        self.prev_motor_targets = self.default_actuator.copy()
        self.last_action[:] = 0
        self.last_last_action[:] = 0
        self.last_last_last_action[:] = 0
        self.imitation_i = 0
        self.imitation_phase = np.array([0.0, 0.0])
        self.commands = [0.0] * 7

    def fallen(self):
        up_z = self.data.site_xmat[self.imu_site_id].reshape(3, 3)[2, 2]
        return up_z < 0.5 or self.data.qpos[2] < 0.08

    def control_step(self):
        """One 50 Hz policy step, identical to MjInfer.run's inner block."""
        self.imitation_i = (self.imitation_i + self.phase_frequency_factor) % self.PRM.nb_steps_in_period
        a = self.imitation_i / self.PRM.nb_steps_in_period * 2 * np.pi
        self.imitation_phase = np.array([np.cos(a), np.sin(a)])
        obs = self.get_obs(self.data, self.commands)
        action = self.policy.infer(obs)
        self.last_last_last_action = self.last_last_action.copy()
        self.last_last_action = self.last_action.copy()
        self.last_action = action.copy()
        self.motor_targets = self.default_actuator + action * self.action_scale
        lim = self.max_motor_velocity * (self.sim_dt * self.decimation)
        self.motor_targets = np.clip(self.motor_targets, self.prev_motor_targets - lim, self.prev_motor_targets + lim)
        self.prev_motor_targets = self.motor_targets.copy()
        self.data.ctrl = self.motor_targets.copy()
        for _ in range(self.decimation):
            mujoco.mj_step(self.model, self.data)

    def rollout(self, schedule, rng, joint_noise=0.02):
        """schedule: list of (n_control_steps, command3). Returns per-step log."""
        self.reset(rng, joint_noise)
        log = {k: [] for k in ("cmd", "vbody", "wz", "zl", "zr", "cl", "cr")}
        for n, cmd in schedule:
            self.commands = list(cmd) + [0.0] * 4
            for _ in range(n):
                self.control_step()
                if self.fallen():
                    log["fell_at"] = len(log["cmd"])
                    return log
                q = self.data.qpos
                yaw = np.arctan2(2 * (q[3] * q[6] + q[4] * q[5]), 1 - 2 * (q[5] ** 2 + q[6] ** 2))
                c, s = np.cos(yaw), np.sin(yaw)
                vx, vy = self.data.qvel[0], self.data.qvel[1]
                log["cmd"].append(cmd)
                log["vbody"].append([c * vx + s * vy, -s * vx + c * vy])
                log["wz"].append(self.data.qvel[5])
                log["zl"].append(self.data.site_xpos[self.left_site][2])
                log["zr"].append(self.data.site_xpos[self.right_site][2])
                cl, cr = self.get_feet_contacts(self.data)
                log["cl"].append(cl)
                log["cr"].append(cr)
        log["fell_at"] = None
        return log


GIF_SCHEDULE = [("stand", 2), ("fwd", 4), ("back", 4), ("left", 4), ("right", 4), ("yaw_l", 4), ("yaw_r", 4),
                ("fwd_yaw", 4)]


def render_gif(r, path, title, fps=20, size=(560, 420)):
    """Showcase rollout through every command, tracking camera, command + time burned in. Needs MUJOCO_GL set."""
    from PIL import Image, ImageDraw, ImageFont

    renderer = mujoco.Renderer(r.model, height=size[1], width=size[0])
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    cam.trackbodyid = r.model.body(r.model.jnt_bodyid[r._floating_base_id]).id
    cam.distance, cam.elevation, cam.azimuth = 1.15, -15.0, 135.0
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    r.reset(np.random.default_rng(0), 0.0)
    frames, hz, every, step_i, fell = [], 50, max(1, round(50 / fps)), 0, None
    for name, secs in GIF_SCHEDULE:
        cmd = SEGMENTS[name]
        r.commands = list(cmd) + [0.0] * 4
        for _ in range(int(secs * hz)):
            r.control_step()
            if fell is None and r.fallen():
                fell = step_i / hz
            step_i += 1
            if step_i % every:
                continue
            renderer.update_scene(r.data, cam)
            img = Image.fromarray(renderer.render())
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, size[0], 50], fill=(0, 0, 0))
            d.text((8, 4), title, fill=(255, 255, 255), font=font)
            text = f"t={step_i / hz:5.1f}s  {name}: vx={cmd[0]:+.2f} vy={cmd[1]:+.2f} wz={cmd[2]:+.2f}"
            d.text((8, 26), text + ("  FELL" if fell is not None else ""),
                   fill=(255, 220, 0) if fell is None else (255, 80, 80), font=font)
            frames.append(img.quantize(colors=128))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=True)
    renderer.close()
    return fell


def clearance(z, contact):
    """Mean per-swing peak height (mm) of a foot site above its median stance height."""
    z, contact = np.asarray(z), np.asarray(contact, bool)
    if contact.sum() < 5:
        return float("nan"), 0
    base = np.median(z[contact])
    peaks, cur = [], None
    for zi, ci in zip(z, contact):
        if not ci:
            cur = zi if cur is None else max(cur, zi)
        elif cur is not None:
            peaks.append(cur - base)
            cur = None
    peaks = [p for p in peaks if p > 0.002]  # ignore contact chatter
    return (float(np.mean(peaks) * 1000) if peaks else 0.0), len(peaks)


def segment_metrics(log, start):
    sl = slice(start, None)
    vb = np.asarray(log["vbody"])[sl]
    cl, cr = np.asarray(log["cl"])[sl], np.asarray(log["cr"])[sl]
    clr_l, nl = clearance(np.asarray(log["zl"])[sl], cl)
    clr_r, nr = clearance(np.asarray(log["zr"])[sl], cr)
    return {
        "vx": float(vb[:, 0].mean()),
        "vy": float(vb[:, 1].mean()),
        "wz": float(np.mean(np.asarray(log["wz"])[sl])),
        "clearance_l_mm": clr_l,
        "clearance_r_mm": clr_r,
        "swings": nl + nr,
        "air_frac": float(np.mean(~(cl & cr))),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--onnx", required=True)
    p.add_argument("--scenes", default="scene_flat_terrain.xml,scene_flat_terrain_backlash.xml")
    p.add_argument("--ref", default="playground/open_duck_mini_v2/data/polynomial_coefficients.pkl")
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--seg_s", type=float, default=10.0)
    p.add_argument("--random_s", type=float, default=60.0)
    p.add_argument("--out", required=True)
    p.add_argument("--gif", default=None, help="also render a showcase GIF on the first scene")
    p.add_argument("--title", default=None)
    args = p.parse_args()

    hz = 50
    result = {"onnx": os.path.abspath(args.onnx), "scenes": {}}
    for scene in args.scenes.split(","):
        r = Runner(f"playground/open_duck_mini_v2/xmls/{scene}", args.onnx, args.ref)
        res = {"segments": {}, "random": []}
        for name, cmd in SEGMENTS.items():
            runs = []
            for seed in range(args.seeds):
                log = r.rollout([(2 * hz, [0, 0, 0]), (int(args.seg_s * hz), cmd)], np.random.default_rng(seed))
                ok = log["fell_at"] is None
                m = segment_metrics(log, 2 * hz + int(0.3 * args.seg_s * hz)) if ok else {}
                runs.append({"survived": ok, "fell_at_s": None if ok else log["fell_at"] / hz, **m})
            res["segments"][name] = {"cmd": cmd, "runs": runs}
        for seed in range(args.seeds * 2):
            rng = np.random.default_rng(100 + seed)
            sched = [(2 * hz, [0, 0, 0])]
            for _ in range(int(args.random_s / 2)):
                c = [rng.uniform(-0.15, 0.15), rng.uniform(-0.2, 0.2), rng.uniform(-1, 1)]
                sched.append((2 * hz, [0.0, 0.0, 0.0] if rng.random() < 0.1 else c))
            log = r.rollout(sched, rng)
            res["random"].append(None if log["fell_at"] is None else log["fell_at"] / hz)
        result["scenes"][scene] = res
    if args.gif:
        scene0 = args.scenes.split(",")[0]
        r = Runner(f"playground/open_duck_mini_v2/xmls/{scene0}", args.onnx, args.ref)
        title = args.title or f"{os.path.basename(args.onnx)}  [{scene0}]"
        result["gif"] = {"path": os.path.abspath(args.gif), "fell_at_s": render_gif(r, args.gif, title)}
    json.dump(result, open(args.out, "w"), indent=1)

    for scene, res in result["scenes"].items():
        print(f"\n== {os.path.basename(args.onnx)} on {scene}")
        print(f"{'segment':9s} {'cmd':>18s} {'surv':>5s} {'vx':>7s} {'vy':>7s} {'wz':>7s} {'clrL':>6s} {'clrR':>6s} {'air':>5s}")
        for name, s in res["segments"].items():
            runs = s["runs"]
            ok = [x for x in runs if x["survived"]]
            f = lambda k: np.mean([x[k] for x in ok]) if ok else float("nan")  # noqa: E731
            print(
                f"{name:9s} {str(s['cmd']):>18s} {len(ok)}/{len(runs):<3d} {f('vx'):7.3f} {f('vy'):7.3f} {f('wz'):7.3f} "
                f"{f('clearance_l_mm'):6.1f} {f('clearance_r_mm'):6.1f} {f('air_frac'):5.2f}"
            )
        falls = [x for x in res["random"] if x is not None]
        print(f"random {args.random_s:.0f}s: {len(res['random']) - len(falls)}/{len(res['random'])} survived, falls at {falls}")


if __name__ == "__main__":
    main()
