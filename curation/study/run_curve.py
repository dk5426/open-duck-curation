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
       kinematic  the cheap filter: clips that pass the kinematic check first, in the same fixed random order as the
                  oracle, then failing ones by kinematic score (amended 11-15: ranking every clip by the kinematic score
                  rated held leans easier than clean gaits)
       oracle     the physics filter: clips the hold test can hold (or that have no held pose) first, in a fixed random
                  order (seed 0), then infeasible ones by increasing lean size
       random     a seeded uniform draw per training seed
       checked    every clip that passes the kinematic check, at its natural size (how the check is used in
                  practice; amended 11-15); trained and evaluated like the main fraction
     Every subset keeps at least one clip of each category val / test hold, by swapping its own best-ranked clip of a
     missing category in for its worst-ranked clip (the same rule for every selector, so sizes stay exact).
  4. finals: selector x fraction x seed (200M), plus full; test evaluation (10 rollouts): nominal for every run, push
     0.3 / 0.6 and friction x 0.6 for the main fraction and full; validation scores (5 rollouts) at the checkpoints
     nearest 25 / 50 / 75 / 100% of training for the main fraction and full (training cost)
  4b. --fstar (amended 11-16): every curated final on validation (final checkpoint, 10 rollouts, original score);
     f* = the fraction with the lowest mean over seeds, the main fraction if within 0.01 -> fstar.json
  4c. --strat (exploratory, amended 11-17 after interim results): curatedstrat at the main fraction and f*, the
     curated ranking with a proportional floor (each val / test category first keeps its best ceil(f x n) train clips)
  4d. --tn (exploratory, 11-19 after Phase 1): curatedtn at the main fraction, ranked by the type-normalised score from
     curation/analysis/score_candidates.py (needs results/<tag>/score_candidates/candidates.json)
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
STATIONARY = ("crouch", "bow", "sway", "head", "lean")  # one motion group for the type-normalised score


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


