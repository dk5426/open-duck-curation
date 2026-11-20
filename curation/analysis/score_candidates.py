"""Exploratory: can a better selection score tell hard-but-feasible clips from infeasible ones? -> results/<tag>/SCORE_CANDIDATES.md

Analysis of the scoring policies' evaluations only (no training). Candidates, each computed per scorer and averaged over
the scorers like the curated ensemble:
  1. type-normalised: score_v3 divided by the median score_v3 of the clip's motion group. Groups: each locomotion type on
     its own; crouch, bow, sway, head and lean together as "stationary" (a lean is a held pose). Two references: the
     group's train clips (`typenorm_train`) or its clean held-out val clips (`typenorm_val`)
  2. learning progress: score_v3 at the final checkpoint divided by score_v3 at an early one. Hard but feasible clips
     keep improving; infeasible ones plateau, so their ratio stays near 1 (`progress_<M>`, `v3_x_progress_<M>`)
  3. balance only: base tilt error plus a fall penalty, ignoring joint and keypoint error (`balance`, `tilt`)
  4. threshold instead of a keep-fraction: keep every train clip that scores no worse than the worst clean val clip
     under the same candidate (label-free; only for candidates with val evaluations)

For each candidate: AUC of feasible (clean + feasible leans) vs infeasible, AUC of clean vs infeasible, and what a
plain top-45 cut (55%) and the threshold rule keep. Needs the evaluations from diag/score_candidates_evals.sh in
results/<tag>/score_candidates/ (early-checkpoint train scores, final-checkpoint val scores).

  OPENDUCK_ROOT=<dir> python3 score_candidates.py --tag cv7 --lib <clips_v7>
"""

import argparse
import glob
import json
import os
import re

import numpy as np

ROOT = os.environ["OPENDUCK_ROOT"]
C = os.path.join(ROOT, "open-duck-curation")
STATIONARY = ("crouch", "bow", "sway", "head", "lean")
E_FAIL = 3.0


def group(cat):
    return "stationary" if cat in STATIONARY else cat


def auc(pos, neg):
    """P(score of a positive (infeasible) > score of a negative), ties count half."""
    p, n = np.asarray(pos)[:, None], np.asarray(neg)[None]
    return float(((p > n) + 0.5 * (p == n)).mean())


