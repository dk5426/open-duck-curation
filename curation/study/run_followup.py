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
the dose check's clean-only run on the same 84 clean clips (results/<tag>/followup/signal_harm.json). Skipped where
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
    p.add_argument("--stage", default="harm", choices=["harm", "budget", "systematic", "signal", "knee"])
    p.add_argument("--steps", type=int, default=200_000_000)
    p.add_argument("--rollouts", type=int, default=10)
    a = p.parse_args()
    P1 = os.path.join(rs.C, "results", a.tag)
    OUT = rs.OUT = os.path.join(P1, "followup")
    for d in ("val", "launch"):
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

    if a.stage == "signal":
        lib, out = os.path.join(rs.C, "data", "clips_v9v"), os.path.join(OUT, "val", "v9v_full_s0.json")
        done = lambda n, g: futures.append(pool.submit(evaluate, n, lib, out, g))  # noqa: E731
        S.wait_for([S.submit(f"{a.tag}f_v9v_full_s0", a.steps, prio=0, seed=0, env={"CURATION_LIBRARY": lib},
                             on_done=done)])
        while futures:
            futures.pop().result()
        full, clean = val_e(out), val_e(os.path.join(P1, "dose", "val_cv9_dose_clean_s0.json"))
        json.dump({"rule": f"val e(full) - val e(clean-only, the dose check's 84 clips) >= {HARM}", "library": "clips_v9v",
                   "val_e_full": full, "val_e_clean_only": clean, "harm": full - clean,
                   "passes": bool(full - clean >= HARM), "time": time.strftime("%Y-%m-%d %H:%M")},
                  open(os.path.join(OUT, "signal_harm.json"), "w"), indent=1)
        rs.log(f"signal harm: full {full:.3f} clean {clean:.3f} harm {full - clean:+.3f} "
               f"{'PASS' if full - clean >= HARM else 'tolerated'}")
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
