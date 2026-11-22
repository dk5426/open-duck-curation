"""Dataset v9: 14 motion types, clean clips split by source, and ~25 broken TRAIN copies inside their own types.

Types: walk_fwd, walk_back, side_step, turn_in_place, walk_turn (Placo gaits); leg_lift (march gaits + keyframed
stomp / kick / tap); crouch, bow, sway, head (IK, make_library); hop, dance, headbang, twist (keyframed, make_wild).
Clean clips per type: 6 train, 3 val, 5 test. Split BY SOURCE, fixed by design below (no random draw): a gait or
stationary train source gives 2 variants (styles), a val / test source 1; a keyframed source is 1 clip. Val / test
sources never appear in train; test parameters are new values, mostly inside the train range.

Clean = passes make_library.check_clip; a keyframed clip must also be no more demanding than the clean v7 walking
gaits on the reference-only measures of dynamic_check.py (servo lag <= the worst v7 gait's, balance margin >= the
worst v7 gait's) and a hop must be within the legs' take-off speed. A listed source that fails is replaced by the
type's next spare (recorded in the manifest).

Broken copies (train only, category = their type, "derived_from" = the clean train clip), two families:
  impossible (physics-verified, feasibility.infeasible = true)
    shove          base pushed forward >= 12 cm / back >= 7 cm along the heading with the soles kept where they were
                   (IK, sole error <= 3 cm; gaits are shoved back, a 12 cm forward shove is out of the legs' reach); the
                   hold test fails on the shoved double-support pose (grown in 2 cm steps until it does)
    joint_limit    a keyframed clip with its amplitude pushed past a joint limit (the targets clip at the limit:
                   check_clip fails with zero joint-limit margin)
    takeoff        a hop whose flight needs more take-off speed than the legs give (dynamic_check takeoff_fail)
    speed          the clip time-compressed 2-3x (same poses, faster, shorter); kept only if its servo lag exceeds the
                   worst clean v7 walking gait's lag (the bar is measured from clips_v7 and recorded)
    one_foot_long  one foot held up for 2-3 s with the CoM not over the stance foot (a sole raised 2.5-3.5 cm and forward by IK on a
                   double-support clip, or a keyframed leg lift's single-support frame held 2.5 s); the hold test, which
                   fails when the raised foot comes down or the robot tips, must fail; the raised sole must clear the
                   floor by > 8 mm; for this test the stance sole is set on the floor (candidates the robot can hold are
                   dropped)
  corrupted (labelled by construction, feasibility.infeasible = false, corrupted = true)
    noise          band-limited random jitter on every joint target (3-8 Hz, 0.07 rad RMS)
    glitch         3 short pose jumps (4 frames, 2-3 joints, 0.3-0.5 rad) that snap back
    foot_skate     the left sole slides 4 cm forward and back while marked in contact (IK re-solve)

  1. new Placo gait sources (CPU):
     python3 curation/clips/make_v9.py --presets <reference_motion_generator dir> data/placo_gaits_v9
     (writes presets + names.txt, then runs the generator; same settings as gen_gaits.sh)
  2. cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_v9.py \
         --gaits ../open-duck-curation/data/placo_gaits_v9 --v7 ../open-duck-curation/data/clips_v7 \
         --out ../open-duck-curation/data/clips_v9
  3. python3 curation/clips/make_v9.py --verify data/clips_v9 --doc docs/DATASET_V9.md

v9x (--extend-test): clips_v9 with 7 more clean test sources per type (12 test clips per type); every clips_v9 clip
is copied unchanged (same id, index and arrays), the new ones are appended with "new_in": "v9x". New sources follow
the rules above (new values, one variant each, same clean checks, failing sources replaced by the type's v9x spares).
  1. python3 curation/clips/make_v9.py --extend-test data/clips_v9 --presets <reference_motion_generator dir> data/placo_gaits_v9x
  2. cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_v9.py \
         --extend-test ../open-duck-curation/data/clips_v9 --gaits ../open-duck-curation/data/placo_gaits_v9x \
         --v7 ../open-duck-curation/data/clips_v7 --out ../open-duck-curation/data/clips_v9x
  3. python3 curation/clips/make_v9.py --verify data/clips_v9x --doc docs/DATASET_V9X.md
"""

import argparse
import collections
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = ["walk_fwd", "walk_back", "side_step", "turn_in_place", "walk_turn", "leg_lift", "crouch", "bow", "sway",
         "head", "hop", "dance", "headbang", "twist"]
GAIT_TYPES = TYPES[:5]
STYLE_PRM = {"normal": (0.30, 0.025, 15), "gentle": (0.40, 0.015, 20)}  # single support s, foot lift m, timesteps
SEED = 9

# gait sources as exact strings (dx, dy, dth): train 3 (both styles), val 3, test 5 (one style each), spares
GAITS = {
    "walk_fwd": dict(train=[("0.02", "0", "0"), ("0.04", "0", "0"), ("0.06", "0", "0")],
                     val=[("0.03", "0", "0"), ("0.05", "0", "0"), ("0.015", "0", "0")],
                     test=[("0.025", "0", "0"), ("0.035", "0", "0"), ("0.045", "0", "0"), ("0.055", "0", "0"),
                           ("0.0275", "0", "0")],
                     spare=[("0.0325", "0", "0"), ("0.0375", "0", "0"), ("0.0525", "0", "0")]),
    "walk_back": dict(train=[("-0.02", "0", "0"), ("-0.03", "0", "0"), ("-0.04", "0", "0")],
                      val=[("-0.025", "0", "0"), ("-0.035", "0", "0"), ("-0.015", "0", "0")],
                      test=[("-0.0225", "0", "0"), ("-0.0275", "0", "0"), ("-0.0325", "0", "0"), ("-0.0375", "0", "0"),
                            ("-0.045", "0", "0")],
                      spare=[("-0.0175", "0", "0"), ("-0.0425", "0", "0")]),
    "side_step": dict(train=[("0", "0.015", "0"), ("0", "-0.02", "0"), ("0", "0.03", "0")],
                      val=[("0", "-0.015", "0"), ("0", "0.025", "0"), ("0", "-0.03", "0")],
                      test=[("0", "0.02", "0"), ("0", "-0.025", "0"), ("0", "0.0225", "0"), ("0", "-0.0175", "0"),
                            ("0", "0.0275", "0")],
                      spare=[("0", "-0.0225", "0"), ("0", "0.0175", "0"), ("0", "-0.0275", "0"), ("0", "0.0125", "0")]),
    "turn_in_place": dict(train=[("0", "0", "0.15"), ("0", "0", "-0.15"), ("0", "0", "0.30")],
                          val=[("0", "0", "-0.30"), ("0", "0", "0.20"), ("0", "0", "-0.10")],
                          test=[("0", "0", "0.25"), ("0", "0", "-0.25"), ("0", "0", "-0.20"), ("0", "0", "0.10"),
                                ("0", "0", "0.175")],
                          spare=[("0", "0", "-0.175"), ("0", "0", "0.225"), ("0", "0", "-0.225"), ("0", "0", "0.125")]),
    "walk_turn": dict(train=[("0.04", "0", "0.15"), ("0.03", "0", "-0.10"), ("0.02", "0", "-0.15")],
                      val=[("0.04", "0", "-0.15"), ("0.02", "0", "0.15"), ("0.03", "0", "0.10")],
                      test=[("0.03", "0", "0.20"), ("0.035", "0", "-0.12"), ("0.025", "0", "0.12"), ("0.035", "0", "0.08"),
                            ("0.025", "0", "-0.18")],
                      spare=[("0.04", "0", "0.10"), ("0.03", "0", "-0.15"), ("0.02", "0", "0.10")]),
}
MARCH = dict(train=["0.015", "0.025"], val=["0.02"], test=["0.03", "0.0175"], spare=["0.0225", "0.0125"])
DY = 0.045  # keyframed leg lifts: sideways weight shift (the 2.5 cm shift is worse balanced than v7 walking)
LEG_WILD = dict(train=[("stomp", dict(lift=0.015, period=1.6, dy=DY)), ("kick", dict(r=0.03, tau=0.4, dy=DY))],
                val=[("tap", dict(reach=0.03, period=1.2, dy=DY)), ("stomp", dict(lift=0.02, period=1.4, dy=DY))],
                test=[("kick", dict(r=0.045, tau=0.5, dy=DY)), ("tap", dict(reach=0.035, period=1.4, dy=DY)),
                      ("stomp", dict(lift=0.025, period=1.2, dy=DY))],
                spare=[("kick", dict(r=0.04, tau=0.4, dy=DY)), ("stomp", dict(lift=0.02, period=1.6, dy=DY)),
                       ("tap", dict(reach=0.03, period=1.6, dy=DY))])
