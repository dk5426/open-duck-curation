"""Compare training runs at matched step counts from their TensorBoard event files: per-step reward terms (episode sum
divided by episode length, so runs with different episode lengths compare fairly), leg error and episode length.

  python compare_runs.py --runs <run dir> [<run dir> ...] --at 25 50 [--terms legs keypoints alive]

Steps are in millions; each run reports the logged evaluation nearest to each requested step.
"""

import argparse
import glob
import os

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

DEFAULT_TERMS = ("legs", "keypoints", "head", "lin_vel", "orientation", "alive")


def load(run):
    f = sorted(glob.glob(os.path.join(run, "events*")))[-1]
    ea = EventAccumulator(f, size_guidance={"scalars": 0})
    ea.Reload()
    return {t: [(s.step, s.value) for s in ea.Scalars(t)] for t in ea.Tags()["scalars"]}


def at(series, step):
    return min(series, key=lambda sv: abs(sv[0] - step))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs", nargs="+", required=True)
    p.add_argument("--at", nargs="+", type=float, required=True, help="steps, in millions")
    p.add_argument("--terms", nargs="+", default=list(DEFAULT_TERMS))
    a = p.parse_args()
    cols = ["ep_len"] + [f"{t}/step" for t in a.terms] + ["legs_err/step"]
    print(f"{'run':28s} {'step':>6s} " + " ".join(f"{c:>14s}" for c in cols))
    for run in a.runs:
        s = load(run)
        for m in a.at:
            st, ln = at(s["eval/avg_episode_length"], m * 1e6)
            vals = [ln] + [at(s[f"eval/episode_reward/{t}"], m * 1e6)[1] / max(ln, 1) for t in a.terms]
            vals.append(at(s["eval/episode_err/legs_rms"], m * 1e6)[1] / max(ln, 1))
            print(f"{os.path.basename(os.path.normpath(run)):28s} {st / 1e6:5.0f}M " + " ".join(f"{v:14.3f}" for v in vals))


if __name__ == "__main__":
    main()
