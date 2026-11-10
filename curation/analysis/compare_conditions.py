"""PREREG P.7-P.9: compare training conditions on the test clips from eval_clips.py outputs.

For every condition: mean test score e, completion, falls, coverage (share of categories with at least one test clip
completed >= 0.8). For curated against each other condition: the paired difference in e over test clips with a 95%
bootstrap CI (10,000 resamples over clips; with several seeds per condition, seeds are averaged per clip first), per
category and overall, and the P.9 pass bar.

  python compare_conditions.py --manifest data/clips_v4/manifest.json --out results/dry_run/comparison.md \
      --cond full=eval_full.json curated=eval_curated.json random=eval_random.json kinematic=eval_kinematic.json \
      [--exclude-category head] [--title "..."]

Each value may be a comma-separated list of JSON files (one per seed).
"""

import argparse
import json

import numpy as np

B = 10_000


def load(paths):
    runs = [json.load(open(p))["clips"] for p in paths.split(",")]
    ids = sorted(set.intersection(*(set(r) for r in runs)))
    return {i: {k: float(np.mean([r[i][k] for r in runs])) for k in ("score", "completion", "falls")} for i in ids}


def boot_ci(d, rng):
    if len(d) < 2:
        return float("nan"), float("nan")
    m = rng.choice(d, size=(B, len(d)), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--cond", nargs="+", required=True, help="name=file[,file...]")
    p.add_argument("--ref", default="curated")
    p.add_argument("--exclude-category", nargs="*", default=[])
    p.add_argument("--title", default="Test-set comparison")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    man = json.load(open(a.manifest))
    cat = {c["id"]: c["category"] for c in man["clips"]}
    conds = dict(kv.split("=", 1) for kv in a.cond)
    res = {k: load(v) for k, v in conds.items()}
    ids = sorted(set.intersection(*(set(r) for r in res.values())))
    ids = [i for i in ids if cat[i] not in a.exclude_category]
    cats = sorted(set(cat[i] for i in ids))
    rng = np.random.default_rng(0)
    L = [f"# {a.title}", "", f"{len(ids)} test clips, {len(cats)} categories"
         + (f" (excluded: {', '.join(a.exclude_category)})" if a.exclude_category else "") + ". Lower e is better.", "",
         "## Per condition", "", "| condition | mean e | completion | falls / clip | coverage |", "|---|---|---|---|---|"]
    for k, r in res.items():
        cov = np.mean([any(r[i]["completion"] >= 0.8 for i in ids if cat[i] == c) for c in cats])
        L.append(f"| {k} | {np.mean([r[i]['score'] for i in ids]):.3f} | {np.mean([r[i]['completion'] for i in ids]):.3f} "
                 f"| {np.mean([r[i]['falls'] for i in ids]):.2f} | {cov:.2f} |")
    L += ["", f"## {a.ref} minus each other condition (paired over test clips; negative = {a.ref} better)", "",
          "| vs | Δe overall [95% CI] | " + " | ".join(cats) + " |", "|---|---|" + "---|" * len(cats)]
    passes = []
    for k in res:
        if k == a.ref:
            continue
        d = np.array([res[a.ref][i]["score"] - res[k][i]["score"] for i in ids])
        lo, hi = boot_ci(d, rng)
        per = []
        for c in cats:
            dc = np.array([res[a.ref][i]["score"] - res[k][i]["score"] for i in ids if cat[i] == c])
            per.append(f"{dc.mean():+.2f}")
        L.append(f"| {k} | {d.mean():+.3f} [{lo:+.3f}, {hi:+.3f}] | " + " | ".join(per) + " |")
        if k in ("full", "random"):
            passes.append((k, hi < 0))
    if "full" in res:
        worst = min(np.mean([res[a.ref][i]["completion"] for i in ids if cat[i] == c])
                    - np.mean([res["full"][i]["completion"] for i in ids if cat[i] == c]) for c in cats)
        L += ["", "## P.9 pass bar", "",
              *[f"- {a.ref} beats {k} with the CI excluding 0: **{'yes' if ok else 'no'}**" for k, ok in passes],
              f"- worst per-category completion drop vs full: {worst:+.3f} (bar: ≥ −0.05): "
              f"**{'yes' if worst >= -0.05 else 'no'}**",
              f"- **pass: {'yes' if all(ok for _, ok in passes) and worst >= -0.05 else 'no'}**"]
    L += ["", "## Per clip (e)", "", "| clip | category | " + " | ".join(res) + " |", "|---|---|" + "---|" * len(res)]
    for i in sorted(ids, key=lambda i: (cat[i], i)):
        L.append(f"| `{i}` | {cat[i]} | " + " | ".join(f"{res[k][i]['score']:.2f}" for k in res) + " |")
    open(a.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L[:30]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
