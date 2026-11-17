"""Why curation loses: does trackability ranking drop hard-but-feasible clean clips? -> results/<tag>/MECHANISM.md, .png

Analysis only (no training). Uses the ensemble selection score from selection_validation.json, the subsets and the
nominal test results of a run_curve.py study.
  1. score overlap: where clean clips, feasible leans and infeasible leans fall in the curated ranking; how many clean
     clips score worse than infeasible leans; the AUC of the score for clean vs infeasible
  2. what curated drops at each keep-fraction: clean clips dropped while infeasible leans are kept, and their rank
  3. link to the test loss: per (val / test category, fraction), the share of the category's train clips curated
     dropped against curated minus oracle test e in that category (oracle keeps every clean clip up to 55%)

  cd Open_Duck_Playground && python mechanism.py --tag cv7 --lib <clips_v7>
"""

import argparse
import json
import os

import matplotlib
import numpy as np
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.environ["OPENDUCK_ROOT"]
C = os.path.join(ROOT, "open-duck-curation")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    p.add_argument("--lib", required=True)
    p.add_argument("--fractions", type=int, nargs="+", default=[40, 55, 70, 85])
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    a = p.parse_args()
    OUT = os.path.join(C, "results", a.tag)
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    train = [c for c in man["clips"] if c["split"] == "train"]
    cat = {c["id"]: c["category"] for c in man["clips"]}
    judged = sorted({c["category"] for c in man["clips"] if c["split"] in ("val", "test")})
    inf = {c["id"]: bool(c["feasibility"]["infeasible"]) for c in train}
    sv = json.load(open(os.path.join(OUT, "selection_validation.json")))
    ens, sel = sv["ensemble"], sv["selection_score"]
    tid = sorted(ens, key=lambda i: (ens[i], i))
    rank = {i: k + 1 for k, i in enumerate(tid)}
    kind = {i: "clean" if cat[i] != "lean" else ("infeasible lean" if inf[i] else "feasible lean") for i in tid}
    clean = [i for i in tid if kind[i] == "clean"]
    bad = [i for i in tid if kind[i] == "infeasible lean"]
    L = [f"# Study {a.tag}: why curation drops clean clips", "",
         f"Ranking: ensemble `{sel}` over {len(sv['candidates'][sel]['auc_per_scorer'])} scoring policies, lower = kept "
         f"first. {len(clean)} clean clips, {sum(k == 'feasible lean' for k in kind.values())} feasible leans, "
         f"{len(bad)} infeasible leans.", ""]

    # 1. overlap
    xc, xb = np.array([ens[i] for i in clean]), np.array([ens[i] for i in bad])
    auc = float(((xb[:, None] > xc[None]) + 0.5 * (xb[:, None] == xc[None])).mean())
    worse_any = [i for i in clean if ens[i] > xb.min()]
    worse_med = [i for i in clean if ens[i] > np.median(xb)]
    L += ["## 1. Score overlap", "",
          f"- AUC, clean vs infeasible leans: **{auc:.3f}** (1 = every infeasible lean scores worse than every clean clip).",
          f"- Clean clips scoring worse than the best-scoring infeasible lean: **{len(worse_any)} of {len(clean)}**.",
          f"- Clean clips scoring worse than the median infeasible lean: **{len(worse_med)} of {len(clean)}**: "
          + (", ".join(f"`{i}`" for i in worse_med) or "none") + ".", "",
          "| category | clean train clips | median score | worst score | worst rank (of 82) |", "|---|---|---|---|---|"]
    for c in judged:
        m = [i for i in clean if cat[i] == c]
        if m:
            L.append(f"| {c} | {len(m)} | {np.median([ens[i] for i in m]):.2f} | {max(ens[i] for i in m):.2f} | "
                     f"{max(rank[i] for i in m)} |")
    L.append(f"| infeasible lean | {len(bad)} | {np.median(xb):.2f} | {xb.max():.2f} | {max(rank[i] for i in bad)} |")
    L.append("")

    # 2. drops per fraction
    L += ["## 2. What curated drops", "", "| keep | clean dropped | infeasible leans kept | clean dropped while ranked "
          "below a kept infeasible lean |", "|---|---|---|---|"]
    drop = {}
    for f in a.fractions:
        ids = set(json.load(open(os.path.join(OUT, "subsets", f"curated_f{f}.json"))))
        drop[f] = {c: 1 - sum(i in ids for i in tid if cat[i] == c) / sum(cat[i] == c for i in tid) for c in judged}
        dc = [i for i in clean if i not in ids]
        kb = [i for i in bad if i in ids]
        under = [i for i in dc if kb and ens[i] > min(ens[j] for j in kb)]
        L.append(f"| {f}% | {len(dc)} | {len(kb)} | {len(under)} |")
    ids55 = set(json.load(open(os.path.join(OUT, "subsets", "curated_f55.json"))))
    kb55 = sorted((i for i in bad if i in ids55), key=lambda i: ens[i])
    L += ["", "At 55%, each dropped clean clip and the infeasible leans kept ahead of it:", "",
          "| dropped clean clip | score | rank | infeasible leans kept with a better score |", "|---|---|---|---|"]
    for i in sorted((i for i in clean if i not in ids55), key=lambda i: ens[i]):
        L.append(f"| `{i}` | {ens[i]:.2f} | {rank[i]} | {sum(ens[j] < ens[i] for j in kb55)} of {len(kb55)} |")
    per = [json.load(open(os.path.join(OUT, x)))["clips"] for x in sorted(os.listdir(OUT)) if x.startswith("scores_train_s")]
    byid = {c["id"]: c for c in train}
    L += ["", "The infeasible leans curated keeps at 55% (they fail the static hold test; the scoring policies' falls):", "",
          "| lean | lean size (cm) | score | scorer falls (of 10 per scorer) |", "|---|---|---|---|"]
    for i in kb55:
        L.append(f"| `{i}` | {100 * byid[i]['params'].get('dx_m', 0):+.1f} | {ens[i]:.2f} | "
                 f"{', '.join(str(s[i]['falls']) for s in per)} |")
    L.append("")

    # 3. link to test loss
    def cat_e(cond, f):
        fs = [os.path.join(OUT, "test", f"{cond}_f{f}_s{s}_nominal.json") for s in a.seeds]
        if not all(os.path.exists(x) for x in fs):
            return None
        per = {}
        for x in fs:
            for k, v in json.load(open(x))["clips"].items():
                per.setdefault(cat[k], []).append(v["score"])
        return {c: float(np.mean(v)) for c, v in per.items()}

    pts = []
    for f in a.fractions:
        cu, orc = cat_e("curated", f), cat_e("oracle", f)
        if cu and orc:
            pts += [(f, c, drop[f][c], cu[c] - orc[c]) for c in judged if c in cu and c in orc]
    L += ["## 3. Dropped clean clips against the test loss", "",
          "Per (category, fraction): the share of the category's train clips curated dropped, and curated minus oracle "
          "mean test e in that category (3 seeds). Oracle keeps every clean clip at 55% and above and 27 of 37 at 40%.", ""]
    if len(pts) > 3:
        x, y = np.array([q[2] for q in pts]), np.array([q[3] for q in pts])
        r, pr = stats.spearmanr(x, y)
        L += [f"Spearman ρ = **{r:.2f}** (p = {pr:.3g}, n = {len(pts)} category × fraction points; points share policies, "
              "so p is optimistic).", "",
              "| fraction | category | share dropped | curated − oracle e |", "|---|---|---|---|"]
        L += [f"| {f}% | {c} | {d:.2f} | {e:+.3f} |" for f, c, d, e in sorted(pts, key=lambda q: -q[3])[:12]]
        L += ["", "(the 12 largest losses)", ""]

    # figure
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    groups = [*judged, "feasible lean", "infeasible lean"]
    col = {"clean": "#4C78A8", "feasible lean": "#54A24B", "infeasible lean": "#E45756"}
    rng = np.random.default_rng(0)
    for g, name in enumerate(groups):
        m = [i for i in tid if (cat[i] == name and kind[i] == "clean") or kind[i] == name]
        ax[0].scatter(g + rng.uniform(-0.18, 0.18, len(m)), [ens[i] for i in m], s=22,
                      c=col["clean" if name in judged else name], edgecolors="none")
    for f in a.fractions:
        n = int(round(f / 100 * len(tid)))
        ax[0].axhline((ens[tid[n - 1]] + ens[tid[min(n, len(tid) - 1)]]) / 2, ls=":", lw=1, c="0.4")
        ax[0].text(len(groups) - 0.45, ens[tid[n - 1]], f"{f}% cut", fontsize=8, va="bottom", ha="right", c="0.3")
    ax[0].set_xticks(range(len(groups)), [g.replace("_", " ") for g in groups], rotation=35, ha="right", fontsize=8)
    ax[0].set_ylabel(f"ensemble {sel} (lower = kept first)")
    ax[0].set_yscale("log")
    ax[0].set_title("Train clips by category: clean (blue), feasible / infeasible leans")
    if pts:
        cm = dict(zip(a.fractions, ["#72B7B2", "#4C78A8", "#F58518", "#B279A2"]))
        for f in a.fractions:
            q = [t for t in pts if t[0] == f]
            ax[1].scatter([t[2] for t in q], [t[3] for t in q], s=30, c=cm[f], label=f"{f}%")
        for f, c, d, e in sorted(pts, key=lambda q: -q[3])[:5]:
            ax[1].annotate(c.replace("_", " "), (d, e), fontsize=7, xytext=(3, 3), textcoords="offset points")
        ax[1].axhline(0, c="0.6", lw=0.8)
        ax[1].set_xlabel("share of the category's train clips curated dropped")
        ax[1].set_ylabel("curated − oracle test e in that category")
        ax[1].legend(title="keep", fontsize=8)
        ax[1].set_title("More clean clips dropped, larger test loss")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "MECHANISM.png"), dpi=150)
    L += ["![mechanism](MECHANISM.png)", ""]
    open(os.path.join(OUT, "MECHANISM.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "MECHANISM.md"))


if __name__ == "__main__":
    main()
