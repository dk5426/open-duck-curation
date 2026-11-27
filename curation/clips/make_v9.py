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

v9c (--contaminate, the contamination follow-up of PREREG_V3): clips_v9x unchanged (every clip, same id, index and
arrays) with broken TRAIN copies appended, k = N / 84 per clean train clip for --broken N (6k per type, balanced). The
clean train clips are regenerated as in v9 and checked bit for bit against clips_v9x, then broken by the generator
above. v9's 25 broken clips are copy 0 of their clean clip; copy r of every other clip draws its impossible kinds in
turn (the kinds its type allows, rotated by clip and copy; parameters vary with clip and copy, so no two copies are the
same), the first that passes its check is kept, and a clip none passes becomes corrupted. Per copy round, corrupted
clips are then topped up (even across types) to v9's mix, 16 impossible : 9 corrupted. Copy r is in every dose with
k > r, so a smaller dose's library is the first rows of a larger one's (one run writes every dose).
  1. cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_v9.py \
         --contaminate ../open-duck-curation/data/clips_v9x --gaits ../open-duck-curation/data/placo_gaits_v9 \
         --v7 ../open-duck-curation/data/clips_v7 --broken 84 252 \
         --out ../open-duck-curation/data/clips_v9c50 ../open-duck-curation/data/clips_v9c75 --jobs 6
  2. python3 curation/clips/make_v9.py --verify data/clips_v9c50 --doc docs/DATASET_V9C.md (and data/clips_v9c75)
"""

import argparse
import collections
import hashlib
import json
import multiprocessing
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
# v9c: per-copy parameter schedules (copy r, clip j of its type, re-draw i); v9's own values are copy 0's first draw
SEED_C = 90  # noise / glitch draws: np.random.default_rng([SEED_C, type, clip, copy])
IMP_FRAC = 16 / 25  # v9's impossible share, kept per copy round
OFL_LIFTS = ((0.03, 0.025), (0.045, 0.03), (0.06, 0.035))  # one_foot (fwd, up) m, as v9
CORRUPTED = ("noise", "glitch", "foot_skate")
# v9s: systematic errors replace their clean train clip (3 of 6 per type, both kinds per type, 21 + 21)
SEED_S = 91
SYSTEMATIC = ("joint_offset", "stance_skate")
OFFSET_J = {"hip_pitch": (2, 11, -1), "knee": (3, 12, 1), "ankle": (4, 13, 1)}  # (left, right, right's sign: hip pitch mirrored)


def imp_kinds(cat, e):
    """Impossible kinds a clean train clip allows: a gait (march too) has no amplitude to push and no double-support
    stretch to raise a foot from; hops take off; leg lifts hold their single-support frame."""
    fam = e.get("family") or cat
    if cat in GAIT_TYPES or fam == "march":
        return ["shove", "speed"]
    if cat == "hop":
        return ["takeoff", "shove", "speed"]
    if fam in ("stomp", "kick", "dance", "headbang", "twist"):
        return ["joint_limit", "one_foot_long", "shove", "speed"]
    return ["shove", "one_foot_long", "speed"]


def redraws(fn, kind, cat, j, r, e0, base):
    """Candidates (arrays, evidence, ok) for one impossible kind on copy r of clean clip j; the parameters differ with
    j and r (shove 1 cm per copy, growing 3 cm per re-draw, gaits backwards and the rest forward or back in turn;
    speed 2-3x; one_foot side and lift; joint-limit amplitude scale; take-off height 1 mm per slot)."""
    fam = e0.get("family") or cat
    if kind == "shove":
        mag = lambda s, i: (0.12 if s > 0 else 0.07) + 0.01 * r + 0.03 * i  # noqa: E731
        gait = cat in GAIT_TYPES or fam == "march"
        s = -1 if gait else (1 if (j + r) % 2 == 0 else -1)
        seq = [s * mag(s, i) for i in range(3)] if gait else [s * mag(s, 0), s * mag(s, 1), -s * mag(-s, 0), -s * mag(-s, 1)]
        for dx in seq:
            yield fn["shove"](base, round(dx, 3))
    elif kind == "speed":
        for kf in (2.0 + 0.15 * (r % 3), 2.5 + 0.15 * (r % 3), 3.0 - 0.05 * (r % 3)):
            yield fn["speed"](base, round(kf, 2))
    elif kind == "one_foot_long":
        if fam in ("stomp", "kick"):
            yield fn["hold_ss"](base, (2.5, 2.2, 2.8)[r % 3])
        else:
            for i in range(6):
                f, u = OFL_LIFTS[(i // 2 + r) % 3]
                yield fn["one_foot"](base, (j + r + i) % 2, (round(f + 0.005 * r, 3), u))
    elif kind == "joint_limit":
        for _, _, clip in fn["amplify"](e0, kind, round(1 + 0.1 * r + 0.03 * j, 3)):
            q, pos, quat, con, prm = clip
            rep, _ = fn["measure"](np.clip(q, fn["lo"], fn["hi"]), pos, quat, con)
            yield (q, pos, quat, con), {"params": prm, "joint_limit_margin_rad": rep["joint_limit_margin_rad"]}, \
                not rep["pass"] and rep["joint_limit_margin_rad"] <= 1e-3
    elif kind == "takeoff":
        for i in range(2):
            p2 = dict({k: v for k, v in e0["params"].items() if k != "ik_foot_err_mm"}, h=round(0.025 + 0.001 * (6 * r + j) + 0.01 * i, 4))
            q, pos, quat, con, prm = fn["wild"]("hop", p2)
            _, dyn = fn["measure"](np.clip(q, fn["lo"], fn["hi"]), pos, quat, con)
            yield (q, pos, quat, con), {"params": prm, "takeoff_need_m_s": dyn["takeoff_need_m_s"],
                                        "takeoff_can_m_s": dyn["takeoff_can_m_s"]}, dyn["takeoff_fail"]


def impossible_slot(fn, slot):
    """Copy r of clean clip j: the clip's impossible kinds in turn (rotated by j + r), each re-drawn; the first that passes
    its check is kept. Returns (kind, arrays, evidence) or None, and the rejections."""
    r, cat, j = slot
    e0, base = fn["train"][cat][j]
    ks = imp_kinds(cat, e0)
    ks = ks[(j + r) % len(ks):] + ks[:(j + r) % len(ks)]
    rej = []
    for kind in ks:
        ev = None
        for arr, ev, ok in redraws(fn, kind, cat, j, r, e0, base):
            if ok:
                return (kind, arr, ev), rej
        rej.append(f"{e0['id']} copy {r}: {kind} rejected (last: {json.dumps(ev, default=str)[:160]})")
    return None, rej


_SLOT = None  # set before the worker pool forks (the break functions are closures over the model)


def _slot(s):
    return _SLOT(s)


def confirmed(c):
    """An impossible clip's own check, read back from its manifest entry (the evidence it was kept on)."""
    k, ev = c["contaminant"], c["feasibility"]["evidence"]
    if k == "speed":
        return ev["rate_lag_rad"] > ev["lag_bar_rad"]
    if k == "takeoff":
        return bool(c["dynamic"]["takeoff_fail"]) and ev["takeoff_need_m_s"] > ev["takeoff_can_m_s"]
    if k == "joint_limit":
        return not c["check"]["pass"] and c["check"]["joint_limit_margin_rad"] <= 1e-3
    if k == "shove":
        return not ev["hold"]["held"] and ev["ik_foot_err_mm"] <= 1000 * SHOVE_IK_MAX
    return not ev["hold"]["held"] and ev["clearance_mm"] >= 8.0 and ev.get("ik_foot_err_mm", 0) <= 1000 * SHOVE_IK_MAX


