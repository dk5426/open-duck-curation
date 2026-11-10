"""Queue gate for warm-started runs: the first eval of a warm start is the restored policy (before any update); fail if
the metric has collapsed by the last eval.
  python gate_no_collapse.py <run_dir> <tensorboard tag> <min_ratio>
  e.g. python gate_no_collapse.py runs/getup_back_smoke_5M eval/episode_stood_up 0.6
"""

import sys

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

run_dir, tag, min_ratio = sys.argv[1], sys.argv[2], float(sys.argv[3])
acc = EventAccumulator(run_dir)
acc.Reload()
if tag not in acc.Tags()["scalars"]:
    print(f"GATE: {tag} not logged in {run_dir}")
    sys.exit(1)
vals = [(s.step, s.value) for s in acc.Scalars(tag)]
first, last = vals[0][1], vals[-1][1]
print(f"GATE {tag}: " + ", ".join(f"{st / 1e6:.1f}M={v:.1f}" for st, v in vals) + f"  (last/first {last / max(first, 1e-9):.2f})")
ok = first > 0 and last >= min_ratio * first
print("GATE PASS" if ok else f"GATE FAIL: {tag} fell below {min_ratio:.0%} of the restored policy's value")
sys.exit(0 if ok else 1)
