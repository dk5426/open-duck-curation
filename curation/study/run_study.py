"""Run the whole study (PREREG Steps 4-5) end to end on a set of GPUs, then write the comparison.

  OPENDUCK_ROOT=<dir holding Open_Duck_Playground, open-duck-curation, tools/launch_train.sh, runs/> \
      python3 run_study.py --gpus 1 2 [--tag st5] [--lib data/clips_v5]

Smoke test of every stage: --tag st5smoke --seeds 0 --score-steps 2000000 --tau-steps 1000000 --final-steps 1000000

Steps (each skipped if its output already exists, so the driver can be restarted):
  1. scoring policy on every train clip (300M); full condition, seeds 0/1/2 (200M) fill the other GPU meanwhile
  2. score train + val (10 rollouts) and test (10 rollouts, for the trackability strata only) with the scoring policy
  3. τ candidates p40/p55/p70/p85; 50M fine-tune of the scoring policy on each; score val with 30 rollouts
  4. τ* = lowest mean val score, ties within 0.02 go to the larger subset
  5. curated, random (one draw per seed) and kinematic subsets; 200M from scratch, seeds 0/1/2
  6. test evaluation of every final policy: nominal, push 0.3 / 0.6 m/s, friction x 0.6 (10 rollouts each)
  7. compare_conditions.py per perturbation (all clips and gaits only) and training curves; SUMMARY.md, DONE
Results go to open-duck-curation/results/<tag>/; runs to runs/<tag>_*.
"""

import argparse
import json
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = os.environ["OPENDUCK_ROOT"]
PG = os.path.join(ROOT, "Open_Duck_Playground")
C = os.path.join(ROOT, "open-duck-curation")
RUNS = os.path.join(ROOT, "runs")
LAUNCH = os.path.join(ROOT, "tools", "launch_train.sh")
PY = os.path.join(PG, ".venv", "bin", "python")
SEEDS = (0, 1, 2)
TAUS = ("p40", "p55", "p70", "p85")
TIE = 0.02
STATIONARY = ("crouch", "bow", "sway", "head")
TESTS = (("nominal", []), ("push03", ["--push", "0.3"]), ("push06", ["--push", "0.6"]), ("fric06", ["--friction", "0.6"]))

a = None
OUT = None
LOG_LOCK = threading.Lock()


def log(msg):
    with LOG_LOCK:
        line = f"{time.strftime('%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        open(os.path.join(OUT, "study.log"), "a").write(line + "\n")


def finished(name):
    f = os.path.join(RUNS, name, "launch.txt")
    return os.path.exists(f) and "exit rc=0" in open(f).read()


def final_ckpt(name):
    d = os.path.join(RUNS, name)
    cks = [x for x in os.listdir(d) if x[:4].isdigit() and not x.endswith(".onnx")]
    return os.path.join(d, max(cks, key=lambda x: int(x.rsplit("_", 1)[1])))


