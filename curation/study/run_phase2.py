"""PREREG v2 Phase 2: other learners on the Phase 1 subsets at one keep-fraction (selection held fixed).

  OPENDUCK_ROOT=<dir> python3 run_phase2.py --gpus 1 2 --tag cv7 --lib data/clips_v7 [--fraction 85]

Runs <tag>_p2_<learner>_<cond>_s<seed> for learner x condition x seed through launch_train.sh (TRAIN_ENTRY =
train_alt.py), one run per GPU, each at the learner's calibrated step count (results/<tag>/phase2_calibration.json:
the steps that fill the Phase 1 PPO mean wall-clock, measured in smoke runs), then the Phase 1 test protocol (nominal,
10 rollouts, eval_clips.py) and analysis/phase2_analysis.py -> results/<tag>/phase2/SUMMARY.md, DONE.

Conditions: full, and curated / kinematic / oracle / random at the fraction (default: f* from fstar.json), using the
Phase 1 subset files unchanged. DAgger's teacher is the Phase 1 PPO final policy of the same condition and seed.
PPO itself is not rerun: its Phase 1 test results at the fraction are the reference row. Every step is skipped if its
output exists, so the driver can be restarted.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_study as rs  # noqa: E402

LEARNERS = ("ppo_noff", "sac", "ars", "dagger")
CONDS = ("full", "curated", "kinematic", "oracle", "random")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gpus", type=int, nargs="+", required=True)
    p.add_argument("--tag", default="cv7")
    p.add_argument("--lib", required=True)
    p.add_argument("--fraction", type=int, default=None, help="default: f* from results/<tag>/fstar.json")
    p.add_argument("--learners", nargs="+", default=list(LEARNERS))
    p.add_argument("--conds", nargs="+", default=list(CONDS))
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    p.add_argument("--rollouts", type=int, default=10)
    p.add_argument("--steps", type=json.loads, default=None, help='override, e.g. \'{"sac": 2000000}\' (smoke tests)')
    p.add_argument("--sub", default="phase2", help="output folder under results/<tag>/ and run-name infix")
    a = p.parse_args()
    a.lib = os.path.abspath(a.lib)
    rs.a = argparse.Namespace(lib=a.lib)
    T = a.tag
    P1 = os.path.join(rs.C, "results", T)
    f = a.fraction or json.load(open(os.path.join(P1, "fstar.json")))["fstar"]
    OUT = rs.OUT = os.path.join(P1, a.sub)
    TEST = os.path.join(OUT, "test")
    for d in (OUT, TEST, os.path.join(OUT, "launch")):
        os.makedirs(d, exist_ok=True)
    steps = json.load(open(os.path.join(P1, "phase2_calibration.json")))["steps"] if a.steps is None else {}
    steps.update(a.steps or {})
    rs.log(f"phase 2 {T}: fraction {f}%, learners {a.learners}, conditions {a.conds}, seeds {a.seeds}, GPUs {a.gpus}, "
           f"steps {steps}")
    json.dump({"fraction": f, "learners": a.learners, "conds": a.conds, "seeds": a.seeds, "steps": steps},
              open(os.path.join(OUT, "config.json"), "w"), indent=1)

    def subset(cond, seed):
        if cond == "full":
            return None
        return os.path.join(P1, "subsets", f"{cond}_f{f}" + (f"_s{seed}" if cond == "random" else "") + ".json")

    def phase1_run(cond, seed):
        return f"{T}_full_s{seed}" if cond == "full" else f"{T}_{cond}_f{f}_s{seed}"

    S = rs.Scheduler(a.gpus)
    pool = ThreadPoolExecutor(max_workers=len(a.gpus))
    futures, names = [], []
    entry = os.path.join(rs.C, "curation", "study", "train_alt.py")
    for li, lr in enumerate(a.learners):
        for cond in a.conds:
            for seed in a.seeds:
                short = f"{a.sub}_{lr}_{cond}_s{seed}"
                extra = ["--learner", lr]
                if lr == "dagger":
                    extra += ["--teacher", rs.final_ckpt(phase1_run(cond, seed))]
                names.append(S.submit(
                    f"{T}_{short}", steps[lr], prio=li, seed=seed, clips=subset(cond, seed), args=extra,
                    env={"TRAIN_ENTRY": entry},
                    on_done=lambda n, g, short=short: futures.append(pool.submit(
                        rs.run_eval, rs.final_ckpt(n), "test", a.rollouts,
                        os.path.join(TEST, f"{short}_nominal.json"), g))))
    S.wait_for(names)
    while futures:
        futures.pop().result()

    r = subprocess.run([rs.PY, os.path.join(rs.C, "curation/analysis/phase2_analysis.py"), "--tag", T, "--lib", a.lib,
                        "--sub", a.sub], cwd=rs.PG, capture_output=True, text=True)
    if r.returncode != 0:
        rs.log(f"ANALYSIS FAILED: {r.stderr[-800:]}")
        raise RuntimeError("analysis")
    open(os.path.join(OUT, "DONE"), "w").write(time.strftime("%Y-%m-%d %H:%M") + "\n")
    rs.log("DONE")


if __name__ == "__main__":
    main()