def row_hash(lib, i):
    return hashlib.sha1(b"".join(lib[k][i].tobytes() for k in ("q", "base_pos", "base_quat", "contacts"))).hexdigest()


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
    splits = ("train",) if a.contaminate or a.systematic else ("train", "val", "test")  # v9c / v9s edit train clips only
    for cat in GAIT_TYPES + ["march"]:
        spec = G.get(cat) if cat != "march" else MA
        tcat = "leg_lift" if cat == "march" else cat
        spares = list(spec["spare"])
        j0 = len((GAITS.get(cat) or MARCH)["test"]) if ext else 0
        for split in splits:
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
    for split in splits:
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
        for split in splits[1:]:
            for src, v in spec.get(split, []):
                while not add(cat, f"{sid_of(src)}__{v}", sid_of(src), split, stat(cat, src, v), "ik"):
                    notes.append(f"{sid_of(src)}__{v} ({split}) failed the checks; replaced by a spare")
                    src, v = spares.pop(0)
    for fam, spec in WI.items():
        spares = list(spec["spare"])
        for split in splits:
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
    keep_head = bool(a.contaminate or a.systematic)  # v9c / v9s: head motion kept in IK edits (see solve_feet), whole holds

    def solve_feet(q0, pos, quat, tgt, iters=120, q_ref=None):
        """Leg joints that put each sole at its target (world pos, rot) with the base at pos / quat. Seeded from q0 (the
        previous solved frame), so the head joints are q0's: in v9 they stay at frame 0's pose (the head motion is lost);
        v9c passes the frame's own pose as q_ref and keeps its head joints (they are not in the leg chains)."""
        qf = home.qpos.copy()
        qf[0:3], qf[3:7], qf[qadr] = pos, quat, q0
        if q_ref is not None:
            qf[qadr[5:9]] = q_ref[5:9]
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
            q2[k], err = solve_feet(q2[k - 1] if k else q[k], pos2[k], quat[k], tgt, q_ref=q[k] if keep_head else None)
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
            q2[k], err = solve_feet(q2[k - 1] if k else q[k], pos[k], quat[k], tgt, q_ref=q[k] if keep_head else None)
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
        rep = int(hold_s * ml.FPS)
        if keep_head:  # v9c: the highest frame whose whole hold fits in the 4 s (v9's stomp copy held frame 138, so only
            hgt = [h_ if k + rep <= T else -1.0 for k, h_ in zip(ss, hgt)]  # 1.2 s of its 2.5 s survived the cut)
        k = ss[int(np.argmax(hgt))]
        sel = list(range(k)) + [k] * rep + list(range(k, len(q)))
        sel = sel[:T]
        q2, pos2, quat2, c2 = q[sel], pos[sel], quat[sel], con[sel]
        h = ht.hold(m, d, qadr, q[k], grounded(q[k], pos[k], quat[k], int(np.argmax(con[k]))), quat[k], con[k])
        return (q2, pos2, quat2, c2), {"held_frame": k, "raised_s": hold_s, "raised_foot": "left" if con[k, 0] < 0.5 else "right",
                                       "clearance_mm": round(1000 * max(hgt), 1), "hold": h}, \
            (not h["held"]) and max(hgt) > 0.008 and (not keep_head or k + rep <= T)

    def noise(base, amp=0.07, rng=rng):
        q, pos, quat, con = base
        b, a_ = butter(2, [3 / (ml.FPS / 2), 8 / (ml.FPS / 2)], btype="band")
        z = filtfilt(b, a_, rng.standard_normal((len(q) + 100, 14)), axis=0)[50:50 + len(q)]
        z = z / z.std(0) * amp
        env = ml.minjerk(t_of(len(q)) / 0.3)[:, None]
        return (q + env * z, pos, quat, con), {"band_hz": [3, 8], "rms_rad": amp}, True

    def glitch(base, rng=rng):
        q, pos, quat, con = base
        q2, ev = q.copy(), []
        times = np.sort(rng.choice(np.arange(int(0.5 * ml.FPS), len(q) - int(0.5 * ml.FPS)), 3, replace=False))
        for k in times:
            js = rng.choice(14, int(rng.integers(2, 4)), replace=False)
            off = rng.choice([-1, 1], len(js)) * rng.uniform(0.3, 0.5, len(js))
            q2[k:k + 4, js] += off
            ev.append({"frame": int(k), "frames": 4, "joints": [ml.ACT[j] for j in js], "offset_rad": [round(float(o), 3) for o in off]})
        return (q2, pos, quat, con), {"jumps": ev}, True

    def skate(base, dist=0.04, foot=0):
        q, pos, quat, con = base
        n = len(q)
        t = t_of(n)
        s = dist * (ml.minjerk((t - 0.8) / 1.0) - ml.minjerk((t - 2.4) / 1.0))
        q2, worst, slid = q.copy(), 0.0, 0
        for k in range(n):
            tgt = fk_feet(q[k], pos[k], quat[k])
            tgt[foot] = (tgt[foot][0] + s[k] * heading(quat[k]), tgt[foot][1])
            q2[k], err = solve_feet(q2[k - 1] if k else q[k], pos[k], quat[k], tgt, q_ref=q[k] if keep_head else None)
            worst = max(worst, err)
            slid += int(con[k, foot] > 0.5 and s[k] > 0.005)
        return (q2, pos, quat, con), {"slide_m": dist, "foot": ("left", "right")[foot], "frames_sliding_in_contact": slid,
                                      "ik_foot_err_mm": round(1000 * worst, 1)}, slid > 10

    # ---- v9s: systematic errors (trackable but wrong; the clip must stay feasible)
    def stance_runs(c):
        """[start, end) frames of each stance phase of one foot."""
        e_ = np.flatnonzero(np.diff(np.r_[0, (c > 0.5).astype(int), 0]))
        return list(zip(e_[::2], e_[1::2]))

    def stance_skate(base, dist, way="forward"):
        """Every stance foot slides `dist` (m) the `way` of the heading (forward / back / left / right, the same for both feet)
        over each of its stance phases (min-jerk) and
        glides back while it swings, so nothing builds up; a foot that never lifts (standing clips) slides once, over
        the whole clip. skate() generalised to both feet and every phase; phases under 5 frames are left alone."""
        q, pos, quat, con = base
        n = len(q)
        off = np.zeros((n, 2))
        for f in range(2):
            runs = stance_runs(con[:, f])
            for s_, e_ in runs:
                if e_ - s_ >= 5:
                    off[s_:e_, f] = ml.minjerk((np.arange(s_, e_) - s_ + 1) / (e_ - s_))
            for (_, e0_), (s1, _) in zip(runs, runs[1:]):
                off[e0_:s1, f] = off[e0_ - 1, f] * (1 - ml.minjerk((np.arange(e0_, s1) - e0_ + 1) / (s1 - e0_)))
            if runs:
                off[runs[-1][1]:, f] = off[runs[-1][1] - 1, f]
        q2, worst = q.copy(), 0.0
        rot = {"forward": (1, 0), "back": (-1, 0), "left": (0, 1), "right": (0, -1)}[way]
        for k in range(n):
            tgt = fk_feet(q[k], pos[k], quat[k])
            h_ = heading(quat[k])
            v_ = rot[0] * h_ + rot[1] * np.array([-h_[1], h_[0], 0.0])
            tgt = [(tgt[f][0] + dist * off[k, f] * v_, tgt[f][1]) for f in range(2)]
            # seeded from the clean frame, not the previous solved one (as skate() is): a gait's knee passes near zero and
            # a previous-frame seed can settle on the other knee branch for the rest of the clip (a ~2 rad error)
            q2[k], err = solve_feet(q[k], pos[k], quat[k], tgt, q_ref=q[k])
            worst = max(worst, err)
        nph = sum(1 for f in range(2) for s_, e_ in stance_runs(con[:, f]) if e_ - s_ >= 5)
        jump = float(np.abs(q2 - q).max())
        return (q2, pos, quat, con), {"slide_m": dist, "direction": way, "stance_phases_slid": nph,
                                      "ik_foot_err_mm": round(1000 * worst, 1), "max_joint_change_rad": round(jump, 3)}, \
            worst <= 0.01 and jump <= 1.0  # v9's skates went to 10.4 mm; > 1 rad = a knee branch flip, not a skate

    def joint_offset(base, joint, amt):
        """A constant offset `amt` (rad) on one pitch joint of both legs, the same physical direction on both (hip pitch
        axes are mirrored, knee and ankle are not), for the whole clip; the base is lowered or raised per frame so the
        stance soles' lowest corners are where the clean clip has them (in flight: the nearest stance frame's shift)."""
        q, pos, quat, con = base
        jl, jr, sr = OFFSET_J[joint]
        q2 = q.copy()
        q2[:, jl] += amt
        q2[:, jr] += sr * amt
        dz = np.full(len(q), np.nan)
        for k in range(len(q)):
            low = []
            for qq in (q[k], q2[k]):
                d.qpos[:] = home.qpos
                d.qpos[0:3], d.qpos[3:7], d.qpos[qadr] = pos[k], quat[k], np.clip(qq, lo, hi)
                mujoco.mj_kinematics(m, d)
                low.append([sole_low(0), sole_low(1)])
            st = con[k] > 0.5
            if st.any():
                dz[k] = float((np.array(low[0]) - np.array(low[1]))[st].mean())
        ok_ = np.flatnonzero(np.isfinite(dz))
        dz = np.interp(np.arange(len(q)), ok_, dz[ok_])
        pos2 = pos.copy()
        pos2[:, 2] += dz
        return (q2, pos2, quat, con), {"joint": joint, "offset_rad": amt, "right_leg_sign": sr,
                                       "root_dz_mm": [round(1000 * float(dz.min()), 1), round(1000 * float(dz.max()), 1)]}, True

    def stance_slide(q, pos, quat, con):
        """Mean over stance phases (>= 5 frames) of a sole's horizontal travel (m) from where the phase began."""
        tr = []
        for f in range(2):
            for s_, e_ in stance_runs(con[:, f]):
                if e_ - s_ >= 5:
                    xy = np.array([fk_feet(q[k], pos[k], quat[k])[f][0][:2] for k in range(s_, e_)])
                    tr.append(float(np.linalg.norm(xy - xy[0], axis=1).max()))
        return float(np.mean(tr)) if tr else 0.0

    def hold_ks(q):
        """Frames for the hold test: the first, and hold_test.py's (the held pose farthest from home, if the clip has one)."""
        qd = np.gradient(q, 1 / ml.FPS, axis=0)
        quiet = np.convolve(np.abs(qd).max(axis=1) < ht.STILL, np.ones(ht.STILL_FRAMES), "same") >= ht.STILL_FRAMES
        still = np.where(quiet)[0]
        return [0] + ([int(still[np.argmax(np.abs(q[still] - home.ctrl).sum(axis=1))])] if len(still) else [])

    def feasible(e0, clean, arr):
        """Feasible = the clean clip's own checks (make_library.check_clip incl. joint-limit margin; servo-lag / balance
        bars for keyframed clips) and the hold test on every frame where the clean clip holds."""
        q, pos, quat, con = arr
        q = np.clip(q, lo, hi)
        rep, dyn = measure(q, pos, quat, con)
        ks = hold_ks(clean[0])  # the clean clip's frames, so both clips are tested on the same poses
        hc = {k: ht.hold(m, d, qadr, clean[0][k], clean[1][k], clean[2][k], clean[3][k]) for k in ks}
        hw = {k: ht.hold(m, d, qadr, q[k], pos[k], quat[k], con[k]) for k in ks}
        held = all(hw[k]["held"] for k in ks if hc[k]["held"])
        f = {"kinematic": rep["pass"], "bars": clean_ok(e0["generator"], rep, dyn), "hold": hw,
             "hold_clean": {k: v["held"] for k, v in hc.items()}, "held": held}
        f["pass"] = bool(f["kinematic"] and f["bars"] and held)
        return (q, pos, quat, con), rep, dyn, f

    train = {c: [(e, arr) for e, arr in clips if e["category"] == c and e["split"] == "train"] for c in TYPES}
    used = collections.Counter()
    broken = []

    def next_base(cat, pred=lambda e: True, kind=None):
        taken = {x[0]["derived_from"] for x in broken if x[0]["contaminant"] == kind}
        cands = [x for x in train[cat] if pred(x[0]) and x[0]["id"] not in taken] or [x for x in train[cat] if pred(x[0])]
        x = cands[used[cat] % len(cands)]
        used[cat] += 1
        return x

    def amplify(e, kind, scale=1.0):
        fam = e.get("family") or e["category"]
        prm = {k: v for k, v in e["params"].items() if k != "ik_foot_err_mm"}
        tries = {"dance": [("a", 1.4), ("a", 1.6)], "headbang": [("a", 0.95), ("a", 1.1)], "twist": [("a", 0.65), ("a", 0.8)],
                 "stomp": [("lift", 0.06), ("lift", 0.08)], "kick": [("r", 0.10), ("r", 0.12)], "hop": [("h", 0.025), ("h", 0.03)]}[fam]
        for k_, v in tries:
            p2 = dict(prm, **{k_: v if scale == 1 else round(v * scale, 4)})  # v9c scales the push per copy
            yield fam, p2, wild(fam, p2)

    if a.systematic:
        fn = dict(train=train, skate=stance_skate, offset=joint_offset, feasible=feasible, slide=stance_slide, lo=lo, hi=hi)
        return write_systematic(a, fn, notes, m, d, qadr, T, {"rate_lag_rad": round(LAG_BAR, 3),
                                                              "zmp_min_margin_mm": round(ZMP_BAR, 1), "n_gait_clips": len(lags)})
    if a.contaminate:
        fn = dict(train=train, shove=shove, speed=speed, one_foot=one_foot, hold_ss=hold_single_support, noise=noise,
                  glitch=glitch, skate=skate, amplify=amplify, wild=wild, measure=measure, lo=lo, hi=hi)
        return write_contaminated(a, fn, notes, m, d, qadr, T, {"rate_lag_rad": round(LAG_BAR, 3),
                                                                "zmp_min_margin_mm": round(ZMP_BAR, 1), "n_gait_clips": len(lags)})

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


