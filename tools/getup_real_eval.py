"""Replay the recorded robot get-up starts in sim with the robot-side effects switched on one at a time:
head-vs-body collision + robot head gains (getup_real.make_real_model), servo overload protection
(servo_protection.py), lower servo torque, and the strict "FULL" body self-collision (every box pair, except
parent-child and the three pairs that already overlap at the home pose). Reports per policy how many robot starts end standing, how often servos
are in protection, and when the first servo enters it.

  cd Open_Duck_Playground && .venv/bin/python ../tools/getup_real_eval.py -o a.onnx [-o b.onnx] \
      --logs ../robot_logs/2026103015*_getup.npz
"""

import argparse
import glob
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getup_eval import ACTION_SCALE, VMAX, GetupSim  # noqa: E402
from getup_replay import start_state  # noqa: E402
from servo_protection import ServoProtection  # noqa: E402

from etils import epath  # noqa: E402

import getup_eval  # noqa: E402
from playground.open_duck_mini_v2 import base  # noqa: E402
from playground.open_duck_mini_v2.getup_real import make_real_model  # noqa: E402

# collision boxes that already overlap at the home pose (box approximations of adjacent parts): never real contacts
HOME_OVERLAPS = [("col_trunk_assembly", "col_left_roll_to_pitch_assembly"),
                 ("col_trunk_assembly", "col_right_roll_to_pitch_assembly"),
                 ("col_head_pitch_to_yaw", "col_head_assembly")]


def full_selfcollision_model():
    """The get-up scene with every body box colliding with every other (parent-child and the home-pose overlaps
    excluded), plus the robot head gains."""
    xml = epath.Path(getup_eval.SCENE).read_text()
    m0 = mujoco.MjModel.from_xml_string(xml, assets=base.get_assets())
    body = lambda g: m0.body(m0.geom_bodyid[m0.geom(g).id]).name  # noqa: E731
    excl = "".join(f'<exclude body1="{body(a)}" body2="{body(b)}"/>' for a, b in HOME_OVERLAPS)
    m = mujoco.MjModel.from_xml_string(xml.replace("</mujoco>", f"<contact>{excl}</contact></mujoco>"),
                                       assets=base.get_assets())
    make_real_model(m)
    for g in range(m.ngeom):
        if m.geom(g).name.startswith("col_"):
            m.geom_contype[g] |= 4
            m.geom_conaffinity[g] |= 4
            m.body_contype[m.geom_bodyid[g]] |= 4
            m.body_conaffinity[m.geom_bodyid[g]] |= 4
    return m


class ProtectedGetupSim(GetupSim):
    protect = False
    soft_s, soft_factor = 0.0, 1.0  # soft start: joint-speed limit x soft_factor for the first soft_s seconds

    def start(self, qpos, qvel=None):
        super().start(qpos, qvel)
        self.prot = ServoProtection(self.m.nu)
        self.prot_steps = 0
        self.first_prot = None
        self.k = 0
        self.peak_torque = 0.0  # max over the first 0.5 s of sum |actuator force| (N m): the start-up current surge

    def step(self):
        a = self.sess.run(None, {"obs": [self.obs()]})[0][0]
        self.a3, self.a2, self.a1 = self.a2, self.a1, a
        t = np.clip(self.home_u + ACTION_SCALE * a, self.lo, self.hi)
        vmax = VMAX * (self.soft_factor if self.k * 0.02 < self.soft_s else 1.0)
        self.targets = np.clip(t, self.targets - vmax * 0.02, self.targets + vmax * 0.02)
        q = self.d.qpos[self.qadr]
        kp = self.m.actuator_gainprm[:, 0]
        tau_max = self.m.actuator_forcerange[:, 1]
        ctrl = self.prot.limit_targets(self.targets, q, kp, tau_max) if self.protect else self.targets
        self.d.ctrl[:] = ctrl
        for _ in range(10):
            mujoco.mj_step(self.m, self.d)
            if self.k < 25:
                self.peak_torque = max(self.peak_torque, float(np.abs(self.d.actuator_force).sum()))
        if self.protect:
            q = self.d.qpos[self.qadr]
            self.prot.update(self.d.actuator_force, np.abs(kp * (self.targets - q)), tau_max)
            self.prot_steps += int(self.prot.protected.any())
            if self.first_prot is None and self.prot.protected.any():
                self.first_prot = self.k * 0.02
        self.k += 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--onnx", action="append", required=True)
    p.add_argument("--logs", nargs="+", required=True)
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--soft", type=float, nargs="*", default=[0.0],
                   help="soft-start durations to compare (s); joint speed x --soft-factor during them")
    p.add_argument("--soft-factor", type=float, default=1 / 3)
    p.add_argument("--configs", default=None, help="|-separated config names to run (default all)")
    a = p.parse_args()
    logs = sorted(set(sum([glob.glob(x) for x in a.logs], [])))
    configs = [("as trained", False, False, 1.0), ("head-vs-body + head gains", True, False, 1.0),
               ("+ overload protection", True, True, 1.0), ("+ protection, torque x0.7", True, True, 0.7),
               ("FULL self-coll + prot", "full", True, 1.0), ("FULL self-coll + prot, x0.7", "full", True, 0.7), ("FULL self-coll + prot, x0.6", "full", True, 0.6),
               ("FULL self-coll + prot, x0.5", "full", True, 0.5)]
    if a.configs:
        configs = [c for c in configs if c[0] in a.configs.split("|")]
    for onnx, soft in [(o, s) for o in a.onnx for s in a.soft]:
        print(f"\n== {os.path.basename(onnx)} on {len(logs)} robot starts, {a.seconds:g} s each"
              + (f"; soft start {soft:g} s at x{a.soft_factor:.2f} joint speed" if soft else "; no soft start"))
        for name, real, protect, tq in configs:
            sim = ProtectedGetupSim(onnx)
            if real == "full":
                sim.m = full_selfcollision_model()
                sim.d = mujoco.MjData(sim.m)
            elif real:
                make_real_model(sim.m)
            sim.m.actuator_forcerange[:] *= tq
            sim.protect = protect
            sim.soft_s, sim.soft_factor = soft, a.soft_factor
            ok, ts, prot_frac, firsts, peaks = 0, [], [], [], []
            for path in logs:
                log = np.load(path)
                q = start_state(sim, log["pos"][0], log["obs"][0, 3:6])
                sim.start(q)
                stand = []
                for _ in range(int(a.seconds * 50)):
                    sim.step()
                    stand.append(sim.standing())
                stand = np.array(stand)
                peaks.append(sim.peak_torque)
                if stand[-50:].all():
                    ok += 1
                    ts.append(np.argmax(stand) / 50)
                if protect:
                    prot_frac.append(sim.prot_steps / len(stand))
                    if sim.first_prot is not None:
                        firsts.append(sim.first_prot)
            extra = ""
            if protect:
                extra = (f"; a servo in protection {100 * np.mean(prot_frac):.0f}% of the time, in "
                         f"{len(firsts)}/{len(logs)} runs" + (f" (first at {np.median(firsts):.1f} s median)" if firsts else ""))
            print(f"  {name:30s} stands {ok:2d}/{len(logs)}" + (f", median {np.median(ts):.1f} s" if ts else "")
                  + f"; start-up peak torque {np.median(peaks):.1f} N m" + extra)


if __name__ == "__main__":
    main()
