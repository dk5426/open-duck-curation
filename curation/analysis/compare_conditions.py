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

--group source (PREREG v2): the bootstrap resamples whole motion sources (a source's variants move together), then one
seed per condition within each drawn clip; --loo adds a leave-one-clip-out table (the overall Δe and its CI with each
test clip dropped in turn: the range shows whether one clip decides the result).

--ci 97.5 (PREREG v3: Bonferroni over two hypotheses) widens every interval; --drop-all-fail 0.5 drops test clips on
which every condition falls in at least half of its rollouts (PREREG v3 test-clip rule) and lists them.
"""

import argparse
import json

import numpy as np

B = 10_000


def load(paths, metric="score"):
    runs = [json.load(open(p))["clips"] for p in paths.split(",")]
    ids = sorted(set.intersection(*(set(r) for r in runs)))
    for r in runs:
        for i in ids:
            r[i]["score"] = r[i][metric]
    out = {i: {k: float(np.mean([r[i][k] for r in runs])) for k in ("score", "completion", "falls")} for i in ids}
    for i in ids:
        out[i]["fall_rate"] = float(np.mean([r[i]["falls"] / r[i].get("rollouts", 1) for r in runs]))
    for i in ids:
        out[i]["seeds"] = np.array([r[i]["score"] for r in runs])
    return out


GROUPS = None  # clip index -> group index, set by main() with --group source
CI = 95.0  # interval level, set by main() with --ci


def boot_ci(ref, oth, rng, groups=None):
    """CI (level CI) of mean(ref - oth): clips (or, with groups, whole groups of clips) resampled, then one seed per condition
    drawn within each drawn clip."""
    n = len(ref)
    if n < 2:
        return float("nan"), float("nan")
    a, b = np.stack(ref), np.stack(oth)  # (clips, seeds)
    if groups is None:
        c = rng.integers(0, n, size=(B, n))
    else:
        members = [np.where(groups == g)[0] for g in np.unique(groups)]
        draws = rng.integers(0, len(members), size=(B, len(members)))
        c = [np.concatenate([members[g] for g in row]) for row in draws]
        L = max(len(x) for x in c)  # pad with -1, masked below
        c = np.stack([np.pad(x, (0, L - len(x)), constant_values=-1) for x in c])
    mask = c >= 0
    cc = np.where(mask, c, 0)
    sa = rng.integers(0, a.shape[1], size=cc.shape)
    sb = rng.integers(0, b.shape[1], size=cc.shape)
    m = ((a[cc, sa] - b[cc, sb]) * mask).sum(1) / mask.sum(1)
    return float(np.percentile(m, (100 - CI) / 2)), float(np.percentile(m, 100 - (100 - CI) / 2))


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
    rows = [f"| vs | clips | Δe [{CI:g}% CI] |", "|---|---|---|"]
    for k in res:
        if k == ref or not ids:
            continue
        d = np.mean([res[ref][i]["score"] - res[k][i]["score"] for i in ids])
        lo, hi = boot_ci([res[ref][i]["seeds"] for i in ids], [res[k][i]["seeds"] for i in ids], rng, grp_of(ids))
        rows.append(f"| {k} | {len(ids)} | {d:+.3f} [{lo:+.3f}, {hi:+.3f}] |")
    return rows


def grp_of(ids):
    return None if GROUPS is None else np.unique([GROUPS[i] for i in ids], return_inverse=True)[1]


def main():
    global GROUPS, CI
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--cond", nargs="+", required=True, help="name=file[,file...]")
    p.add_argument("--ref", default="curated")
    p.add_argument("--exclude-category", nargs="*", default=[])
    p.add_argument("--strata-scores", default=None, help="eval_clips.py JSON of the test clips under the scoring policy")
    p.add_argument("--tau", type=float, default=None)
    p.add_argument("--metric", default="score", help="per-clip key to compare (score, score_v2, score_v3, pos_err, yaw_err, tilt_err)")
    p.add_argument("--group", choices=("clip", "source"), default="clip", help="bootstrap unit")
    p.add_argument("--loo", action="store_true", help="leave-one-clip-out sensitivity table")
    p.add_argument("--title", default="Test-set comparison")
    p.add_argument("--ci", type=float, default=95.0, help="interval level in percent")
    p.add_argument("--drop-all-fail", type=float, default=None, metavar="RATE",
                   help="drop test clips on which every condition's fall rate is at least RATE")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    man = json.load(open(a.manifest))
    cat = {c["id"]: c["category"] for c in man["clips"]}
    if a.group == "source":
        GROUPS = {c["id"]: c["source"] for c in man["clips"]}
    conds = dict(kv.split("=", 1) for kv in a.cond)
    res = {k: load(v, a.metric) for k, v in conds.items()}
    ids = sorted(set.intersection(*(set(r) for r in res.values())))
    ids = [i for i in ids if cat[i] not in a.exclude_category]
    CI = a.ci
    dropped = []
    if a.drop_all_fail is not None:
        dropped = [i for i in ids if all(r[i]["fall_rate"] >= a.drop_all_fail for r in res.values())]
        ids = [i for i in ids if i not in dropped]
    cats = sorted(set(cat[i] for i in ids))
    rng = np.random.default_rng(0)
    L = [f"# {a.title}", "", f"{len(ids)} test clips ({len(set(GROUPS[i] for i in ids)) if GROUPS else len(ids)} "
         f"bootstrap units: {a.group}s), {len(cats)} categories, metric `{a.metric}`"
         + (f" (excluded: {', '.join(a.exclude_category)})" if a.exclude_category else "") + ". Lower e is better."
         + (f" Dropped (every condition falls in >= {a.drop_all_fail:g} of rollouts): "
            + (", ".join(f"`{i}`" for i in dropped) or "none") + "." if a.drop_all_fail is not None else ""), "",
         "## Per condition", "", "| condition | mean e | completion | falls / clip | coverage |", "|---|---|---|---|---|"]
    for k, r in res.items():
        cov = np.mean([any(r[i]["completion"] >= 0.8 for i in ids if cat[i] == c) for c in cats])
        L.append(f"| {k} | {np.mean([r[i]['score'] for i in ids]):.3f} | {np.mean([r[i]['completion'] for i in ids]):.3f} "
                 f"| {np.mean([r[i]['falls'] for i in ids]):.2f} | {cov:.2f} |")
    L += ["", f"## {a.ref} minus each other condition (paired over test clips; negative = {a.ref} better)", "",
          f"| vs | Δe overall [{CI:g}% CI] | " + " | ".join(cats) + " |", "|---|---|" + "---|" * len(cats)]
    passes = []
    for k in res:
        if k == a.ref:
            continue
        d = np.array([res[a.ref][i]["score"] - res[k][i]["score"] for i in ids])
        lo, hi = boot_ci([res[a.ref][i]["seeds"] for i in ids], [res[k][i]["seeds"] for i in ids], rng, grp_of(ids))
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
    if a.loo:
        L += ["", f"## Leave-one-clip-out: {a.ref} minus each condition with each test clip dropped", "",
              "| vs | Δe range | CI upper bound range | drops that flip the CI past 0 |", "|---|---|---|---|"]
        rl = np.random.default_rng(2)
        for k in res:
            if k == a.ref:
                continue
            ds, his, flips = [], [], []
            _, full_hi = boot_ci([res[a.ref][i]["seeds"] for i in ids], [res[k][i]["seeds"] for i in ids], rl, grp_of(ids))
            for drop in ids:
                sub = [i for i in ids if i != drop]
                ds.append(np.mean([res[a.ref][i]["score"] - res[k][i]["score"] for i in sub]))
                _, h = boot_ci([res[a.ref][i]["seeds"] for i in sub], [res[k][i]["seeds"] for i in sub], rl, grp_of(sub))
                his.append(h)
                if (h < 0) != (full_hi < 0):
                    flips.append(drop)
            L.append(f"| {k} | {min(ds):+.3f} .. {max(ds):+.3f} | {min(his):+.3f} .. {max(his):+.3f} | "
                     f"{', '.join(f'`{x}`' for x in flips) or 'none'} |")
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