def write_contaminated(a, fn, notes, m, d, qadr, T, bars):
    """v9c: the clips_v9x library unchanged (same rows, ids, indices) with broken train copies appended, k per clean train
    clip for each --broken N (k = N / 84); one library per N, a smaller dose being the first rows of a larger one."""
    global _SLOT
    from make_infeasible import arrays
    base = np.load(os.path.join(a.contaminate, "library.npz"))
    man = json.load(open(os.path.join(a.contaminate, "manifest.json")))
    assert bars == man["bars_from_v7_walking"], (bars, man["bars_from_v7_walking"])
    assert len(a.broken) == len(a.out) and all(n % 84 == 0 for n in a.broken), (a.broken, a.out)
    train, N0, K = fn["train"], len(man["clips"]), max(a.broken) // 84

    def row(q, pos, quat, con):
        out = {}
        for k_, x in arrays(m, d, qadr, q, pos, quat, con).items():
            out[k_] = np.zeros((T,) + x.shape[1:], dtype=base[k_].dtype)
            out[k_][:len(x)], out[k_][len(x):] = x, x[-1]
        return out

    # the regenerated clean train clips are clips_v9x's, entry and arrays bit for bit (they are what gets broken)
    by_id = {c["id"]: c for c in man["clips"]}
    for cat in TYPES:
        assert len(train[cat]) == 6, (cat, len(train[cat]))
        for e, arr in train[cat]:
            c = dict(by_id[e["id"]])
            i = c.pop("index")
            e_ = json.loads(json.dumps({k: v for k, v in e.items() if not (k == "family" and v is None)}, default=float))
            assert e_ == c, e["id"]
            assert all(x.tobytes() == base[k_][i].tobytes() for k_, x in row(*arr).items()), e["id"]
    print(f"{sum(map(len, train.values()))} regenerated clean train clips identical to {a.contaminate}")

    # copy 0 of a clip v9 broke is v9's broken clip; every other (copy, type, clip) slot is drawn here
    jof = {e["id"]: (cat, j) for cat in TYPES for j, (e, _) in enumerate(train[cat])}
    v9b = {jof[c["derived_from"]]: c for c in man["clips"] if c.get("contaminant")}
    assert len(v9b) == sum(1 for c in man["clips"] if c.get("contaminant")), "v9 broke a clip twice"
    slots = [(r, cat, j) for r in range(K) for cat in TYPES for j in range(6) if r or (cat, j) not in v9b]
    _SLOT = lambda s: impossible_slot(fn, s)  # noqa: E731
    if a.jobs > 1:
        with multiprocessing.get_context("fork").Pool(a.jobs) as pool:
            res = dict(zip(slots, pool.map(_slot, slots, chunksize=1)))
    else:
        res = {s: _slot(s) for s in slots}
    snotes = collections.defaultdict(list)  # notes by copy round
    for s in slots:
        snotes[s[0]] += res[s][1]

    # per copy round: corrupted = clips no impossible kind passed, topped up evenly across types to v9's mix; the top-up
    # takes the type's most common impossible kind first; a corrupted kind is the type's least used so far
    imp_n = {c: collections.Counter() for c in TYPES}
    cor_n = {c: collections.Counter() for c in TYPES}
    for (cat, _), c in v9b.items():
        (imp_n if c["contaminant"] in IMPOSSIBLE else cor_n)[cat][c["contaminant"]] += 1
    final = {}
    for r in range(K):
        rs = [s for s in slots if s[0] == r]
        corr = collections.Counter({c: sum(1 for (c_, _), x in v9b.items() if c_ == c and x["contaminant"] not in IMPOSSIBLE)
                                    for c in TYPES} if r == 0 else {})
        to_cor = []
        for s in rs:
            if res[s][0] is None:
                to_cor.append(s)
                corr[s[1]] += 1
                snotes[r].append(f"{train[s[1]][s[2]][0]['id']} copy {r}: no impossible kind passed; made corrupted")
            else:
                imp_n[s[1]][res[s][0][0]] += 1
        target = 84 - round(84 * IMP_FRAC)
        avail = {c: [s for s in rs if s[1] == c and res[s][0] is not None] for c in TYPES}
        topped = 0
        while sum(corr.values()) < target and any(avail.values()):
            c = min((c for c in TYPES if avail[c]), key=lambda c: (corr[c], (TYPES.index(c) - 5 * r) % len(TYPES)))
            s = max(avail[c], key=lambda s: (imp_n[c][res[s][0][0]], -s[2]))
            avail[c].remove(s)
            imp_n[c][res[s][0][0]] -= 1
            to_cor.append(s)
            corr[c] += 1
            topped += 1
        nc = sum(corr.values())
        snotes[r].append(f"copy {r}: {topped} clips whose impossible kind passed were made corrupted for v9's mix "
                         f"({84 - nc} impossible : {nc} corrupted, target {84 - target} : {target})")
        for s in rs:
            if s not in to_cor:
                final[s] = res[s][0]
        for s in sorted(to_cor, key=lambda s: (TYPES.index(s[1]), s[2])):
            _, cat, j = s
            ks = sorted(CORRUPTED[(j + r) % 3:] + CORRUPTED[:(j + r) % 3], key=lambda k: cor_n[cat][k])
            for kind in ks:
                rng = np.random.default_rng([SEED_C, TYPES.index(cat), j, r])
                arr, ev, ok = (fn["noise"](train[cat][j][1], rng=rng) if kind == "noise" else
                               fn["glitch"](train[cat][j][1], rng=rng) if kind == "glitch" else
                               fn["skate"](train[cat][j][1], dist=(0.04, 0.035, 0.045)[r % 3], foot=(j + r) % 2))
                if ok:
                    break
                snotes[r].append(f"{train[cat][j][0]['id']} copy {r}: {kind} rejected ({json.dumps(ev, default=str)[:160]})")
            cor_n[cat][kind] += 1
            final[s] = (kind, arr, ev)

    # entries (as v9's broken clips) in copy, type, clip order; ids as v9 ("b" appended while taken)
    ids = {c["id"] for c in man["clips"]}
    new, rows, hashes = [], [], {row_hash(base, i): c["id"] for i, c in enumerate(man["clips"])}
    for s in sorted(final, key=lambda s: (s[0], TYPES.index(s[1]), s[2])):
        r, cat, j = s
        kind, (q, pos, quat, con), ev = final[s]
        e0 = train[cat][j][0]
        q = np.clip(q, fn["lo"], fn["hi"])
        rep, dyn = fn["measure"](q, pos, quat, con)
        fam = "impossible" if kind in IMPOSSIBLE else "corrupted"
        cid = f"{e0['id']}__broken_{kind}"
        while cid in ids:
            cid += "b"
        ids.add(cid)
        e = {"id": cid, "category": cat, "source": cid, "derived_from": e0["id"], "split": "train",
             "params": e0["params"], "check": rep, "dynamic": dyn, "length": len(q), "contaminant": kind,
             "generator": "broken", "family": e0.get("family"),
             "feasibility": {"infeasible": fam == "impossible", "corrupted": True, "family": fam, "kind": kind,
                             "kinematic": rep["pass"], "evidence": ev}, "new_in": "v9c", "copy": r}
        if e["family"] is None:
            e.pop("family")
        e = json.loads(json.dumps(e, default=float))
        assert fam == "corrupted" or confirmed(e), (cid, ev)
        rw = row(q, pos, quat, con)
        h = hashlib.sha1(b"".join(rw[k_].tobytes() for k_ in ("q", "base_pos", "base_quat", "contacts"))).hexdigest()
        assert h not in hashes, f"{cid} repeats {hashes.get(h)}"
        hashes[h] = cid
        new.append(e)
        rows.append(rw)
        print(f"  broken {cid:64s} copy {r} {fam:10s} {json.dumps(ev, default=str)[:120]}")

    ntr = sum(c["split"] == "train" and not c.get("contaminant") for c in man["clips"])
    for nb, out in zip(a.broken, a.out):
        k = nb // 84
        sel = [x for x, e in enumerate(new) if e["copy"] < k]
        lib = {k_: np.concatenate([base[k_]] + [rows[x][k_][None] for x in sel]) for k_ in rows[0]}
        lib["length"] = np.concatenate([base["length"], np.array([new[x]["length"] for x in sel], dtype=base["length"].dtype)])
        ver = f"v9c{round(100 * nb / (ntr + nb))}"
        os.makedirs(out, exist_ok=True)
        np.savez_compressed(os.path.join(out, "library.npz"), **lib)
        manifest = dict(man, version=ver, extended_from=os.path.basename(os.path.normpath(a.contaminate)),
                        split=man["split"] + f"; {ver} appends {len(sel)} broken train copies (make_v9.py --contaminate)",
                        contamination={"broken": nb, "per_clean_clip": k, "seed": SEED_C, "impossible_share": IMP_FRAC,
                                       "v9_broken_kept": len(v9b), "doses": sorted(a.broken)},
                        notes=man["notes"] + [f"{ver}: {x}" for r in range(k) for x in snotes[r]],
                        clips=man["clips"] + [dict(new[x], index=N0 + i) for i, x in enumerate(sel)])
        json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1, default=float)
        print(f"{out}: {N0} clips from {a.contaminate} + {len(sel)} broken copies ({nb} broken with v9's)")


