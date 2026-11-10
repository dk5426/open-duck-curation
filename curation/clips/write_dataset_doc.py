"""Write docs/DATASET.md from a library's manifest (counts, splits, dropped clips and the per-clip table), so the doc
never drifts from the data.

  python3 curation/clips/write_dataset_doc.py --lib data/clips_v4 --out docs/DATASET.md
"""

import argparse
import collections
import json
import os

GAITS = ("walk_fwd", "walk_back", "side_step", "turn_in_place", "walk_turn", "march")
STATIONARY = ("crouch", "bow", "sway", "head")


def describe(c):
    p = c["params"]
    cat = c["category"]
    if cat in GAITS:
        return (f"vx {p['mean_vx']:+.3f} m/s, vy {p['mean_vy']:+.3f}, yaw {p['mean_yaw_rate']:+.2f} rad/s; "
                f"{p['style']} (single support {p['single_support_s']} s, lift {100 * p['foot_lift_m']:.1f} cm)")
    if cat == "crouch":
        return f"depth {1000 * p['depth_m']:.1f} mm, down/up {p['move_s']} s, hold {p['hold_s']} s"
    if cat == "bow":
        return f"trunk pitch {p['pitch_deg']}°, down/up {p['move_s']} s, hold {p['hold_s']} s"
    if cat == "sway":
        return f"fore-aft sway ±{1000 * p['amp_m']:.0f} mm at {p['freq_hz']} Hz"
    return f"head {p['move'].replace('_', ' ')} at {p['freq_hz']} Hz"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = json.load(open(os.path.join(a.lib, "manifest.json")))
    name = os.path.basename(os.path.normpath(a.lib))
    clips = m["clips"]
    n = collections.Counter(c["split"] for c in clips)
    cats = [c for c in GAITS + STATIONARY if any(k["category"] == c for k in clips)]
    rows = []
    for cat in cats:
        cs = [c for c in clips if c["category"] == cat]
        src = {sp: len({c["source"] for c in cs if c["split"] == sp}) for sp in ("train", "val", "test")}
        cl = collections.Counter(c["split"] for c in cs)
        rows.append(f"| {cat} | {len({c['source'] for c in cs})} | {cl['train']} / {cl['val']} / {cl['test']} "
                    f"| {src['train']} / {src['val']} / {src['test']} |")
    table = []
    for cat in cats:
        for c in sorted((c for c in clips if c["category"] == cat), key=lambda c: c["id"]):
            ck = c["check"]
            table.append(f"| `{c['id']}` | {cat} | {c['split']} | {describe(c)} | {ck['peak_joint_speed_rad_s']:.1f}"
                         f"{' ⚠' if ck['fast_for_servo'] else ''} | {ck['joint_limit_margin_rad']:.3f} |")
    dropped = ", ".join(f"`{d}`" for d in m["dropped_by_checks"]) or "none"
    doc = f"""# Reference-clip dataset ({name})

Built by `curation/clips/make_library.py`; this file is written by `curation/clips/write_dataset_doc.py` from
`data/{name}/manifest.json`. GIFs of every clip: `results/{name}/<category>.gif` (kinematic replay).
**Status: draft for team review.** The splits and the check rules become final only when `PREREG.md` is signed off.

## Contents

- **{len(clips)} clips**, 50 Hz, up to {max(c['length'] for c in clips) / m['fps']:.0f} s. Train / val / test:
  **{n['train']} / {n['val']} / {n['test']}**.
- Model knee limit {m['knee_limit_rad']} rad (measured on the robot; the stock model has 1.57). Deepest crouch with
  every joint 0.03 rad inside its range: {1000 * m['max_crouch_drop_m']:.1f} mm.
- **Dropped by the hard checks ({len(m['dropped_by_checks'])}):** {dropped}.

| category | sources | clips train / val / test | sources train / val / test |
|---|---|---|---|
{chr(10).join(rows)}

## How the clips are made

- **Gaits** (`curation/clips/gen_gaits.sh`, Placo reference generator):
  - walking height 0.220 m, so the knee stays inside its range (upstream's 0.205 m bends it to 1.95 rad);
  - sources = walking directions (and foot-lift heights for `march`), 2 variants each: `normal` (single support
    0.30 s, foot lift 2.5 cm) and `gentle` (0.40 s, 1.5 cm);
  - head held at home; base height recomputed so the planted sole touches the floor; body-frame velocities and yaw rate
    recomputed from the recorded orientation (the generator's stored yaw rate is about 40× too small).
- **Crouch:** inverse kinematics, trunk upright, both soles fixed; min-jerk down, hold, up. Sources = depth as a
  fraction of the deepest crouch; variants fast (0.8 s moves, 1.0 s hold) / slow (1.5 s, 0.5 s).
- **Bow:** trunk pitched forward with the centre of mass kept over the feet; sources = pitch; variants fast / slow.
- **Sway:** the base sways fore-aft with the soles fixed; sources = amplitude; variants = frequency.
- **Head:** nod, shake, look around, tilt with the legs at home; variants = frequency.
- **Splits:** drawn per **source** after the checks (only sources with a passing variant), stratified by category,
  seed {m['split_seed']}: 1 val and 1 test source when a category has ≥ 3 sources, 1 val when it has 2, the rest
  train. Both variants of a source share its split (`splits.json`).

## Format (`library.npz` + `manifest.json`)

- `q`, `qd` (N, T, 14): joint targets and velocities, model actuator order.
- `base_pos`, `base_quat` (wxyz): base pose. `lin_vel`, `ang_vel`: body-frame base velocity.
- `contacts` (N, T, 2). `keypts` (N, T, 5, 3): body-frame left foot, right foot, left knee, right knee, head.
- `length`: real frames per clip (shorter clips are padded with their last frame).
- The manifest holds each clip's category, source, split, parameters and check report.

## Checks

- **Hard (clip dropped):** every joint inside its range; feet at least 8 cm apart (self-collision proxy); planted
  soles within 5 mm of the floor.
- **Soft (⚠ in the table):** peak joint speed above the STS3215's no-load 4.7 rad/s. How well a clip can actually be
  tracked is what the scoring step measures; that is the point of the study.

## Clips

| id | category | split | parameters | peak joint speed (rad/s) | joint-limit margin (rad) |
|---|---|---|---|---|---|
{chr(10).join(table)}
"""
    open(a.out, "w").write(doc)
    print("wrote", a.out, len(clips), "clips")


if __name__ == "__main__":
    main()
