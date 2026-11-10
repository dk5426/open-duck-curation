"""PREREG P.7-P.9: compare training conditions on the test clips from eval_clips.py outputs.

For every condition: mean test score e, completion, falls, coverage (share of categories with at least one test clip
completed >= 0.8). For curated against each other condition: the paired difference in e over test clips with a 95%
bootstrap CI (10,000 resamples over clips; with several seeds per condition, seeds are resampled within each drawn
clip, as P.8 states), per category and overall, and the P.9 pass bar.

  python compare_conditions.py --manifest data/clips_v4/manifest.json --out results/dry_run/comparison.md \
      --cond full=eval_full.json curated=eval_curated.json random=eval_random.json kinematic=eval_kinematic.json \
      [--exclude-category head] [--strata-scores scores_test_scoring.json --tau 1.2] [--title "..."]

Secondary analyses (PREREG P.8): with --strata-scores and --tau, the paired differences are also reported separately
for test clips the scoring policy tracks within τ ("trackable") and beyond it. Every run also splits test clips by
whether their motion parameters lie inside the range the category's training clips cover.

Each value may be a comma-separated list of JSON files (one per seed).
"""

import argparse
import json

import numpy as np

B = 10_000


def load(paths):
    runs = [json.load(open(p))["clips"] for p in paths.split(",")]
    ids = sorted(set.intersection(*(set(r) for r in runs)))
    out = {i: {k: float(np.mean([r[i][k] for r in runs])) for k in ("score", "completion", "falls")} for i in ids}
    for i in ids:
        out[i]["seeds"] = np.array([r[i]["score"] for r in runs])
    return out


def boot_ci(ref, oth, rng):
    """95% CI of mean(ref - oth): clips resampled, then one seed per condition drawn within each drawn clip."""
    n = len(ref)
    if n < 2:
        return float("nan"), float("nan")
    a, b = np.stack(ref), np.stack(oth)  # (clips, seeds)
    c = rng.integers(0, n, size=(B, n))
    sa = rng.integers(0, a.shape[1], size=(B, n))
    sb = rng.integers(0, b.shape[1], size=(B, n))
    m = (a[c, sa] - b[c, sb]).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


# Numeric motion parameters that define each category's range (manifest "params"); magnitudes, so mirrored clips count
RANGE_KEYS = {"walk_fwd": ("dx", "foot_lift_m"), "walk_back": ("dx", "foot_lift_m"), "side_step": ("dy", "foot_lift_m"),
              "turn_in_place": ("dtheta", "foot_lift_m"), "walk_turn": ("dx", "dtheta", "foot_lift_m"),
              "march": ("foot_lift_m",), "crouch": ("depth_frac",), "bow": ("pitch_deg",), "sway": ("amp_m", "freq_hz"),
              "head": ("move",)}


def in_train_range(man):
    """Test clip id -> True if each of its category's parameters lies inside the training clips' range (a categorical
    parameter must match a training value)."""
    clips = man["clips"]
    out = {}
    for c in clips:
        if c["split"] != "test":
            continue
        tr = [t for t in clips if t["split"] == "train" and t["category"] == c["category"]]
        ok = True
        for k in RANGE_KEYS.get(c["category"], ()):
            v = c["params"].get(k)
            vals = [t["params"].get(k) for t in tr]
            if isinstance(v, str):
                ok &= v in vals
            else:
                mags = [abs(x) for x in vals]
                ok &= min(mags) - 1e-9 <= abs(v) <= max(mags) + 1e-9
        out[c["id"]] = bool(ok)
    return out


def delta_table(res, ref, ids, rng):
    rows = ["| vs | clips | Δe [95% CI] |", "|---|---|---|"]
    for k in res:
        if k == ref or not ids:
            continue
        d = np.mean([res[ref][i]["score"] - res[k][i]["score"] for i in ids])
        lo, hi = boot_ci([res[ref][i]["seeds"] for i in ids], [res[k][i]["seeds"] for i in ids], rng)
        rows.append(f"| {k} | {len(ids)} | {d:+.3f} [{lo:+.3f}, {hi:+.3f}] |")
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--cond", nargs="+", required=True, help="name=file[,file...]")
    p.add_argument("--ref", default="curated")
    p.add_argument("--exclude-category", nargs="*", default=[])
    p.add_argument("--strata-scores", default=None, help="eval_clips.py JSON of the test clips under the scoring policy")
    p.add_argument("--tau", type=float, default=None)
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
        lo, hi = boot_ci([res[a.ref][i]["seeds"] for i in ids], [res[k][i]["seeds"] for i in ids], rng)
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
    rng2 = np.random.default_rng(1)
    rng_ok = in_train_range(man)
    L += ["", "## Secondary: test clips inside vs outside the training parameter range", "",
          f"Inside: {', '.join(sorted(i for i in ids if rng_ok.get(i))) or 'none'}", ""]
    for name, grp in (("inside", [i for i in ids if rng_ok.get(i)]), ("outside", [i for i in ids if not rng_ok.get(i)])):
        L += [f"**{name}**", "", *delta_table(res, a.ref, grp, rng2), ""]
    if a.strata_scores and a.tau is not None:
        st = json.load(open(a.strata_scores))["clips"]
        easy = [i for i in ids if i in st and st[i]["score"] <= a.tau]
        hard = [i for i in ids if i in st and st[i]["score"] > a.tau]
        L += [f"## Secondary: test clips by trackability under the scoring policy (τ* = {a.tau:.3f})", ""]
        for name, grp in (("trackable (e ≤ τ*)", easy), ("beyond τ*", hard)):
            L += [f"**{name}**", "", *delta_table(res, a.ref, grp, rng2), ""]
    L += ["", "## Per clip (e)", "", "| clip | category | " + " | ".join(res) + " |", "|---|---|" + "---|" * len(res)]
    for i in sorted(ids, key=lambda i: (cat[i], i)):
        L.append(f"| `{i}` | {cat[i]} | " + " | ".join(f"{res[k][i]['score']:.2f}" for k in res) + " |")
    open(a.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L[:30]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
