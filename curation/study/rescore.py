"""Re-evaluate the final policies of finished studies with the position / heading terms (eval_clips.py pos_err, yaw_err,
score_v2) and write the comparison per metric. Judging only: the studies' clip selection is unchanged.

  OPENDUCK_ROOT=<dir> python3 rescore.py --gpus 1 2 --tags st7 cs30 camb cs50

Per study: results/<tag>/test_v2/<cond>_s<seed>_<test>.json, comparison_v2_<test>_<metric>.md and RESCORE.md (headline
rows for every metric). The old `score` is recomputed too, as a check against results/<tag>/test/.
"""

import argparse
import json
import os
import queue
import re
import subprocess
import threading
import time

ROOT = os.environ["OPENDUCK_ROOT"]
PG = os.path.join(ROOT, "Open_Duck_Playground")
C = os.path.join(ROOT, "open-duck-curation")
RUNS = os.path.join(ROOT, "runs")
PY = os.path.join(PG, ".venv", "bin", "python")
TESTS = (("nominal", []), ("push03", ["--push", "0.3"]), ("push06", ["--push", "0.6"]), ("fric06", ["--friction", "0.6"]))
METRICS = ("score_v2", "pos_err", "yaw_err", "score")
STATIONARY = ("crouch", "bow", "sway", "head")


def final_ckpt(name):
    d = os.path.join(RUNS, name)
    cks = [x for x in os.listdir(d) if x[:4].isdigit() and not x.endswith(".onnx")]
    return os.path.join(d, max(cks, key=lambda x: int(x.rsplit("_", 1)[1])))


def study(tag):
    """Library, conditions -> seeds, tau* of a finished study (from its results folder)."""
    out = os.path.join(C, "results", tag)
    lib = re.search(r"Library `([^`]+)`", open(os.path.join(out, "SUMMARY.md")).read()).group(1)
    conds = {}
    for f in os.listdir(os.path.join(out, "test")):
        m = re.match(r"(\w+?)_s(\d+)_nominal\.json$", f)
        if m:
            conds.setdefault(m.group(1), []).append(int(m.group(2)))
    tau = json.load(open(os.path.join(out, "tau_choice.json")))["tau_value"]
    return out, os.path.join(C, "data", lib), {k: sorted(v) for k, v in conds.items()}, tau


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gpus", type=int, nargs="+", required=True)
    p.add_argument("--tags", nargs="+", required=True)
    a = p.parse_args()
    jobs = queue.Queue()
    for tag in a.tags:
        out, lib, conds, _ = study(tag)
        os.makedirs(os.path.join(out, "test_v2"), exist_ok=True)
        for cond, seeds in conds.items():
            for s in seeds:
                for t, extra in TESTS:
                    f = os.path.join(out, "test_v2", f"{cond}_s{s}_{t}.json")
                    if not os.path.exists(f):
                        jobs.put((lib, final_ckpt(f"{tag}_{cond}_s{s}"), extra, f))
    print(f"{jobs.qsize()} evaluations", flush=True)

    def worker(gpu):
        while True:
            try:
                lib, ck, extra, f = jobs.get_nowait()
            except queue.Empty:
                return
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), XLA_PYTHON_CLIENT_PREALLOCATE="false",
                       CURATION_LIBRARY=lib)
            r = subprocess.run([PY, os.path.join(C, "curation/eval/eval_clips.py"), "--ckpt", ck, "--clips", "test",
                                "--rollouts", "10", *extra, "--out", f], cwd=PG, env=env, capture_output=True, text=True)
            print(f"{time.strftime('%H:%M:%S')} {'ok' if r.returncode == 0 else 'FAILED'} {f}", flush=True)
            if r.returncode != 0:
                print(r.stderr[-800:], flush=True)

    ts = [threading.Thread(target=worker, args=(g,)) for g in a.gpus]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    cc = os.path.join(C, "curation/analysis/compare_conditions.py")
    for tag in a.tags:
        out, lib, conds, tau = study(tag)
        man = os.path.join(lib, "manifest.json")
        summ = [f"# Study {tag}: test re-scored with position and heading error", "",
                "Judging only; clip selection unchanged. `score_v2` = score + pos_err / 0.05 m + yaw_err / 0.2 rad per frame; "
                "`pos_err` (m) and `yaw_err` (rad) alone are threshold-free. `score` is the original metric, recomputed.", ""]
        for t, _ in TESTS:
            cargs = [f"{c}=" + ",".join(os.path.join(out, "test_v2", f"{c}_s{s}_{t}.json") for s in seeds)
                     for c, seeds in conds.items()]
            for suffix, ex in (("", []), ("_gaits", ["--exclude-category", *STATIONARY])):
                for m in METRICS:
                    f = os.path.join(out, f"comparison_v2_{t}{suffix}_{m}.md")
                    subprocess.run([PY, cc, "--manifest", man, "--cond", *cargs, *ex, "--metric", m, "--strata-scores",
                                    os.path.join(out, "scores_test_scoring.json"), "--tau", str(tau), "--title",
                                    f"Study {tag}, test, {t}{', gaits only' if ex else ''}, {m}", "--out", f],
                                   check=True, capture_output=True)
                    body = open(f).read().split("\n")
                    end = body.index("## Secondary: test clips inside vs outside the training parameter range")
                    keep = [ln for ln in body[:end] if (ln.startswith("| ") and not ln.startswith(("| `", "| clip ")))
                            or ln.startswith(("- **pass", "- curated beats"))]
                    summ += [f"## {t}{' (gaits only)' if ex else ''}: {m}", "", *keep, ""]
        open(os.path.join(out, "RESCORE.md"), "w").write("\n".join(summ) + "\n")
        print("wrote", os.path.join(out, "RESCORE.md"), flush=True)


if __name__ == "__main__":
    main()