def stratified(ranked, n, cat, judged, frac):
    """Curation with a proportional floor (exploratory, amended 11-17): each judged category first keeps its best-ranked
    ceil(frac x its train clips), then the rest of the n slots are filled in global rank order."""
    keep = []
    for c in sorted(judged):
        mem = [i for i in ranked if cat[i] == c]
        keep += mem[:int(np.ceil(frac * len(mem)))]
    keep += [i for i in ranked if i not in keep][:max(0, n - len(keep))]
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
    p.add_argument("--fstar", action="store_true", help="after the finals, pick f* on validation (amendment 11-16)")
    p.add_argument("--strat", action="store_true", help="exploratory stratified curation at the main fraction and f*")
    p.add_argument("--tn", action="store_true", help="exploratory type-normalised curation at the main fraction "
                   "(ranking from score_candidates.py, or computed here from the scorers' val evaluations)")
    p.add_argument("--fixed-score", default=None, help="selection score fixed in advance (a library without feasibility "
                   "labels: no AUC validation)")
    p.add_argument("--no-extras", action="store_true", help="skip the checked and curatedscore conditions")
    p.add_argument("--tn-groups", choices=("stationary", "type"), default="stationary", help="type-normalised score: "
                   "motion groups (cv7: the stationary types and leans form one group; v9: every type its own group)")
    p.add_argument("--analysis", choices=("curve", "none"), default="curve", help="none: stop after training and test "
                   "evaluation (a study with its own analysis)")
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
    for m in (() if a.fixed_score else CANDIDATES):
        aucs = [auc([per[k][i][m] for i in tid], y) for k in per]
        rhos = [spearman([per[k][i][m] for i in tid], [per[j][i][m] for i in tid]) for k in per for j in per if k < j]
        val[m] = {"auc_per_scorer": aucs, "auc": float(np.mean(aucs)), "spearman_between_scorers": rhos}
    if a.fixed_score:
        sel = a.fixed_score
    else:
        best = max(v["auc"] for v in val.values())
        sel = "score" if val["score"]["auc"] >= best - AUC_TIE else max(val, key=lambda m: val[m]["auc"])
    ens = {i: float(np.mean([per[k][i][sel] for k in per])) for i in tid}
    json.dump({"candidates": val, "tie": AUC_TIE, "selection_score": sel, "ensemble": ens},
              open(os.path.join(OUT, "selection_validation.json"), "w"), indent=1)
    rs.log("selection validation: " + ", ".join(f"{m} AUC {v['auc']:.3f}" for m, v in val.items()) + f" -> {sel}")

    # 3. subsets
    byid = {c["id"]: c for c in train}
    lean = lambda i: abs(byid[i]["params"].get("dx_m", 0.0))  # noqa: E731
    rng0_order = list(np.random.default_rng(0).permutation(sorted(tid)))
    feas = [i for i in rng0_order if not infeasible[i]]
    ranked = {"curated": sorted(tid, key=lambda i: (ens[i], i)),
              "kinematic": [i for i in rng0_order if byid[i]["check"]["pass"]]
                           + sorted((i for i in tid if not byid[i]["check"]["pass"]), key=lambda i: (kinematic_score(byid[i]), i)),
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
                rs.log(f"subset {name}: {len(ids)} clips, clean {sum(cat[i] != 'lean' for i in ids)}, "
                       f"leans {sum(cat[i] == 'lean' for i in ids)}, "
                       f"measured infeasible {sum(infeasible[i] for i in ids)}/{sum(infeasible.values())}")

    checked = sorted(i for i in tid if byid[i]["check"]["pass"])
    cpath = os.path.join(SUB, "checked.json")
    json.dump(checked, open(cpath, "w"), indent=1)
    rs.log(f"subset checked: {len(checked)} clips, clean {sum(cat[i] != 'lean' for i in checked)}, "
           f"leans {sum(cat[i] == 'lean' for i in checked)}, measured infeasible {sum(infeasible[i] for i in checked)}")

    # label-free curation (amended 11-15): when validation picked another score, the main fraction is also curated by
    # the original score, which needs no feasibility labels, i.e. what a real user would run
    extra = {} if a.no_extras else {"checked": cpath}
    if sel != "score" and not a.no_extras:
        ens0 = {i: float(np.mean([per[k][i]["score"] for k in per])) for i in tid}
        ids = with_coverage(sorted(tid, key=lambda i: (ens0[i], i)), int(round(a.main / 100 * len(tid))), cat, judged)
        extra[f"curatedscore_f{a.main}"] = os.path.join(SUB, f"curatedscore_f{a.main}.json")
        json.dump(ids, open(extra[f"curatedscore_f{a.main}"], "w"), indent=1)
        rs.log(f"subset curatedscore_f{a.main}: {len(ids)} clips, clean {sum(cat[i] != 'lean' for i in ids)}, "
               f"leans {sum(cat[i] == 'lean' for i in ids)}, measured infeasible {sum(infeasible[i] for i in ids)}")

    # 4. finals
    for stem, path in extra.items():
        for seed in a.seeds:
            finals[(stem, None, seed)] = S.submit(f"{T}_{stem}_s{seed}", a.final_steps, prio=1, seed=seed, clips=path,
                                                  on_done=lambda n, g: evals(n, g, a.main))
    for f in a.fractions:
        for s_ in a.selectors:
            for seed in a.seeds:
                path = subsets[(s_, f, seed if s_ == "random" else None)]
                finals[(s_, f, seed)] = S.submit(f"{T}_{s_}_f{f}_s{seed}", a.final_steps, prio=1 if f == a.main else 3,
                                                 seed=seed, clips=path, on_done=lambda n, g, f=f: evals(n, g, f))
    S.wait_for(list(finals.values()))
    while futures:
        futures.pop().result()

    # 4b. f* (amendment 11-16): curated's best keep-fraction on validation, final checkpoint, 10 rollouts, original score
    fstar = None
    if a.fstar:
        vm = {}
        for f in a.fractions:
            per_seed = []
            for seed in a.seeds:
                out = os.path.join(VAL, f"fstar_curated_f{f}_s{seed}.json")
                rs.run_eval(rs.final_ckpt(f"{T}_curated_f{f}_s{seed}"), "val", a.rollouts, out, a.gpus[0])
                per_seed.append(float(np.mean([v["score"] for v in json.load(open(out))["clips"].values()])))
            vm[f] = per_seed
        best = min(a.fractions, key=lambda f: np.mean(vm[f]))
        fstar = a.main if np.mean(vm[a.main]) <= np.mean(vm[best]) + 0.01 else best
        json.dump({"val_e_per_seed": vm, "best": best, "tie": 0.01, "fstar": fstar},
                  open(os.path.join(OUT, "fstar.json"), "w"), indent=1)
        rs.log("f*: " + ", ".join(f"{f}% val e {np.mean(v):.3f}" for f, v in vm.items()) + f" -> f* = {fstar}%")

    # 4c. exploratory (amended 11-17, after interim results): curation with a proportional per-category floor
    if a.strat:
        strat = {}
        for f in sorted({a.main, *([fstar] if fstar else [])}):
            ids = stratified(ranked["curated"], int(round(f / 100 * len(tid))), cat, judged, f / 100)
            path = os.path.join(SUB, f"curatedstrat_f{f}.json")
            json.dump(ids, open(path, "w"), indent=1)
            rs.log(f"subset curatedstrat_f{f}: {len(ids)} clips, clean {sum(cat[i] != 'lean' for i in ids)}, "
                   f"leans {sum(cat[i] == 'lean' for i in ids)}, measured infeasible {sum(infeasible[i] for i in ids)}")
            for seed in a.seeds:
                strat[(f, seed)] = S.submit(f"{T}_curatedstrat_f{f}_s{seed}", a.final_steps, prio=1, seed=seed,
                                            clips=path, on_done=lambda n, g: evals(n, g, a.main))
        S.wait_for(list(strat.values()))
        while futures:
            futures.pop().result()

    # 4d. exploratory (11-19, after Phase 1): curation by the type-normalised score (score_candidates.py, candidate
    # "1. typenorm_val": score_v3 over the median of the clip's motion group's clean val clips), same coverage rule
    if a.tn:
        cpath_ = os.path.join(OUT, "score_candidates", "candidates.json")
        if os.path.exists(cpath_):
            tnr = json.load(open(cpath_))["1. typenorm_val"]
        else:  # the same definition as score_candidates.py, from each scorer's final checkpoint on the val clips
            vids = [c["id"] for c in man["clips"] if c["split"] == "val"]
            grp = (lambda i: cat[i]) if a.tn_groups == "type" else (  # noqa: E731
                lambda i: "stationary" if cat[i] in STATIONARY else cat[i])
            os.makedirs(os.path.join(OUT, "score_candidates"), exist_ok=True)
            tn_per = []
            for k, name in zip(a.score_seeds, scorers):
                f = os.path.join(OUT, "score_candidates", f"scores_val_s{k}_final.json")
                rs.run_eval(rs.final_ckpt(name), "val", a.rollouts, f, a.gpus[0])
                vv = json.load(open(f))["clips"]
                med = {g: float(np.median([vv[i]["score_v3"] for i in vids if grp(i) == g])) for g in {grp(i) for i in vids}}
                tn_per.append({i: per[k][i]["score_v3"] / med[grp(i)] for i in tid})
            tnr = {i: float(np.mean([t[i] for t in tn_per])) for i in tid}
            json.dump(tnr, open(os.path.join(OUT, "score_candidates", "typenorm_val.json"), "w"), indent=1)
        ids = with_coverage(sorted(tid, key=lambda i: (tnr[i], i)), int(round(a.main / 100 * len(tid))), cat, judged)
        path = os.path.join(SUB, f"curatedtn_f{a.main}.json")
        json.dump(ids, open(path, "w"), indent=1)
        rs.log(f"subset curatedtn_f{a.main}: {len(ids)} clips, clean {sum(cat[i] != 'lean' for i in ids)}, "
               f"leans {sum(cat[i] == 'lean' for i in ids)}, measured infeasible {sum(infeasible[i] for i in ids)}")
        tn = [S.submit(f"{T}_curatedtn_f{a.main}_s{seed}", a.final_steps, prio=1, seed=seed, clips=path,
                       on_done=lambda n, g: evals(n, g, a.main)) for seed in a.seeds]
        S.wait_for(tn)
        while futures:
            futures.pop().result()

    if a.analysis == "none":
        open(os.path.join(OUT, "DONE"), "w").write(time.strftime("%Y-%m-%d %H:%M") + "\n")
        rs.log("DONE (training and test evaluation; analysis is separate)")
        return

    # 5. analysis
    r = subprocess.run([rs.PY, os.path.join(rs.C, "curation/analysis/curve_analysis.py"), "--tag", T, "--lib", a.lib,
                        "--fractions", *map(str, a.fractions), "--main", str(a.main), "--selectors", *a.selectors,
                        "--seeds", *map(str, a.seeds)], cwd=rs.PG, capture_output=True, text=True)
    if r.returncode != 0:
        rs.log(f"ANALYSIS FAILED: {r.stderr[-800:]}")
        raise RuntimeError("analysis")
    r = subprocess.run([rs.PY, os.path.join(rs.C, "curation/analysis/mechanism.py"), "--tag", T, "--lib", a.lib,
                        "--fractions", *map(str, a.fractions), "--seeds", *map(str, a.seeds)],
                       cwd=rs.PG, capture_output=True, text=True)
    if r.returncode != 0:
        rs.log(f"MECHANISM ANALYSIS FAILED (non-fatal): {r.stderr[-800:]}")
    open(os.path.join(OUT, "DONE"), "w").write(time.strftime("%Y-%m-%d %H:%M") + "\n")
    rs.log("DONE")


if __name__ == "__main__":
    main()
