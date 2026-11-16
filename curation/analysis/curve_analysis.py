"""PREREG v2 analysis of a run_curve.py study -> results/<tag>/SUMMARY.md (+ comparison_*.md).

  1. selection validation: AUC of each candidate score for flagging the measured-infeasible train clips, stability
     across the three scorers, the score chosen
  2. subset composition: leans and measured-infeasible clips each selector kept at each fraction
  3. the curve: mean test e (nominal) per selector and fraction, mean and seed range; curated minus each other selector
     at every fraction with the source-level 95% CI
  4. primary (main fraction, nominal, original score e): compare_conditions.py --group source --loo, curated against
     full, random, kinematic, oracle; the pass bar; then score_v2, score_v3, tilt_err, and push / friction
  5. training cost (main fraction and full): wall-clock and steps per hour from the checkpoint times, validation e at
     25 / 50 / 75 / 100% of training, steps and hours to reach the threshold 1.1 x the best final validation e

  cd Open_Duck_Playground && python curve_analysis.py --tag cv7 --lib <clips_v7> [--fractions 40 55 70 85 --main 55]
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_conditions as cc  # noqa: E402

ROOT = os.environ["OPENDUCK_ROOT"]
C = os.path.join(ROOT, "open-duck-curation")
RUNS = os.path.join(ROOT, "runs")
METRICS = ("score", "score_v2", "score_v3", "tilt_err")
TESTS = ("nominal", "push03", "push06", "fric06")
THRESH = 1.1


def ckpt_times(name):
    """[(step, datetime)] of a run's checkpoints (folder names YYYY_MM_DD_HHMMSS_step)."""
    d = os.path.join(RUNS, name)
    out = []
    for x in os.listdir(d):
        if x[:4].isdigit() and not x.endswith(".onnx"):
            *t, s = x.split("_")
            out.append((int(s), datetime.datetime.strptime("_".join(t), "%Y_%m_%d_%H%M%S")))
    return sorted(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    p.add_argument("--lib", required=True)
    p.add_argument("--fractions", type=int, nargs="+", default=[40, 55, 70, 85])
    p.add_argument("--main", type=int, default=55)
    p.add_argument("--selectors", nargs="+", default=["curated", "kinematic", "oracle", "random"])
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    a = p.parse_args()
    T, OUT = a.tag, os.path.join(C, "results", a.tag)
    TEST, VAL, SUB = (os.path.join(OUT, x) for x in ("test", "val_ckpts", "subsets"))
    manp = os.path.join(a.lib, "manifest.json")
    man = json.load(open(manp))
    cat = {c["id"]: c["category"] for c in man["clips"]}
    cc.GROUPS = {c["id"]: c["source"] for c in man["clips"]}
    infeasible = {c["id"]: c["feasibility"]["infeasible"] for c in man["clips"] if c["split"] == "train"}
    rng = np.random.default_rng(0)
    L = [f"# Study {T}: summary (PREREG v2)", "", f"Library `{os.path.basename(a.lib)}`: {len(infeasible)} train clips "
         f"({sum(infeasible.values())} measured infeasible), "
         f"{sum(c['split'] == 'test' for c in man['clips'])} test clips. Seeds {a.seeds}. Lower e is better.", ""]

    # 1. selection validation
    sv = json.load(open(os.path.join(OUT, "selection_validation.json")))
    L += ["## Selection score validation", "", "| candidate | AUC (mean over scorers) | per scorer | Spearman between scorers |",
          "|---|---|---|---|"]
    for m, v in sv["candidates"].items():
        L.append(f"| {m} | {v['auc']:.3f} | {', '.join(f'{x:.3f}' for x in v['auc_per_scorer'])} | "
                 f"{', '.join(f'{x:.2f}' for x in v['spearman_between_scorers'])} |")
    L += ["", f"Selection score: **{sv['selection_score']}** (highest AUC; within {sv['tie']} the original score wins).", ""]
    # label stability (curation/clips/label_stability.py): AUCs and kept counts without the borderline clips
    stab = json.load(open(os.path.join(a.lib, "label_stability.json")))["clips"]
    border = {i for i, v in stab.items() if v["borderline"]}
    L += [f"Label stability: {len(border)} of {len(stab)} held poses are borderline (< 80% of 27 perturbed hold tests "
          f"agree with the label): {', '.join(f'`{i}`' for i in sorted(border)) or 'none'}.", ""]
    if border:
        per = [json.load(open(os.path.join(OUT, x)))["clips"] for x in sorted(os.listdir(OUT))
               if x.startswith("scores_train_s")]
        keep = [i for i in infeasible if i not in border]
        L += ["| candidate | AUC without the borderline clips (mean over scorers) |", "|---|---|"]
        for m in sv["candidates"]:
            vals = []
            for sc in per:
                x = np.array([sc[i]["falls"] / sc[i]["rollouts"] if m == "fall_rate" else sc[i][m] for i in keep])
                y = np.array([infeasible[i] for i in keep])
                pos, neg = x[y], x[~y]
                vals.append(float(((pos[:, None] > neg[None]) + 0.5 * (pos[:, None] == neg[None])).mean()))
            L.append(f"| {m} | {np.mean(vals):.3f} |")
        L.append("")

    # 2. composition
    L += ["## Subsets: clean clips, leans and measured-infeasible clips kept", "", "| selector | " +
          " | ".join(f"{f}%" for f in a.fractions) + " |", "|---|" + "---|" * len(a.fractions)]
    for s_ in a.selectors:
        row = []
        for f in a.fractions:
            name = f"{s_}_f{f}" + ("_s0" if s_ == "random" else "")
            ids = json.load(open(os.path.join(SUB, name + ".json")))
            row.append(f"{len(ids)} clips: {sum(cat[i] != 'lean' for i in ids)} clean, {sum(cat[i] == 'lean' for i in ids)} leans, "
                       f"{sum(infeasible[i] for i in ids)} infeasible, {sum(i in border for i in ids)} borderline")
        L.append(f"| {s_}{' (seed 0)' if s_ == 'random' else ''} | " + " | ".join(row) + " |")
    L.append("")

    # 3. the curve
    def files(cond, f, test="nominal"):
        stem = cond if cond in ("full", "checked") or cond.startswith("curatedscore") else f"{cond}_f{f}"
        return ",".join(os.path.join(TEST, f"{stem}_s{s}_{test}.json") for s in a.seeds)

    res = {(s_, f): cc.load(files(s_, f)) for s_ in a.selectors for f in a.fractions}
    full = cc.load(files("full", None))
    chk = cc.load(files("checked", None))
    ids = sorted(full)
    mean = lambda r: np.mean([r[i]["score"] for i in ids])  # noqa: E731
    seedm = lambda r: [np.mean([r[i]["seeds"][k] for i in ids]) for k in range(len(a.seeds))]  # noqa: E731
    L += ["## The curve: mean test e (nominal), mean over seeds [seed range]", "",
          f"full (all {len(infeasible)} clips): {mean(full):.3f} [{min(seedm(full)):.3f}, {max(seedm(full)):.3f}]; "
          f"checked (every kinematic-check pass, natural size): {mean(chk):.3f} [{min(seedm(chk)):.3f}, {max(seedm(chk)):.3f}]", "",
          "| selector | " + " | ".join(f"{f}%" for f in a.fractions) + " |", "|---|" + "---|" * len(a.fractions)]
    for s_ in a.selectors:
        L.append(f"| {s_} | " + " | ".join(f"{mean(res[(s_, f)]):.3f} [{min(seedm(res[(s_, f)])):.3f}, "
                                          f"{max(seedm(res[(s_, f)])):.3f}]" for f in a.fractions) + " |")
    L += ["", "Curated minus each selector (source-level 95% CI; negative = curated better):", "",
          "| vs | " + " | ".join(f"{f}%" for f in a.fractions) + " |", "|---|" + "---|" * len(a.fractions)]
    grp = cc.grp_of(ids)
    for other in ["full", *[s_ for s_ in a.selectors if s_ != "curated"]]:
        row = []
        for f in a.fractions:
            ref, oth = res[("curated", f)], full if other == "full" else res[(other, f)]
            d = np.mean([ref[i]["score"] - oth[i]["score"] for i in ids])
            lo, hi = cc.boot_ci([ref[i]["seeds"] for i in ids], [oth[i]["seeds"] for i in ids], rng, grp)
            row.append(f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        L.append(f"| {other} | " + " | ".join(row) + " |")
    L.append("")

    # 4. primary and secondary at the main fraction
    LF = f"curatedscore_f{a.main}"  # curated by the original score (label-free), run when validation picked another

    def label_free(test):
        return [f"{LF}={files(LF, None, test)}"] if os.path.exists(os.path.join(TEST, f"{LF}_s{a.seeds[0]}_{test}.json")) \
            else []

    py = sys.executable
    for test in TESTS:
        for m in METRICS if test == "nominal" else ("score",):
            conds = [f"curated={files('curated', a.main, test)}", f"full={files('full', None, test)}",
                     *[f"{s_}={files(s_, a.main, test)}" for s_ in a.selectors if s_ != "curated"],
                     f"checked={files('checked', None, test)}", *label_free(test)]
            out = os.path.join(OUT, f"comparison_f{a.main}_{test}_{m}.md")
            subprocess.run([py, os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare_conditions.py"),
                            "--manifest", manp, "--cond", *conds, "--metric", m, "--group", "source",
                            *(["--loo"] if (test, m) == ("nominal", "score") else []),
                            "--title", f"Study {T}, {a.main}% keep-fraction, test {test}, {m}", "--out", out],
                           check=True, capture_output=True)
            body = open(out).read().split("\n")
            end = body.index("## Secondary: test clips inside vs outside the training parameter range")
            keep = [ln for ln in body[:end] if (ln.startswith("| ") and not ln.startswith(("| `", "| clip ")))
                    or ln.startswith(("- ", "## Leave"))]
            primary = (test, m) == ("nominal", "score")
            L += [f"## {'PRIMARY: ' if primary else ''}{a.main}% keep-fraction, test {test}, {m}", "", *keep, ""]

    # 5. training cost
    L += [f"## Training cost ({a.main}% keep-fraction and full)", ""]
    rows, finals = [], {}
    for cond in ["full", *a.selectors, "checked", *([LF] if label_free("nominal") else [])]:
        stem = cond if cond in ("full", "checked", LF) else f"{cond}_f{a.main}"
        hrs, sph, curve = [], [], {}
        for s in a.seeds:
            ct = ckpt_times(f"{T}_{stem}_s{s}")
            h = (ct[-1][1] - ct[0][1]).total_seconds() / 3600
            hrs.append(h)
            sph.append(ct[-1][0] / h / 1e6 if h else float("nan"))
            for fn in os.listdir(VAL):
                if fn.startswith(f"{stem}_s{s}_"):
                    step = int(fn.rsplit("_", 1)[1].split(".")[0])
                    e = np.mean([v["score"] for v in json.load(open(os.path.join(VAL, fn)))["clips"].values()])
                    curve.setdefault(s, []).append((step, e))
        for s in curve:
            curve[s].sort()
        finals[cond] = float(np.mean([curve[s][-1][1] for s in curve]))
        rows.append((cond, hrs, sph, curve))
    thr = THRESH * min(finals.values())
    L += [f"Threshold: validation e ≤ {thr:.3f} ({THRESH} × the best final validation e). Headline cost: M steps to "
          "threshold. Wall-clock is secondary: evaluations share the GPU with training and launches wait for them.", "",
          "| condition | M steps to threshold (per seed) | val e at 25 / 50 / 75 / 100% | h to threshold | wall-clock h | M steps / h |",
          "|---|---|---|---|---|---|"]
    for cond, hrs, sph, curve in rows:
        pts = np.mean([[e for _, e in curve[s]] for s in curve], axis=0) if curve else []
        reach, reach_h = [], []
        for s, c in curve.items():
            hit = next((st for st, e in c if e <= thr), None)
            reach.append(hit / 1e6 if hit is not None else float("nan"))
            reach_h.append(hit / 1e6 / sph[a.seeds.index(s)] if hit is not None else float("nan"))
        L.append(f"| {cond} | {', '.join('—' if np.isnan(x) else f'{x:.0f}' for x in reach)} | "
                 f"{' / '.join(f'{x:.3f}' for x in pts)} | "
                 f"{', '.join('—' if np.isnan(x) else f'{x:.2f}' for x in reach_h)} | {np.mean(hrs):.2f} | {np.nanmean(sph):.0f} |")
    # selection overhead: what each selector costs before any final policy trains
    sc_h = []
    for x in sorted(os.listdir(RUNS)):
        if x.startswith(f"{T}_score_s"):
            ct = ckpt_times(x)
            sc_h.append((ct[-1][1] - ct[0][1]).total_seconds() / 3600)
    ev = [ln for ln in open(os.path.join(OUT, "study.log")) if "scores_train_s" in ln and " eval " in ln]
    L += ["", "**Selection overhead** (paid once, before any final policy trains):", "",
          f"- curated: {len(sc_h)} scoring policies, {sum(sc_h):.1f} GPU-h of training "
          f"({', '.join(f'{h:.2f}' for h in sc_h)} h), plus scoring every train clip with each ({len(ev)} evaluations)",
          "- kinematic: the kinematic check, seconds of CPU", "- oracle (physics filter): the hold test, about a "
          "second of CPU per clip", "- random, full: none",
          "", "Total GPU-h per condition at this fraction = 3 seeds × wall-clock above, plus the overhead for curated."]
    open(os.path.join(OUT, "SUMMARY.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "SUMMARY.md"))


if __name__ == "__main__":
    main()