def run_eval(ckpt, clips, rollouts, out, gpu, extra=()):
    if os.path.exists(out):
        return
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), XLA_PYTHON_CLIENT_PREALLOCATE="false",
               CURATION_LIBRARY=a.lib)
    r = subprocess.run([PY, os.path.join(C, "curation/eval/eval_clips.py"), "--ckpt", ckpt, "--clips", clips,
                        "--rollouts", str(rollouts), *extra, "--out", out], cwd=PG, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        log(f"EVAL FAILED {out}: {r.stderr[-800:]}")
        raise RuntimeError(out)
    log(f"eval {os.path.basename(out)}")


class Scheduler:
    """Priority queue of training runs over the GPUs, one run per GPU, through launch_train.sh."""

    def __init__(self, gpus):
        self.gpus, self.pending, self.running, self.done = list(gpus), [], {}, set()
        self.cool = {g: 0.0 for g in gpus}
        self.n = 0

    def submit(self, name, steps, prio, clips=None, seed=0, restore=None, on_done=None):
        if finished(name):
            log(f"skip {name} (finished)")
            self.done.add(name)
            if on_done:
                on_done(name, self.gpus[0])
            return name
        self.n += 1
        self.pending.append(dict(name=name, steps=steps, prio=prio, clips=clips, seed=seed, restore=restore,
                                 on_done=on_done, order=self.n))
        return name

    def tick(self):
        for name, (p, job, gpu, t0) in list(self.running.items()):
            rc = p.poll()
            if rc is None:
                continue
            del self.running[name]
            if rc in (2, 3, 4) and time.time() - t0 < 120:  # launch refused: GPU busy or locked; retry later
                self.cool[gpu] = time.time() + 60
                self.pending.append(job)
                log(f"launch of {name} on GPU {gpu} refused (rc {rc}); retrying")
            elif rc == 0 and finished(name):
                self.done.add(name)
                log(f"done {name} (GPU {gpu})")
                if job["on_done"]:
                    job["on_done"](name, gpu)
            else:
                open(os.path.join(OUT, "FAILED"), "w").write(f"{name} rc {rc}\n")
                log(f"FAILED {name} rc {rc}")
                raise RuntimeError(name)
        busy = {v[2] for v in self.running.values()}
        for g in self.gpus:
            if g in busy or time.time() < self.cool[g] or not self.pending:
                continue
            self.pending.sort(key=lambda j: (j["prio"], j["order"]))
            job = self.pending.pop(0)
            if finished(job["name"]):  # finished while queued (e.g. left running by a previous driver)
                self.done.add(job["name"])
                log(f"skip {job['name']} (finished)")
                if job["on_done"]:
                    job["on_done"](job["name"], g)
                continue
            env = dict(os.environ, CURATION_LIBRARY=a.lib, PPO_OVERRIDES_JSON=json.dumps({"seed": job["seed"]}))
            if job["clips"]:
                env["CURATION_CLIPS"] = job["clips"]
            args = [LAUNCH, str(g), job["name"], str(job["steps"]), "--env", "tracking"]
            if job["restore"]:
                args += ["--restore_checkpoint_path", job["restore"]]
            out = open(os.path.join(OUT, "launch", job["name"] + ".out"), "w")
            p = subprocess.Popen(args, cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
            self.running[job["name"]] = (p, job, g, time.time())
            log(f"start {job['name']} on GPU {g} (seed {job['seed']}, "
                f"{len(json.load(open(job['clips']))) if job['clips'] else 'all train'} clips)")

    def wait_for(self, names):
        while not set(names) <= self.done:
            self.tick()
            time.sleep(20)


def main():
    global a, OUT, SEEDS
    p = argparse.ArgumentParser()
    p.add_argument("--gpus", type=int, nargs="+", required=True)
    p.add_argument("--tag", default="st5")
    p.add_argument("--lib", default=os.path.join(C, "data/clips_v5"))
    p.add_argument("--score-steps", type=int, default=300_000_000)
    p.add_argument("--tau-steps", type=int, default=50_000_000)
    p.add_argument("--final-steps", type=int, default=200_000_000)
    p.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS), help="fewer only for a smoke test")
    a = p.parse_args()
    a.lib = os.path.abspath(a.lib)
    SEEDS = tuple(a.seeds)
    OUT = os.path.join(C, "results", a.tag)
    SUB, TEST = os.path.join(OUT, "subsets"), os.path.join(OUT, "test")
    for d in (OUT, SUB, TEST, os.path.join(OUT, "launch")):
        os.makedirs(d, exist_ok=True)
    man = os.path.join(a.lib, "manifest.json")
    log(f"study {a.tag}: library {a.lib}, GPUs {a.gpus}")
    S = Scheduler(a.gpus)
    pool = ThreadPoolExecutor(max_workers=len(a.gpus))
    futures = []
    T = a.tag

    def test_evals(name, gpu):
        ck = final_ckpt(name)
        futures.append(pool.submit(lambda: [run_eval(ck, "test", 10, os.path.join(TEST, f"{name[len(T) + 1:]}_{tag}.json"),
                                                     gpu, extra) for tag, extra in TESTS]))

    # 1. scoring policy; full condition fills the other GPU
    score = S.submit(f"{T}_score", a.score_steps, prio=0)
    finals = {("full", s): S.submit(f"{T}_full_s{s}", a.final_steps, prio=2, seed=s, on_done=test_evals) for s in SEEDS}
    S.wait_for([score])

    # 2. score train / val / test with the scoring policy
    ck = final_ckpt(score)
    S.tick()
    g = a.gpus[0]
    run_eval(ck, "train", 10, os.path.join(OUT, "scores_train.json"), g)
    run_eval(ck, "val", 30, os.path.join(OUT, "scores_val_scoring.json"), g)
    run_eval(ck, "test", 10, os.path.join(OUT, "scores_test_scoring.json"), g)
    subprocess.run([PY, os.path.join(C, "curation/select/select_subsets.py"), "--scores",
                    os.path.join(OUT, "scores_train.json"), "--manifest", man, "--out", SUB], check=True,
                   stdout=open(os.path.join(OUT, "subsets.log"), "w"), stderr=subprocess.STDOUT)
    log("tau candidates: " + json.dumps({k: round(v, 3) for k, v in json.load(open(os.path.join(SUB, "tau_candidates.json"))).items()}))

    # 3. τ fine-tunes, each scored on val with 30 rollouts
    def val_eval(name, gpu):
        futures.append(pool.submit(run_eval, final_ckpt(name), "val", 30,
                                   os.path.join(OUT, f"scores_val_{name.rsplit('_', 1)[1]}.json"), gpu))

    taus = [S.submit(f"{T}_tau_{q}", a.tau_steps, prio=1, clips=os.path.join(SUB, f"curated_{q}.json"), restore=ck,
                     on_done=val_eval) for q in TAUS]
    S.wait_for(taus)
    while futures:
        futures.pop().result()

    # 4. τ*
    rows = []
    for q in TAUS:
        sc = json.load(open(os.path.join(OUT, f"scores_val_{q}.json")))["clips"]
        rows.append((q, float(np.mean([v["score"] for v in sc.values()])),
                     len(json.load(open(os.path.join(SUB, f"curated_{q}.json"))))))
    best = min(r[1] for r in rows)
    pick = max((r for r in rows if r[1] <= best + TIE), key=lambda r: r[2])
    cands = json.load(open(os.path.join(SUB, "tau_candidates.json")))
    json.dump({"candidates": [{"tau": q, "value": cands[q], "mean_val_score": m, "clips": n} for q, m, n in rows],
               "tie_band": TIE, "tau_star": pick[0], "tau_value": cands[pick[0]]},
              open(os.path.join(OUT, "tau_choice.json"), "w"), indent=1)
    log("tau: " + ", ".join(f"{q} {m:.3f} ({n} clips)" for q, m, n in rows) + f" -> tau* = {pick[0]}")

    # 5. matched subsets and the final runs
    subprocess.run([PY, os.path.join(C, "curation/select/select_subsets.py"), "--scores",
                    os.path.join(OUT, "scores_train.json"), "--manifest", man, "--out", SUB, "--match",
                    os.path.join(SUB, f"curated_{pick[0]}.json"), "--seeds", *map(str, SEEDS)], check=True,
                   stdout=open(os.path.join(OUT, "subsets.log"), "a"), stderr=subprocess.STDOUT)
    clips = {"curated": lambda s: f"curated_{pick[0]}.json", "random": lambda s: f"random_s{s}.json",
             "kinematic": lambda s: "kinematic.json"}
    for s in SEEDS:
        for cond, f in clips.items():
            finals[(cond, s)] = S.submit(f"{T}_{cond}_s{s}", a.final_steps, prio=1, seed=s,
                                         clips=os.path.join(SUB, f(s)), on_done=test_evals)
    S.wait_for(list(finals.values()))
    while futures:
        futures.pop().result()

    # 7. analysis
    tau_v = cands[pick[0]]
    cc = os.path.join(C, "curation/analysis/compare_conditions.py")
    summary = [f"# Study {T}: summary", "", f"Library `{os.path.basename(a.lib)}`; τ* = {pick[0]} ({tau_v:.3f}); "
               f"seeds {', '.join(map(str, SEEDS))}; {a.final_steps // 1_000_000}M steps per final run.", ""]
    for tag, _ in TESTS:
        conds = [f"{c}=" + ",".join(os.path.join(TEST, f"{c}_s{s}_{tag}.json") for s in SEEDS)
                 for c in ("full", "curated", "random", "kinematic")]
        for suffix, ex in (("", []), ("_gaits", ["--exclude-category", *STATIONARY])):
            out = os.path.join(OUT, f"comparison_{tag}{suffix}.md")
            subprocess.run([PY, cc, "--manifest", man, "--cond", *conds, *ex, "--strata-scores",
                            os.path.join(OUT, "scores_test_scoring.json"), "--tau", str(tau_v), "--title",
                            f"Study {T}, test clips, {tag}{', gaits only' if ex else ''}", "--out", out], check=True,
                           capture_output=True)
            body = open(out).read().split("\n")
            keep = [ln for ln in body if (ln.startswith("| ") and not ln.startswith(("| `", "| clip "))) or
                    ln.startswith(("- ", "**", "## Secondary"))]
            summary += [f"## {tag}{' (gaits only)' if ex else ''}", "", *keep, ""]
    curves = subprocess.run([PY, os.path.join(C, "curation/analysis/compare_runs.py"), "--runs",
                             *[os.path.join(RUNS, n) for n in finals.values()], "--at", "50", "100", "200",
                             "--terms", "legs", "keypoints", "alive"], cwd=PG, capture_output=True, text=True).stdout
    open(os.path.join(OUT, "curves.txt"), "w").write(curves)
    summary += ["## Training curves", "", "```", curves.strip(), "```"]
    open(os.path.join(OUT, "SUMMARY.md"), "w").write("\n".join(summary) + "\n")
    open(os.path.join(OUT, "DONE"), "w").write(time.strftime("%Y-%m-%d %H:%M") + "\n")
    log("DONE")


if __name__ == "__main__":
    main()
