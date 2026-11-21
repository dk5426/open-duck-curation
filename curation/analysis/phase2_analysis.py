"""Phase 2 summary: every learner on the Phase 1 subsets -> results/<tag>/<sub>/SUMMARY.md

PPO's row is Phase 1's test results at the same fraction. Per learner: mean test e (nominal, original score) per
condition and paired differences. The reference condition is the oracle when the study has one (PREREG v2: cv7) and
type-normalised curation otherwise (PREREG v3: cv9); the full - reference gap is how much the broken clips cost that
learner, and P4 / P5 compare a learner's gap with PPO's (difference of gaps, source-level bootstrap over test clips).
All Phase 2 comparisons are SECONDARY: no pass bar, no multiple-comparison correction.

  cd Open_Duck_Playground && python phase2_analysis.py --tag cv7 --lib <clips_v7> [--sub phase2]
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_conditions as cc  # noqa: E402

ROOT = os.environ["OPENDUCK_ROOT"]
C = os.path.join(ROOT, "open-duck-curation")
NAMES = {"ppo": "PPO (Phase 1)", "ppo_noff": "PPO without feed-forward", "sac": "SAC", "ars": "ARS",
         "dagger": "DAgger (student of the Phase 1 PPO)", "fasttd3": "FastTD3"}
B = 10_000


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    p.add_argument("--lib", required=True)
    p.add_argument("--sub", default="phase2")
    a = p.parse_args()
    P1 = os.path.join(C, "results", a.tag)
    OUT = os.path.join(P1, a.sub)
    cfg = json.load(open(os.path.join(OUT, "config.json")))
    f, seeds, conds = cfg["fraction"], cfg["seeds"], cfg["conds"]
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    src = {c["id"]: c["source"] for c in man["clips"]}

    def files(lr, cond):
        if lr == "ppo":
            fs = [os.path.join(P1, "test", (f"full_s{s}" if cond == "full" else f"{cond}_f{f}_s{s}") + "_nominal.json")
                  for s in seeds]
        else:
            fs = [os.path.join(OUT, "test", f"{a.sub}_{lr}_{cond}_s{s}_nominal.json") for s in seeds]
        return [x for x in fs if os.path.exists(x)]

    res = {}
    for lr in ["ppo", *cfg["learners"]]:
        for cond in conds:
            fs = files(lr, cond)
            if fs:
                res[(lr, cond)] = (cc.load(",".join(fs)), len(fs))
    learners = [lr for lr in ["ppo", *cfg["learners"]] if any((lr, c) in res for c in conds)]
    rng = np.random.default_rng(0)

    def cmp(x, y):
        """mean(x - y) over shared test clips, with the source-level bootstrap CI of compare_conditions.py."""
        ids = sorted(set(x) & set(y))
        cc.GROUPS = src
        d = float(np.mean([x[i]["score"] - y[i]["score"] for i in ids]))
        lo, hi = cc.boot_ci([x[i]["seeds"] for i in ids], [y[i]["seeds"] for i in ids], rng, cc.grp_of(ids))
        return f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}]"

    REF = "oracle" if "oracle" in conds else "curatedtn"

    def gap(lr):
        r = {c: res[(lr, c)][0] for c in ("full", REF)}
        return {i: r["full"][i]["score"] - r[REF][i]["score"] for i in set(r["full"]) & set(r[REF])}

    L = [f"# Study {a.tag}, Phase 2: other learners at {f}%", "",
         "SECONDARY (pre-registered, no pass bar, no correction for multiple comparisons). Same subsets, test clips and "
         "evaluator as Phase 1; only the learner changes. Lower e is better.", "",
         "## Mean test e (nominal), mean over seeds [seed range]", "",
         "| learner | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
    for lr in learners:
        row = []
        for c in conds:
            if (lr, c) not in res:
                row.append("—")
                continue
            r, n = res[(lr, c)]
            per = np.array([r[i]["seeds"] for i in r]).mean(0)
            row.append(f"{np.mean([v['score'] for v in r.values()]):.3f} [{per.min():.3f}, {per.max():.3f}]"
                       + (f" ({n} seeds)" if n != len(seeds) else ""))
        L.append(f"| {NAMES.get(lr, lr)} | " + " | ".join(row) + " |")
    L += ["", "## Completion and falls per clip", "", "| learner | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
    for lr in learners:
        L.append(f"| {NAMES.get(lr, lr)} | " + " | ".join(
            f"{np.mean([v['completion'] for v in res[(lr, c)][0].values()]):.3f} / "
            f"{np.mean([v['falls'] for v in res[(lr, c)][0].values()]):.2f}" if (lr, c) in res else "—" for c in conds) + " |")
    pairs = ([("curated", "full"), ("curated", "oracle"), ("full", "oracle")] if REF == "oracle" else
             [(c, "full") for c in conds if c != "full"] + [("curatedtn", "random")])
    pairs = [(x, y) for x, y in pairs if x in conds and y in conds]
    L += ["", "## Paired differences (source-level 95% CI; negative = the first condition better)", "",
          "| learner | " + " | ".join(f"{x} − {y}" for x, y in pairs) + " |", "|---|" + "---|" * len(pairs)]
    for lr in learners:
        g = lambda x, y: cmp(res[(lr, x)][0], res[(lr, y)][0]) if (lr, x) in res and (lr, y) in res else "—"  # noqa: E731
        L.append(f"| {NAMES.get(lr, lr)} | " + " | ".join(g(x, y) for x, y in pairs) + " |")

    L += ["", f"## P4 / P5: does a learner gain more from curation ({REF}) than PPO?", "",
          f"Difference of gaps: (full − {REF}) for the learner minus (full − {REF}) for PPO, per test clip (seed means), "
          "sources resampled. Positive = the learner gains more. P4 predicts positive for SAC and FastTD3 (and PPO "
          "without feed-forward).", "", "| learner | difference of gaps [95% CI] |", "|---|---|"]
    if ("ppo", "full") in res and ("ppo", REF) in res:
        g0 = gap("ppo")
        for lr in learners[1:]:
            if (lr, "full") not in res or (lr, REF) not in res:
                continue
            g1 = gap(lr)
            ids = sorted(set(g0) & set(g1))
            dd = np.array([g1[i] - g0[i] for i in ids])
            groups = np.unique([src[i] for i in ids], return_inverse=True)[1]
            members = [np.where(groups == k)[0] for k in range(groups.max() + 1)]
            draws = rng.integers(0, len(members), size=(B, len(members)))
            bm = np.array([np.mean(np.concatenate([dd[members[k]] for k in row])) for row in draws])
            L.append(f"| {NAMES.get(lr, lr)} | {dd.mean():+.3f} [{np.percentile(bm, 2.5):+.3f}, "
                     f"{np.percentile(bm, 97.5):+.3f}] |")
    open(os.path.join(OUT, "SUMMARY.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "SUMMARY.md"))


if __name__ == "__main__":
    main()
