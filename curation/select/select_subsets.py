"""Clip subsets for the curation study (S4.3-S4.5), following docs/PREREG.md P.3-P.6.

Input: per-clip scores of the TRAIN clips under the scoring policy (curation/eval/eval_clips.py --clips train) and the
library manifest. Output (JSON, one file per subset, each a list of clip ids, usable as CURATION_CLIPS):
  tau_candidates.json  the 40/55/70/85th percentiles of the train scores (P.4)
  curated_<pXX>.json   P.3 selection for each candidate tau
  random_s<seed>.json  P.5: uniform draws matched in duration to a given curated set (one per seed)
  kinematic.json       optional baseline: same size as the curated set, ranked by a kinematic-only score
                       (peak joint speed / servo speed + hip-roll demand + joint-limit closeness), same coverage rule
  checked.json         every train clip that passes the library's kinematic check (the cheap filter alone)

  python select_subsets.py --scores scores_train.json --manifest data/clips_v1/manifest.json --out subsets/ \
      [--match curated_p70.json --seeds 0 1 2]
"""

import argparse
import json
import os

import numpy as np

PERCENTILES = (40, 55, 70, 85)
MIN_COMPLETION, COVERAGE_COMPLETION = 0.8, 0.5


def curate(scores, man, tau):
    """P.3: keep clips with e <= tau and completion >= 0.8; each category keeps its best clip if completion >= 0.5."""
    cat = {c["id"]: c["category"] for c in man["clips"]}
    keep = {cid for cid, r in scores.items() if r["score"] <= tau and r["completion"] >= MIN_COMPLETION}
    for c in sorted(set(cat[i] for i in scores)):
        ids = [i for i in scores if cat[i] == c]
        best = min(ids, key=lambda i: scores[i]["score"])
        if scores[best]["completion"] >= COVERAGE_COMPLETION:
            keep.add(best)
    return sorted(keep)


def kinematic_score(c):
    ck = c["check"]
    return (ck["speed_vs_servo"] + ck["peak_hip_roll_dev_rad"] / 0.1
            + max(0.0, 0.1 - ck["joint_limit_margin_rad"]) / 0.1)


def kinematic_subset(man, train_ids, n):
    """Same size as the curated set, lowest kinematic score first, every category keeps its lowest-score clip."""
    by = {c["id"]: c for c in man["clips"] if c["id"] in train_ids}
    ranked = sorted(by, key=lambda i: kinematic_score(by[i]))
    keep = []
    for cat in sorted(set(c["category"] for c in by.values())):
        keep.append(min((i for i in by if by[i]["category"] == cat), key=lambda i: kinematic_score(by[i])))
    for i in ranked:
        if len(keep) >= n:
            break
        if i not in keep:
            keep.append(i)
    return sorted(keep)


def random_subset(man, train_ids, target_frames, seed):
    """P.5: uniform draw without replacement, stopping at the total duration closest to the target (the old 90% stop
    always left random about 10% shorter than curated, since every clip is 200 frames)."""
    rng = np.random.default_rng(seed)
    length = {c["id"]: c["length"] for c in man["clips"]}
    order = list(rng.permutation(sorted(train_ids)))
    out, total = [], 0
    for i in order:
        if abs(total + length[i] - target_frames) >= abs(total - target_frames):
            break
        out.append(i)
        total += length[i]
    return sorted(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scores", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--match", default=None, help="curated subset file to match random / kinematic subsets to")
    p.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2])
    p.add_argument("--percentiles", type=int, nargs="+", default=list(PERCENTILES))
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    man = json.load(open(a.manifest))
    scores = json.load(open(a.scores))["clips"]
    train = {c["id"] for c in man["clips"] if c["split"] == "train"}
    assert set(scores) <= train, "scores must be for train clips only"
    vals = np.array([scores[i]["score"] for i in scores])
    cands = {f"p{q}": float(np.percentile(vals, q)) for q in a.percentiles}
    json.dump(cands, open(os.path.join(a.out, "tau_candidates.json"), "w"), indent=1)
    print("train scores:", ", ".join(f"{i}={scores[i]['score']:.2f}" for i in sorted(scores, key=lambda k: scores[k]['score'])))
    for name, tau in cands.items():
        sub = curate(scores, man, tau)
        json.dump(sub, open(os.path.join(a.out, f"curated_{name}.json"), "w"), indent=1)
        print(f"tau {name} = {tau:.3f}: curated {len(sub)} clips")
    checked = sorted(c["id"] for c in man["clips"] if c["split"] == "train" and c["check"]["pass"])
    json.dump(checked, open(os.path.join(a.out, "checked.json"), "w"), indent=1)
    print(f"checked: {len(checked)} clips")
    if a.match:
        ref = json.load(open(a.match))
        length = {c["id"]: c["length"] for c in man["clips"]}
        target = sum(length[i] for i in ref)
        for s in a.seeds:
            sub = random_subset(man, train, target, s)
            json.dump(sub, open(os.path.join(a.out, f"random_s{s}.json"), "w"), indent=1)
            print(f"random seed {s}: {len(sub)} clips")
        kin = kinematic_subset(man, train, len(ref))
        json.dump(kin, open(os.path.join(a.out, "kinematic.json"), "w"), indent=1)
        print(f"kinematic: {len(kin)} clips")


if __name__ == "__main__":
    main()