def main():
    pa = argparse.ArgumentParser()
    pa.add_argument("--tag", required=True)
    pa.add_argument("--lib", required=True)
    pa.add_argument("--keep", type=int, default=55)
    a = pa.parse_args()
    OUT = os.path.join(C, "results", a.tag)
    SC = os.path.join(OUT, "score_candidates")
    man = json.load(open(os.path.join(a.lib, "manifest.json")))
    cat = {c["id"]: c["category"] for c in man["clips"]}
    train = [c["id"] for c in man["clips"] if c["split"] == "train"]
    val = [c["id"] for c in man["clips"] if c["split"] == "val"]
    inf = {c["id"]: bool(c["feasibility"]["infeasible"]) for c in man["clips"] if c["split"] == "train"}
    clean = [i for i in train if cat[i] != "lean"]
    bad = [i for i in train if inf[i]]
    good = [i for i in train if not inf[i]]

    seeds = sorted(int(re.search(r"_s(\d+)\.json", f).group(1)) for f in glob.glob(os.path.join(OUT, "scores_train_s*.json")))
    final = {s: json.load(open(os.path.join(OUT, f"scores_train_s{s}.json")))["clips"] for s in seeds}
    early, valf, vale = {}, {}, {}
    for f in glob.glob(os.path.join(SC, "scores_*_s*_*.json")):
        sp, s, st = re.search(r"scores_(train|val|valearly)_s(\d+)_(\d+)\.json", f).groups()
        d = json.load(open(f))["clips"]
        if sp == "val":
            valf[int(s)] = d
        elif sp == "valearly":
            vale.setdefault(int(st), {})[int(s)] = d
        else:
            early.setdefault(int(st), {})[int(s)] = d
    early = {st: v for st, v in early.items() if sorted(v) == seeds}
    has_val = sorted(valf) == seeds

    def balance(r):
        return r["tilt_err"] / 0.1 + E_FAIL * (1 - r["completion"])

    # candidate -> seed -> {clip: value}, for train (and val where it can be computed)
    cands, cands_val = {}, {}
    cands["score (original)"] = {s: {i: final[s][i]["score"] for i in train} for s in seeds}
    cands["score_v3 (current)"] = {s: {i: final[s][i]["score_v3"] for i in train} for s in seeds}
    cands["balance"] = {s: {i: balance(final[s][i]) for i in train} for s in seeds}
    cands["tilt"] = {s: {i: final[s][i]["tilt_err"] for i in train} for s in seeds}
    if has_val:
        cands_val["score (original)"] = {s: {i: valf[s][i]["score"] for i in val} for s in seeds}
        cands_val["score_v3 (current)"] = {s: {i: valf[s][i]["score_v3"] for i in val} for s in seeds}
        cands_val["balance"] = {s: {i: balance(valf[s][i]) for i in val} for s in seeds}
        cands_val["tilt"] = {s: {i: valf[s][i]["tilt_err"] for i in val} for s in seeds}
    tn_tr, tn_val, tn_val_v = {}, {}, {}
    for s in seeds:
        v3 = {i: final[s][i]["score_v3"] for i in train}
        med = {g: np.median([v3[i] for i in train if group(cat[i]) == g]) for g in {group(cat[i]) for i in train}}
        tn_tr[s] = {i: v3[i] / med[group(cat[i])] for i in train}
        if has_val:
            vv = {i: valf[s][i]["score_v3"] for i in val}
            vmed = {g: np.median([vv[i] for i in val if group(cat[i]) == g]) for g in {group(cat[i]) for i in val}}
            tn_val[s] = {i: v3[i] / vmed[group(cat[i])] for i in train}
            tn_val_v[s] = {i: vv[i] / vmed[group(cat[i])] for i in val}
    cands["1. typenorm_train"] = tn_tr
    if has_val:
        cands["1. typenorm_val"] = tn_val
        cands_val["1. typenorm_val"] = tn_val_v
    for st in sorted(early):
        m = round(st / 1e6)
        ratio = {s: {i: final[s][i]["score_v3"] / max(early[st][s][i]["score_v3"], 1e-6) for i in train} for s in seeds}
        cands[f"2. progress_{m}M"] = ratio
        cands[f"2. v3_x_progress_{m}M"] = {s: {i: final[s][i]["score_v3"] * ratio[s][i] for i in train} for s in seeds}
        if has_val:
            cands[f"1+2. typenorm_val_x_progress_{m}M"] = {s: {i: tn_val[s][i] * ratio[s][i] for i in train} for s in seeds}
        if has_val and sorted(vale.get(st, {})) == seeds:
            vr = {s: {i: valf[s][i]["score_v3"] / max(vale[st][s][i]["score_v3"], 1e-6) for i in val} for s in seeds}
            cands_val[f"2. progress_{m}M"] = vr
            cands_val[f"2. v3_x_progress_{m}M"] = {s: {i: valf[s][i]["score_v3"] * vr[s][i] for i in val} for s in seeds}
            cands_val[f"1+2. typenorm_val_x_progress_{m}M"] = {s: {i: tn_val_v[s][i] * vr[s][i] for i in val} for s in seeds}

    n_keep = int(round(a.keep / 100 * len(train)))
    rows, details = [], {}
    for name, per in cands.items():
        ens = {i: float(np.mean([per[s][i] for s in seeds])) for i in train}
        auc_g = auc([ens[i] for i in bad], [ens[i] for i in good])
        auc_c = auc([ens[i] for i in bad], [ens[i] for i in clean])
        per_auc = [auc([per[s][i] for i in bad], [per[s][i] for i in good]) for s in seeds]
        top = sorted(train, key=lambda i: (ens[i], i))[:n_keep]
        cut = (len([i for i in clean if i not in top]), len([i for i in bad if i in top]))
        thr = None
        if name in cands_val:
            ev = {i: float(np.mean([cands_val[name][s][i] for s in seeds])) for i in val}
            t = max(ev.values())
            kept = [i for i in train if ens[i] <= t]
            thr = (t, len(kept), len([i for i in clean if i not in kept]), len([i for i in bad if i in kept]))
        rows.append((name, auc_g, per_auc, auc_c, cut, thr))
        details[name] = ens
    rows_sorted = sorted(rows, key=lambda r: -r[1])

    L = [f"# Study {a.tag}: exploratory selection-score candidates", "",
         "EXPLORATORY (added 2026-11-19 after Phase 1 results; not pre-registered). No training: the scoring policies' "
         f"evaluations only. {len(train)} train clips: {len(clean)} clean, {len(good) - len(clean)} feasible leans, "
         f"{len(bad)} infeasible leans. Scorers: seeds {seeds}. Early checkpoints: "
         + (", ".join(f"{round(st / 1e6)}M" for st in sorted(early)) or "none") + ".", "",
         "AUC = probability an infeasible lean scores worse than a feasible clip (1 = perfect separation). The top-"
         f"{n_keep} cut ({a.keep}%) is a plain global cut without the coverage rule. The threshold rule keeps every train "
         "clip no worse than the worst clean val clip under the same candidate.", "",
         f"| candidate | AUC feasible vs infeasible | per scorer | AUC clean vs infeasible | top-{n_keep}: clean dropped / infeasible kept "
         "| threshold: value, clips kept, clean dropped, infeasible kept |",
         "|---|---|---|---|---|---|"]
    for name, ag, pa_, ac, cut, thr in rows_sorted:
        t = f"{thr[0]:.2f}, {thr[1]}, {thr[2]}, {thr[3]}" if thr else "n/a (no val evaluation)"
        L.append(f"| {name} | **{ag:.3f}** | {', '.join(f'{x:.3f}' for x in pa_)} | {ac:.3f} | {cut[0]} / {cut[1]} | {t} |")
    L += ["", "Reference: curated (score_v3 ensemble with the coverage rule) at 55% dropped 10 clean clips and kept 10 "
          "infeasible leans; stratified curation kept 31 clean and 6 infeasible; the oracle keeps all 37 clean and 0 "
          "infeasible.", ""]
    # per-category view of the best candidate against the current one
    best = rows_sorted[0][0]
    L += [f"## Ranks by motion type: `{best}` against `score_v3 (current)`", "",
          "| type | clips | worst rank, current | worst rank, best candidate |", "|---|---|---|---|"]
    rk = {n: {i: k + 1 for k, i in enumerate(sorted(train, key=lambda i: (details[n][i], i)))} for n in (best, "score_v3 (current)")}
    kinds = sorted({cat[i] for i in clean}) + ["feasible lean", "infeasible lean"]
    for k in kinds:
        m = ([i for i in clean if cat[i] == k] if k in cat.values() and k != "lean" else
             [i for i in train if cat[i] == "lean" and inf[i] == (k == "infeasible lean")])
        if m:
            L.append(f"| {k} | {len(m)} | {max(rk['score_v3 (current)'][i] for i in m)} | {max(rk[best][i] for i in m)} |")
    L += ["", "For infeasible leans the best rank (the first one kept) matters more: current "
          f"{min(rk['score_v3 (current)'][i] for i in bad)}, best candidate {min(rk[best][i] for i in bad)}.", ""]
    open(os.path.join(OUT, "SCORE_CANDIDATES.md"), "w").write("\n".join(L) + "\n")
    json.dump({n: details[n] for n in details}, open(os.path.join(SC, "candidates.json"), "w"), indent=1)
    print("wrote", os.path.join(OUT, "SCORE_CANDIDATES.md"))


if __name__ == "__main__":
    main()
