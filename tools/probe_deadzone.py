"""Sweep single-axis commands and report base velocity + action magnitude, to map the policy's command dead zone."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from duck_eval import Runner, segment_metrics

r = Runner("playground/open_duck_mini_v2/xmls/" + sys.argv[2], sys.argv[1], "playground/open_duck_mini_v2/data/polynomial_coefficients.pkl")
for axis, vals in [(0, [-0.15, -0.1, -0.05, 0.05, 0.075, 0.1, 0.125, 0.15]), (1, [-0.2, -0.15, -0.1, -0.05, 0.05, 0.1, 0.15, 0.2]), (2, [-1, -0.5, -0.25, 0.25, 0.5, 1])]:
    for v in vals:
        cmd = [0.0, 0.0, 0.0]; cmd[axis] = v
        log = r.rollout([(100, [0, 0, 0]), (400, cmd)], np.random.default_rng(0))
        m = segment_metrics(log, 220) if log["fell_at"] is None else {}
        print(f"axis {axis} cmd {v:+.3f} -> vx {m.get('vx',np.nan):+.3f} vy {m.get('vy',np.nan):+.3f} wz {m.get('wz',np.nan):+.3f} air {m.get('air_frac',np.nan):.2f} |a| {np.abs(r.last_action).mean():.3f}")
