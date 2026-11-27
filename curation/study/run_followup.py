"""PREREG v3 contamination follow-up (amendment 2026-11-23): broken share 0 / 23 / 50 / 75% on the same clean clips.

  OPENDUCK_ROOT=<dir> python3 run_followup.py --gpus 1 2 --stage harm

Stage harm: PPO (Phase 1 base configuration, 200M steps, seed 0) on every clip of clips_v9c50 and clips_v9c75, val
evaluation (10 rollouts, original score), and the harm check against the dose check's clean-only run on the same val
clips: a level goes on only if val e(full) - val e(clean-only) >= HARM (results/<tag>/followup/harm.json).
Stage budget (amendment 2026-11-25): the same check on clips_v9c75 at BUDGETS env steps, full against clean-only
trained at the same budget (results/<tag>/followup/budget_harm.json).
Stage systematic (amendment 2026-11-25): the same check on clips_v9s at 200M, full (42 clean + 42 wrong) against its
42 clean clips (results/<tag>/followup/systematic_harm.json).
Stage signal (amendment 2026-11-25): full on clips_v9v (84 clean + 84 copies with inconsistent signals) at 200M against
the dose check's clean-only run on the same 84 clean clips (results/<tag>/followup/signal_harm.json).
Stage knee (amendment 2026-11-25): the 78 clean clips without the backward-knee ones against all 84
(results/<tag>/followup/knee_harm.json).
Stage alias (amendment 2026-11-26): as signal, on clips_v9a (84 clean + 84 copies the policy cannot tell from them that
reward other feet keypoints and contacts), plus both runs on the 168 test clips (results/<tag>/followup/alias_harm.json).
Stage aliascur (amendment 2026-11-27): the alias run scores every clips_v9a train clip; type-normalised curation and a
random draw each keep 84 of 168; test e(random) - test e(curatedtn) with a 97.5% clip-bootstrap CI
(results/<tag>/followup/alias_curation.json).
Skipped where
outputs exist, so the driver can be restarted.
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

LEVELS = {"c50": "data/clips_v9c50", "c75": "data/clips_v9c75"}
HARM = 0.10
BUDGETS = (25_000_000, 50_000_000)
KNEE_FRAMES = 20  # backward knee: either knee < 0 rad on at least this many frames


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gpus", type=int, nargs="+", required=True)
    p.add_argument("--tag", default="cv9")
    p.add_argument("--stage", default="harm", choices=["harm", "budget", "systematic", "signal", "knee", "alias", "aliascur"])
    p.add_argument("--steps", type=int, default=200_000_000)
    p.add_argument("--rollouts", type=int, default=10)
    a = p.parse_args()
    P1 = os.path.join(rs.C, "results", a.tag)
    OUT = rs.OUT = os.path.join(P1, "followup")
    for d in ("val", "test", "launch"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    libs = {k: os.path.join(rs.C, v) for k, v in LEVELS.items()}
    rs.a = argparse.Namespace(lib=libs["c50"])  # each job sets its own CURATION_LIBRARY
    S = rs.Scheduler(a.gpus)
    pool = ThreadPoolExecutor(max_workers=len(a.gpus))
    futures = []

    def evaluate(run, lib, out, gpu, clips="val"):
        if os.path.exists(out):
            return
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), XLA_PYTHON_CLIENT_PREALLOCATE="false", CURATION_LIBRARY=lib)
        r = subprocess.run([rs.PY, os.path.join(rs.C, "curation/eval/eval_clips.py"), "--ckpt", rs.final_ckpt(run),
                            "--clips", clips, "--rollouts", str(a.rollouts), "--out", out], cwd=rs.PG, env=env,
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            rs.log(f"EVAL FAILED {out}: {r.stderr[-800:]}")
            raise RuntimeError(out)
        rs.log(f"eval {os.path.basename(out)}")

    def val_e(path):
        return float(np.mean([v["score"] for v in json.load(open(path))["clips"].values()]))

    if a.stage == "aliascur":
        sys.path.insert(0, os.path.join(rs.C, "curation", "analysis"))
        import compare_conditions as cc
        from run_curve import with_coverage
        lib = os.path.join(rs.C, "data", "clips_v9a")
        man = json.load(open(os.path.join(lib, "manifest.json")))
        cat = {c["id"]: c["category"] for c in man["clips"]}
        copy = {c["id"]: c.get("generator") == "aliased" for c in man["clips"]}
        tid = sorted(c["id"] for c in man["clips"] if c["split"] == "train")
        judged = {c["category"] for c in man["clips"] if c["split"] in ("val", "test")}
        # scorer: the alias stage's run on all 168 train clips; type-normalised score as Phase 1 (score_v3 over the
        # median of the clean val clips of the clip's type, the scorer's own val evaluation)
        scorer, sc = f"{a.tag}f_v9a_full_s0", os.path.join(OUT, "scores", "v9a_train_s0.json")
        os.makedirs(os.path.dirname(sc), exist_ok=True)
        evaluate(scorer, lib, sc, a.gpus[0], "train")
        tr, vv = json.load(open(sc))["clips"], json.load(open(os.path.join(OUT, "val", "v9a_full_s0.json")))["clips"]
        med = {t: float(np.median([v["score_v3"] for i, v in vv.items() if cat[i] == t])) for t in judged}
        tn = {i: tr[i]["score_v3"] / med[cat[i]] for i in tid}
        n = len(tid) // 2
        subs = {"tn50": with_coverage(sorted(tid, key=lambda i: (tn[i], i)), n, cat, judged),
                "rand50": with_coverage(list(np.random.default_rng(1000).permutation(tid)), n, cat, judged)}
        val, test, names = {}, {}, []
        for k, ids in subs.items():
            path = os.path.join(OUT, f"v9a_{k}.json")
            json.dump(ids, open(path, "w"), indent=1)
            rs.log(f"subset v9a_{k}: {len(ids)} clips, aliased copies {sum(copy[i] for i in ids)}/84")
            val[k], test[k] = os.path.join(OUT, "val", f"v9a_{k}_s0.json"), os.path.join(OUT, "test", f"v9a_{k}_s0.json")

            def done(nm, g, k=k):
                futures.append(pool.submit(evaluate, nm, lib, val[k], g))
                futures.append(pool.submit(evaluate, nm, lib, test[k], g, "test"))
            names.append(S.submit(f"{a.tag}f_v9a_{k}_s0", a.steps, prio=0, seed=0, clips=path,
                                  env={"CURATION_LIBRARY": lib}, on_done=done))
        S.wait_for(names)
        while futures:
            futures.pop().result()
        # references already run: all 168 (alias stage) and the 84 clean clips (the dose check's clean-only run)
        val.update(full=os.path.join(OUT, "val", "v9a_full_s0.json"), clean=os.path.join(P1, "dose", "val_cv9_dose_clean_s0.json"))
        test.update(full=os.path.join(OUT, "test", "v9a_full_s0.json"), clean=os.path.join(OUT, "test", "knee84_s0.json"))
        cc.CI = 97.5
        rng = np.random.default_rng(0)
        res = {"copies_kept": {k: sum(copy[i] for i in ids) for k, ids in subs.items()}, "n_clips": n}
        for split, files in (("test", test), ("val", val)):
            R = {k: json.load(open(f))["clips"] for k, f in files.items()}
            ids = sorted(R["tn50"])
            for m in ("score", "keypoints"):
                res[f"{split}_{m}"] = {k: float(np.mean([r[i][m] for i in ids])) for k, r in R.items()}
                lo, hi = cc.boot_ci([[R["rand50"][i][m]] for i in ids], [[R["tn50"][i][m]] for i in ids], rng)
                res[f"{split}_{m}_random_minus_curatedtn"] = {"mean": res[f"{split}_{m}"]["rand50"] - res[f"{split}_{m}"]["tn50"],
                                                              "ci97.5": [lo, hi]}
        d = res["test_score_random_minus_curatedtn"]
        res["curation_helps"] = bool(d["ci97.5"][0] > 0)
        json.dump({"rule": "curation helps if the 97.5% clip-bootstrap CI of test e(random) - test e(curatedtn) is above 0",
                   "library": "clips_v9a", **res, "time": time.strftime("%Y-%m-%d %H:%M")},
                  open(os.path.join(OUT, "alias_curation.json"), "w"), indent=1)
        rs.log(f"alias curation: test e random {res['test_score']['rand50']:.3f} curatedtn {res['test_score']['tn50']:.3f} "
               f"diff {d['mean']:+.3f} CI [{d['ci97.5'][0]:+.3f}, {d['ci97.5'][1]:+.3f}] "
               f"{'HELPS' if res['curation_helps'] else 'no gain'}; copies kept {res['copies_kept']}")
        return

    if a.stage == "knee":
        lib = os.path.join(rs.C, "data", "clips_v9x")
        man, arr = json.load(open(os.path.join(lib, "manifest.json"))), np.load(os.path.join(lib, "library.npz"))
        K = [man["joints"].index(j) for j in ("left_knee", "right_knee")]
        knee = {c["id"] for c in man["clips"] if not c.get("contaminant")
                and ((arr["q"][c["index"], :c["length"]][:, K] < 0).any(1).sum() >= KNEE_FRAMES)}
        clean = json.load(open(os.path.join(P1, "dose", "clean_only.json")))
        ids = os.path.join(OUT, "knee_removed.json")
        json.dump(sorted(set(clean) - knee), open(ids, "w"), indent=1)
        runs = {"78": f"{a.tag}f_knee78_s0", "84": f"{a.tag}_dose_clean_s0"}
        out = {(k, s): os.path.join(OUT, s, f"knee{k}_s0.json") for k in runs for s in ("val", "test")}
        os.makedirs(os.path.join(OUT, "test"), exist_ok=True)
        jobs = [(runs["84"], out[("84", "test")], "test")]  # the dose run's val evaluation already exists
        done = lambda n, g: [futures.append(pool.submit(evaluate, n, lib, out[("78", s)], g, s))  # noqa: E731
                             for s in ("val", "test")]
        name = S.submit(runs["78"], a.steps, prio=0, seed=0, clips=ids, env={"CURATION_LIBRARY": lib}, on_done=done)
        for run, o, s in jobs:
            futures.append(pool.submit(evaluate, run, lib, o, a.gpus[-1], s))
        S.wait_for([name])
        while futures:
            futures.pop().result()
        out[("84", "val")] = os.path.join(P1, "dose", "val_cv9_dose_clean_s0.json")

        def e(path, keep):
            c = json.load(open(path))["clips"]
            return float(np.mean([v["score"] for i, v in c.items() if keep(i)]))

        res = {k: {"val_e_clean": e(out[(k, "val")], lambda i: i not in knee),
                   "test_e_clean": e(out[(k, "test")], lambda i: i not in knee),
                   "test_e_knee": e(out[(k, "test")], lambda i: i in knee)} for k in runs}
        harm = res["84"]["val_e_clean"] - res["78"]["val_e_clean"]
        json.dump({"rule": f"val e(84) - val e(78), val without backward-knee clips, >= {HARM}",
                   "backward_knee": {"criterion": f"either knee < 0 rad on >= {KNEE_FRAMES} frames",
                                     "ids": sorted(knee)}, "runs": res, "harm": harm, "passes": bool(harm >= HARM),
                   "time": time.strftime("%Y-%m-%d %H:%M")}, open(os.path.join(OUT, "knee_harm.json"), "w"), indent=1)
        rs.log(f"knee harm: val(clean) 84 {res['84']['val_e_clean']:.3f} 78 {res['78']['val_e_clean']:.3f} harm "
               f"{harm:+.3f} {'PASS' if harm >= HARM else 'tolerated'}")
        return

    if a.stage in ("signal", "alias"):
        name = {"signal": "v9v", "alias": "v9a"}[a.stage]
        lib, out = os.path.join(rs.C, "data", f"clips_{name}"), os.path.join(OUT, "val", f"{name}_full_s0.json")
        test = os.path.join(OUT, "test", f"{name}_full_s0.json")

        def done(n, g):
            futures.append(pool.submit(evaluate, n, lib, out, g))
            if a.stage == "alias":  # secondary: the 168 test clips (the clean-only run's are test/knee84_s0.json)
                futures.append(pool.submit(evaluate, n, lib, test, g, "test"))

        S.wait_for([S.submit(f"{a.tag}f_{name}_full_s0", a.steps, prio=0, seed=0, env={"CURATION_LIBRARY": lib},
                             on_done=done)])
        while futures:
            futures.pop().result()
        clean_val = os.path.join(P1, "dose", "val_cv9_dose_clean_s0.json")
        full, clean = val_e(out), val_e(clean_val)
        res = {"val_e_full": full, "val_e_clean_only": clean, "harm": full - clean, "passes": bool(full - clean >= HARM)}
        if a.stage == "alias":
            comp = lambda path, k: float(np.mean([v[k] for v in json.load(open(path))["clips"].values()]))  # noqa: E731
            clean_test = os.path.join(OUT, "test", "knee84_s0.json")
            res.update({f"{s}_{k}_{c}": comp(f, k) for s, (fa, fc) in (("val", (out, clean_val)), ("test", (test, clean_test)))
                        for c, f in (("full", fa), ("clean_only", fc)) for k in ("keypoints", "legs_rms")},
                       test_e_full=val_e(test), test_e_clean_only=val_e(clean_test))
        json.dump({"rule": f"val e(full) - val e(clean-only, the dose check's 84 clips) >= {HARM}",
                   "library": f"clips_{name}", **res, "time": time.strftime("%Y-%m-%d %H:%M")},
                  open(os.path.join(OUT, f"{a.stage}_harm.json"), "w"), indent=1)
        rs.log(f"{a.stage} harm: full {full:.3f} clean {clean:.3f} harm {full - clean:+.3f} "
               f"{'PASS' if res['passes'] else 'tolerated'}")
        return

    if a.stage == "systematic":
        lib = os.path.join(rs.C, "data", "clips_v9s")
        val, names = {}, []
        for cond, clips in (("full", None), ("clean", os.path.join(lib, "clean_only.json"))):
            val[cond] = os.path.join(OUT, "val", f"v9s_{cond}_s0.json")
            done = lambda n, g, k=cond: futures.append(pool.submit(evaluate, n, lib, val[k], g))  # noqa: E731
            names.append(S.submit(f"{a.tag}f_v9s_{cond}_s0", a.steps, prio=0, seed=0, clips=clips,
                                  env={"CURATION_LIBRARY": lib}, on_done=done))
        S.wait_for(names)
        while futures:
            futures.pop().result()
        full, clean = val_e(val["full"]), val_e(val["clean"])
        res = {"val_e_full": full, "val_e_clean_only": clean, "harm": full - clean, "passes": bool(full - clean >= HARM),
               "val_e_v9_clean_only_84": val_e(os.path.join(P1, "dose", "val_cv9_dose_clean_s0.json"))}
        json.dump({"rule": f"val e(full) - val e(clean-only, 42 clips) >= {HARM}", "library": "clips_v9s", **res,
                   "time": time.strftime("%Y-%m-%d %H:%M")},
                  open(os.path.join(OUT, "systematic_harm.json"), "w"), indent=1)
        rs.log(f"systematic harm: full {full:.3f} clean {clean:.3f} harm {full - clean:+.3f} "
               f"{'PASS' if res['passes'] else 'tolerated'}")
        return

    if a.stage == "budget":
        lib, clean_ids = libs["c75"], os.path.join(P1, "dose", "clean_only.json")
        val = {}
        names = []
        for b in BUDGETS:
            for cond, clips in (("full", None), ("clean", clean_ids)):
                k = f"b{b // 1_000_000}m_{cond}"
                val[k] = os.path.join(OUT, "val", f"c75_{k}_s0.json")
                done = lambda n, g, k=k: futures.append(pool.submit(evaluate, n, lib, val[k], g))  # noqa: E731
                names.append(S.submit(f"{a.tag}f_c75_{k}_s0", b, prio=0, seed=0, clips=clips,
                                      env={"CURATION_LIBRARY": lib}, on_done=done))
        S.wait_for(names)
        while futures:
            futures.pop().result()
        res = {}
        for b in BUDGETS:
            m = b // 1_000_000
            full, clean = val_e(val[f"b{m}m_full"]), val_e(val[f"b{m}m_clean"])
            res[f"{m}M"] = {"val_e_full": full, "val_e_clean_only": clean, "harm": full - clean,
                            "passes": bool(full - clean >= HARM)}
        json.dump({"rule": f"val e(full) - val e(clean-only) >= {HARM}, both at the same budget", "library": "clips_v9c75",
                   "budgets": res, "time": time.strftime("%Y-%m-%d %H:%M")},
                  open(os.path.join(OUT, "budget_harm.json"), "w"), indent=1)
        rs.log("budget harm: " + ", ".join(f"{k} full {r['val_e_full']:.3f} clean {r['val_e_clean_only']:.3f} harm "
                                           f"{r['harm']:+.3f} {'PASS' if r['passes'] else 'tolerated'}"
                                           for k, r in res.items()))
        return

    val = {k: os.path.join(OUT, "val", f"full_{k}_s0.json") for k in libs}
    names = []
    for k, lib in libs.items():
        done = lambda n, g, k=k: futures.append(pool.submit(evaluate, n, libs[k], val[k], g))  # noqa: E731
        names.append(S.submit(f"{a.tag}f_{k}_full_s0", a.steps, prio=0, seed=0, env={"CURATION_LIBRARY": lib},
                              on_done=done))
    S.wait_for(names)
    while futures:
        futures.pop().result()

    clean = val_e(os.path.join(P1, "dose", "val_cv9_dose_clean_s0.json"))
    res = {k: {"val_e_full": val_e(val[k]), "harm": val_e(val[k]) - clean} for k in libs}
    for r in res.values():
        r["passes"] = bool(r["harm"] >= HARM)
    json.dump({"rule": f"val e(full) - val e(clean-only) >= {HARM}", "val_e_clean_only": clean,
               "v9_23pct": {"val_e_full": val_e(os.path.join(P1, "dose", "val_cv9_full_s0.json"))}, "levels": res,
               "time": time.strftime("%Y-%m-%d %H:%M")}, open(os.path.join(OUT, "harm.json"), "w"), indent=1)
    rs.log("harm: " + ", ".join(f"{k} e {r['val_e_full']:.3f} harm {r['harm']:+.3f} {'PASS' if r['passes'] else 'tolerated'}"
                                for k, r in res.items()))


if __name__ == "__main__":
    main()