def check_regenerated(train, man, base, row, src):
    """The regenerated clean train clips are the library's, entry and arrays bit for bit (they are what gets edited)."""
    by_id = {c["id"]: c for c in man["clips"]}
    for cat in TYPES:
        assert len(train[cat]) == 6, (cat, len(train[cat]))
        for e, arr in train[cat]:
            c = dict(by_id[e["id"]])
            i = c.pop("index")
            e_ = json.loads(json.dumps({k: v for k, v in e.items() if not (k == "family" and v is None)}, default=float))
            assert e_ == c, e["id"]
            assert all(x.tobytes() == base[k_][i].tobytes() for k_, x in row(*arr).items()), e["id"]
    print(f"{sum(map(len, train.values()))} regenerated clean train clips identical to {src}")


def write_systematic(a, fn, notes, m, d, qadr, T, bars):
    """v9s: clips_v9x's val and test clips unchanged; in train, 3 of each type's 6 clean clips are REPLACED by a
    systematically wrong version (no broken clips, none of v9's 25). Joint offsets and stance skates, both in every
    type (2 + 1 or 1 + 2, 21 + 21), each re-drawn until it is feasible."""
    import itertools
    from make_infeasible import arrays
    base = np.load(os.path.join(a.systematic, "library.npz"))
    man = json.load(open(os.path.join(a.systematic, "manifest.json")))
    assert bars == man["bars_from_v7_walking"], (bars, man["bars_from_v7_walking"])
    train, lo, hi = fn["train"], fn["lo"], fn["hi"]

    def row(q, pos, quat, con):
        out = {}
        for k_, x in arrays(m, d, qadr, q, pos, quat, con).items():
            out[k_] = np.zeros((T,) + x.shape[1:], dtype=base[k_].dtype)
            out[k_][:len(x)], out[k_][len(x):] = x, x[-1]
        return out

    check_regenerated(train, man, base, row, a.systematic)
    rng = np.random.default_rng(SEED_S)
    # which 3 clips per type: a seeded order of the 3-subsets, those that leave the fewest clean style twins first (a gait
    # or stationary source has 2 clips, so replacing 3 of 6 leaves at least one twin there; keyframed sources have 1);
    # the first subset is the draw, a later one is used only if no kind assignment is feasible on it (recorded)
    pick = {}
    for cat in TYPES:
        srcs = [e["source"] for e, _ in train[cat]]
        twins = lambda sub: sum(1 for j in sub if any(srcs[i] == srcs[j] for i in range(6) if i not in sub))  # noqa: E731
        subs = [tuple(int(j) for j in sb) for sb in itertools.combinations(range(6), 3)]
        pick[cat] = sorted((subs[i] for i in rng.permutation(len(subs))), key=twins)  # stable: seeded order within a twin count
    two_off = set(rng.permutation(len(TYPES))[:len(TYPES) // 2].tolist())  # types with 2 offsets + 1 skate
    kinds_of = {}
    for ti, cat in enumerate(TYPES):
        ks = ["joint_offset", "joint_offset", "stance_skate"] if ti in two_off else ["joint_offset", "stance_skate", "stance_skate"]
        kinds_of[cat] = rng.permutation(ks).tolist()
    plan = [(cat, j, k) for cat in TYPES for j, k in zip(pick[cat][0], kinds_of[cat])]
    # parameters: offsets cycle hip pitch / knee / ankle and the sign, skates the direction; magnitudes drawn (offset
    # 0.10-0.15 rad, slide 3-5 cm); a re-draw moves to the next joint / sign (offset) or direction (skate)
    joints = list(OFFSET_J)
    snotes = []

    def draw(cat, j, kind, i_k):
        """Draws of one kind on one clip until one is feasible (offset 6, skate 8 = each direction twice); None if none is."""
        e0, cl0 = train[cat][j]
        for att in range(6 if kind == "joint_offset" else 8):
            if kind == "joint_offset":
                jn, sg = joints[(i_k + att) % 3], (1, -1)[(i_k // 3 + att // 3) % 2]
                arr, ev, ok = fn["offset"](cl0, jn, sg * round(float(rng.uniform(0.10, 0.15)), 3))
            else:  # forward / back alternate across clips; re-draws go through the other three directions
                ways = ["forward", "back"] if i_k % 2 == 0 else ["back", "forward"]
                arr, ev, ok = fn["skate"](cl0, round(float(rng.uniform(0.03, 0.05)), 3), (ways + ["left", "right"])[att % 4])
            arr, rep, dyn, fz = fn["feasible"](e0, cl0, arr)
            if ok and fz["pass"]:
                return arr, rep, dyn, fz, ev
            snotes.append(f"{e0['id']} {kind}: draw {att + 1} not feasible ({json.dumps(dict(ev, kinematic=fz['kinematic'], bars=fz['bars'], held=fz['held'], solved=ok), default=str)[:170]}); re-drawn")
            print("   ", snotes[-1], {k: v.get("why", "held") for k, v in fz["hold"].items()}, flush=True)
        return None

    # per type: the planned kinds; if a clip has no feasible draw, the type's kinds are re-assigned among its 3 replaced
    # clips (same clips, same 2 + 1 split) in a fixed order until every clip has one
    n_k, made, failed = collections.Counter(), [], []
    for cat in TYPES:
        k0 = kinds_of[cat]
        orders = [k0] + [list(o) for o in sorted(set(itertools.permutations(k0))) if list(o) != k0]
        n0, ok_ = collections.Counter(n_k), False
        for si, js in enumerate(pick[cat][:8]):
            for o in orders:
                n_k, res = collections.Counter(n0), []
                for j, kind in zip(js, o):
                    res.append(draw(cat, j, kind, n_k[kind]))
                    n_k[kind] += 1
                    if res[-1] is None:
                        break
                if len(res) == 3 and all(r is not None for r in res):
                    ok_ = True
                    break
                snotes.append(f"{cat}: kinds {o} on {[train[cat][j][0]['id'] for j in js]} not all feasible; re-assigned")
            if ok_:
                break
            snotes.append(f"{cat}: no feasible kind assignment on clips {[train[cat][j][0]['id'] for j in js]}; clips re-drawn "
                          "(next subset of the seeded order)")
        if not ok_:
            failed.append(cat)
            continue
        made += [(cat, j, kind, r) for j, kind, r in zip(js, o, res)]
    assert not failed, f"no feasible assignment: {failed}"
    plan = [(c, j, k) for c, j, k, _ in made]
    wrong = []
    for cat, j, kind, (arr, rep, dyn, fz, ev) in made:
        e0, cl0 = train[cat][j]
        q, pos, quat, con = arr
        dq = np.abs(q - np.clip(cl0[0], lo, hi))
        legs = [0, 1, 2, 3, 4, 9, 10, 11, 12, 13]
        err = {"mean_abs_leg_joint_err_rad": round(float(dq[:, legs].mean()), 4), "max_abs_joint_err_rad": round(float(dq.max()), 4),
               "stance_slide_cm": round(100 * fn["slide"](q, pos, quat, con), 2),
               "stance_slide_clean_cm": round(100 * fn["slide"](*cl0), 2),
               "root_dz_mean_mm": round(1000 * float((pos[:, 2] - cl0[1][:, 2]).mean()), 1)}
        e = {"id": f"{e0['id']}__sys_{kind}", "category": cat, "source": e0["source"], "replaces": e0["id"], "split": "train",
             "params": e0["params"], "check": rep, "dynamic": dyn, "length": len(q), "contaminant": kind,
             "generator": "systematic", "family": e0.get("family"), "systematic": True,
             "feasibility": {"infeasible": False, "corrupted": True, "family": "systematic", "kind": kind, "kinematic": rep["pass"],
                             "feasible": fz, "evidence": ev}, "error": err}
        if e["family"] is None:
            e.pop("family")
        wrong.append((json.loads(json.dumps(e, default=float)), row(q, pos, quat, con)))
        print(f"  {cat:14s} {e['id']:58s} {json.dumps(ev, default=str)[:80]} {err}")
    assert collections.Counter(k for _, _, k in plan) == {"joint_offset": 21, "stance_skate": 21}

    # rows: clips_v9x's kept clean train, val and test clips in their order (new indices), then the wrong clips
    gone = {train[c][j][0]["id"] for c, j, _ in plan}
    keep = [c for c in man["clips"] if not c.get("contaminant") and c["id"] not in gone]
    lib = {k_: np.concatenate([base[k_][[c["index"] for c in keep]]] + [w[1][k_][None] for w in wrong]) for k_ in wrong[0][1]}
    lib["length"] = np.concatenate([base["length"][[c["index"] for c in keep]],
                                    np.array([w[0]["length"] for w in wrong], dtype=base["length"].dtype)])
    clips = [dict(c, index=i) for i, c in enumerate(keep)] + [dict(w[0], index=len(keep) + i) for i, w in enumerate(wrong)]
    os.makedirs(a.out, exist_ok=True)
    np.savez_compressed(os.path.join(a.out, "library.npz"), **lib)
    clean = sorted(c["id"] for c in keep if c["split"] == "train")
    manifest = dict(man, version="v9s", edited_from=os.path.basename(os.path.normpath(a.systematic)),
                    split=man["split"] + "; v9s replaces 3 clean train clips per type by systematically wrong versions and "
                                         "drops v9's broken clips (make_v9.py --systematic)",
                    systematic={"seed": SEED_S, "replaced": sorted(gone), "kinds": list(SYSTEMATIC),
                                "offset_joints": {k: [man["joints"][v[0]], man["joints"][v[1]]] for k, v in OFFSET_J.items()}},
                    notes=man["notes"] + [f"v9s: {x}" for x in snotes], clips=clips)
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1, default=float)
    json.dump(clean, open(os.path.join(a.out, "clean_only.json"), "w"), indent=1)
    print(f"{a.out}: {len(clips)} clips: {len(clean)} clean + {len(wrong)} wrong train, val / test from {a.systematic}")


# ----------------------------------------------------------------------------------------------- v9v: signals
TURN_TYPES = ["turn_in_place", "walk_turn"]
SIGNAL_KEYS = ("lin_vel", "ang_vel", "base_pos")  # the only arrays a v9v copy changes


def write_signals(base_dir, out):
    """v9v (PREREG v3 amendment 2026-11-25): the 84 clean train clips of clips_v9x plus one copy of each whose summary
    signals (observed and rewarded: base linear velocity, yaw rate, base height) disagree with its own unchanged joints,
    keypoints and contacts. Gaits: linear velocity x0.5 or x2, alternating; turning types: yaw rate (and linear velocity)
    x0.5 or x2; other types: base height +2 to +4 cm. Constant over the clip. val / test as clips_v9x. Numpy only."""
    blib = np.load(os.path.join(base_dir, "library.npz"))
    bman = json.load(open(os.path.join(base_dir, "manifest.json")))
    bcl = bman["clips"]
    clean = [c for c in bcl if c["split"] == "train" and not c.get("contaminant")]
    keep = clean + [c for c in bcl if c["split"] != "train"]
    rng = np.random.default_rng(SEED + 7)
    arr = {k: [blib[k][c["index"]] for c in keep] for k in blib.files}
    clips, n_type = [dict(c, index=i) for i, c in enumerate(keep)], collections.Counter()
    for c in clean:
        cat, j = c["category"], n_type[c["category"]]
        n_type[cat] += 1
        row = {k: blib[k][c["index"]].copy() for k in blib.files}
        if cat in GAIT_TYPES:
            f = (0.5, 2.0)[j % 2]
            kind, err = ("speed_x2" if f > 1 else "speed_half"), {"lin_vel_scale": f}
            row["lin_vel"][:, :2] *= np.float32(f)
            if cat in TURN_TYPES:
                kind = "turn_x2" if f > 1 else "turn_half"
                row["ang_vel"][:, 2] *= np.float32(f)
                err["yaw_rate_scale"] = f
        else:
            dz = float(np.round(rng.uniform(0.02, 0.04), 4))
            kind, err = "height_up", {"base_height_offset_m": dz}
            row["base_pos"][:, 2] += np.float32(dz)
        cid = f"{c['id']}__sig_{kind}"
        clips.append(dict(c, id=cid, source=cid, derived_from=c["id"], contaminant=kind, generator="signal",
                          index=len(clips), signal_error=err,
                          feasibility=dict(c["feasibility"], corrupted=True, family="signal", kind=kind)))
        for k in blib.files:
            arr[k].append(row[k])
    kinds = dict(collections.Counter(c["contaminant"] for c in clips if c.get("generator") == "signal"))
    man = {k: v for k, v in bman.items() if k not in ("clips", "extended_from")}
    man.update(edited_from=os.path.basename(os.path.normpath(base_dir)), signals=kinds, clips=clips)
    os.makedirs(out, exist_ok=True)
    np.savez_compressed(os.path.join(out, "library.npz"), **{k: np.stack(v) for k, v in arr.items()})
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    json.dump(sorted(c["id"] for c in clean), open(os.path.join(out, "clean_only.json"), "w"), indent=1)
    print(f"wrote {out}: {len(clips)} clips, {len(clean)} clean + {len(clean)} signal copies {kinds}")


def verify_signals(lib_dir, lib, man, cl):
    """v9v: kept clips are their clips_v9x clips (entry except index, every array bit for bit); every copy equals its
    clean clip in every array but SIGNAL_KEYS, and differs there exactly by its recorded error."""
    base_dir = os.path.join(os.path.dirname(os.path.normpath(lib_dir)), man["edited_from"])
    blib = np.load(os.path.join(base_dir, "library.npz"))
    B = {c["id"]: c for c in json.load(open(os.path.join(base_dir, "manifest.json")))["clips"]}
    by_id = {c["id"]: c for c in cl}
    kept = [c for c in cl if c.get("generator") != "signal"]
    for c in kept:
        b = B[c["id"]]
        assert {k: v for k, v in c.items() if k != "index"} == {k: v for k, v in b.items() if k != "index"}, c["id"]
        for k in lib.files:
            assert lib[k][c["index"]].tobytes() == blib[k][b["index"]].tobytes(), (c["id"], k)
    assert {c["id"] for c in kept if c["split"] != "train"} == {i for i, b in B.items() if b["split"] != "train"}
    sig = [c for c in cl if c.get("generator") == "signal"]
    assert len(sig) == sum(1 for c in kept if c["split"] == "train") == 84
    for c in sig:
        e, i, j = c["signal_error"], c["index"], by_id[c["derived_from"]]["index"]
        for k in lib.files:
            if k not in SIGNAL_KEYS:
                assert lib[k][i].tobytes() == lib[k][j].tobytes(), (c["id"], k)
        f, g = e.get("lin_vel_scale", 1.0), e.get("yaw_rate_scale", 1.0)
        assert np.allclose(lib["lin_vel"][i][:, :2], lib["lin_vel"][j][:, :2] * f, atol=1e-6), c["id"]
        assert np.array_equal(lib["lin_vel"][i][:, 2], lib["lin_vel"][j][:, 2]), c["id"]
        assert np.allclose(lib["ang_vel"][i][:, 2], lib["ang_vel"][j][:, 2] * g, atol=1e-6), c["id"]
        assert np.array_equal(lib["ang_vel"][i][:, :2], lib["ang_vel"][j][:, :2]), c["id"]
        assert np.array_equal(lib["base_pos"][i][:, :2], lib["base_pos"][j][:, :2]), c["id"]
        assert np.allclose(lib["base_pos"][i][:, 2] - lib["base_pos"][j][:, 2], e.get("base_height_offset_m", 0.0),
                           atol=1e-6), c["id"]
    print(f"  {man['edited_from']}: {len(kept)} clips identical (entry + {len(lib.files)} arrays); {len(sig)} signal "
          f"copies differ from their clean clip only in {', '.join(SIGNAL_KEYS)}, exactly by their recorded error")


# ----------------------------------------------------------------------------------------------- v9a: aliased
ALIAS_KEYS = ("keypts", "contacts")  # rewarded, never observed: the only arrays a v9a copy changes
KP_SIGMA = (0.5, 0.004, 0.03)  # tracking.py keypoint tolerance: clip(rel * amplitude, floor, cap)
KP_PULL = 0.5 ** 0.5  # target miss in tolerances: exp(-(e / sigma)^2) is steepest at e = sigma / sqrt(2)


def home_keypoints(blib, bman):
    """Body-frame keypoints at the home pose: frame 0 of the head clips (legs and base at home); they must agree."""
    k0 = np.array([blib["keypts"][c["index"], 0] for c in bman["clips"] if c["category"] == "head"])
    assert np.abs(k0 - k0[0]).max() < 1e-4, "head clips do not start at one pose"
    return k0[0]


def kp_sigma(kp, home):
    rel, floor, cap = KP_SIGMA
    return float(np.clip(rel * np.mean(np.linalg.norm(kp - home, axis=-1)), floor, cap))


def write_aliased(base_dir, out):
    """v9a (PREREG v3 amendment 2026-11-26): the 84 clean train clips of clips_v9x plus one copy of each that the policy
    cannot tell from it (joints, velocities, base pose: every observed reference channel bit for bit) but that rewards
    something else: both foot keypoints shifted forward in the body frame by d (a retargeting offset), d set per clip so
    that tracking the clean motion misses the copy's keypoint target by sigma / sqrt(2) under the copy's own tolerance,
    and the foot contact labels swapped left / right. val / test as clips_v9x. Numpy only."""
    blib = np.load(os.path.join(base_dir, "library.npz"))
    bman = json.load(open(os.path.join(base_dir, "manifest.json")))
    bcl, home = bman["clips"], home_keypoints(blib, bman)
    clean = [c for c in bcl if c["split"] == "train" and not c.get("contaminant")]
    keep = clean + [c for c in bcl if c["split"] != "train"]
    arr = {k: [blib[k][c["index"]] for c in keep] for k in blib.files}
    clips = [dict(c, index=i) for i, c in enumerate(keep)]
    feet = [bman["keypoints"].index(n) for n in ("left_foot", "right_foot")]
    for c in clean:
        row = {k: blib[k][c["index"]].copy() for k in blib.files}
        n = c["length"]

        def shifted(d):
            kp = row["keypts"][:n].copy()
            kp[:, feet, 0] += d
            return kp

        lo, hi = 0.0, 0.2  # miss / sigma grows with d: bisect for KP_PULL
        for _ in range(60):
            d = (lo + hi) / 2
            kp = shifted(d)
            miss = np.mean(np.linalg.norm(kp - row["keypts"][:n], axis=-1))
            lo, hi = (d, hi) if miss < KP_PULL * kp_sigma(kp, home) else (lo, d)
        d = float(np.float32(round(d, 5)))
        row["keypts"][:n, feet, 0] += np.float32(d)
        row["contacts"] = row["contacts"][:, ::-1].copy()
        kind = "alias_feet_fwd_contacts_swapped"
        cid = f"{c['id']}__{kind}"
        err = {"feet_kp_forward_m": d, "contacts_swapped": True,
               "kp_sigma_m": kp_sigma(row["keypts"][:n], home), "kp_sigma_clean_m": kp_sigma(blib["keypts"][c["index"], :n], home)}
        clips.append(dict(c, id=cid, source=cid, derived_from=c["id"], contaminant=kind, generator="aliased",
                          index=len(clips), alias_error=err,
                          feasibility=dict(c["feasibility"], corrupted=True, family="aliased", kind=kind)))
        for k in blib.files:
            arr[k].append(row[k])
    kinds = dict(collections.Counter(c["contaminant"] for c in clips if c.get("generator") == "aliased"))
    man = {k: v for k, v in bman.items() if k not in ("clips", "extended_from")}
    man.update(edited_from=os.path.basename(os.path.normpath(base_dir)), aliased=kinds, clips=clips)
    os.makedirs(out, exist_ok=True)
    np.savez_compressed(os.path.join(out, "library.npz"), **{k: np.stack(v) for k, v in arr.items()})
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    json.dump(sorted(c["id"] for c in clean), open(os.path.join(out, "clean_only.json"), "w"), indent=1)
    ds = [c["alias_error"]["feet_kp_forward_m"] for c in clips if c.get("generator") == "aliased"]
    print(f"wrote {out}: {len(clips)} clips, {len(clean)} clean + {len(clean)} aliased copies {kinds}; "
          f"foot shift {1000 * min(ds):.1f} to {1000 * max(ds):.1f} mm (median {1000 * np.median(ds):.1f})")


def verify_aliased(lib_dir, lib, man, cl):
    """v9a: kept clips are their clips_v9x clips (entry except index, every array bit for bit); every copy equals its
    clean clip in every array but ALIAS_KEYS, its feet keypoints are shifted forward by exactly its recorded d (all else
    in keypts unchanged), its contacts are its clean clip's swapped, and the clean motion misses it by sigma / sqrt(2)."""
    base_dir = os.path.join(os.path.dirname(os.path.normpath(lib_dir)), man["edited_from"])
    blib = np.load(os.path.join(base_dir, "library.npz"))
    bman = json.load(open(os.path.join(base_dir, "manifest.json")))
    B, home = {c["id"]: c for c in bman["clips"]}, home_keypoints(blib, bman)
    by_id = {c["id"]: c for c in cl}
    kept = [c for c in cl if c.get("generator") != "aliased"]
    for c in kept:
        b = B[c["id"]]
        assert {k: v for k, v in c.items() if k != "index"} == {k: v for k, v in b.items() if k != "index"}, c["id"]
        for k in lib.files:
            assert lib[k][c["index"]].tobytes() == blib[k][b["index"]].tobytes(), (c["id"], k)
    assert {c["id"] for c in kept if c["split"] != "train"} == {i for i, b in B.items() if b["split"] != "train"}
    al = [c for c in cl if c.get("generator") == "aliased"]
    assert len(al) == sum(1 for c in kept if c["split"] == "train") == 84
    feet = [man["keypoints"].index(n) for n in ("left_foot", "right_foot")]
    other = [i for i in range(len(man["keypoints"])) if i not in feet]
    misses = []
    for c in al:
        e, i, j, n = c["alias_error"], c["index"], by_id[c["derived_from"]]["index"], c["length"]
        for k in lib.files:
            if k not in ALIAS_KEYS:
                assert lib[k][i].tobytes() == lib[k][j].tobytes(), (c["id"], k)
        dk = lib["keypts"][i] - lib["keypts"][j]
        assert np.allclose(dk[:n, feet, 0], e["feet_kp_forward_m"], atol=1e-6), c["id"]
        assert not dk[:n, feet, 1:].any() and not dk[:, other].any() and not dk[n:].any(), c["id"]
        assert np.array_equal(lib["contacts"][i], lib["contacts"][j][:, ::-1]), c["id"]
        miss = np.mean(np.linalg.norm(dk[:n], axis=-1)) / kp_sigma(lib["keypts"][i, :n], home)
        assert abs(miss - KP_PULL) < 0.01, (c["id"], miss)
        misses.append(miss)
    print(f"  {man['edited_from']}: {len(kept)} clips identical (entry + {len(lib.files)} arrays); {len(al)} aliased "
          f"copies differ from their clean clip only in {', '.join(ALIAS_KEYS)} (feet keypoints forward by their recorded "
          f"d, contacts swapped); clean motion misses each copy by {min(misses):.3f} to {max(misses):.3f} tolerances")


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
    if man.get("systematic"):
        return verify_systematic(lib_dir, lib, man, cl)
    if man.get("signals"):
        return verify_signals(lib_dir, lib, man, cl)
    if man.get("aliased"):
        return verify_aliased(lib_dir, lib, man, cl)
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
        if man.get("contamination"):  # v9c: appended clips are broken train copies, k per clean train clip
            return verify_contaminated(lib, man, cl, bcl, xs)
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


def verify_systematic(lib_dir, lib, man, cl):
    """v9s: every clip that is not a wrong version is its clips_v9x clip (entry and arrays bit for bit); val / test are
    exactly clips_v9x's; 3 wrong per type, each replacing a clean train clip of its type (gone from the library), both
    kinds in every type, 21 + 21; every wrong clip passes its feasibility checks; clean_only.json = the clean train."""
    base_dir = os.path.join(os.path.dirname(os.path.normpath(lib_dir)), man["edited_from"])
    blib = np.load(os.path.join(base_dir, "library.npz"))
    bcl = {c["id"]: c for c in json.load(open(os.path.join(base_dir, "manifest.json")))["clips"]}
    assert sorted(blib.files) == sorted(lib.files)
    same = [c for c in cl if not c.get("systematic")]
    for c in same:
        b = bcl[c["id"]]
        assert {k: v for k, v in c.items() if k != "index"} == {k: v for k, v in b.items() if k != "index"}, c["id"]
        assert not c.get("contaminant") and all(lib[k][c["index"]].tobytes() == blib[k][b["index"]].tobytes() for k in lib.files), c["id"]
    for sp in ("val", "test"):
        assert {c["id"] for c in cl if c["split"] == sp} == {i for i, b in bcl.items() if b["split"] == sp}, sp
    wr = [c for c in cl if c.get("systematic")]
    bars = man["bars_from_v7_walking"]
    for c in wr:
        b = bcl[c["replaces"]]
        assert b["split"] == "train" and not b.get("contaminant") and b["category"] == c["category"] and b["source"] == c["source"]
        assert c["replaces"] not in {x["id"] for x in cl} and c["contaminant"] in SYSTEMATIC and c["split"] == "train"
        f = c["feasibility"]["feasible"]
        y = c["dynamic"]
        bar_ok = b["generator"] != "keyframed" or (y["rate_lag_rad"] <= bars["rate_lag_rad"] + 5e-4 and
                                                             y["zmp_min_margin_mm"] >= bars["zmp_min_margin_mm"] - 0.05 and not y["takeoff_fail"])
        held = all(f["hold"][k]["held"] for k, v in f["hold_clean"].items() if v)
        assert c["check"]["pass"] and c["check"]["joint_limit_margin_rad"] > 0 and f["bars"] and held and f["pass"] and bar_ok, c["id"]
        assert not c["feasibility"]["infeasible"], c["id"]
    n = collections.Counter((c["category"], c["contaminant"]) for c in wr)
    for t in man["types"]:
        assert sum(1 for c in wr if c["category"] == t) == 3 and all(n[(t, k)] >= 1 for k in SYSTEMATIC), t
    assert collections.Counter(c["contaminant"] for c in wr) == {k: 21 for k in SYSTEMATIC}
    clean = sorted(c["id"] for c in cl if c["split"] == "train" and not c.get("systematic"))
    assert len(clean) == 42 and json.load(open(os.path.join(lib_dir, "clean_only.json"))) == clean
    h = [row_hash(lib, c["index"]) for c in cl]
    assert len(set(h)) == len(h), "two clips are the same"
    print(f"  {man['edited_from']}: {len(same)} clips identical (manifest + {len(lib.files)} arrays, bit for bit), val / test "
          f"exactly its; {len(wr)} wrong versions (3 per type, both kinds in each, 21 + 21), all feasible; "
          f"clean_only.json = the {len(clean)} clean train clips; no two clips the same")


def verify_contaminated(lib, man, cl, bcl, xs):
    """v9c: every appended clip is a broken train copy of a clean train clip of its type, each clean train clip has
    exactly k copies (v9's included), every impossible copy passes its check, and no two clips are the same."""
    k = man["contamination"]["per_clean_clip"]
    assert len(xs) + sum(1 for c in bcl if c.get("contaminant")) == man["contamination"]["broken"] == 84 * k
    assert all(c["split"] == "train" and c.get("contaminant") and c.get("new_in") == "v9c" and 0 <= c["copy"] < k for c in xs)
    clean = {c["id"] for c in cl if c["split"] == "train" and not c.get("contaminant")}
    br = [c for c in cl if c.get("contaminant")]
    per = collections.Counter(c["derived_from"] for c in br)
    assert set(per) == clean and set(per.values()) == {k}, per
    imp = [c for c in br if c["contaminant"] in IMPOSSIBLE]
    bad = [c["id"] for c in imp if not confirmed(c) or not c["feasibility"]["infeasible"]]
    assert not bad, bad
    assert all(c["feasibility"]["family"] == ("impossible" if c["contaminant"] in IMPOSSIBLE else "corrupted") for c in br)
    h = [row_hash(lib, c["index"]) for c in cl]
    assert len(set(h)) == len(h), "two clips are the same"
    print(f"  {man['extended_from']}: {len(bcl)} clips identical (manifest + {len(lib.files)} arrays, bit for bit); "
          f"{len(xs)} broken copies appended; {k} per clean train clip ({6 * k} per type); {len(imp)} impossible "
          f"({100 * len(imp) / len(br):.1f}%), all pass their checks; no two clips the same")


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


def contam_txt(man, base, br):
    """v9c Contents bullets."""
    k, nb = man["contamination"]["per_clean_clip"], man["contamination"]["broken"]
    nx = sum(1 for c in br if c.get("new_in"))
    return f"""- **Contamination of `data/{base}`:** every {base} clip is copied unchanged (same id, index and arrays, checked
  bit for bit by `--verify`), so the 84 clean train clips, val and test are exactly {base}'s; {nx} broken train copies
  are appended (`"new_in": "v9c"`). With v9's {man['contamination']['v9_broken_kept']} broken clips, every clean train clip has exactly **{k}** broken
  {'copy' if k == 1 else 'copies'} ({6 * k} per type, {nb} in all). A copy's `copy` field is its round (v9's clips are copy 0): copy r is in every
  library with more than r copies per clip, so a smaller dose's library is the first rows of a larger one's:
{chr(10).join(f"  - `data/clips_{dose_name(man, n)}`: {len(man['clips']) - nb + n} clips (the first {len(man['clips']) - nb + n} rows), train {84 + n} = 84 clean + "
              f"{n} broken ({100 * n / (84 + n):.0f}%), {n // 84} per clean train clip" for n in man["contamination"]["doses"])}
- Broken copies are made by the v9 generator (`make_v9.py --contaminate`): copy r of a clean clip tries the impossible
  kinds its type allows in turn (rotated by clip and copy) and keeps the first that passes its check; parameters change
  with clip and copy (shove size and direction, compression, raised foot and lift, amplitude, hop height, noise seed),
  so no two clips are the same (checked by `--verify`). A clip no impossible kind passes is corrupted instead, and each
  round is topped up with corrupted clips, evenly across types, to v9's 16 impossible : 9 corrupted.
"""


V9C_DEPARTURES = """## Departures (v9c)

- **Balance unit.** "Balanced across types" is read as one broken copy per clean train clip per dose round (6 per
  type at 84, 18 at 252), so each clean clip is broken equally often.
- **Head motion kept (v9 generator fix, v9c only).** v9's shove, one_foot_long (IK) and foot_skate seed each frame's
  IK from the previous solved frame, so the head joints stay at frame 0's pose and the head motion is lost (in v9:
  `head__nod_a1__slow__broken_shove`, `head__nod_a1__fast__broken_one_foot_long`, `dance__f1.5_a0.5__broken_foot_skate`;
  the latter two head clips are still for most of the clip). Left as is, two head clips with the same leg edit come out
  identical. v9c keeps each frame's head joints (not in the leg chains, so the leg solution is unchanged); v9's 25
  clips are kept exactly as built.
- **Whole single-support holds (v9c only).** v9's leg-lift hold picks the highest single-support frame, and for its
  stomp copy that is frame 138, so only 1.2 s of the recorded 2.5 s hold fits in the 4 s clip. v9c picks the highest
  frame whose whole hold fits. v9's clip is kept as built.
- **Kind mix per type.** The 16 : 9 mix is met per dose (64.3%), not per type. Gaits allow only shove (backwards,
  7-15 cm) and speed (2-3x), and most walk_fwd / walk_back / turn_in_place / walk_turn copies pass neither, so those
  types are mostly corrupted (walk_back 1 impossible of 18 at 75%); the top-up then makes fewer corrupted clips in the
  other types (up to 15 impossible of 18). Speed was not pushed past 3x, nor shoves past 15 cm.
- **Parameter schedules.** Shoves grow 3 cm per re-draw with 1 cm per copy (v9: 2 cm steps); non-gait shoves alternate
  forward / back; foot_skate alternates the foot and slides 3.5-4.5 cm (v9: left, 4 cm); hop take-off heights step 1 mm
  per slot (2.5-4.2 cm). "No two the same" is checked as exact array equality: a few copies differ only slightly
  (for example two hops 1 mm apart in height).

"""


def dose_name(man, n):
    return f"v9c{round(100 * n / (84 + n))}"


def contam_tables(man, br):
    """v9c: broken clips per type and kind in each dose's library, and the impossible clips' checks."""
    ks = [k for k in IMPOSSIBLE + CORRUPTED if any(c["contaminant"] == k for c in br)]
    out = []
    for nd in man["contamination"]["doses"]:
        bd = [c for c in br if c.get("copy", 0) < nd // 84]
        n = collections.Counter((c["category"], c["contaminant"]) for c in bd)
        imp = [c for c in bd if c["contaminant"] in IMPOSSIBLE]
        rows = [f"| {t} | " + " | ".join(str(n[(t, k)]) for k in ks) + f" | {sum(n[(t, k)] for k in ks if k in IMPOSSIBLE)} | "
                f"{sum(n[(t, k)] for k in ks if k in CORRUPTED)} |" for t in man["types"]]
        tot = collections.Counter(c["contaminant"] for c in bd)
        rows.append("| **all** | " + " | ".join(f"**{tot[k]}**" for k in ks) + f" | **{len(imp)}** | **{len(bd) - len(imp)}** |")
        out.append(f"""
**{dose_name(man, nd)}** ({len(bd)} broken: {len(imp)} impossible = {100 * len(imp) / len(bd):.1f}%, v9's mix is 64.0%; impossible clips
passing their check: **{sum(map(confirmed, imp))} of {len(imp)}**):

| type | {" | ".join(ks)} | impossible | corrupted |
|---|{"---|" * (len(ks) + 2)}
{chr(10).join(rows)}
""")
    return "".join(out) + f"""
An impossible clip's check is read back from its manifest entry by `--verify` (shove / one_foot_long: the hold test
fails, sole IK error ≤ {1000 * SHOVE_IK_MAX:.0f} mm, a raised sole ≥ 8 mm clear; speed: servo lag > {man['bars_from_v7_walking']['rate_lag_rad']} rad; takeoff: the hop
needs more take-off speed than the legs give; joint_limit: targets clipped at a limit). The table below lists every
broken clip of the largest dose; `copy` 0 is the smallest dose's set.
"""


V9S_HANDLING = """## How each type is handled

- **Joint offset** (every type): the same constant offset for the whole clip, on both legs' hip pitch, knee or ankle
  (the first draw cycles them in that order with the sign; re-draws move on, so the final split is in the table
  below), 0.10-0.15 rad. Both legs get the same
  physical direction: the hip pitch axes are mirrored in the model (left -y, right +y), so the right hip pitch gets the
  opposite joint-space sign; knee and ankle axes are not mirrored. The base is raised or lowered per frame so each stance
  sole's lowest corner is where the clean clip has it (mean of the stance feet; frames with no stance foot, a hop's
  flight, take the nearest stance frame's shift). Standing types (crouch, bow, sway, head, dance, headbang, twist) have
  one whole-clip stance phase, so the offset is a constant posture error with the base re-seated; gaits, leg lifts and
  hops get it through every step. The offset also tilts the soles and moves the feet under the base, so some stance
  slip comes with it (the `stance slide` column).
- **Stance skate** (every type): each stance foot slides 3-5 cm over each stance phase of at least 5 frames
  (min-jerk), and glides back while it swings, so no offset builds up between steps (`skate()` generalised to both feet
  and every phase; IK as v9's but seeded from the clean frame, sole error ≤ 10 mm, the largest v9's skates reached,
  and no joint more than 1 rad from the clean clip, which rejects a knee-branch flip; head joints kept). The first
  draw slides forward or back (alternating across clips) along the heading; re-draws try the other of the two, then
  left and right (both feet the same way). On some gait clips no direction is feasible (forward runs a leg into a
  joint limit, the others out of reach); then the kinds are re-assigned or other clips drawn (see the notes). In standing clips both feet
  never lift, so each slides once, slowly, over the whole clip: the feet creep out from under a still base. Hops slide
  in each ground phase between flights.
- **Feasible** = the checks the clean clip passed: `make_library.check_clip` (joint-limit margin > 0, stance soles within
  5 mm, foot gap), the servo-lag / balance / take-off bars for keyframed clips, and the hold test on the clean clip's
  hold frames (the first frame, and hold_test.py's held pose when the clip has one) wherever the clean clip holds. A
  failed draw is re-drawn (offset: next joint / sign, new size; skate: next direction, new size; up to 6 / 8 draws)
  and recorded below. If a clip has no feasible draw of its kind, the type's kinds are re-assigned among its 3 replaced
  clips (same clips, same 2 + 1 split, next order), also recorded.
- **Which clips:** a seeded draw (seed 91) per type among the 3-of-6 choices that leave the fewest clean style twins
  (a seeded order of the choices, fewest twins first; the first is the draw). Gait and stationary sources have two
  clips (two styles), so one twin per type is unavoidable there; leg_lift (2 march pairs + stomp + kick) and the
  keyframed types have none. If no kind assignment is feasible on the drawn clips, the next choice in the order is
  used (recorded). Which 7 types get 2 offsets + 1 skate is seeded too.
"""


def write_doc_systematic(lib_dir, out):
    """v9s doc: contents, how each type is handled, feasibility, error sizes, the wrong clips, notes, clean clips."""
    man = json.load(open(os.path.join(lib_dir, "manifest.json")))
    cl = man["clips"]
    wr = [c for c in cl if c.get("systematic")]
    n = collections.Counter((c["category"], c["split"], c.get("contaminant")) for c in cl)
    rows = [f"| {t} | {n[(t, 'train', None)]} | {n[(t, 'train', 'joint_offset')]} | {n[(t, 'train', 'stance_skate')]} | "
            f"{n[(t, 'val', None)]} | {n[(t, 'test', None)]} |" for t in man["types"]]
    fz = [c["feasibility"]["feasible"] for c in wr]
    held_n = sum(all(f["hold"][k]["held"] for k, v in f["hold_clean"].items() if v) for f in fz)
    clean_fail = sum(1 for f in fz for v in f["hold_clean"].values() if not v)
    def stats(kind):
        e = [c["error"] for c in wr if c["contaminant"] == kind]
        mean = lambda k: np.mean([x[k] for x in e])  # noqa: E731
        return (f"| {kind} | {len(e)} | {mean('mean_abs_leg_joint_err_rad'):.3f} | {mean('max_abs_joint_err_rad'):.3f} | "
                f"{mean('stance_slide_clean_cm'):.2f} | {mean('stance_slide_cm'):.2f} | {mean('root_dz_mean_mm'):+.1f} |")
    def par(c):
        ev = c["feasibility"]["evidence"]
        if c["contaminant"] == "joint_offset":
            return f"{ev['joint']} {ev['offset_rad']:+.3f} rad; base {ev['root_dz_mm'][0]:+.1f} to {ev['root_dz_mm'][1]:+.1f} mm"
        return f"slide {100 * ev['slide_m']:.1f} cm {ev['direction']} over {ev['stance_phases_slid']} stance phases"
    wrow = [f"| `{c['id']}` | {c['category']} | {c['contaminant']} | {par(c)} | {c['error']['mean_abs_leg_joint_err_rad']:.3f} | "
            f"{c['error']['stance_slide_clean_cm']:.2f} → {c['error']['stance_slide_cm']:.2f} | "
            f"{', '.join(f'{k}: ' + ('holds' if v['held'] else v['why']) for k, v in c['feasibility']['feasible']['hold'].items())} |"
            for c in sorted(wr, key=lambda c: (man["types"].index(c["category"]), c["contaminant"], c["id"]))]
    crow = [f"| `{c['id']}` | {c['category']} | {c['split']}{' (' + c['new_in'] + ')' if c.get('new_in') else ''} | {describe(c)} | "
            f"{c['check']['peak_joint_speed_rad_s']:.1f} |"
            for t in man["types"] for c in sorted((c for c in cl if c["category"] == t and not c.get("systematic")),
                                                    key=lambda c: (("train", "val", "test").index(c["split"]), c["id"]))]
    name, base = os.path.basename(os.path.normpath(lib_dir)), man["edited_from"]
    vnotes = [x for x in man["notes"] if x.startswith("v9s: ")]
    doc = f"""# Reference-clip dataset {man['version']}

Built by `curation/clips/make_v9.py --systematic`; this file is written from `data/{name}/manifest.json`
(`python3 curation/clips/make_v9.py --verify data/{name} --doc docs/{os.path.basename(out)}`). The systematic-error
follow-up of PREREG_V3 (amendment of 2026-11-25). No GIFs yet.

## Contents

- **{len(cl)} clips**, 50 Hz, at most 4 s. Train / val / test: **{sum(c['split'] == 'train' for c in cl)} /
  {sum(c['split'] == 'val' for c in cl)} / {sum(c['split'] == 'test' for c in cl)}**.
- **Val and test are exactly `data/{base}`'s** (same ids and entries, arrays bit for bit; checked by `--verify`).
- **Train = {len(cl) - len(wr) - sum(c['split'] != 'train' for c in cl)} clean + {len(wr)} wrong.** In every type, 3 of the 6 clean train clips are **replaced** by a
  systematically wrong version (`"systematic": true`, `contaminant` = the kind, `replaces` = the clean clip, which is
  not in the library; `source` stays the clean clip's). The other 3 are {base}'s clips, bit for bit. None of v9's 25
  broken clips is in the library. Wrong clips are `feasibility.infeasible: false, corrupted: true, family:
  "systematic"`, so tools that count `contaminant` count them.
- `data/{name}/clean_only.json` lists the {len(cl) - len(wr) - sum(c['split'] != 'train' for c in cl)} clean train ids (the format of `results/cv9/dose/clean_only.json`).
- Row order: {base}'s kept clips in their order, then the wrong clips (indices differ from {base}'s; match by id).

| type | train clean | joint_offset | stance_skate | val | test |
|---|---|---|---|---|---|
{chr(10).join(rows)}
| **all** | **{sum(1 for c in cl if c['split'] == 'train' and not c.get('systematic'))}** | **{sum(c['contaminant'] == 'joint_offset' for c in wr)}** | **{sum(c['contaminant'] == 'stance_skate' for c in wr)}** | **{sum(c['split'] == 'val' for c in cl)}** | **{sum(c['split'] == 'test' for c in cl)}** |

{V9S_HANDLING}
## Feasibility

Of {len(wr)} wrong clips: kinematic check (incl. joint-limit margin) **{sum(f['kinematic'] for f in fz)} / {len(wr)}**, keyframed bars
**{sum(f['bars'] for f in fz)} / {len(wr)}** (they apply to keyframed clips only), hold test where the clean clip holds **{held_n} / {len(wr)}**
({sum(len(f['hold']) for f in fz)} hold frames), all three **{sum(f['pass'] for f in fz)} / {len(wr)}**. {sum('not feasible' in x for x in vnotes)} draws were re-drawn and
{sum('re-assigned' in x for x in vnotes)} kind assignments / {sum('clips re-drawn' in x for x in vnotes)} clip choices replaced (listed under Generation notes); {clean_fail} hold frames where the
clean clip itself does not hold were not required.

Parameters kept: joint_offset on {', '.join(f"{k} {v}" for k, v in sorted(collections.Counter(c['feasibility']['evidence']['joint'] for c in wr if c['contaminant'] == 'joint_offset').items()))}
(sign + {sum(c['feasibility']['evidence']['offset_rad'] > 0 for c in wr if c['contaminant'] == 'joint_offset')}, − {sum(c['feasibility']['evidence']['offset_rad'] < 0 for c in wr if c['contaminant'] == 'joint_offset')}); stance_skate {', '.join(f"{k} {v}" for k, v in sorted(collections.Counter(c['feasibility']['evidence']['direction'] for c in wr if c['contaminant'] == 'stance_skate').items()))}.

## Error size

Against the clean clip each replaces (mean over the clips of each kind): leg-joint error = mean |Δq| over the 10 leg
joints and all frames; stance slide = mean over stance phases of a sole's horizontal travel from where the phase began.

| kind | clips | mean leg-joint error (rad) | max joint error (rad) | stance slide, clean (cm) | stance slide, wrong (cm) | base height change (mm) |
|---|---|---|---|---|---|---|
{stats('joint_offset')}
{stats('stance_skate')}

## Wrong clips

| clip | type | kind | parameters | leg-joint error (rad) | stance slide (cm) | hold test (frame: result) |
|---|---|---|---|---|---|---|
{chr(10).join(wrow)}

## Generation notes

{chr(10).join(f"- {x[5:]}" for x in vnotes) or "- none (every first draw was feasible)"}

## Clean clips

| clip | type | split | parameters | peak joint speed (rad/s) |
|---|---|---|---|---|
{chr(10).join(crow)}
"""
    open(out, "w").write(doc)
    print("wrote", out)


def write_doc(lib_dir, out):
    man = json.load(open(os.path.join(lib_dir, "manifest.json")))
    if man.get("systematic"):
        return write_doc_systematic(lib_dir, out)
    cl = man["clips"]
    n = collections.Counter((c["category"], c["split"], bool(c.get("contaminant"))) for c in cl)
    rows = [f"| {t} | {n[(t, 'train', False)]} | {n[(t, 'train', True)]} | {n[(t, 'val', False)]} | {n[(t, 'test', False)]} |"
            for t in man["types"]]
    br = [c for c in cl if c.get("contaminant")]
    kinds = collections.Counter((c["feasibility"]["family"], c["contaminant"]) for c in br)
    cm = man.get("contamination")
    brow = [f"| `{c['id']}` | {c['category']} | {c['feasibility']['family']} | {c['contaminant']} |"
            f"{' ' + str(c.get('copy', 0)) + ' |' if cm else ''} {evidence(c)} |"
            for c in sorted(br, key=lambda c: (c["feasibility"]["family"] != "impossible", c["contaminant"], c["category"],
                                               c.get("copy", 0)))]
    crow = [f"| `{c['id']}` | {c['category']} | {c['split']}{' (' + c['new_in'] + ')' if c.get('new_in') else ''} | {describe(c)} | "
            f"{c['check']['peak_joint_speed_rad_s']:.1f} |"
            for t in man["types"] for c in sorted((c for c in cl if c["category"] == t and not c.get("contaminant")),
                                                    key=lambda c: (("train", "val", "test").index(c["split"]), c["id"]))]
    ntr = sum(c["split"] == "train" for c in cl)
    b = man["bars_from_v7_walking"]
    name, base = os.path.basename(os.path.normpath(lib_dir)), man.get("extended_from")
    xs = [c for c in cl if c.get("new_in") == man["version"]]
    ntest = collections.Counter(c["category"] for c in cl if c["split"] == "test")
    per_test = f"{min(ntest.values())}" if min(ntest.values()) == max(ntest.values()) else "5-12"
    gifs = ("GIFs of every clip, labelled\nwith split and broken kind: [`results/clips_v9/gifs/`](../results/clips_v9/gifs/README.md)."
            if not base else f"GIFs of the clips_v9 clips (the\nnew {'broken' if cm else 'test'} clips have none yet): "
            "[`results/clips_v9/gifs/`](../results/clips_v9/gifs/README.md).")
    ext_txt = "" if not base else contam_txt(man, base, br) if cm else (
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
    title = ", ".join(dose_name(man, n) for n in cm["doses"]) if cm else man["version"]
    doc = f"""# Reference-clip dataset{"s" if cm and len(cm["doses"]) > 1 else ""} {title}

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
  jumps), foot_skate ({"a sole slides 3.5-4.5 cm" if cm else "the left sole slides 4 cm"} while marked in contact).

| family | kind | clips |
|---|---|---|
{chr(10).join(f"| {f} | {k} | {v} |" for (f, k), v in sorted(kinds.items()))}
{contam_tables(man, br) if cm else ""}
| clip | type | family | kind |{" copy |" if cm else ""} evidence |
|---|---|---|---|{"---|" if cm else ""}---|
{chr(10).join(brow)}

{V9C_DEPARTURES if cm else ""}## Generation notes

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
    p.add_argument("--out", nargs="+", help="one directory (one per --broken N with --contaminate)")
    p.add_argument("--verify")
    p.add_argument("--doc")
    p.add_argument("--extend-test", metavar="V9_DIR", help="v9x: keep this library and append the new test sources")
    p.add_argument("--contaminate", metavar="V9X_DIR", help="v9c: keep this library and append broken train copies")
    p.add_argument("--broken", nargs="+", type=int, help="v9c: broken clips per library (multiples of 84)")
    p.add_argument("--jobs", type=int, default=1, help="v9c: worker processes for the impossible candidates")
    p.add_argument("--systematic", metavar="V9X_DIR", help="v9s: keep val / test, replace 3 train clips per type by wrong ones")
    p.add_argument("--signals", metavar="V9X_DIR", help="v9v: clean train + one copy each with inconsistent signals")
    p.add_argument("--aliased", metavar="V9X_DIR", help="v9a: clean train + one copy each the policy cannot tell apart "
                   "that rewards other feet keypoints and contacts")
    a = p.parse_args()
    if a.signals:
        return write_signals(a.signals, *a.out)
    if a.aliased:
        return write_aliased(a.aliased, *a.out)
    if a.out and not a.contaminate:
        (a.out,) = a.out
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
