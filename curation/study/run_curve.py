"""PREREG v2 confirmatory study: tracking quality and training cost against training-set size, per clip selector.

  OPENDUCK_ROOT=<dir> python3 run_curve.py --gpus 1 2 --tag cv7 --lib data/clips_v7

Steps (each skipped if its output exists, so the driver can be restarted):
  1. three scoring policies (seeds 0/1/2, every train clip, 300M); the full condition (seeds 0/1/2, 200M) fills GPUs
  2. every train clip scored by each scoring policy (10 rollouts); selection_validation.json: for each candidate
     score (score, score_v2, score_v3, fall rate), the AUC for separating the measured-infeasible train clips from the
     rest (mean over the three scorers) and the ranking's stability across scorers (Spearman). The selection score is
     the candidate with the highest mean AUC; within 0.02 of the best, the original `score` wins. Ensemble = mean of the
     three scorers' values.
  3. subsets at each keep-fraction (round(f * train clips)):
       curated    lowest ensemble selection score first
       kinematic  lowest kinematic score first (select_subsets.kinematic_score)
       oracle     the physics filter: clips the hold test can hold (or that have no held pose) first, in a fixed random
                  order (seed 0), then infeasible ones by increasing lean size
       random     a seeded uniform draw per training seed
     Every subset keeps at least one clip of each category val / test hold, by swapping its own best-ranked clip of a
     missing category in for its worst-ranked clip (the same rule for every selector, so sizes stay exact).
  4. finals: selector x fraction x seed (200M), plus full; test evaluation (10 rollouts): nominal for every run, push
     0.3 / 0.6 and friction x 0.6 for the main fraction and full; validation scores (5 rollouts) at the checkpoints
     nearest 25 / 50 / 75 / 100% of training for the main fraction and full (training cost)
  5. analysis: curation/analysis/curve_analysis.py -> SUMMARY.md, DONE
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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "select"))
import run_study as rs  # noqa: E402
from select_subsets import kinematic_score  # noqa: E402

FRACTIONS = (40, 55, 70, 85)
MAIN = 55
SELECTORS = ("curated", "kinematic", "oracle", "random")
CANDIDATES = ("score", "score_v2", "score_v3", "fall_rate")
AUC_TIE = 0.02


def auc(x, y):
    """Probability that a random infeasible clip (y = 1) scores higher than a random feasible one (ties count half)."""
    x, y = np.asarray(x, float), np.asarray(y, bool)
    pos, neg = x[y], x[~y]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(((pos[:, None] > neg[None]) + 0.5 * (pos[:, None] == neg[None])).mean())


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def with_coverage(ranked, n, cat, judged):
    """First n of `ranked`, then for each judged category with no clip, swap in its best-ranked clip for the
    worst-ranked clip whose category keeps another member."""
    keep = list(ranked[:n])
    for c in sorted(judged):
        if any(cat[i] == c for i in keep):
            continue
        best = next((i for i in ranked if cat[i] == c), None)
        if best is None:
            continue
        for j in range(len(keep) - 1, -1, -1):
            if sum(cat[k] == cat[keep[j]] for k in keep) > 1:
                keep[j] = best
                break
    return sorted(keep)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gpus", type=int, nargs="+", required=True)
    p.add_argument("--tag", default="cv7")
    p.add_argument("--lib", required=True)
    p.add_argument("--fractions", type=int, nargs="+", default=list(FRACTIONS))
    p.add_argument("--main", type=int, default=MAIN)
    p.add_argument("--selectors", nargs="+", default=list(SELECTORS))
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    p.add_argument("--score-seeds", type=int, nargs="+", default=[0, 1, 2])
    p.add_argument("--score-steps", type=int, default=300_000_000)
    p.add_argument("--final-steps", type=int, default=200_000_000)
    p.add_argument("--rollouts", type=int, default=10)
    a = p.parse_args()
    a.lib = os.path.abspath(a.lib)
    rs.a = argparse.Namespace(lib=a.lib)
    T = a.tag
    OUT = rs.OUT = os.path.join(rs.C, "results", T)
    SUB, TEST, VAL = (os.path.join(OUT, x) for x in ("subsets", "test", "val_ckpts"))
    for d in (OUT, SUB, TEST, VAL, os.path.join(OUT, "launch")):
        os.makedirs(d, exist_ok=True)
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    train = [c for c in man["clips"] if c["split"] == "train"]
    tid = [c["id"] for c in train]
    cat = {c["id"]: c["category"] for c in man["clips"]}
    judged = {c["category"] for c in man["clips"] if c["split"] in ("val", "test")}
    infeasible = {c["id"]: bool(c["feasibility"]["infeasible"]) for c in train}
    rs.log(f"curve study {T}: library {a.lib}, {len(tid)} train clips ({sum(infeasible.values())} measured infeasible), "
           f"fractions {a.fractions}, selectors {a.selectors}, seeds {a.seeds}, GPUs {a.gpus}")
    S = rs.Scheduler(a.gpus)
    pool = ThreadPoolExecutor(max_workers=len(a.gpus))
    futures = []

    def evals(name, gpu, frac):
        ck = rs.final_ckpt(name)
        tests = rs.TESTS if frac in (a.main, None) else rs.TESTS[:1]
        short = name[len(T) + 1:]
        futures.append(pool.submit(lambda: [rs.run_eval(ck, "test", a.rollouts, os.path.join(TEST, f"{short}_{t}.json"),
                                                         gpu, extra) for t, extra in tests]))
        if frac in (a.main, None):
            d = os.path.join(rs.RUNS, name)
            cks = sorted((x for x in os.listdir(d) if x[:4].isdigit() and not x.endswith(".onnx")),
                         key=lambda x: int(x.rsplit("_", 1)[1]))
            steps = np.array([int(x.rsplit("_", 1)[1]) for x in cks])
            picks = sorted({int(np.argmin(np.abs(steps - q * steps[-1]))) for q in (0.25, 0.5, 0.75, 1.0)})
            futures.append(pool.submit(lambda: [rs.run_eval(os.path.join(d, cks[k]), "val", 5,
                                                             os.path.join(VAL, f"{short}_{steps[k]}.json"), gpu)
                                                 for k in picks]))

    # 1. scoring policies; full fills the GPUs meanwhile
    scorers = [S.submit(f"{T}_score_s{k}", a.score_steps, prio=0, seed=k) for k in a.score_seeds]
    finals = {("full", None, s): S.submit(f"{T}_full_s{s}", a.final_steps, prio=2, seed=s,
                                          on_done=lambda n, g: evals(n, g, None)) for s in a.seeds}
    S.wait_for(scorers)

    # 2. score every train clip with each scorer; validate the candidate selection scores
    S.tick()
    per = {}
    for k, name in zip(a.score_seeds, scorers):
        f = os.path.join(OUT, f"scores_train_s{k}.json")
        rs.run_eval(rs.final_ckpt(name), "train", a.rollouts, f, a.gpus[0])
        sc = json.load(open(f))["clips"]
        for v in sc.values():
            v["fall_rate"] = v["falls"] / v["rollouts"]
        per[k] = sc
    y = [infeasible[i] for i in tid]
    val = {}
    for m in CANDIDATES:
        aucs = [auc([per[k][i][m] for i in tid], y) for k in per]
        rhos = [spearman([per[k][i][m] for i in tid], [per[j][i][m] for i in tid]) for k in per for j in per if k < j]
        val[m] = {"auc_per_scorer": aucs, "auc": float(np.mean(aucs)), "spearman_between_scorers": rhos}
    best = max(v["auc"] for v in val.values())
    sel = "score" if val["score"]["auc"] >= best - AUC_TIE else max(val, key=lambda m: val[m]["auc"])
    ens = {i: float(np.mean([per[k][i][sel] for k in per])) for i in tid}
    json.dump({"candidates": val, "tie": AUC_TIE, "selection_score": sel, "ensemble": ens},
              open(os.path.join(OUT, "selection_validation.json"), "w"), indent=1)
    rs.log("selection validation: " + ", ".join(f"{m} AUC {v['auc']:.3f}" for m, v in val.items()) + f" -> {sel}")

    # 3. subsets
    byid = {c["id"]: c for c in train}
    lean = lambda i: abs(byid[i]["params"].get("dx_m", 0.0))  # noqa: E731
    rng0 = np.random.default_rng(0)
    feas = [i for i in rng0.permutation(sorted(tid)) if not infeasible[i]]
    ranked = {"curated": sorted(tid, key=lambda i: (ens[i], i)),
              "kinematic": sorted(tid, key=lambda i: (kinematic_score(byid[i]), i)),
              "oracle": feas + sorted((i for i in tid if infeasible[i]), key=lambda i: (lean(i), i))}
    subsets = {}
    for f in a.fractions:
        n = int(round(f / 100 * len(tid)))
        for s_ in a.selectors:
            for seed in (a.seeds if s_ == "random" else [None]):
                order = list(np.random.default_rng(1000 + seed).permutation(sorted(tid))) if s_ == "random" else ranked[s_]
                ids = with_coverage(order, n, cat, judged)
                name = f"{s_}_f{f}" + (f"_s{seed}" if seed is not None else "")
                path = os.path.join(SUB, name + ".json")
                json.dump(ids, open(path, "w"), indent=1)
                subsets[(s_, f, seed)] = path
                rs.log(f"subset {name}: {len(ids)} clips, leans {sum(cat[i] == 'lean' for i in ids)}, "
                       f"measured infeasible {sum(infeasible[i] for i in ids)}/{sum(infeasible.values())}")

    # 4. finals
    for f in a.fractions:
        for s_ in a.selectors:
            for seed in a.seeds:
                path = subsets[(s_, f, seed if s_ == "random" else None)]
                finals[(s_, f, seed)] = S.submit(f"{T}_{s_}_f{f}_s{seed}", a.final_steps, prio=1 if f == a.main else 3,
                                                 seed=seed, clips=path, on_done=lambda n, g, f=f: evals(n, g, f))
    S.wait_for(list(finals.values()))
    while futures:
        futures.pop().result()

    # 5. analysis
    r = subprocess.run([rs.PY, os.path.join(rs.C, "curation/analysis/curve_analysis.py"), "--tag", T, "--lib", a.lib,
                        "--fractions", *map(str, a.fractions), "--main", str(a.main), "--selectors", *a.selectors,
                        "--seeds", *map(str, a.seeds)], cwd=rs.PG, capture_output=True, text=True)
    if r.returncode != 0:
        rs.log(f"ANALYSIS FAILED: {r.stderr[-800:]}")
        raise RuntimeError("analysis")
    open(os.path.join(OUT, "DONE"), "w").write(time.strftime("%Y-%m-%d %H:%M") + "\n")
    rs.log("DONE")


if __name__ == "__main__":
    main()
