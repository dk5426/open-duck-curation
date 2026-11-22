"""PREREG v3 Phase 2 v2 (amendment 2026-11-22): every learner under one contract, equal tuning, a competence gate.

  OPENDUCK_ROOT=<dir> python3 run_phase2v2.py --gpus 1 2 --tag cv9 --lib data/clips_v9 --test-lib data/clips_v9x \
      [--learners ppo fasttd3 fastsac ars dagger] [--stage tune|gate|main|all]

Contract: the Phase 1 env, reward, randomization, clip lists and feed-forward action for every learner; critics see
privileged_state (train_alt.py). Stages, each skipped where its outputs exist (the driver can be restarted):
  tune  each learner's 4 configurations (results/<tag>/phase2v2/tuning.json, fixed before any tuning run) on full,
        seed 0, at the learner's calibrated wall-clock steps; val evaluation (10 rollouts). PPO's Phase 1
        configuration is PPO's "base" and its run is cv9_full_s0 itself.
  gate  per learner, the configuration with the lowest mean val score; competent if val score <= GATE_E x PPO's best
        and val fall rate <= GATE_FALL (gate.json). A learner that fails gets one run at BUDGET_X x its steps (full,
        seed 0, best configuration) with a val evaluation, to show whether it is budget-bound.
  main  competent learners on full and curated / curatedtn / kinematic / random at f* (the Phase 1 subset files),
        seeds 0-2, with test evaluations (nominal and --dr, 10 rollouts) on --test-lib's test clips. PPO reuses its
        Phase 1 runs when "base" wins; DAgger's teacher is the PPO row's run of the same condition and seed.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_study as rs  # noqa: E402

LEARNERS = ("ppo", "fasttd3", "fastsac", "ars", "dagger")
CONDS = ("full", "curated", "curatedtn", "kinematic", "random")
GATE_E, GATE_FALL, BUDGET_X = 2.0, 0.2, 4


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gpus", type=int, nargs="+", required=True)
    p.add_argument("--tag", default="cv9")
    p.add_argument("--lib", required=True, help="training library (train / val clips)")
    p.add_argument("--test-lib", required=True, help="library whose test clips are evaluated (clips_v9x)")
    p.add_argument("--learners", nargs="+", default=list(LEARNERS))
    p.add_argument("--stage", default="all", choices=["tune", "gate", "main", "all"])
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    p.add_argument("--rollouts", type=int, default=10)
    a = p.parse_args()
    a.lib, a.test_lib = os.path.abspath(a.lib), os.path.abspath(a.test_lib)
    rs.a = argparse.Namespace(lib=a.lib)
    T = a.tag
    P1 = os.path.join(rs.C, "results", T)
    OUT = rs.OUT = os.path.join(P1, "phase2v2")
    for d in ("tune", "budget", "test", "launch"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    f = json.load(open(os.path.join(P1, "fstar.json")))["fstar"]
    steps = json.load(open(os.path.join(P1, "phase2_calibration.json")))["steps"]
    steps["ppo"] = steps["ppo_noff"]  # the Phase 1 PPO run length is the budget itself
    tuning = json.load(open(os.path.join(OUT, "tuning.json")))
    entry = os.path.join(rs.C, "curation", "study", "train_alt.py")
    S = rs.Scheduler(a.gpus)
    pool = ThreadPoolExecutor(max_workers=len(a.gpus))
    futures = []

    def evaluate(run, clips, lib, out, gpu, extra=()):
        if os.path.exists(out):
            return
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), XLA_PYTHON_CLIENT_PREALLOCATE="false", CURATION_LIBRARY=lib)
        r = subprocess.run([rs.PY, os.path.join(rs.C, "curation/eval/eval_clips.py"), "--ckpt", rs.final_ckpt(run),
                            "--clips", clips, "--rollouts", str(a.rollouts), *extra, "--out", out], cwd=rs.PG, env=env,
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            rs.log(f"EVAL FAILED {out}: {r.stderr[-800:]}")
            raise RuntimeError(out)
        rs.log(f"eval {os.path.basename(out)}")

    def subset(cond, seed):
        if cond == "full":
            return None
        return os.path.join(P1, "subsets", f"{cond}_f{f}" + (f"_s{seed}" if cond == "random" else "") + ".json")

    def submit(name, learner, cfg, n_steps, cond, seed, teacher=None, on_done=None, prio=0):
        if learner == "ppo":  # Phase 1's trainer itself
            env = {"PPO_OVERRIDES_JSON": json.dumps({**cfg, "seed": seed})}
            args = []
        else:
            env = {"TRAIN_ENTRY": entry, "ALT_OVERRIDES_JSON": json.dumps(cfg)}
            args = ["--learner", learner] + (["--teacher", rs.final_ckpt(teacher)] if teacher else [])
        return S.submit(name, n_steps, prio=prio, seed=seed, clips=subset(cond, seed), args=args, env=env,
                        on_done=on_done)

    def val_stats(path):
        c = json.load(open(path))["clips"]
        return float(np.mean([v["score"] for v in c.values()])), float(np.mean([v["falls"] / v["rollouts"] for v in c.values()]))

    def tune_run(lr, cfg_name):
        return f"{T}_full_s0" if (lr == "ppo" and cfg_name == "base") else f"{T}_p2v2_tune_{lr}_{cfg_name}"

    def val_path(lr, cfg_name):
        return os.path.join(OUT, "tune", f"{lr}_{cfg_name}_val.json")

    # ------------------------------------------------------------------ tune
    if a.stage in ("tune", "all"):
        names = []
        for li, lr in enumerate(a.learners):
            for cfg_name, cfg in tuning[lr].items():
                run = tune_run(lr, cfg_name)
                teacher = f"{T}_full_s0" if lr == "dagger" else None
                done = lambda n, g, lr=lr, cfg_name=cfg_name: futures.append(pool.submit(  # noqa: E731
                    evaluate, n, "val", a.lib, val_path(lr, cfg_name), g))
                names.append(submit(run, lr, cfg, steps[lr], "full", 0, teacher, done, prio=li))
        S.wait_for(names)
        while futures:
            futures.pop().result()

    # ------------------------------------------------------------------ gate
    gate_f = os.path.join(OUT, "gate.json")
    if a.stage in ("gate", "all"):
        gate = {}
        for lr in tuning:
            got = {c: val_stats(val_path(lr, c)) for c in tuning[lr] if os.path.exists(val_path(lr, c))}
            if len(got) < len(tuning[lr]):
                rs.log(f"gate: {lr} has {len(got)}/{len(tuning[lr])} tuning evaluations; skipped")
                continue
            best = min(got, key=lambda c: got[c][0])
            gate[lr] = {"configs": {c: {"val_e": e, "val_fall_rate": fr} for c, (e, fr) in got.items()}, "best": best,
                        "val_e": got[best][0], "val_fall_rate": got[best][1]}
        ref = gate["ppo"]["val_e"]
        for lr, g in gate.items():
            g["competent"] = bool(g["val_e"] <= GATE_E * ref and g["val_fall_rate"] <= GATE_FALL)
        json.dump({"rule": f"val e <= {GATE_E} x PPO's best val e ({ref:.3f}) and val fall rate <= {GATE_FALL}",
                   "learners": gate}, open(gate_f, "w"), indent=1)
        rs.log("gate: " + ", ".join(f"{lr} {g['best']} e {g['val_e']:.3f} falls {g['val_fall_rate']:.2f} "
                                     f"{'PASS' if g['competent'] else 'FAIL'}" for lr, g in gate.items()))
        names = []
        for li, (lr, g) in enumerate(gate.items()):
            if g["competent"] or lr not in a.learners:
                continue
            run = f"{T}_p2v2_budget{BUDGET_X}x_{lr}"
            teacher = f"{T}_full_s0" if lr == "dagger" else None
            done = lambda n, g_, lr=lr: futures.append(pool.submit(  # noqa: E731
                evaluate, n, "val", a.lib, os.path.join(OUT, "budget", f"{lr}_val.json"), g_))
            names.append(submit(run, lr, tuning[lr][g["best"]], BUDGET_X * steps[lr], "full", 0, teacher, done, prio=li))
        S.wait_for(names)
        while futures:
            futures.pop().result()

    # ------------------------------------------------------------------ main
    if a.stage in ("main", "all"):
        gate = json.load(open(gate_f))["learners"]
        ppo_base = gate["ppo"]["best"] == "base"

        def row_run(lr, cond, seed):
            if lr == "ppo" and ppo_base:
                return f"{T}_full_s{seed}" if cond == "full" else f"{T}_{cond}_f{f}_s{seed}"
            if cond == "full" and seed == 0:
                return tune_run(lr, gate[lr]["best"])
            return f"{T}_p2v2_{lr}_{cond}_s{seed}"

        names = []
        order = ["ppo"] + [lr for lr in a.learners if lr != "ppo"]  # DAgger needs its PPO teachers first
        for li, lr in enumerate(order):
            if not gate.get(lr, {}).get("competent"):
                continue
            for cond in CONDS:
                for seed in a.seeds:
                    run = row_run(lr, cond, seed)
                    teacher = row_run("ppo", cond, seed) if lr == "dagger" else None
                    if teacher and not rs.finished(teacher):
                        S.wait_for([teacher])

                    def done(n, g, lr=lr, cond=cond, seed=seed):
                        for extra, kind in (((), "nominal"), (("--dr",), "dr")):
                            futures.append(pool.submit(evaluate, n, "test", a.test_lib, os.path.join(
                                OUT, "test", f"{lr}_{cond}_s{seed}_{kind}.json"), g, extra))
                    names.append(submit(run, lr, tuning[lr][gate[lr]["best"]], steps[lr], cond, seed, teacher, done,
                                        prio=li))
        S.wait_for(names)
        while futures:
            futures.pop().result()
        open(os.path.join(OUT, "DONE"), "w").write(time.strftime("%Y-%m-%d %H:%M") + "\n")
        rs.log("DONE (phase 2 v2 training and test evaluation)")


if __name__ == "__main__":
    main()