# stationary: train sources (2 variants each), val / test (source, variant)
STAT = {
    "crouch": dict(train=[0.2, 0.5, 1.0], val=[(0.35, "fast"), (0.65, "slow"), (0.85, "fast")],
                   test=[(0.3, "slow"), (0.4, "fast"), (0.6, "slow"), (0.75, "fast"), (0.9, "slow")],
                   spare=[(0.45, "slow"), (0.55, "fast")]),
    "bow": dict(train=[10, 18, 25], val=[(13, "fast"), (20, "slow"), (23, "fast")],
                test=[(12, "slow"), (15, "fast"), (17, "slow"), (22, "fast"), (24, "slow")], spare=[(14, "slow"), (21, "fast")]),
    "sway": dict(train=[0.01, 0.02, 0.03], val=[(0.015, "f0.5"), (0.025, "f1.0"), (0.0125, "f1.0")],
                 test=[(0.0175, "f1.0"), (0.0225, "f0.5"), (0.0275, "f1.0"), (0.0325, "f0.5"), (0.0135, "f0.5")],
                 spare=[(0.0275, "f0.5"), (0.0175, "f0.5")]),
    "head": dict(train=[("nod", 1.0), ("shake", 1.0), ("tilt", 1.0)],
                 val=[(("look_around", 1.0), "slow"), (("nod", 0.7), "fast"), (("shake", 0.7), "slow")],
                 test=[(("nod_tilt", 1.0), "slow"), (("look_tilt", 1.0), "fast"), (("tilt", 0.7), "fast"),
                       (("nod", 0.85), "slow"), (("shake", 0.85), "fast")],
                 spare=[(("tilt", 0.85), "slow"), (("look_around", 0.8), "fast")]),
}
STAT_VARIANTS = {"crouch": ("fast", "slow"), "bow": ("fast", "slow"), "sway": ("f0.5", "f1.0"), "head": ("slow", "fast")}
WILD = {
    "hop": dict(train=[(0.004, 2), (0.006, 2), (0.008, 1), (0.005, 1), (0.009, 2), (0.007, 1)],
                val=[(0.0055, 2), (0.0085, 1), (0.0045, 1)],
                test=[(0.0065, 2), (0.0075, 1), (0.0035, 2), (0.006, 1), (0.0095, 1)],
                spare=[(0.003, 1), (0.0045, 2), (0.0065, 1), (0.0035, 1)]),
    "dance": dict(train=[(1, 0.6), (1.5, 0.5), (2, 0.6), (2.5, 0.5), (1.25, 0.7), (1.75, 0.8)],
                  val=[(1.25, 0.6), (2.25, 0.5), (1.5, 0.7)],
                  test=[(1.75, 0.5), (1, 0.75), (2, 0.45), (2.25, 0.65), (1.25, 0.55)],
                  spare=[(1, 0.5), (1.5, 0.6), (2, 0.5), (1.75, 0.6), (2.5, 0.4)]),
    "headbang": dict(train=[(1, 0.25), (1, 0.5), (2, 0.25), (2, 0.5), (3, 0.25), (1.5, 0.4)],
                     val=[(1.5, 0.25), (2.5, 0.3), (1, 0.35)],
                     test=[(1.5, 0.35), (1, 0.4), (2.5, 0.2), (2, 0.35), (3, 0.2)],
                     spare=[(1, 0.3), (2, 0.3), (1.5, 0.3)]),
    "twist": dict(train=[(0.5, 0.15), (0.5, 0.3), (1.5, 0.15), (1.5, 0.3), (1, 0.25), (0.75, 0.2)],
                  val=[(1, 0.2), (1.25, 0.25), (0.6, 0.25)],
                  test=[(0.75, 0.25), (1.25, 0.15), (1, 0.3), (0.5, 0.2), (1.5, 0.2)],
                  spare=[(0.6, 0.15), (1.25, 0.3), (0.75, 0.15)]),
}
WILD_PRM = {"hop": lambda s: dict(h=s[0], n=s[1]), "dance": lambda s: dict(f=s[0], a=s[1]),
            "headbang": lambda s: dict(f=s[0], a=s[1]), "twist": lambda s: dict(f=s[0], a=s[1])}

# v9x: 7 new test sources per type (test only) and their spares; values differ from every train / val / test / spare
# source above (checked at build), mostly inside the range the train clips actually cover (a failed train source does
# not count: side_step trains only +dy 1.25-1.75 cm, turn_in_place |dth| 0.15-0.175, walk_turn dx 2-3 cm)
GAITS_X = {
    "walk_fwd": dict(test=[("0.0225", "0", "0"), ("0.024", "0", "0"), ("0.029", "0", "0"), ("0.031", "0", "0"),
                           ("0.034", "0", "0"), ("0.0365", "0", "0"), ("0.039", "0", "0")],
                     spare=[("0.0215", "0", "0"), ("0.0345", "0", "0"), ("0.038", "0", "0"), ("0.0425", "0", "0")]),
    "walk_back": dict(test=[("-0.021", "0", "0"), ("-0.024", "0", "0"), ("-0.026", "0", "0"), ("-0.029", "0", "0"),
                            ("-0.031", "0", "0"), ("-0.034", "0", "0"), ("-0.039", "0", "0")],
                      spare=[("-0.036", "0", "0"), ("-0.0385", "0", "0"), ("-0.0215", "0", "0")]),
    "side_step": dict(test=[("0", "0.0135", "0"), ("0", "0.0145", "0"), ("0", "0.016", "0"), ("0", "0.019", "0"),
                            ("0", "-0.0135", "0"), ("0", "-0.0155", "0"), ("0", "-0.019", "0")],
                      spare=[("0", "0.0165", "0"), ("0", "-0.0145", "0"), ("0", "0.021", "0"), ("0", "-0.0165", "0"),
                             ("0", "0.0115", "0"), ("0", "-0.0115", "0"), ("0", "-0.021", "0")]),
    "turn_in_place": dict(test=[("0", "0", "0.14"), ("0", "0", "-0.14"), ("0", "0", "0.16"), ("0", "0", "-0.16"),
                                ("0", "0", "0.19"), ("0", "0", "-0.19"), ("0", "0", "-0.125")],
                          spare=[("0", "0", "0.13"), ("0", "0", "-0.13"), ("0", "0", "0.165"), ("0", "0", "-0.165"),
                                 ("0", "0", "0.21"), ("0", "0", "-0.21")]),
    "walk_turn": dict(test=[("0.025", "0", "-0.10"), ("0.02", "0", "-0.12"), ("0.03", "0", "-0.13"), ("0.0275", "0", "-0.06"),
                            ("0.0225", "0", "0.05"), ("0.02", "0", "0.07"), ("0.03", "0", "0.06")],
                      spare=[("0.0225", "0", "-0.14"), ("0.0275", "0", "0.09"), ("0.025", "0", "-0.14"), ("0.02", "0", "-0.08"),
                             ("0.03", "0", "-0.08"), ("0.0225", "0", "0.12")]),
}
MARCH_X = dict(test=["0.016", "0.0215", "0.024"], spare=["0.019", "0.0135", "0.0265"])
LEG_WILD_X = dict(test=[("stomp", dict(lift=0.0175, period=1.5, dy=DY)), ("kick", dict(r=0.035, tau=0.4, dy=DY)),
                        ("tap", dict(reach=0.025, period=1.4, dy=DY)), ("kick", dict(r=0.025, tau=0.45, dy=DY))],
                  spare=[("stomp", dict(lift=0.0125, period=1.4, dy=DY)), ("tap", dict(reach=0.0325, period=1.5, dy=DY)),
                         ("kick", dict(r=0.0325, tau=0.5, dy=DY)), ("stomp", dict(lift=0.0225, period=1.6, dy=DY))])
