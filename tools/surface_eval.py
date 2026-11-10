"""Walker sensitivity to floor surface (friction + softness), MuJoCo CPU, same loop as duck_eval.py.

The floor geom has priority 1, so its friction/solref/solimp decide every foot contact. Surfaces:
  tile        mu 0.30, hard            wood   mu 0.50, hard        default  mu 0.60, hard (training floor)
  rubber_mat  mu 1.00, slightly soft   carpet mu 0.90, soft        thick_carpet mu 0.90, softer
"Softness" = solref time constant (MuJoCo default 0.02 s) and a lower solimp dmin, i.e. a springier, deeper contact.
Reports static sink while standing (mean sole penetration, mm), then forward/backward/turn speed and random-command
survival from a 2 s standstill.

  uv run python ../tools/surface_eval.py -o <policy.onnx> [-o <other.onnx>] --gif carpet.gif
"""

import argparse
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from duck_eval import SEGMENTS, Runner, render_gif, segment_metrics  # noqa: E402

SURFACES = {
    "tile": (0.30, (0.02, 1.0), (0.9, 0.95, 0.001)),
    "wood": (0.50, (0.02, 1.0), (0.9, 0.95, 0.001)),
    "default": (0.60, (0.02, 1.0), (0.9, 0.95, 0.001)),
    "rubber_mat": (1.00, (0.03, 1.0), (0.8, 0.95, 0.002)),
    "carpet": (0.90, (0.05, 1.0), (0.5, 0.95, 0.005)),
    "thick_carpet": (0.90, (0.08, 0.8), (0.3, 0.95, 0.010)),
}


def set_surface(r, name):
    mu, solref, solimp = SURFACES[name]
    f = r.model.geom("floor").id
    r.model.geom_friction[f, 0] = mu
    r.model.geom_solref[f] = solref
    r.model.geom_solimp[f, :3] = solimp


def standing_sink_mm(r):
    r.reset(np.random.default_rng(0), 0.0)
    for _ in range(100):
        r.control_step()
    soles = {r.model.geom(n).id for n in ["left_foot_bottom_tpu", "right_foot_bottom_tpu"]}
    d = [c.dist for c in r.data.contact[: r.data.ncon] if c.geom1 in soles or c.geom2 in soles]
    return -1000 * float(np.mean(d)) if d else float("nan")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--onnx", action="append", required=True)
    p.add_argument("--scene", default="scene_flat_terrain_backlash.xml")
    p.add_argument("--gif", default=None, help="GIF of the first policy on carpet then tile")
    a = p.parse_args()
    ref = "playground/open_duck_mini_v2/data/polynomial_coefficients.pkl"
    for onnx in a.onnx:
        r = Runner(f"playground/open_duck_mini_v2/xmls/{a.scene}", onnx, ref)
        print(f"\n== {os.path.basename(onnx)}")
        print(f"{'surface':13s} {'sink':>6s} {'fwd vx':>7s} {'back vx':>8s} {'yaw_r wz':>9s} {'yaw_l wz':>9s} {'random 60s':>11s}")
        for name in SURFACES:
            set_surface(r, name)
            sink = standing_sink_mm(r)
            out = []
            for seg, k in [("fwd", "vx"), ("back", "vx"), ("yaw_r", "wz"), ("yaw_l", "wz")]:
                log = r.rollout([(100, [0, 0, 0]), (500, SEGMENTS[seg])], np.random.default_rng(0))
                out.append(f"{segment_metrics(log, 250)[k]:+.3f}" if log["fell_at"] is None else "FELL")
            ok = 0
            for seed in range(6):
                rng = np.random.default_rng(100 + seed)
                sched = [(100, [0, 0, 0])]
                for _ in range(30):
                    c = [rng.uniform(-0.15, 0.15), rng.uniform(-0.2, 0.2), rng.uniform(-1, 1)]
                    sched.append((100, [0.0, 0.0, 0.0] if rng.random() < 0.1 else c))
                ok += r.rollout(sched, rng)["fell_at"] is None
            print(f"{name:13s} {sink:5.1f}mm {out[0]:>7s} {out[1]:>8s} {out[2]:>9s} {out[3]:>9s} {ok:>8d}/6")
        if a.gif and onnx == a.onnx[0]:
            paths = []
            for name in ["thick_carpet", "tile"]:
                set_surface(r, name)
                path = a.gif.replace(".gif", f"_{name}.gif")
                render_gif(r, path, f"{os.path.basename(onnx)} on {name}")
                paths.append(path)
            print("GIFs:", paths)


if __name__ == "__main__":
    main()