STAT_X = {  # variants complete the v9 test list to 6 / 6
    "crouch": dict(test=[(0.25, "fast"), (0.33, "slow"), (0.42, "fast"), (0.58, "slow"), (0.7, "fast"), (0.8, "slow"),
                         (0.95, "fast")], spare=[(0.27, "slow"), (0.48, "fast"), (0.68, "slow")]),
    "bow": dict(test=[(11, "fast"), (16, "slow"), (19, "fast"), (12.5, "slow"), (14.5, "fast"), (20.5, "slow"), (23.5, "fast")],
                spare=[(16.5, "slow"), (21.5, "fast"), (10.5, "slow")]),
    "sway": dict(test=[(0.011, "f1.0"), (0.0145, "f0.5"), (0.016, "f1.0"), (0.019, "f0.5"), (0.0215, "f1.0"), (0.024, "f0.5"),
                       (0.0285, "f1.0")], spare=[(0.0265, "f0.5"), (0.012, "f1.0"), (0.0185, "f1.0")]),
    "head": dict(test=[(("nod", 0.9), "fast"), (("shake", 0.9), "slow"), (("tilt", 0.9), "slow"), (("look_around", 0.9), "fast"),
                       (("nod_tilt", 0.8), "slow"), (("look_tilt", 0.8), "fast"), (("shake", 0.75), "slow")],
                 spare=[(("tilt", 0.75), "fast"), (("nod", 0.75), "slow"), (("look_around", 0.7), "slow")]),
}
WILD_X = {
    "hop": dict(test=[(0.0042, 1), (0.0048, 2), (0.0052, 2), (0.0058, 1), (0.0068, 2), (0.0072, 1), (0.0082, 2)],
                spare=[(0.0078, 1), (0.0062, 1), (0.0088, 2), (0.0054, 1)]),
    "dance": dict(test=[(1.1, 0.55), (1.4, 0.65), (1.6, 0.55), (1.9, 0.7), (2.1, 0.55), (2.4, 0.6), (1.3, 0.75)],
                  spare=[(1.6, 0.7), (2.2, 0.6), (1.8, 0.5), (1.2, 0.65)]),
    "headbang": dict(test=[(1.25, 0.3), (1.75, 0.4), (2.25, 0.25), (1.25, 0.45), (2.75, 0.25), (1.75, 0.3), (2.25, 0.4)],
                     spare=[(1.5, 0.45), (2.5, 0.25), (1.25, 0.2), (2, 0.4)]),
    "twist": dict(test=[(0.6, 0.2), (0.9, 0.15), (1.1, 0.25), (1.4, 0.25), (0.8, 0.3), (1.2, 0.2), (0.7, 0.175)],
                  spare=[(0.9, 0.25), (1.1, 0.175), (1.4, 0.15), (0.6, 0.3)]),
}
# broken copies: (type, kind, options); ~3 per kind, spread across types, 25 in total
BROKEN = [("walk_fwd", "shove", dict(dx=-0.07)), ("walk_fwd", "noise", {}),
          ("walk_back", "shove", dict(dx=-0.07)), ("walk_back", "glitch", {}),
          ("side_step", "speed", {}), ("side_step", "foot_skate", {}),
          ("turn_in_place", "speed", {}), ("turn_in_place", "noise", {}),
          ("walk_turn", "speed", {}), ("head", "shove", dict(dx=0.12)),
          ("leg_lift", "one_foot_long", {}), ("leg_lift", "joint_limit", {}),
          ("crouch", "shove", dict(dx=-0.07)), ("crouch", "glitch", {}),
          ("bow", "shove", dict(dx=0.12)),
          ("sway", "one_foot_long", {}), ("sway", "foot_skate", {}),
          ("head", "one_foot_long", {}),
          ("hop", "takeoff", dict(h=0.025)), ("hop", "takeoff", dict(h=0.03)),
          ("dance", "joint_limit", {}), ("dance", "foot_skate", {}),
          ("headbang", "joint_limit", {}), ("headbang", "glitch", {}),
          ("twist", "noise", {})]
SPEED_FALLBACK = ["walk_turn", "turn_in_place", "walk_back", "walk_fwd", "leg_lift", "crouch", "headbang", "bow"]
SHOVE_IK_MAX = 0.03  # m: a shove whose soles cannot be kept in place is not a shove
IMPOSSIBLE = ("shove", "joint_limit", "takeoff", "speed", "one_foot_long")


def gait_name(cat, src, style):
    if cat == "march":
        return f"march__lift{src}__{style}"
    dx, dy, dth = src
    return f"{cat}__dx{dx}_dy{dy}_dth{dth}__{style}"


def stat_sid(cat, s):
    return (f"crouch__depth{s:.2f}" if cat == "crouch" else f"bow__pitch{s}deg" if cat == "bow"
            else f"sway__amp{s:.4f}m" if cat == "sway" else f"head__{s[0]}_a{s[1]:g}")


def listed_sources(gaits, march, leg_wild, stat, wild, clip_id):
    """Every source id a set of tables names (all splits and spares), as a list (duplicates kept)."""
    out = [gait_name(c, s, "x").rsplit("__", 1)[0] for c, sp in gaits.items() for k in sp for s in sp[k]]
    out += [gait_name("march", s, "x").rsplit("__", 1)[0] for k in march for s in march[k]]
    out += [clip_id(f, p) for k in leg_wild for f, p in leg_wild[k]]
    out += [stat_sid(c, s) for c, sp in stat.items() for s in sp.get("train", [])]
    out += [stat_sid(c, s) for c, sp in stat.items() for k in sp if k != "train" for s, _ in sp[k]]
    out += [clip_id(f, WILD_PRM[f](s)) for f, sp in wild.items() for k in sp for s in sp[k]]
    return out


def write_presets(gen, out, ext=False):
    """Placo presets for every gait source (both styles), then run the generator (as gen_gaits.sh); ext: v9x sources only."""
    os.makedirs(os.path.join(out, "presets"), exist_ok=True)
    base = json.load(open(os.path.join(gen, "open_duck_reference_motion_generator/robots/open_duck_mini_v2/placo_presets/medium.json")))
    names = []
    G, MA = (GAITS_X, MARCH_X) if ext else (GAITS, MARCH)
    jobs = [(cat, s) for cat, sp in G.items() for k in ("train", "val", "test", "spare") for s in sp.get(k, [])]
    jobs += [("march", s) for k in ("train", "val", "test", "spare") for s in MA.get(k, [])]
    for cat, src in jobs:
        for sty, (ss, fh, sst) in STYLE_PRM.items():
            b = dict(base)
            if cat == "march":
                b.update(dx=0.0, dy=0.0, dtheta=0.0, walk_foot_height=float(src))
            else:
                b.update(dx=float(src[0]), dy=float(src[1]), dtheta=float(src[2]), walk_foot_height=fh)
            b.update(duration=10, walk_com_height=0.220, single_support_duration=ss, single_support_timesteps=sst)
            n = gait_name(cat, src, sty)
            json.dump(b, open(os.path.join(out, "presets", n + ".json"), "w"), indent=1)
            names.append(n)
    open(os.path.join(out, "names.txt"), "w").write("\n".join(names) + "\n")
    out = os.path.abspath(out)
    cmd = (f"cat {out}/names.txt | xargs -P 24 -I{{}} sh -c \"timeout 900 .venv/bin/python "
           f"open_duck_reference_motion_generator/gait_generator.py --duck open_duck_mini_v2 --preset {out}/presets/{{}}.json "
           f"--name {{}} --output_dir {out} > {out}/{{}}.log 2>&1 || echo 'FAILED {{}}'\"")
    subprocess.run(cmd, shell=True, cwd=gen, check=False)
    print(len(names), "presets;", len([f for f in os.listdir(out) if f.endswith(".json")]), "recordings")


# ----------------------------------------------------------------------------------------------------------- build
def build_library(a):
    import mujoco
    from scipy.signal import butter, filtfilt
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, HERE)
    import hold_test as ht
    import make_library as ml
    from dynamic_check import check as dyn_check
    from make_infeasible import arrays
    from make_wild import LEGS, build as wild_build, clip_id

    m, d = ml.load_model()
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
    home = m.keyframe("home")
    T = int(ml.CLIP_S * ml.FPS)
    v7man = json.load(open(os.path.join(a.v7, "manifest.json")))
    max_drop = v7man.get("max_crouch_drop_m") or ml.max_crouch_drop(m, d, qadr, margin=0.03)
    rng = np.random.default_rng(SEED)

    # bars from the clean v7 walking gaits (every split)
    v7 = np.load(os.path.join(a.v7, "library.npz"))
    lags, zmps = [], []
    for c in v7man["clips"]:
        if c["category"] in GAIT_TYPES + ["march"]:
            i, n = c["index"], c["length"]
            r = dyn_check(m, d, qadr, v7["q"][i, :n], v7["base_pos"][i, :n], v7["base_quat"][i, :n], v7["contacts"][i, :n])
            lags.append(r["rate_lag_rad"])
            zmps.append(r["zmp_min_margin_mm"])
    LAG_BAR, ZMP_BAR = float(max(lags)), float(min(zmps))
    print(f"v7 walking bars: servo lag {LAG_BAR:.3f} rad (worst of {len(lags)}), balance margin {ZMP_BAR:.1f} mm")

    gaits = ml.gait_files(a.gaits)

    def gait(cat, src, sty):
        key = (cat, gait_name(cat, src, sty).rsplit("__", 1)[0])
        path = gaits.get(key, {}).get(sty)
        if path is None:
            return None
        q, pos, quat, con, prm = ml.gait_clip(m, d, qadr, path, 1.0)
        lin, ang = ml.body_velocities(pos, quat)
        prm = {"dx": prm.get("dx"), "dy": prm.get("dy"), "dtheta": prm.get("dtheta"), "style": sty,
               "single_support_s": prm.get("single_support_duration"), "foot_lift_m": prm.get("walk_foot_height"),
               "mean_vx": round(float(lin[:, 0].mean()), 4), "mean_vy": round(float(lin[:, 1].mean()), 4),
               "mean_yaw_rate": round(float(ang[:, 2].mean()), 4)}
        return q, pos, quat, con, prm

    def head_clip(move, amp, var):
        q, pos, quat, con, prm = ml.stationary_clip(m, d, qadr, "head", move, var)
        q[:, 5:9] = home.ctrl[5:9] + amp * (q[:, 5:9] - home.ctrl[5:9])
        return q, pos, quat, con, dict(prm, amp_scale=amp)

    def stat(cat, src, var):
        if cat == "crouch":
            tm, th = ml.CROUCH_STYLES[var]
            return ml.crouch_clip(m, d, qadr, src, tm, th, max_drop)
        if cat == "head":
            return head_clip(src[0], src[1], var)
        return ml.stationary_clip(m, d, qadr, cat, src, var)

    def wild(fam, prm):
        q, pos, quat, con, err = wild_build(m, d, qadr, fam, prm)
        return q, pos, quat, con, dict(prm, ik_foot_err_mm=round(1000 * err, 2))

    def measure(q, pos, quat, con):
        qd = np.gradient(q, 1 / ml.FPS, axis=0)
        return ml.check_clip(m, d, qadr, q, qd, pos, quat, con), dyn_check(m, d, qadr, q, pos, quat, con)

    def clean_ok(kind, rep, dyn):
        if not rep["pass"]:
            return False
        if kind == "keyframed":
            return dyn["rate_lag_rad"] <= LAG_BAR and dyn["zmp_min_margin_mm"] >= ZMP_BAR and not dyn["takeoff_fail"]
        return True

    clips, notes = [], []

    def add(cat, cid, src_id, split, clip, kind, extra=None):
        q, pos, quat, con, prm = clip
        q = np.clip(q, lo, hi)
        rep, dyn = measure(q, pos, quat, con)
        if not clean_ok(kind, rep, dyn):
            return False
        e = {"id": cid, "category": cat, "source": src_id, "split": split, "params": prm, "check": rep, "dynamic": dyn,
             "length": len(q), "generator": kind}
        if extra:
            e.update(extra)
        if split == "train":
            e["feasibility"] = {"infeasible": False, "corrupted": False, "labelled": True}
        clips.append((e, (q, pos, quat, con)))
        return True

    # ---- clean clips (v9x: only the new test sources, whose gait styles continue the v9 test list's alternation)
    ext = bool(a.extend_test)
    G, MA, LW, ST, WI = (GAITS_X, MARCH_X, LEG_WILD_X, STAT_X, WILD_X) if ext else (GAITS, MARCH, LEG_WILD, STAT, WILD)
    if ext:
        v9man = json.load(open(os.path.join(a.extend_test, "manifest.json")))
        assert max_drop == v9man["max_crouch_drop_m"], (max_drop, v9man["max_crouch_drop_m"])
        v9_src = set(listed_sources(GAITS, MARCH, LEG_WILD, STAT, WILD, clip_id)) | {c["source"] for c in v9man["clips"]}
        x_src = listed_sources(G, MA, LW, ST, WI, clip_id)
        assert len(set(x_src)) == len(x_src), "a v9x source is listed twice"
        assert not v9_src & set(x_src), sorted(v9_src & set(x_src))
    for cat in GAIT_TYPES + ["march"]:
        spec = G.get(cat) if cat != "march" else MA
        tcat = "leg_lift" if cat == "march" else cat
        spares = list(spec["spare"])
        j0 = len((GAITS.get(cat) or MARCH)["test"]) if ext else 0
        for split in ("train", "val", "test"):
            for j, src in enumerate(spec.get(split, []), j0 if split == "test" else 0):
                while True:
                    sid = gait_name(cat, src, "x").rsplit("__", 1)[0]
                    styles = ("normal", "gentle") if split == "train" else (("normal", "gentle")[j % 2], ("gentle", "normal")[j % 2])
                    got = []
                    for sty in styles:
                        g = gait(cat, src, sty)
                        if g is not None and clean_ok("gait", *measure(g[0], g[1], g[2], g[3])):
                            got.append((sty, g))
                    need = 2 if split == "train" else 1
                    if len(got) >= need:
                        for sty, g in got[:need]:
                            add(tcat, f"{sid}__{sty}", sid, split, g, "gait", {"family": "march" if cat == "march" else None})
                        break
                    notes.append(f"{sid} ({split}) failed the checks; replaced by a spare")
                    if not spares:
                        notes.append(f"{cat}: out of spares")
                        break
                    src = spares.pop(0)
    for split in ("train", "val", "test"):
        spares = list(LW["spare"])
        for fam, prm in LW.get(split, []):
            while not add("leg_lift", clip_id(fam, prm), clip_id(fam, prm), split, wild(fam, prm), "keyframed", {"family": fam}):
                notes.append(f"{clip_id(fam, prm)} ({split}) not clean; replaced by a spare")
                fam, prm = spares.pop(0)
    for cat, spec in ST.items():
        spares = list(spec["spare"])
        sid_of = lambda s: stat_sid(cat, s)  # noqa: E731
        for src in spec.get("train", []):
            for v in STAT_VARIANTS[cat]:
                if not add(cat, f"{sid_of(src)}__{v}", sid_of(src), "train", stat(cat, src, v), "ik"):
                    notes.append(f"{sid_of(src)}__{v} (train) failed the checks")
        for split in ("val", "test"):
            for src, v in spec.get(split, []):
                while not add(cat, f"{sid_of(src)}__{v}", sid_of(src), split, stat(cat, src, v), "ik"):
                    notes.append(f"{sid_of(src)}__{v} ({split}) failed the checks; replaced by a spare")
                    src, v = spares.pop(0)
    for fam, spec in WI.items():
        spares = list(spec["spare"])
        for split in ("train", "val", "test"):
            for s in spec.get(split, []):
                while not add(fam, clip_id(fam, WILD_PRM[fam](s)), clip_id(fam, WILD_PRM[fam](s)), split,
                              wild(fam, WILD_PRM[fam](s)), "keyframed"):
                    notes.append(f"{clip_id(fam, WILD_PRM[fam](s))} ({split}) not clean; replaced by a spare")
                    s = spares.pop(0)
    if ext:
        return write_extended(a, clips, notes, m, d, qadr, T, {"rate_lag_rad": round(LAG_BAR, 3), "zmp_min_margin_mm": round(ZMP_BAR, 1),
                                                              "n_gait_clips": len(lags)})

    # ---- broken copies
    sites = [m.site("left_foot").id, m.site("right_foot").id]

    def fk_feet(q, pos, quat):
        d.qpos[:] = home.qpos
        d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos, quat, q
        mujoco.mj_kinematics(m, d)
        return [(d.site_xpos[s].copy(), d.site_xmat[s].reshape(3, 3).copy()) for s in sites]

    Wr = np.array([0.3, 0.3, 0.3])

    def solve_feet(q0, pos, quat, tgt, iters=120):
        """Leg joints that put each sole at its target (world pos, rot) with the base at pos / quat."""
        qf = home.qpos.copy()
        qf[0:3], qf[3:7], qf[qadr] = pos, quat, q0
        err = 0.0
        for _ in range(iters):
            d.qpos[:] = qf
            mujoco.mj_kinematics(m, d)
            mujoco.mj_comPos(m, d)
            err = 0.0
            for leg, s in enumerate(sites):
                dofs = [m.jnt_dofadr[m.joint(n).id] for n in LEGS[leg]]
                qa = [m.jnt_qposadr[m.joint(n).id] for n in LEGS[leg]]
                e = np.concatenate([tgt[leg][0] - d.site_xpos[s], Wr * ml.mat_log(tgt[leg][1] @ d.site_xmat[s].reshape(3, 3).T)])
                err = max(err, float(np.linalg.norm(e[:3])))
                jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
                mujoco.mj_jacSite(m, d, jp, jr, s)
                J = np.vstack([jp, Wr[:, None] * jr])[:, dofs]
                qf[qa] += np.linalg.solve(J.T @ J + 1e-4 * np.eye(5), J.T @ e)
            if err < 1e-5:
                break
        return np.clip(qf[qadr], lo, hi), err

    def heading(quat):
        w, x, y, z = quat
        yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        return np.array([np.cos(yaw), np.sin(yaw), 0.0])

    t_of = lambda n: np.arange(n) / ml.FPS  # noqa: E731
    corners8 = np.array(np.meshgrid([-1, 1], [-1, 1], [-1, 1])).T.reshape(-1, 3)

    def grounded(q, pos, quat, stance):
        """Base position with the stance sole's lowest corner on the floor (the home keyframe sits ~1.5 cm deep, which
        the settling of a two-foot hold absorbs, but which leaves a raised foot almost touching)."""
        d.qpos[:] = home.qpos
        d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos, quat, q
        mujoco.mj_kinematics(m, d)
        return pos - np.array([0, 0, sole_low(stance) - 0.0005])

    def sole_low(side):
        """Lowest world z of a sole's box (after mj_kinematics on the pose in d)."""
        g = m.geom(ht.SOLES[side]).id
        c = m.geom_aabb[g, :3] + corners8 * m.geom_aabb[g, 3:]
        return float((c @ d.geom_xmat[g].reshape(3, 3).T)[:, 2].min() + d.geom_xpos[g][2])

    def shove(base, dx):
        q, pos, quat, con = base
        n = len(q)
        s = ml.minjerk((t_of(n) - 0.4) / 0.6) * dx
        q2, pos2, worst = q.copy(), pos.copy(), 0.0
        for k in range(n):
            tgt = fk_feet(q[k], pos[k], quat[k])
            pos2[k] = pos[k] + s[k] * heading(quat[k])
            q2[k], err = solve_feet(q2[k - 1] if k else q[k], pos2[k], quat[k], tgt)
            worst = max(worst, err)
        ds = [k for k in range(n) if s[k] >= 0.98 * dx if dx > 0] or [k for k in range(n) if s[k] <= 0.98 * dx]
        ds = [k for k in ds if con[k].min() > 0.5]
        k = ds[len(ds) // 2]
        h = ht.hold(m, d, qadr, q2[k], pos2[k], quat[k], con[k])
        return (q2, pos2, quat, con), {"shove_m": dx, "ik_foot_err_mm": round(1000 * worst, 1), "hold_frame": k, "hold": h}, \
            not h["held"] and worst <= SHOVE_IK_MAX

    def speed(base, kfac):
        q, pos, quat, con = base
        n = int(np.ceil(len(q) / kfac))
        q2, pos2, c2 = ml.resample(q, kfac, n), ml.resample(pos, kfac, n), (ml.resample(con, kfac, n) > 0.5).astype(np.float32)
        quat2 = ml.resample(quat, kfac, n)
        quat2 /= np.linalg.norm(quat2, axis=1, keepdims=True)
        lag = dyn_check(m, d, qadr, q2, pos2, quat2, c2)["rate_lag_rad"]
        return (q2, pos2, quat2, c2), {"compression": kfac, "rate_lag_rad": lag, "lag_bar_rad": round(LAG_BAR, 3)}, lag > LAG_BAR

    qc_full = ml.solve_crouch_legs(m, d, qadr, max_drop)[0]

    def one_foot(base, side, lift):
        """Raise one sole forward and up by `lift` = (fwd, up) m from 0.6 to 3.2 s on top of the clip, no weight shift
        (IK, stance sole kept; straight up runs the knee into its limit)."""
        q, pos, quat, con = base
        n = len(q)
        t = t_of(n)
        f = ml.minjerk((t - 0.6) / 0.4) - ml.minjerk((t - 3.2) / 0.4)
        q2, worst = q.copy(), 0.0
        for k in range(n):
            tgt = fk_feet(q[k], pos[k], quat[k])
            tgt[side] = (tgt[side][0] + f[k] * (lift[0] * heading(quat[k]) + np.array([0, 0, lift[1]])), tgt[side][1])
            q2[k], err = solve_feet(q2[k - 1] if k else q[k], pos[k], quat[k], tgt)
            worst = max(worst, err)
        c2 = con.copy()
        c2[f > 0.05, side] = 0
        k = int(np.argmin(np.abs(t - 1.9)))
        d.qpos[:] = home.qpos
        d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos[k], quat[k], q2[k]
        mujoco.mj_kinematics(m, d)
        clear = sole_low(side) - sole_low(1 - side)  # raised sole above the stance sole
        h = ht.hold(m, d, qadr, q2[k], grounded(q2[k], pos[k], quat[k], 1 - side), quat[k], c2[k])
        nm = ("left", "right")[side]
        return (q2, pos, quat, c2), {"raised_foot": nm, "foot_fwd_up_m": list(lift), "raised_s": 2.6, "clearance_mm": round(1000 * clear, 1),
                                     "ik_foot_err_mm": round(1000 * worst, 1), "hold_frame": k, "hold": h}, \
            (not h["held"]) and clear > 0.008 and worst <= SHOVE_IK_MAX

    def hold_single_support(base, hold_s=2.5):
        """Hold the single-support frame where the raised sole is highest for hold_s seconds."""
        q, pos, quat, con = base
        ss = [k for k in range(len(q)) if con[k].min() < 0.5]
        hgt = []
        for k in ss:
            d.qpos[:] = home.qpos
            d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos[k], quat[k], q[k]
            mujoco.mj_kinematics(m, d)
            up = int(np.argmin(con[k]))
            hgt.append(sole_low(up) - sole_low(1 - up))
        k = ss[int(np.argmax(hgt))]
        rep = int(hold_s * ml.FPS)
        sel = list(range(k)) + [k] * rep + list(range(k, len(q)))
        sel = sel[:T]
        q2, pos2, quat2, c2 = q[sel], pos[sel], quat[sel], con[sel]
        h = ht.hold(m, d, qadr, q[k], grounded(q[k], pos[k], quat[k], int(np.argmax(con[k]))), quat[k], con[k])
        return (q2, pos2, quat2, c2), {"held_frame": k, "raised_s": hold_s, "raised_foot": "left" if con[k, 0] < 0.5 else "right",
                                       "clearance_mm": round(1000 * max(hgt), 1), "hold": h}, \
            (not h["held"]) and max(hgt) > 0.008

    def noise(base, amp=0.07):
        q, pos, quat, con = base
        b, a_ = butter(2, [3 / (ml.FPS / 2), 8 / (ml.FPS / 2)], btype="band")
        z = filtfilt(b, a_, rng.standard_normal((len(q) + 100, 14)), axis=0)[50:50 + len(q)]
        z = z / z.std(0) * amp
        env = ml.minjerk(t_of(len(q)) / 0.3)[:, None]
        return (q + env * z, pos, quat, con), {"band_hz": [3, 8], "rms_rad": amp}, True

    def glitch(base):
        q, pos, quat, con = base
        q2, ev = q.copy(), []
        times = np.sort(rng.choice(np.arange(int(0.5 * ml.FPS), len(q) - int(0.5 * ml.FPS)), 3, replace=False))
        for k in times:
            js = rng.choice(14, int(rng.integers(2, 4)), replace=False)
            off = rng.choice([-1, 1], len(js)) * rng.uniform(0.3, 0.5, len(js))
            q2[k:k + 4, js] += off
            ev.append({"frame": int(k), "frames": 4, "joints": [ml.ACT[j] for j in js], "offset_rad": [round(float(o), 3) for o in off]})
        return (q2, pos, quat, con), {"jumps": ev}, True

    def skate(base, dist=0.04):
        q, pos, quat, con = base
        n = len(q)
        t = t_of(n)
        s = dist * (ml.minjerk((t - 0.8) / 1.0) - ml.minjerk((t - 2.4) / 1.0))
        q2, worst, slid = q.copy(), 0.0, 0
        for k in range(n):
            tgt = fk_feet(q[k], pos[k], quat[k])
            tgt[0] = (tgt[0][0] + s[k] * heading(quat[k]), tgt[0][1])
            q2[k], err = solve_feet(q2[k - 1] if k else q[k], pos[k], quat[k], tgt)
            worst = max(worst, err)
            slid += int(con[k, 0] > 0.5 and s[k] > 0.005)
        return (q2, pos, quat, con), {"slide_m": dist, "foot": "left", "frames_sliding_in_contact": slid,
                                      "ik_foot_err_mm": round(1000 * worst, 1)}, slid > 10

    train = {c: [(e, arr) for e, arr in clips if e["category"] == c and e["split"] == "train"] for c in TYPES}
    used = collections.Counter()
    broken = []

    def next_base(cat, pred=lambda e: True, kind=None):
        taken = {x[0]["derived_from"] for x in broken if x[0]["contaminant"] == kind}
        cands = [x for x in train[cat] if pred(x[0]) and x[0]["id"] not in taken] or [x for x in train[cat] if pred(x[0])]
        x = cands[used[cat] % len(cands)]
        used[cat] += 1
        return x

    def amplify(e, kind):
        fam = e.get("family") or e["category"]
        prm = {k: v for k, v in e["params"].items() if k != "ik_foot_err_mm"}
        tries = {"dance": [("a", 1.4), ("a", 1.6)], "headbang": [("a", 0.95), ("a", 1.1)], "twist": [("a", 0.65), ("a", 0.8)],
                 "stomp": [("lift", 0.06), ("lift", 0.08)], "kick": [("r", 0.10), ("r", 0.12)], "hop": [("h", 0.025), ("h", 0.03)]}[fam]
        for k_, v in tries:
            p2 = dict(prm, **{k_: v})
            yield fam, p2, wild(fam, p2)

    for cat, kind, opt in BROKEN:
        done = False
        for attempt in range(6):
            if kind == "speed":
                e0, base = next_base(cat, kind="speed")
                for kf in (2.0, 2.5, 3.0):
                    arr, ev, ok = speed(base, kf)
                    if ok:
                        break
            elif kind == "shove":
                e0, base = next_base(cat)
                dx = opt["dx"] + np.sign(opt["dx"]) * 0.02 * attempt
                arr, ev, ok = shove(base, dx)
            elif kind == "one_foot_long":
                if cat == "leg_lift":
                    e0, base = next_base(cat, lambda e: e.get("family") in ("stomp", "kick"))
                    arr, ev, ok = hold_single_support(base)
                else:
                    e0, base = next_base(cat)
                    arr, ev, ok = one_foot(base, attempt % 2, ((0.03, 0.025), (0.045, 0.03), (0.06, 0.035))[attempt // 2 % 3])
            elif kind in ("joint_limit", "takeoff"):
                pred = (lambda e: e.get("family") in ("stomp", "kick")) if cat == "leg_lift" else (lambda e: True)
                e0, base = next_base(cat, pred)
                ok = False
                for fam, p2, clip in amplify(e0, kind):
                    if kind == "takeoff":
                        p2 = dict(p2, h=opt["h"])
                        clip = wild(fam, p2)
                    q, pos, quat, con, prm = clip
                    rep, dyn = measure(np.clip(q, lo, hi), pos, quat, con)
                    ok = (not rep["pass"] and rep["joint_limit_margin_rad"] <= 1e-3) if kind == "joint_limit" else dyn["takeoff_fail"]
                    ev = ({"params": prm, "joint_limit_margin_rad": rep["joint_limit_margin_rad"]} if kind == "joint_limit" else
                          {"params": prm, "takeoff_need_m_s": dyn["takeoff_need_m_s"], "takeoff_can_m_s": dyn["takeoff_can_m_s"]})
                    arr = (q, pos, quat, con)
                    if ok:
                        break
            elif kind == "noise":
                e0, base = next_base(cat)
                arr, ev, ok = noise(base)
            elif kind == "glitch":
                e0, base = next_base(cat)
                arr, ev, ok = glitch(base)
            elif kind == "foot_skate":
                e0, base = next_base(cat)
                arr, ev, ok = skate(base)
            if ok:
                done = True
                break
            notes.append(f"{cat} {kind}: candidate from {e0['id']} rejected ({json.dumps(ev, default=str)[:160]})")
        if not done and kind == "speed":
            taken = {x[0]["derived_from"] for x in broken if x[0]["contaminant"] == "speed"}
            for alt in SPEED_FALLBACK:
                for e0, base in train[alt]:
                    if e0["id"] in taken:
                        continue
                    for kf in (2.0, 2.5, 3.0):
                        arr, ev, ok = speed(base, kf)
                        if ok:
                            break
                    if ok:
                        break
                if ok:
                    notes.append(f"speed: {cat} had no clip past the lag bar at 2-3x; used {alt} ({e0['id']}) instead")
                    cat, done = alt, True
                    break
        if not done:
            notes.append(f"{cat} {kind}: NO valid candidate, skipped")
            continue
        q, pos, quat, con = arr
        q = np.clip(q, lo, hi)
        rep, dyn = measure(q, pos, quat, con)
        fam = "impossible" if kind in IMPOSSIBLE else "corrupted"
        cid = f"{e0['id']}__broken_{kind}"
        while any(x["id"] == cid for x, _ in clips + broken):
            cid += "b"
        e = {"id": cid, "category": cat, "source": cid, "derived_from": e0["id"], "split": "train",
             "params": e0["params"], "check": rep, "dynamic": dyn, "length": len(q), "contaminant": kind,
             "generator": "broken", "family": e0.get("family"),
             "feasibility": {"infeasible": fam == "impossible", "corrupted": True, "family": fam, "kind": kind,
                             "kinematic": rep["pass"], "evidence": ev}}
        broken.append((e, (q, pos, quat, con)))
        print(f"  broken {cid:60s} {fam:10s} {json.dumps(ev, default=str)[:140]}")

    allc = clips + broken
    for e, _ in allc:
        if e.get("family") is None:
            e.pop("family", None)
    lib = {k: np.zeros((len(allc), T) + v, dtype=np.float32) for k, v in
           (("q", (14,)), ("qd", (14,)), ("base_pos", (3,)), ("base_quat", (4,)), ("lin_vel", (3,)), ("ang_vel", (3,)),
            ("contacts", (2,)), ("keypts", (len(ml.KEYPOINTS), 3)))}
    man_clips = []
    for j, (e, (q, pos, quat, con)) in enumerate(allc):
        assert len(q) <= T, e["id"]
        arr = arrays(m, d, qadr, q, pos, quat, con)
        for k_, x in arr.items():
            lib[k_][j, :len(x)] = x
            lib[k_][j, len(x):] = x[-1]
        man_clips.append(dict(e, index=j))
    lib["length"] = np.array([e["length"] for e, _ in allc], dtype=np.int32)
    os.makedirs(a.out, exist_ok=True)
    np.savez_compressed(os.path.join(a.out, "library.npz"), **lib)
    manifest = {"version": "v9", "fps": ml.FPS, "joints": ml.ACT, "keypoints": ml.KEYPOINT_NAMES, "seed": SEED,
                "split": "fixed by design in make_v9.py (no random draw)", "types": TYPES,
                "max_crouch_drop_m": max_drop, "servo_max_speed_rad_s": ml.SERVO_MAX_SPEED, "knee_limit_rad": ml.KNEE_LIMIT,
                "bars_from_v7_walking": {"rate_lag_rad": round(LAG_BAR, 3), "zmp_min_margin_mm": round(ZMP_BAR, 1),
                                         "n_gait_clips": len(lags)},
                "keyframed_weight_shift_m": DY, "notes": notes, "clips": man_clips}
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1, default=float)
    print("\n".join(notes))
    print(f"{a.out}: {len(allc)} clips")


def write_extended(a, clips, notes, m, d, qadr, T, bars):
    """v9x: the clips_v9 library unchanged (same rows, ids, indices) with the new clean test clips appended."""
    from make_infeasible import arrays
    v9 = np.load(os.path.join(a.extend_test, "library.npz"))
    man = json.load(open(os.path.join(a.extend_test, "manifest.json")))
    assert bars == man["bars_from_v7_walking"], (bars, man["bars_from_v7_walking"])
    N = len(man["clips"])
    new = {k: np.zeros((len(clips),) + v9[k].shape[1:], dtype=v9[k].dtype) for k in v9.files if k != "length"}
    man_new = []
    for j, (e, (q, pos, quat, con)) in enumerate(clips):
        assert e["split"] == "test" and len(q) <= T, e["id"]
        if e.get("family") is None:
            e.pop("family", None)
        for k_, x in arrays(m, d, qadr, q, pos, quat, con).items():
            new[k_][j, :len(x)] = x
            new[k_][j, len(x):] = x[-1]
        man_new.append(dict(e, index=N + j, new_in="v9x"))
    lib = {k: np.concatenate([v9[k], new[k]]) for k in new}
    lib["length"] = np.concatenate([v9["length"], np.array([e["length"] for e, _ in clips], dtype=v9["length"].dtype)])
    os.makedirs(a.out, exist_ok=True)
    np.savez_compressed(os.path.join(a.out, "library.npz"), **lib)
    manifest = dict(man, version="v9x", extended_from=os.path.basename(os.path.normpath(a.extend_test)),
                    split=man["split"] + "; v9x appends 7 test sources per type (make_v9.py --extend-test)",
                    notes=man["notes"] + [f"v9x: {x}" for x in notes], clips=man["clips"] + man_new)
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1, default=float)
    print("\n".join(notes))
    print(f"{a.out}: {N} clips from {a.extend_test} + {len(clips)} new test clips")


# ----------------------------------------------------------------------------------------------- verify and doc
def verify(lib_dir):
    lib = np.load(os.path.join(lib_dir, "library.npz"))
    man = json.load(open(os.path.join(lib_dir, "manifest.json")))
    cl = man["clips"]
    N, T = lib["q"].shape[:2]
    assert N == len(cl) and T == 200, (N, len(cl), T)
    assert sorted(c["index"] for c in cl) == list(range(N))
    for c in cl:
        assert c["length"] == lib["length"][c["index"]] <= 200, c["id"]
        q = lib["q"][c["index"], :c["length"]]
        assert np.isfinite(q).all() and np.isfinite(lib["keypts"][c["index"]]).all(), c["id"]
    assert len({c["id"] for c in cl}) == N, "duplicate ids"
    src = collections.defaultdict(set)
    for c in cl:
        src[c["source"]].add(c["split"])
    leak = [s for s, sp in src.items() if len(sp) > 1]
    assert not leak, leak
    for c in cl:
        if c["split"] == "train":
            assert "feasibility" in c, c["id"]
        if c.get("derived_from"):
            parent = next(x for x in cl if x["id"] == c["derived_from"])
            assert parent["split"] == "train" and parent["category"] == c["category"], c["id"]
    clean_train = [c for c in cl if c["split"] == "train" and not c.get("contaminant")]
    moved = set()
    for c in clean_train:
        q = lib["q"][c["index"], :c["length"]]
        moved |= set(np.flatnonzero(np.abs(q - q[0]).max(0) > 0.02).tolist())
    missing = [man["joints"][j] for j in range(14) if j not in moved]
    assert not missing, f"joints never moved in clean train: {missing}"
    n = collections.Counter((c["category"], c["split"], bool(c.get("contaminant"))) for c in cl)
    for t in man["types"]:
        print(f"  {t:14s} train clean {n[(t, 'train', False)]}  broken {n[(t, 'train', True)]}  "
              f"val {n[(t, 'val', False)]}  test {n[(t, 'test', False)]}")
    nb = sum(1 for c in cl if c.get("contaminant"))
    ntr = sum(1 for c in cl if c["split"] == "train")
    print(f"verify OK: {N} clips, train {ntr} ({nb} broken = {100 * nb / ntr:.1f}%), every joint moves in clean train, "
          "no source in two splits")
    if man.get("extended_from"):  # v9x: every base clip unchanged (manifest entry and every array, bit for bit)
        base_dir = os.path.join(os.path.dirname(os.path.normpath(lib_dir)), man["extended_from"])
        blib = np.load(os.path.join(base_dir, "library.npz"))
        bcl = json.load(open(os.path.join(base_dir, "manifest.json")))["clips"]
        assert sorted(blib.files) == sorted(lib.files), (blib.files, lib.files)
        nb_ = len(bcl)
        assert cl[:nb_] == bcl, "a base manifest entry changed"
        for k in lib.files:
            assert lib[k].dtype == blib[k].dtype and lib[k][:nb_].tobytes() == blib[k].tobytes(), k
        xs = cl[nb_:]
        assert all(c["split"] == "test" and c.get("new_in") == "v9x" and c["check"]["pass"] for c in xs)
        bars = man["bars_from_v7_walking"]
        for c in xs:
            if c["generator"] == "keyframed":
                y = c["dynamic"]
                assert y["rate_lag_rad"] <= bars["rate_lag_rad"] + 5e-4 and y["zmp_min_margin_mm"] >= bars["zmp_min_margin_mm"] - 0.05 \
                    and not y["takeoff_fail"], c["id"]
        sp = {c["source"] for c in bcl}
        assert not sp & {c["source"] for c in xs}
        print(f"  {man['extended_from']}: {nb_} clips identical (manifest + {len(lib.files)} arrays, bit for bit); "
              f"{len(xs)} new test clips, all pass the clean checks, no source shared with {man['extended_from']}")


def describe(c):
    p = c["params"]
    cat, g = c["category"], c.get("generator")
    if g == "gait":
        return (f"vx {p['mean_vx']:+.3f} m/s, vy {p['mean_vy']:+.3f}, yaw {p['mean_yaw_rate']:+.2f} rad/s; "
                f"{p['style']} (lift {100 * p['foot_lift_m']:.1f} cm)")
    if cat == "crouch":
        return f"depth {1000 * p['depth_m']:.1f} mm, down/up {p['move_s']} s"
    if cat == "bow":
        return f"pitch {p['pitch_deg']}°, down/up {p['move_s']} s"
    if cat == "sway":
        return f"±{1000 * p['amp_m']:.1f} mm at {p['freq_hz']} Hz"
    if cat == "head":
        return f"{p['move'].replace('_', ' ')} ×{p['amp_scale']} at {p['freq_hz']} Hz"
    return ", ".join(f"{k} {v}" for k, v in p.items() if k != "ik_foot_err_mm")


def evidence(c):
    f = c["feasibility"]
    ev, k = f["evidence"], f["kind"]
    if k == "shove":
        h = ev["hold"]
        return f"base {100 * ev['shove_m']:+.0f} cm; hold test on frame {ev['hold_frame']}: {h.get('why', 'held')} at {h.get('t_fail_s')} s"
    if k == "speed":
        return f"×{ev['compression']} faster; servo lag {ev['rate_lag_rad']:.2f} rad > bar {ev['lag_bar_rad']:.2f}"
    if k == "joint_limit":
        return f"{ev['params']}; joint-limit margin {ev['joint_limit_margin_rad']:.3f} rad"
    if k == "takeoff":
        return f"h {ev['params']['h']} m: needs {ev['takeoff_need_m_s']:.2f} m/s, legs give {ev['takeoff_can_m_s']:.2f}"
    if k == "one_foot_long":
        h = ev["hold"]
        up = f", {ev['clearance_mm']} mm clear" if "clearance_mm" in ev else ""
        return f"{ev['raised_foot']} foot up {ev['raised_s']} s{up}; hold test: {h.get('why', 'held')} at {h.get('t_fail_s')} s"
    if k == "noise":
        return f"{ev['rms_rad']} rad RMS, {ev['band_hz'][0]}-{ev['band_hz'][1]} Hz"
    if k == "glitch":
        return "; ".join(f"frame {j['frame']}: {', '.join(j['joints'])}" for j in ev["jumps"])
    return f"{ev['foot']} sole slides {100 * ev['slide_m']:.0f} cm over {ev['frames_sliding_in_contact']} frames in contact"


def write_doc(lib_dir, out):
    man = json.load(open(os.path.join(lib_dir, "manifest.json")))
    cl = man["clips"]
    n = collections.Counter((c["category"], c["split"], bool(c.get("contaminant"))) for c in cl)
    rows = [f"| {t} | {n[(t, 'train', False)]} | {n[(t, 'train', True)]} | {n[(t, 'val', False)]} | {n[(t, 'test', False)]} |"
            for t in man["types"]]
    br = [c for c in cl if c.get("contaminant")]
    kinds = collections.Counter((c["feasibility"]["family"], c["contaminant"]) for c in br)
    brow = [f"| `{c['id']}` | {c['category']} | {c['feasibility']['family']} | {c['contaminant']} | {evidence(c)} |"
            for c in sorted(br, key=lambda c: (c["feasibility"]["family"] != "impossible", c["contaminant"], c["category"]))]
    crow = [f"| `{c['id']}` | {c['category']} | {c['split']}{' (' + c['new_in'] + ')' if c.get('new_in') else ''} | {describe(c)} | "
            f"{c['check']['peak_joint_speed_rad_s']:.1f} |"
            for t in man["types"] for c in sorted((c for c in cl if c["category"] == t and not c.get("contaminant")),
                                                    key=lambda c: (("train", "val", "test").index(c["split"]), c["id"]))]
    ntr = sum(c["split"] == "train" for c in cl)
    b = man["bars_from_v7_walking"]
    name, base = os.path.basename(os.path.normpath(lib_dir)), man.get("extended_from")
    xs = [c for c in cl if c.get("new_in")]
    ntest = collections.Counter(c["category"] for c in cl if c["split"] == "test")
    per_test = f"{min(ntest.values())}" if min(ntest.values()) == max(ntest.values()) else "5-12"
    gifs = ("GIFs of every clip, labelled\nwith split and broken kind: [`results/clips_v9/gifs/`](../results/clips_v9/gifs/README.md)."
            if not base else f"GIFs of the {base} clips (the\nnew test clips have none yet): [`results/clips_v9/gifs/`](../results/clips_v9/gifs/README.md).")
    ext_txt = "" if not base else (
        f"""- **Extension of `data/{base}`:** every {base} clip is copied unchanged (same id, index and arrays, checked
  bit for bit by `--verify`); {len(xs)} new clean test clips are appended, marked `"new_in": "{man['version']}"`, 7 per type, one
  variant per new source (sources listed in `GAITS_X` ... `WILD_X` of `make_v9.py`, none equal to any {base} train /
  val / test / spare source). Train and val are exactly {base}'s.
""")
    xrow = [f"| `{c['id']}` | {c['category']} | {describe(c)} | {c['check']['joint_limit_margin_rad']:.3f} | "
            f"{c['check']['peak_joint_speed_rad_s']:.1f} | {c['dynamic']['rate_lag_rad']:.3f} | {c['dynamic']['zmp_min_margin_mm']:.1f} | "
            f"{'pass' if c['check']['pass'] else 'FAIL'} |" for t in man["types"] for c in xs if c["category"] == t]
    xsec = "" if not xs else f"""
## New test clips ({man['version']})

Each passes `make_library.check_clip`; keyframed clips also pass the servo-lag / balance bars above (and hops the
take-off check). Servo lag and balance margin are `dynamic_check.py`'s reference-only measures (shown for every clip;
the bars apply to keyframed clips only, as in {base}).

| clip | type | parameters | joint-limit margin (rad) | peak joint speed (rad/s) | servo lag (rad) | balance margin (mm) | check |
|---|---|---|---|---|---|---|---|
{chr(10).join(xrow)}
"""
    doc = f"""# Reference-clip dataset {man['version']}

Built by `curation/clips/make_v9.py`; this file is written from `data/{name}/manifest.json`
(`python3 curation/clips/make_v9.py --verify data/{name} --doc docs/{os.path.basename(out)}`). {gifs}

## Contents

- **{len(cl)} clips**, 50 Hz, at most 4 s. Train / val / test: **{ntr} / {sum(c['split'] == 'val' for c in cl)} /
  {sum(c['split'] == 'test' for c in cl)}**; {len(br)} of the train clips are broken copies ({100 * len(br) / ntr:.1f}% of train).
{ext_txt}- 14 motion types. Clean clips per type: 6 train, 3 val, {per_test} test, split by source (a source's clips are all in one
  split); val / test sources are parameter values no train clip has, mostly inside the train range.
- Splits are fixed by design in `make_v9.py` (no random draw). Every actuated joint moves in the clean train clips.
- `leg_lift` merges march (Placo gaits) with keyframed stomp, kick and tap (weight shifted {100 * man['keyframed_weight_shift_m']:.1f} cm).
- Keyframed clips are kept clean only if no more demanding than the clean v7 walking gaits on the reference-only
  measures of `dynamic_check.py`: servo lag ≤ **{b['rate_lag_rad']} rad** and balance margin ≥ **{b['zmp_min_margin_mm']} mm**
  (worst of {b['n_gait_clips']} v7 gait clips), and hops within the legs' take-off speed.

| type | train clean | train broken | val | test |
|---|---|---|---|---|
{chr(10).join(rows)}
{xsec}
## Broken clips

Each is a copy of a clean train clip of the same type (`derived_from`), in the train split only.
`feasibility` = {{"infeasible", "corrupted": true, "family", "kind", "evidence"}}.

- **impossible** (physics-verified, `infeasible: true`): shove (hold test fails on the shoved pose), joint_limit
  (targets clip at a joint limit), takeoff (the hop needs more take-off speed than the legs give), speed
  (time-compressed until the servo lag exceeds the worst clean v7 walking gait's, {b['rate_lag_rad']} rad),
  one_foot_long (a foot held up 2-3 s off balance; the hold test fails).
- **corrupted** (by construction, `infeasible: false`): noise (3-8 Hz jitter, 0.07 rad RMS), glitch (3 short pose
  jumps), foot_skate (the left sole slides 4 cm while marked in contact).

| family | kind | clips |
|---|---|---|
{chr(10).join(f"| {f} | {k} | {v} |" for (f, k), v in sorted(kinds.items()))}

| clip | type | family | kind | evidence |
|---|---|---|---|---|
{chr(10).join(brow)}

## Generation notes

{chr(10).join(f"- {x}" for x in man['notes']) or "- none"}

## Clean clips

| clip | type | split | parameters | peak joint speed (rad/s) |
|---|---|---|---|---|
{chr(10).join(crow)}
"""
    open(out, "w").write(doc)
    print("wrote", out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--presets", nargs=2, metavar=("GEN", "OUT"))
    p.add_argument("--gaits")
    p.add_argument("--v7")
    p.add_argument("--out")
    p.add_argument("--verify")
    p.add_argument("--doc")
    p.add_argument("--extend-test", metavar="V9_DIR", help="v9x: keep this library and append the new test sources")
    a = p.parse_args()
    if a.presets:
        write_presets(*a.presets, ext=bool(a.extend_test))
    elif a.verify:
        verify(a.verify)
        if a.doc:
            write_doc(a.verify, a.doc)
    else:
        build_library(a)


if __name__ == "__main__":
    main()
