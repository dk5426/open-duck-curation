# Reference-clip dataset v9s

Built by `curation/clips/make_v9.py --systematic`; this file is written from `data/clips_v9s/manifest.json`
(`python3 curation/clips/make_v9.py --verify data/clips_v9s --doc docs/DATASET_V9S.md`). The systematic-error
follow-up of PREREG_V3 (amendment of 2026-11-25). No GIFs yet.

## Contents

- **294 clips**, 50 Hz, at most 4 s. Train / val / test: **84 /
  42 / 168**.
- **Val and test are exactly `data/clips_v9x`'s** (same ids and entries, arrays bit for bit; checked by `--verify`).
- **Train = 42 clean + 42 wrong.** In every type, 3 of the 6 clean train clips are **replaced** by a
  systematically wrong version (`"systematic": true`, `contaminant` = the kind, `replaces` = the clean clip, which is
  not in the library; `source` stays the clean clip's). The other 3 are clips_v9x's clips, bit for bit. None of v9's 25
  broken clips is in the library. Wrong clips are `feasibility.infeasible: false, corrupted: true, family:
  "systematic"`, so tools that count `contaminant` count them.
- `data/clips_v9s/clean_only.json` lists the 42 clean train ids (the format of `results/cv9/dose/clean_only.json`).
- Row order: clips_v9x's kept clips in their order, then the wrong clips (indices differ from clips_v9x's; match by id).

| type | train clean | joint_offset | stance_skate | val | test |
|---|---|---|---|---|---|
| walk_fwd | 3 | 2 | 1 | 3 | 12 |
| walk_back | 3 | 1 | 2 | 3 | 12 |
| side_step | 3 | 2 | 1 | 3 | 12 |
| turn_in_place | 3 | 1 | 2 | 3 | 12 |
| walk_turn | 3 | 1 | 2 | 3 | 12 |
| leg_lift | 3 | 2 | 1 | 3 | 12 |
| crouch | 3 | 2 | 1 | 3 | 12 |
| bow | 3 | 2 | 1 | 3 | 12 |
| sway | 3 | 2 | 1 | 3 | 12 |
| head | 3 | 1 | 2 | 3 | 12 |
| hop | 3 | 1 | 2 | 3 | 12 |
| dance | 3 | 1 | 2 | 3 | 12 |
| headbang | 3 | 1 | 2 | 3 | 12 |
| twist | 3 | 2 | 1 | 3 | 12 |
| **all** | **42** | **21** | **21** | **42** | **168** |

## How each type is handled

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

## Feasibility

Of 42 wrong clips: kinematic check (incl. joint-limit margin) **42 / 42**, keyframed bars
**42 / 42** (they apply to keyframed clips only), hold test where the clean clip holds **42 / 42**
(48 hold frames), all three **42 / 42**. 76 draws were re-drawn and
4 kind assignments / 1 clip choices replaced (listed under Generation notes); 0 hold frames where the
clean clip itself does not hold were not required.

Parameters kept: joint_offset on ankle 6, hip_pitch 13, knee 2
(sign + 15, − 6); stance_skate back 11, forward 10.

## Error size

Against the clean clip each replaces (mean over the clips of each kind): leg-joint error = mean |Δq| over the 10 leg
joints and all frames; stance slide = mean over stance phases of a sole's horizontal travel from where the phase began.

| kind | clips | mean leg-joint error (rad) | max joint error (rad) | stance slide, clean (cm) | stance slide, wrong (cm) | base height change (mm) |
|---|---|---|---|---|---|---|
| joint_offset | 21 | 0.025 | 0.124 | 0.02 | 0.10 | +1.1 |
| stance_skate | 21 | 0.070 | 0.420 | 0.00 | 3.74 | +0.0 |

## Wrong clips

| clip | type | kind | parameters | leg-joint error (rad) | stance slide (cm) | hold test (frame: result) |
|---|---|---|---|---|---|---|
| `walk_fwd__dx0.02_dy0_dth0__gentle__sys_joint_offset` | walk_fwd | joint_offset | hip_pitch -0.138 rad; base +6.2 to +7.7 mm | 0.028 | 0.00 → 0.18 | 0: holds |
| `walk_fwd__dx0.04_dy0_dth0__normal__sys_joint_offset` | walk_fwd | joint_offset | hip_pitch +0.117 rad; base +2.2 to +4.6 mm | 0.023 | 0.00 → 0.11 | 0: holds |
| `walk_fwd__dx0.02_dy0_dth0__normal__sys_stance_skate` | walk_fwd | stance_skate | slide 3.9 cm forward over 10 stance phases | 0.064 | 0.00 → 3.90 | 0: holds |
| `walk_back__dx-0.02_dy0_dth0__normal__sys_joint_offset` | walk_back | joint_offset | hip_pitch -0.119 rad; base +5.7 to +7.0 mm | 0.024 | 0.00 → 0.13 | 0: holds |
| `walk_back__dx-0.02_dy0_dth0__gentle__sys_stance_skate` | walk_back | stance_skate | slide 3.3 cm back over 8 stance phases | 0.055 | 0.00 → 3.30 | 0: holds |
| `walk_back__dx-0.03_dy0_dth0__gentle__sys_stance_skate` | walk_back | stance_skate | slide 3.6 cm back over 8 stance phases | 0.061 | 0.00 → 3.60 | 0: holds |
| `side_step__dx0_dy0.0125_dth0__gentle__sys_joint_offset` | side_step | joint_offset | hip_pitch -0.143 rad; base +6.9 to +7.3 mm | 0.029 | 0.00 → 0.17 | 0: holds |
| `side_step__dx0_dy0.0125_dth0__normal__sys_joint_offset` | side_step | joint_offset | hip_pitch -0.132 rad; base +6.5 to +6.8 mm | 0.026 | 0.00 → 0.15 | 0: holds |
| `side_step__dx0_dy0.015_dth0__gentle__sys_stance_skate` | side_step | stance_skate | slide 4.1 cm back over 8 stance phases | 0.078 | 0.00 → 4.09 | 0: holds |
| `turn_in_place__dx0_dy0_dth0.15__normal__sys_joint_offset` | turn_in_place | joint_offset | hip_pitch -0.136 rad; base +6.3 to +7.7 mm | 0.027 | 0.00 → 0.16 | 0: holds |
| `turn_in_place__dx0_dy0_dth-0.175__gentle__sys_stance_skate` | turn_in_place | stance_skate | slide 3.5 cm back over 8 stance phases | 0.065 | 0.00 → 3.49 | 0: holds |
| `turn_in_place__dx0_dy0_dth0.15__gentle__sys_stance_skate` | turn_in_place | stance_skate | slide 3.2 cm back over 8 stance phases | 0.058 | 0.00 → 3.19 | 0: holds |
| `walk_turn__dx0.03_dy0_dth-0.15__gentle__sys_joint_offset` | walk_turn | joint_offset | hip_pitch -0.121 rad; base +5.1 to +7.8 mm | 0.024 | 0.01 → 0.16 | 0: holds |
| `walk_turn__dx0.02_dy0_dth0.10__gentle__sys_stance_skate` | walk_turn | stance_skate | slide 3.6 cm forward over 8 stance phases | 0.062 | 0.00 → 3.59 | 0: holds |
| `walk_turn__dx0.02_dy0_dth0.10__normal__sys_stance_skate` | walk_turn | stance_skate | slide 3.8 cm forward over 10 stance phases | 0.064 | 0.00 → 3.79 | 0: holds |
| `march__lift0.015__gentle__sys_joint_offset` | leg_lift | joint_offset | hip_pitch +0.134 rad; base +3.4 to +3.6 mm | 0.027 | 0.00 → 0.16 | 0: holds |
| `march__lift0.015__normal__sys_joint_offset` | leg_lift | joint_offset | hip_pitch +0.116 rad; base +3.2 to +3.3 mm | 0.023 | 0.00 → 0.12 | 0: holds |
| `stomp__lift0.015_period1.6_dy0.045__sys_stance_skate` | leg_lift | stance_skate | slide 4.9 cm forward over 4 stance phases | 0.103 | 0.00 → 4.88 | 0: holds |
| `crouch__depth1.00__fast__sys_joint_offset` | crouch | joint_offset | hip_pitch +0.145 rad; base -1.9 to -1.8 mm | 0.029 | 0.07 → 0.19 | 0: holds, 65: holds |
| `crouch__depth1.00__slow__sys_joint_offset` | crouch | joint_offset | ankle +0.112 rad; base -0.9 to -0.9 mm | 0.022 | 0.07 → 0.07 | 0: holds, 93: holds |
| `crouch__depth0.20__slow__sys_stance_skate` | crouch | stance_skate | slide 3.6 cm back over 2 stance phases | 0.065 | 0.01 → 3.60 | 0: holds, 91: holds |
| `bow__pitch25deg__fast__sys_joint_offset` | bow | joint_offset | ankle +0.104 rad; base -1.3 to -1.1 mm | 0.021 | 0.14 → 0.15 | 0: holds, 69: holds |
| `bow__pitch25deg__slow__sys_joint_offset` | bow | joint_offset | hip_pitch +0.106 rad; base -6.9 to -3.0 mm | 0.021 | 0.14 → 0.25 | 0: holds, 99: holds |
| `bow__pitch18deg__slow__sys_stance_skate` | bow | stance_skate | slide 3.1 cm forward over 2 stance phases | 0.067 | 0.07 → 3.10 | 0: holds, 97: holds |
| `sway__amp0.0200m__f1.0__sys_joint_offset` | sway | joint_offset | knee +0.108 rad; base -7.8 to -6.0 mm | 0.022 | 0.00 → 0.09 | 0: holds |
| `sway__amp0.0300m__f1.0__sys_joint_offset` | sway | joint_offset | ankle +0.112 rad; base -0.9 to -0.9 mm | 0.022 | 0.01 → 0.01 | 0: holds |
| `sway__amp0.0300m__f0.5__sys_stance_skate` | sway | stance_skate | slide 4.3 cm back over 2 stance phases | 0.082 | 0.01 → 4.30 | 0: holds |
| `head__nod_a1__slow__sys_joint_offset` | head | joint_offset | hip_pitch +0.140 rad; base -2.0 to -2.0 mm | 0.028 | 0.00 → 0.00 | 0: holds |
| `head__nod_a1__fast__sys_stance_skate` | head | stance_skate | slide 3.5 cm forward over 2 stance phases | 0.068 | 0.00 → 3.50 | 0: holds |
| `head__shake_a1__fast__sys_stance_skate` | head | stance_skate | slide 3.4 cm back over 2 stance phases | 0.060 | 0.00 → 3.40 | 0: holds |
| `hop__h0.006_n2__sys_joint_offset` | hop | joint_offset | ankle +0.144 rad; base +0.3 to +0.3 mm | 0.029 | 0.00 → 0.00 | 0: holds |
| `hop__h0.007_n1__sys_stance_skate` | hop | stance_skate | slide 4.0 cm back over 4 stance phases | 0.073 | 0.00 → 4.00 | 0: holds |
| `hop__h0.009_n2__sys_stance_skate` | hop | stance_skate | slide 3.1 cm forward over 6 stance phases | 0.061 | 0.00 → 3.10 | 0: holds |
| `dance__f1.75_a0.8__sys_joint_offset` | dance | joint_offset | ankle +0.141 rad; base +0.1 to +0.2 mm | 0.028 | 0.00 → 0.00 | 0: holds |
| `dance__f1.25_a0.7__sys_stance_skate` | dance | stance_skate | slide 3.5 cm back over 2 stance phases | 0.063 | 0.00 → 3.50 | 0: holds |
| `dance__f1_a0.6__sys_stance_skate` | dance | stance_skate | slide 4.0 cm forward over 2 stance phases | 0.080 | 0.00 → 4.00 | 0: holds |
| `headbang__f1.5_a0.4__sys_joint_offset` | headbang | joint_offset | hip_pitch +0.112 rad; base -2.4 to -2.3 mm | 0.022 | 0.00 → 0.07 | 0: holds |
| `headbang__f1_a0.25__sys_stance_skate` | headbang | stance_skate | slide 4.5 cm forward over 2 stance phases | 0.091 | 0.00 → 4.50 | 0: holds |
| `headbang__f2_a0.5__sys_stance_skate` | headbang | stance_skate | slide 3.9 cm back over 2 stance phases | 0.071 | 0.00 → 3.90 | 0: holds |
| `twist__f0.75_a0.2__sys_joint_offset` | twist | joint_offset | ankle +0.125 rad; base -0.4 to -0.4 mm | 0.025 | 0.00 → 0.00 | 0: holds |
| `twist__f1.5_a0.15__sys_joint_offset` | twist | joint_offset | knee +0.109 rad; base -7.1 to -7.0 mm | 0.022 | 0.00 → 0.02 | 0: holds |
| `twist__f0.5_a0.15__sys_stance_skate` | twist | stance_skate | slide 3.8 cm forward over 2 stance phases | 0.074 | 0.00 → 3.80 | 0: holds |

## Generation notes

- walk_fwd__dx0.02_dy0_dth0__gentle joint_offset: draw 1 not feasible ({"joint": "hip_pitch", "offset_rad": 0.14, "right_leg_sign": -1, "root_dz_mm": [2.9, 4.4], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_fwd__dx0.02_dy0_dth0__gentle joint_offset: draw 2 not feasible ({"joint": "knee", "offset_rad": 0.118, "right_leg_sign": 1, "root_dz_mm": [-0.7, 1.1], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_fwd__dx0.02_dy0_dth0__gentle joint_offset: draw 3 not feasible ({"joint": "ankle", "offset_rad": 0.124, "right_leg_sign": 1, "root_dz_mm": [4.2, 4.4], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_fwd__dx0.04_dy0_dth0__normal joint_offset: draw 1 not feasible ({"joint": "knee", "offset_rad": 0.136, "right_leg_sign": 1, "root_dz_mm": [-1.1, 2.2], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_fwd__dx0.04_dy0_dth0__normal joint_offset: draw 2 not feasible ({"joint": "ankle", "offset_rad": 0.133, "right_leg_sign": 1, "root_dz_mm": [4.5, 4.7], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_back__dx-0.02_dy0_dth0__normal joint_offset: draw 1 not feasible ({"joint": "ankle", "offset_rad": 0.112, "right_leg_sign": 1, "root_dz_mm": [3.8, 4.0], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_back__dx-0.02_dy0_dth0__normal joint_offset: draw 2 not feasible ({"joint": "hip_pitch", "offset_rad": 0.144, "right_leg_sign": -1, "root_dz_mm": [2.6, 4.3], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_back__dx-0.02_dy0_dth0__normal joint_offset: draw 3 not feasible ({"joint": "knee", "offset_rad": 0.138, "right_leg_sign": 1, "root_dz_mm": [-1.0, 0.6], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_back__dx-0.02_dy0_dth0__normal joint_offset: draw 4 not feasible ({"joint": "ankle", "offset_rad": -0.101, "right_leg_sign": 1, "root_dz_mm": [6.1, 6.3], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_back__dx-0.03_dy0_dth0__gentle stance_skate: draw 1 not feasible ({"slide_m": 0.04, "direction": "forward", "stance_phases_slid": 8, "ik_foot_err_mm": 11.0, "max_joint_change_rad": 0.665, "kinematic": false, "bars": false, "held": true,); re-drawn
- side_step__dx0_dy0.0125_dth0__gentle joint_offset: draw 1 not feasible ({"joint": "knee", "offset_rad": -0.149, "right_leg_sign": 1, "root_dz_mm": [11.5, 13.5], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- side_step__dx0_dy0.0125_dth0__gentle joint_offset: draw 2 not feasible ({"joint": "ankle", "offset_rad": -0.12, "right_leg_sign": 1, "root_dz_mm": [7.2, 7.5], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- turn_in_place__dx0_dy0_dth0.15__normal joint_offset: draw 1 not feasible ({"joint": "ankle", "offset_rad": -0.105, "right_leg_sign": 1, "root_dz_mm": [6.4, 6.6], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- turn_in_place__dx0_dy0_dth0.15__gentle stance_skate: draw 1 not feasible ({"slide_m": 0.043, "direction": "forward", "stance_phases_slid": 8, "ik_foot_err_mm": 8.6, "max_joint_change_rad": 0.648, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 1 not feasible ({"slide_m": 0.036, "direction": "forward", "stance_phases_slid": 10, "ik_foot_err_mm": 1.8, "max_joint_change_rad": 0.456, "kinematic": false, "bars": false, "held": true); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 2 not feasible ({"slide_m": 0.038, "direction": "back", "stance_phases_slid": 10, "ik_foot_err_mm": 14.3, "max_joint_change_rad": 0.698, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 3 not feasible ({"slide_m": 0.045, "direction": "left", "stance_phases_slid": 10, "ik_foot_err_mm": 33.6, "max_joint_change_rad": 0.728, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 4 not feasible ({"slide_m": 0.043, "direction": "right", "stance_phases_slid": 10, "ik_foot_err_mm": 32.8, "max_joint_change_rad": 0.664, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 5 not feasible ({"slide_m": 0.037, "direction": "forward", "stance_phases_slid": 10, "ik_foot_err_mm": 1.9, "max_joint_change_rad": 0.463, "kinematic": false, "bars": false, "held": true); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 6 not feasible ({"slide_m": 0.034, "direction": "back", "stance_phases_slid": 10, "ik_foot_err_mm": 12.0, "max_joint_change_rad": 0.657, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 7 not feasible ({"slide_m": 0.04, "direction": "left", "stance_phases_slid": 10, "ik_foot_err_mm": 29.8, "max_joint_change_rad": 0.65, "kinematic": false, "bars": false, "held": true, "s); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 8 not feasible ({"slide_m": 0.035, "direction": "right", "stance_phases_slid": 10, "ik_foot_err_mm": 26.6, "max_joint_change_rad": 0.616, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn: kinds ['stance_skate', 'joint_offset', 'stance_skate'] on ['walk_turn__dx0.03_dy0_dth-0.15__normal', 'walk_turn__dx0.03_dy0_dth-0.15__gentle', 'walk_turn__dx0.02_dy0_dth0.10__gentle'] not all feasible; re-assigned
- walk_turn__dx0.03_dy0_dth-0.15__normal joint_offset: draw 1 not feasible ({"joint": "hip_pitch", "offset_rad": 0.139, "right_leg_sign": -1, "root_dz_mm": [2.1, 5.3], "kinematic": false, "bars": false, "held": false, "solved": true}); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal joint_offset: draw 2 not feasible ({"joint": "knee", "offset_rad": 0.142, "right_leg_sign": 1, "root_dz_mm": [-1.3, 9.6], "kinematic": false, "bars": false, "held": false, "solved": true}); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal joint_offset: draw 3 not feasible ({"joint": "ankle", "offset_rad": 0.141, "right_leg_sign": 1, "root_dz_mm": [4.8, 4.9], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 1 not feasible ({"slide_m": 0.037, "direction": "forward", "stance_phases_slid": 8, "ik_foot_err_mm": 1.8, "max_joint_change_rad": 0.454, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 2 not feasible ({"slide_m": 0.045, "direction": "back", "stance_phases_slid": 8, "ik_foot_err_mm": 18.0, "max_joint_change_rad": 0.764, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 3 not feasible ({"slide_m": 0.042, "direction": "left", "stance_phases_slid": 8, "ik_foot_err_mm": 32.3, "max_joint_change_rad": 0.687, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 4 not feasible ({"slide_m": 0.049, "direction": "right", "stance_phases_slid": 8, "ik_foot_err_mm": 36.6, "max_joint_change_rad": 0.685, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 5 not feasible ({"slide_m": 0.045, "direction": "forward", "stance_phases_slid": 8, "ik_foot_err_mm": 3.6, "max_joint_change_rad": 0.561, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 6 not feasible ({"slide_m": 0.031, "direction": "back", "stance_phases_slid": 8, "ik_foot_err_mm": 10.1, "max_joint_change_rad": 0.626, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 7 not feasible ({"slide_m": 0.041, "direction": "left", "stance_phases_slid": 8, "ik_foot_err_mm": 31.5, "max_joint_change_rad": 0.687, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 8 not feasible ({"slide_m": 0.034, "direction": "right", "stance_phases_slid": 8, "ik_foot_err_mm": 24.9, "max_joint_change_rad": 0.63, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn: kinds ['joint_offset', 'stance_skate', 'stance_skate'] on ['walk_turn__dx0.03_dy0_dth-0.15__normal', 'walk_turn__dx0.03_dy0_dth-0.15__gentle', 'walk_turn__dx0.02_dy0_dth0.10__gentle'] not all feasible; re-assigned
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 1 not feasible ({"slide_m": 0.044, "direction": "forward", "stance_phases_slid": 10, "ik_foot_err_mm": 2.2, "max_joint_change_rad": 0.534, "kinematic": false, "bars": false, "held": true); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 2 not feasible ({"slide_m": 0.031, "direction": "back", "stance_phases_slid": 10, "ik_foot_err_mm": 10.4, "max_joint_change_rad": 0.65, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 3 not feasible ({"slide_m": 0.045, "direction": "left", "stance_phases_slid": 10, "ik_foot_err_mm": 33.6, "max_joint_change_rad": 0.728, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 4 not feasible ({"slide_m": 0.038, "direction": "right", "stance_phases_slid": 10, "ik_foot_err_mm": 28.9, "max_joint_change_rad": 0.617, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 5 not feasible ({"slide_m": 0.049, "direction": "forward", "stance_phases_slid": 10, "ik_foot_err_mm": 2.5, "max_joint_change_rad": 0.616, "kinematic": false, "bars": false, "held": true); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 6 not feasible ({"slide_m": 0.046, "direction": "back", "stance_phases_slid": 10, "ik_foot_err_mm": 19.1, "max_joint_change_rad": 0.843, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 7 not feasible ({"slide_m": 0.033, "direction": "left", "stance_phases_slid": 10, "ik_foot_err_mm": 24.4, "max_joint_change_rad": 0.65, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__normal stance_skate: draw 8 not feasible ({"slide_m": 0.03, "direction": "right", "stance_phases_slid": 10, "ik_foot_err_mm": 22.8, "max_joint_change_rad": 0.58, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn: kinds ['stance_skate', 'stance_skate', 'joint_offset'] on ['walk_turn__dx0.03_dy0_dth-0.15__normal', 'walk_turn__dx0.03_dy0_dth-0.15__gentle', 'walk_turn__dx0.02_dy0_dth0.10__gentle'] not all feasible; re-assigned
- walk_turn: no feasible kind assignment on clips ['walk_turn__dx0.03_dy0_dth-0.15__normal', 'walk_turn__dx0.03_dy0_dth-0.15__gentle', 'walk_turn__dx0.02_dy0_dth0.10__gentle']; clips re-drawn (next subset of the seeded order)
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 1 not feasible ({"slide_m": 0.032, "direction": "forward", "stance_phases_slid": 8, "ik_foot_err_mm": 1.6, "max_joint_change_rad": 0.434, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 2 not feasible ({"slide_m": 0.031, "direction": "back", "stance_phases_slid": 8, "ik_foot_err_mm": 10.1, "max_joint_change_rad": 0.626, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 3 not feasible ({"slide_m": 0.039, "direction": "left", "stance_phases_slid": 8, "ik_foot_err_mm": 29.9, "max_joint_change_rad": 0.687, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 4 not feasible ({"slide_m": 0.042, "direction": "right", "stance_phases_slid": 8, "ik_foot_err_mm": 31.1, "max_joint_change_rad": 0.662, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 5 not feasible ({"slide_m": 0.033, "direction": "forward", "stance_phases_slid": 8, "ik_foot_err_mm": 1.6, "max_joint_change_rad": 0.435, "kinematic": false, "bars": false, "held": true,); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 6 not feasible ({"slide_m": 0.038, "direction": "back", "stance_phases_slid": 8, "ik_foot_err_mm": 13.9, "max_joint_change_rad": 0.702, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 7 not feasible ({"slide_m": 0.043, "direction": "left", "stance_phases_slid": 8, "ik_foot_err_mm": 33.1, "max_joint_change_rad": 0.687, "kinematic": false, "bars": false, "held": true, "); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle stance_skate: draw 8 not feasible ({"slide_m": 0.046, "direction": "right", "stance_phases_slid": 8, "ik_foot_err_mm": 34.2, "max_joint_change_rad": 0.685, "kinematic": false, "bars": false, "held": true, ); re-drawn
- walk_turn: kinds ['stance_skate', 'joint_offset', 'stance_skate'] on ['walk_turn__dx0.03_dy0_dth-0.15__gentle', 'walk_turn__dx0.02_dy0_dth0.10__normal', 'walk_turn__dx0.02_dy0_dth0.10__gentle'] not all feasible; re-assigned
- walk_turn__dx0.03_dy0_dth-0.15__gentle joint_offset: draw 1 not feasible ({"joint": "hip_pitch", "offset_rad": 0.11, "right_leg_sign": -1, "root_dz_mm": [1.6, 4.2], "kinematic": false, "bars": false, "held": true, "solved": true}); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle joint_offset: draw 2 not feasible ({"joint": "knee", "offset_rad": 0.127, "right_leg_sign": 1, "root_dz_mm": [-1.1, 8.6], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_turn__dx0.03_dy0_dth-0.15__gentle joint_offset: draw 3 not feasible ({"joint": "ankle", "offset_rad": 0.107, "right_leg_sign": 1, "root_dz_mm": [3.6, 3.8], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- walk_turn__dx0.02_dy0_dth0.10__gentle stance_skate: draw 1 not feasible ({"slide_m": 0.031, "direction": "back", "stance_phases_slid": 8, "ik_foot_err_mm": 7.6, "max_joint_change_rad": 0.558, "kinematic": false, "bars": false, "held": true, "s); re-drawn
- march__lift0.015__normal joint_offset: draw 1 not feasible ({"joint": "knee", "offset_rad": 0.124, "right_leg_sign": 1, "root_dz_mm": [-0.7, 0.6], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- march__lift0.015__normal joint_offset: draw 2 not feasible ({"joint": "ankle", "offset_rad": 0.137, "right_leg_sign": 1, "root_dz_mm": [4.6, 4.8], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- march__lift0.015__gentle joint_offset: draw 1 not feasible ({"joint": "ankle", "offset_rad": 0.14, "right_leg_sign": 1, "root_dz_mm": [4.7, 4.9], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- crouch__depth1.00__fast joint_offset: draw 1 not feasible ({"joint": "hip_pitch", "offset_rad": -0.124, "right_leg_sign": -1, "root_dz_mm": [7.3, 7.4], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- crouch__depth1.00__fast joint_offset: draw 2 not feasible ({"joint": "knee", "offset_rad": -0.11, "right_leg_sign": 1, "root_dz_mm": [12.1, 12.9], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- crouch__depth1.00__fast joint_offset: draw 3 not feasible ({"joint": "ankle", "offset_rad": -0.147, "right_leg_sign": 1, "root_dz_mm": [8.8, 8.8], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- crouch__depth1.00__slow joint_offset: draw 1 not feasible ({"joint": "knee", "offset_rad": -0.138, "right_leg_sign": 1, "root_dz_mm": [15.0, 16.0], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- crouch__depth1.00__slow joint_offset: draw 2 not feasible ({"joint": "ankle", "offset_rad": -0.124, "right_leg_sign": 1, "root_dz_mm": [7.5, 7.5], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- crouch__depth1.00__slow joint_offset: draw 3 not feasible ({"joint": "hip_pitch", "offset_rad": -0.118, "right_leg_sign": -1, "root_dz_mm": [7.0, 7.1], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- crouch__depth1.00__slow joint_offset: draw 4 not feasible ({"joint": "knee", "offset_rad": 0.136, "right_leg_sign": 1, "root_dz_mm": [-8.3, -6.5], "kinematic": false, "bars": false, "held": true, "solved": true}); re-drawn
- bow__pitch25deg__fast joint_offset: draw 1 not feasible ({"joint": "ankle", "offset_rad": -0.101, "right_leg_sign": 1, "root_dz_mm": [6.1, 6.1], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- bow__pitch25deg__fast joint_offset: draw 2 not feasible ({"joint": "hip_pitch", "offset_rad": -0.101, "right_leg_sign": -1, "root_dz_mm": [6.7, 10.1], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- bow__pitch25deg__fast joint_offset: draw 3 not feasible ({"joint": "knee", "offset_rad": -0.127, "right_leg_sign": 1, "root_dz_mm": [13.8, 14.3], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- head__nod_a1__slow joint_offset: draw 1 not feasible ({"joint": "hip_pitch", "offset_rad": -0.134, "right_leg_sign": -1, "root_dz_mm": [7.8, 7.8], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- head__nod_a1__slow joint_offset: draw 2 not feasible ({"joint": "knee", "offset_rad": -0.109, "right_leg_sign": 1, "root_dz_mm": [12.0, 12.0], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- head__nod_a1__slow joint_offset: draw 3 not feasible ({"joint": "ankle", "offset_rad": -0.119, "right_leg_sign": 1, "root_dz_mm": [7.2, 7.2], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- hop__h0.006_n2 joint_offset: draw 1 not feasible ({"joint": "knee", "offset_rad": -0.137, "right_leg_sign": 1, "root_dz_mm": [13.7, 15.7], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- hop__h0.006_n2 joint_offset: draw 2 not feasible ({"joint": "ankle", "offset_rad": -0.127, "right_leg_sign": 1, "root_dz_mm": [7.6, 7.6], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- hop__h0.006_n2 joint_offset: draw 3 not feasible ({"joint": "hip_pitch", "offset_rad": -0.142, "right_leg_sign": -1, "root_dz_mm": [8.1, 8.3], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- hop__h0.006_n2 joint_offset: draw 4 not feasible ({"joint": "knee", "offset_rad": 0.119, "right_leg_sign": 1, "root_dz_mm": [-7.8, -6.3], "kinematic": false, "bars": false, "held": true, "solved": true}); re-drawn
- dance__f1.75_a0.8 joint_offset: draw 1 not feasible ({"joint": "ankle", "offset_rad": -0.116, "right_leg_sign": 1, "root_dz_mm": [7.0, 7.0], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- dance__f1.75_a0.8 joint_offset: draw 2 not feasible ({"joint": "hip_pitch", "offset_rad": -0.102, "right_leg_sign": -1, "root_dz_mm": [6.2, 6.2], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn
- dance__f1.75_a0.8 joint_offset: draw 3 not feasible ({"joint": "knee", "offset_rad": -0.131, "right_leg_sign": 1, "root_dz_mm": [14.2, 14.6], "kinematic": true, "bars": true, "held": false, "solved": true}); re-drawn

## Clean clips

| clip | type | split | parameters | peak joint speed (rad/s) |
|---|---|---|---|---|
| `walk_fwd__dx0.0325_dy0_dth0__gentle` | walk_fwd | train | vx +0.040 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.7 |
| `walk_fwd__dx0.0325_dy0_dth0__normal` | walk_fwd | train | vx +0.057 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.3 |
| `walk_fwd__dx0.04_dy0_dth0__gentle` | walk_fwd | train | vx +0.049 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.0 |
| `walk_fwd__dx0.015_dy0_dth0__normal` | walk_fwd | val | vx +0.026 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 8.7 |
| `walk_fwd__dx0.03_dy0_dth0__normal` | walk_fwd | val | vx +0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_fwd__dx0.05_dy0_dth0__gentle` | walk_fwd | val | vx +0.061 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.7 |
| `walk_fwd__dx0.0225_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.028 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 4.9 |
| `walk_fwd__dx0.024_dy0_dth0__normal` | walk_fwd | test (v9x) | vx +0.042 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.3 |
| `walk_fwd__dx0.025_dy0_dth0__normal` | walk_fwd | test | vx +0.044 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.4 |
| `walk_fwd__dx0.0275_dy0_dth0__normal` | walk_fwd | test | vx +0.049 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.7 |
| `walk_fwd__dx0.029_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.036 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 5.9 |
| `walk_fwd__dx0.031_dy0_dth0__normal` | walk_fwd | test (v9x) | vx +0.055 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.1 |
| `walk_fwd__dx0.034_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.042 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 7.7 |
| `walk_fwd__dx0.035_dy0_dth0__gentle` | walk_fwd | test | vx +0.043 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 8.6 |
| `walk_fwd__dx0.0365_dy0_dth0__normal` | walk_fwd | test (v9x) | vx +0.064 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 12.0 |
| `walk_fwd__dx0.039_dy0_dth0__gentle` | walk_fwd | test (v9x) | vx +0.049 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.1 |
| `walk_fwd__dx0.045_dy0_dth0__normal` | walk_fwd | test | vx +0.079 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 13.9 |
| `walk_fwd__dx0.055_dy0_dth0__gentle` | walk_fwd | test | vx +0.068 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.9 |
| `walk_back__dx-0.03_dy0_dth0__normal` | walk_back | train | vx -0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.04_dy0_dth0__gentle` | walk_back | train | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.04_dy0_dth0__normal` | walk_back | train | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.015_dy0_dth0__normal` | walk_back | val | vx -0.026 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 8.7 |
| `walk_back__dx-0.025_dy0_dth0__normal` | walk_back | val | vx -0.044 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.4 |
| `walk_back__dx-0.035_dy0_dth0__gentle` | walk_back | val | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.021_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.026 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 4.8 |
| `walk_back__dx-0.0225_dy0_dth0__normal` | walk_back | test | vx -0.040 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.2 |
| `walk_back__dx-0.024_dy0_dth0__normal` | walk_back | test (v9x) | vx -0.042 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.3 |
| `walk_back__dx-0.026_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.033 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 5.4 |
| `walk_back__dx-0.0275_dy0_dth0__gentle` | walk_back | test | vx -0.034 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 5.6 |
| `walk_back__dx-0.029_dy0_dth0__normal` | walk_back | test (v9x) | vx -0.051 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.9 |
| `walk_back__dx-0.031_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.0325_dy0_dth0__normal` | walk_back | test | vx -0.053 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.034_dy0_dth0__normal` | walk_back | test (v9x) | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (lift 2.5 cm) | 10.0 |
| `walk_back__dx-0.0375_dy0_dth0__gentle` | walk_back | test | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.039_dy0_dth0__gentle` | walk_back | test (v9x) | vx -0.037 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 6.0 |
| `walk_back__dx-0.045_dy0_dth0__normal` | walk_back | test | vx -0.053 m/s, vy -0.007, yaw +0.01 rad/s; normal (lift 2.5 cm) | 9.9 |
| `side_step__dx0_dy0.015_dth0__normal` | side_step | train | vx +0.000 m/s, vy +0.019, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.4 |
| `side_step__dx0_dy0.0175_dth0__gentle` | side_step | train | vx +0.000 m/s, vy +0.012, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `side_step__dx0_dy0.0175_dth0__normal` | side_step | train | vx +0.000 m/s, vy +0.024, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.0 |
| `side_step__dx0_dy-0.015_dth0__normal` | side_step | val | vx +0.000 m/s, vy -0.034, yaw +0.02 rad/s; normal (lift 2.5 cm) | 13.4 |
| `side_step__dx0_dy-0.03_dth0__gentle` | side_step | val | vx -0.001 m/s, vy -0.048, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 14.5 |
| `side_step__dx0_dy0.025_dth0__gentle` | side_step | val | vx -0.001 m/s, vy +0.021, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.5 |
| `side_step__dx0_dy-0.0135_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy -0.027, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `side_step__dx0_dy-0.0155_dth0__normal` | side_step | test (v9x) | vx +0.000 m/s, vy -0.035, yaw +0.02 rad/s; normal (lift 2.5 cm) | 13.6 |
| `side_step__dx0_dy-0.0175_dth0__gentle` | side_step | test | vx -0.002 m/s, vy -0.032, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.4 |
| `side_step__dx0_dy-0.019_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy -0.034, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.3 |
| `side_step__dx0_dy-0.025_dth0__gentle` | side_step | test | vx -0.002 m/s, vy -0.041, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 12.7 |
| `side_step__dx0_dy0.0135_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy +0.007, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 10.9 |
| `side_step__dx0_dy0.0145_dth0__normal` | side_step | test (v9x) | vx +0.000 m/s, vy +0.018, yaw +0.02 rad/s; normal (lift 2.5 cm) | 9.3 |
| `side_step__dx0_dy0.016_dth0__gentle` | side_step | test (v9x) | vx -0.001 m/s, vy +0.010, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 11.5 |
| `side_step__dx0_dy0.019_dth0__normal` | side_step | test (v9x) | vx +0.000 m/s, vy +0.026, yaw +0.02 rad/s; normal (lift 2.5 cm) | 10.5 |
| `side_step__dx0_dy0.0225_dth0__normal` | side_step | test | vx +0.000 m/s, vy +0.033, yaw +0.02 rad/s; normal (lift 2.5 cm) | 14.1 |
| `side_step__dx0_dy0.0275_dth0__gentle` | side_step | test | vx -0.002 m/s, vy +0.024, yaw +0.01 rad/s; gentle (lift 1.5 cm) | 14.4 |
| `side_step__dx0_dy0.02_dth0__normal` | side_step | test | vx +0.000 m/s, vy +0.028, yaw +0.02 rad/s; normal (lift 2.5 cm) | 11.1 |
| `turn_in_place__dx0_dy0_dth-0.15__gentle` | turn_in_place | train | vx +0.003 m/s, vy -0.018, yaw -0.16 rad/s; gentle (lift 1.5 cm) | 8.6 |
| `turn_in_place__dx0_dy0_dth-0.15__normal` | turn_in_place | train | vx +0.002 m/s, vy -0.018, yaw -0.24 rad/s; normal (lift 2.5 cm) | 10.0 |
| `turn_in_place__dx0_dy0_dth-0.175__normal` | turn_in_place | train | vx +0.002 m/s, vy -0.020, yaw -0.28 rad/s; normal (lift 2.5 cm) | 11.8 |
| `turn_in_place__dx0_dy0_dth-0.10__normal` | turn_in_place | val | vx +0.001 m/s, vy -0.014, yaw -0.16 rad/s; normal (lift 2.5 cm) | 9.1 |
| `turn_in_place__dx0_dy0_dth-0.30__normal` | turn_in_place | val | vx +0.004 m/s, vy -0.029, yaw -0.50 rad/s; normal (lift 2.5 cm) | 16.2 |
| `turn_in_place__dx0_dy0_dth0.20__gentle` | turn_in_place | val | vx -0.004 m/s, vy -0.004, yaw +0.25 rad/s; gentle (lift 1.5 cm) | 10.2 |
| `turn_in_place__dx0_dy0_dth-0.125__gentle` | turn_in_place | test (v9x) | vx +0.002 m/s, vy -0.017, yaw -0.14 rad/s; gentle (lift 1.5 cm) | 6.2 |
| `turn_in_place__dx0_dy0_dth-0.14__normal` | turn_in_place | test (v9x) | vx +0.002 m/s, vy -0.017, yaw -0.22 rad/s; normal (lift 2.5 cm) | 9.7 |
| `turn_in_place__dx0_dy0_dth-0.16__normal` | turn_in_place | test (v9x) | vx +0.002 m/s, vy -0.019, yaw -0.26 rad/s; normal (lift 2.5 cm) | 10.6 |
| `turn_in_place__dx0_dy0_dth-0.19__normal` | turn_in_place | test (v9x) | vx +0.003 m/s, vy -0.021, yaw -0.31 rad/s; normal (lift 2.5 cm) | 13.9 |
| `turn_in_place__dx0_dy0_dth-0.20__normal` | turn_in_place | test | vx +0.002 m/s, vy -0.021, yaw -0.33 rad/s; normal (lift 2.5 cm) | 13.9 |
| `turn_in_place__dx0_dy0_dth-0.25__gentle` | turn_in_place | test | vx +0.004 m/s, vy -0.023, yaw -0.28 rad/s; gentle (lift 1.5 cm) | 11.3 |
| `turn_in_place__dx0_dy0_dth0.10__gentle` | turn_in_place | test | vx -0.002 m/s, vy -0.007, yaw +0.13 rad/s; gentle (lift 1.5 cm) | 5.2 |
| `turn_in_place__dx0_dy0_dth0.14__gentle` | turn_in_place | test (v9x) | vx -0.003 m/s, vy -0.006, yaw +0.18 rad/s; gentle (lift 1.5 cm) | 6.3 |
| `turn_in_place__dx0_dy0_dth0.16__gentle` | turn_in_place | test (v9x) | vx -0.005 m/s, vy -0.005, yaw +0.20 rad/s; gentle (lift 1.5 cm) | 8.0 |
| `turn_in_place__dx0_dy0_dth0.175__normal` | turn_in_place | test | vx -0.002 m/s, vy +0.002, yaw +0.32 rad/s; normal (lift 2.5 cm) | 9.6 |
| `turn_in_place__dx0_dy0_dth0.19__gentle` | turn_in_place | test (v9x) | vx -0.004 m/s, vy -0.005, yaw +0.23 rad/s; gentle (lift 1.5 cm) | 9.4 |
| `turn_in_place__dx0_dy0_dth0.25__normal` | turn_in_place | test | vx -0.004 m/s, vy +0.006, yaw +0.45 rad/s; normal (lift 2.5 cm) | 13.5 |
| `walk_turn__dx0.02_dy0_dth-0.15__gentle` | walk_turn | train | vx +0.027 m/s, vy -0.017, yaw -0.16 rad/s; gentle (lift 1.5 cm) | 11.2 |
| `walk_turn__dx0.02_dy0_dth-0.15__normal` | walk_turn | train | vx +0.036 m/s, vy -0.016, yaw -0.24 rad/s; normal (lift 2.5 cm) | 13.4 |
| `walk_turn__dx0.03_dy0_dth-0.15__normal` | walk_turn | train | vx +0.054 m/s, vy -0.015, yaw -0.24 rad/s; normal (lift 2.5 cm) | 18.3 |
| `walk_turn__dx0.02_dy0_dth0.15__gentle` | walk_turn | val | vx +0.021 m/s, vy -0.007, yaw +0.19 rad/s; gentle (lift 1.5 cm) | 11.2 |
| `walk_turn__dx0.03_dy0_dth0.10__normal` | walk_turn | val | vx +0.051 m/s, vy -0.004, yaw +0.19 rad/s; normal (lift 2.5 cm) | 9.9 |
| `walk_turn__dx0.04_dy0_dth-0.15__normal` | walk_turn | val | vx +0.071 m/s, vy -0.015, yaw -0.24 rad/s; normal (lift 2.5 cm) | 18.1 |
| `walk_turn__dx0.0225_dy0_dth0.05__gentle` | walk_turn | test (v9x) | vx +0.027 m/s, vy -0.009, yaw +0.07 rad/s; gentle (lift 1.5 cm) | 5.7 |
| `walk_turn__dx0.025_dy0_dth-0.10__gentle` | walk_turn | test (v9x) | vx +0.032 m/s, vy -0.014, yaw -0.11 rad/s; gentle (lift 1.5 cm) | 10.4 |
| `walk_turn__dx0.025_dy0_dth-0.18__normal` | walk_turn | test | vx +0.046 m/s, vy -0.018, yaw -0.29 rad/s; normal (lift 2.5 cm) | 17.9 |
| `walk_turn__dx0.025_dy0_dth0.12__normal` | walk_turn | test | vx +0.042 m/s, vy -0.003, yaw +0.22 rad/s; normal (lift 2.5 cm) | 9.6 |
| `walk_turn__dx0.0275_dy0_dth-0.06__normal` | walk_turn | test (v9x) | vx +0.049 m/s, vy -0.011, yaw -0.09 rad/s; normal (lift 2.5 cm) | 11.9 |
| `walk_turn__dx0.02_dy0_dth-0.12__normal` | walk_turn | test (v9x) | vx +0.037 m/s, vy -0.015, yaw -0.19 rad/s; normal (lift 2.5 cm) | 14.5 |
| `walk_turn__dx0.02_dy0_dth0.07__normal` | walk_turn | test (v9x) | vx +0.034 m/s, vy -0.004, yaw +0.14 rad/s; normal (lift 2.5 cm) | 8.9 |
| `walk_turn__dx0.035_dy0_dth-0.12__gentle` | walk_turn | test | vx +0.044 m/s, vy -0.014, yaw -0.13 rad/s; gentle (lift 1.5 cm) | 12.4 |
| `walk_turn__dx0.035_dy0_dth0.08__gentle` | walk_turn | test | vx +0.041 m/s, vy -0.009, yaw +0.10 rad/s; gentle (lift 1.5 cm) | 11.1 |
| `walk_turn__dx0.03_dy0_dth-0.13__gentle` | walk_turn | test (v9x) | vx +0.040 m/s, vy -0.015, yaw -0.14 rad/s; gentle (lift 1.5 cm) | 11.5 |
| `walk_turn__dx0.03_dy0_dth0.06__gentle` | walk_turn | test (v9x) | vx +0.035 m/s, vy -0.009, yaw +0.08 rad/s; gentle (lift 1.5 cm) | 10.1 |
| `walk_turn__dx0.03_dy0_dth0.20__normal` | walk_turn | test | vx +0.050 m/s, vy -0.000, yaw +0.36 rad/s; normal (lift 2.5 cm) | 15.4 |
| `kick__r0.03_tau0.4_dy0.045` | leg_lift | train | r 0.03, tau 0.4, dy 0.045 | 4.7 |
| `march__lift0.025__gentle` | leg_lift | train | vx +0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 2.5 cm) | 6.1 |
| `march__lift0.025__normal` | leg_lift | train | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.5 cm) | 8.3 |
| `march__lift0.02__normal` | leg_lift | val | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.0 cm) | 7.1 |
| `stomp__lift0.02_period1.4_dy0.045` | leg_lift | val | lift 0.02, period 1.4, dy 0.045 | 3.5 |
| `tap__reach0.03_period1.2_dy0.045` | leg_lift | val | reach 0.03, period 1.2, dy 0.045 | 3.7 |
| `kick__r0.025_tau0.45_dy0.045` | leg_lift | test (v9x) | r 0.025, tau 0.45, dy 0.045 | 4.7 |
| `kick__r0.035_tau0.4_dy0.045` | leg_lift | test (v9x) | r 0.035, tau 0.4, dy 0.045 | 4.7 |
| `kick__r0.045_tau0.5_dy0.045` | leg_lift | test | r 0.045, tau 0.5, dy 0.045 | 4.7 |
| `march__lift0.016__normal` | leg_lift | test (v9x) | vx -0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 1.6 cm) | 5.9 |
| `march__lift0.0175__gentle` | leg_lift | test | vx -0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 1.8 cm) | 4.7 |
| `march__lift0.0215__gentle` | leg_lift | test (v9x) | vx -0.000 m/s, vy -0.010, yaw +0.01 rad/s; gentle (lift 2.1 cm) | 5.5 |
| `march__lift0.024__normal` | leg_lift | test (v9x) | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 2.4 cm) | 8.1 |
| `march__lift0.03__normal` | leg_lift | test | vx +0.000 m/s, vy -0.007, yaw +0.02 rad/s; normal (lift 3.0 cm) | 9.4 |
| `stomp__lift0.0175_period1.5_dy0.045` | leg_lift | test (v9x) | lift 0.0175, period 1.5, dy 0.045 | 3.5 |
| `stomp__lift0.025_period1.2_dy0.045` | leg_lift | test | lift 0.025, period 1.2, dy 0.045 | 4.7 |
| `tap__reach0.025_period1.4_dy0.045` | leg_lift | test (v9x) | reach 0.025, period 1.4, dy 0.045 | 3.5 |
| `tap__reach0.035_period1.4_dy0.045` | leg_lift | test | reach 0.035, period 1.4, dy 0.045 | 3.5 |
| `crouch__depth0.20__fast` | crouch | train | depth 2.4 mm, down/up 0.8 s | 0.1 |
| `crouch__depth0.50__fast` | crouch | train | depth 6.0 mm, down/up 0.8 s | 0.3 |
| `crouch__depth0.50__slow` | crouch | train | depth 6.0 mm, down/up 1.5 s | 0.1 |
| `crouch__depth0.35__fast` | crouch | val | depth 4.2 mm, down/up 0.8 s | 0.2 |
| `crouch__depth0.65__slow` | crouch | val | depth 7.8 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.85__fast` | crouch | val | depth 10.2 mm, down/up 0.8 s | 0.5 |
| `crouch__depth0.25__fast` | crouch | test (v9x) | depth 3.0 mm, down/up 0.8 s | 0.1 |
| `crouch__depth0.30__slow` | crouch | test | depth 3.6 mm, down/up 1.5 s | 0.1 |
| `crouch__depth0.33__slow` | crouch | test (v9x) | depth 4.0 mm, down/up 1.5 s | 0.1 |
| `crouch__depth0.40__fast` | crouch | test | depth 4.8 mm, down/up 0.8 s | 0.2 |
| `crouch__depth0.42__fast` | crouch | test (v9x) | depth 5.0 mm, down/up 0.8 s | 0.2 |
| `crouch__depth0.58__slow` | crouch | test (v9x) | depth 7.0 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.60__slow` | crouch | test | depth 7.2 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.70__fast` | crouch | test (v9x) | depth 8.4 mm, down/up 0.8 s | 0.4 |
| `crouch__depth0.75__fast` | crouch | test | depth 9.0 mm, down/up 0.8 s | 0.4 |
| `crouch__depth0.80__slow` | crouch | test (v9x) | depth 9.6 mm, down/up 1.5 s | 0.2 |
| `crouch__depth0.90__slow` | crouch | test | depth 10.8 mm, down/up 1.5 s | 0.3 |
| `crouch__depth0.95__fast` | crouch | test (v9x) | depth 11.4 mm, down/up 0.8 s | 0.5 |
| `bow__pitch10deg__fast` | bow | train | pitch 10°, down/up 0.8 s | 0.9 |
| `bow__pitch10deg__slow` | bow | train | pitch 10°, down/up 1.5 s | 0.5 |
| `bow__pitch18deg__fast` | bow | train | pitch 18°, down/up 0.8 s | 1.7 |
| `bow__pitch13deg__fast` | bow | val | pitch 13°, down/up 0.8 s | 1.1 |
| `bow__pitch20deg__slow` | bow | val | pitch 20°, down/up 1.5 s | 1.1 |
| `bow__pitch23deg__fast` | bow | val | pitch 23°, down/up 0.8 s | 2.1 |
| `bow__pitch11deg__fast` | bow | test (v9x) | pitch 11°, down/up 0.8 s | 0.9 |
| `bow__pitch12.5deg__slow` | bow | test (v9x) | pitch 12.5°, down/up 1.5 s | 0.6 |
| `bow__pitch12deg__slow` | bow | test | pitch 12°, down/up 1.5 s | 0.6 |
| `bow__pitch14.5deg__fast` | bow | test (v9x) | pitch 14.5°, down/up 0.8 s | 1.3 |
| `bow__pitch15deg__fast` | bow | test | pitch 15°, down/up 0.8 s | 1.4 |
| `bow__pitch16deg__slow` | bow | test (v9x) | pitch 16°, down/up 1.5 s | 0.8 |
| `bow__pitch17deg__slow` | bow | test | pitch 17°, down/up 1.5 s | 0.9 |
| `bow__pitch19deg__fast` | bow | test (v9x) | pitch 19°, down/up 0.8 s | 1.8 |
| `bow__pitch20.5deg__slow` | bow | test (v9x) | pitch 20.5°, down/up 1.5 s | 1.1 |
| `bow__pitch22deg__fast` | bow | test | pitch 22°, down/up 0.8 s | 2.1 |
| `bow__pitch23.5deg__fast` | bow | test (v9x) | pitch 23.5°, down/up 0.8 s | 2.2 |
| `bow__pitch24deg__slow` | bow | test | pitch 24°, down/up 1.5 s | 1.2 |
| `sway__amp0.0100m__f0.5` | sway | train | ±10.0 mm at 0.5 Hz | 0.3 |
| `sway__amp0.0100m__f1.0` | sway | train | ±10.0 mm at 1.0 Hz | 0.6 |
| `sway__amp0.0200m__f0.5` | sway | train | ±20.0 mm at 0.5 Hz | 0.7 |
| `sway__amp0.0125m__f1.0` | sway | val | ±12.5 mm at 1.0 Hz | 0.7 |
| `sway__amp0.0150m__f0.5` | sway | val | ±15.0 mm at 0.5 Hz | 0.5 |
| `sway__amp0.0250m__f1.0` | sway | val | ±25.0 mm at 1.0 Hz | 1.4 |
| `sway__amp0.0110m__f1.0` | sway | test (v9x) | ±11.0 mm at 1.0 Hz | 0.6 |
| `sway__amp0.0135m__f0.5` | sway | test | ±13.5 mm at 0.5 Hz | 0.4 |
| `sway__amp0.0145m__f0.5` | sway | test (v9x) | ±14.5 mm at 0.5 Hz | 0.5 |
| `sway__amp0.0160m__f1.0` | sway | test (v9x) | ±16.0 mm at 1.0 Hz | 0.9 |
| `sway__amp0.0175m__f1.0` | sway | test | ±17.5 mm at 1.0 Hz | 1.0 |
| `sway__amp0.0190m__f0.5` | sway | test (v9x) | ±19.0 mm at 0.5 Hz | 0.6 |
| `sway__amp0.0215m__f1.0` | sway | test (v9x) | ±21.5 mm at 1.0 Hz | 1.2 |
| `sway__amp0.0225m__f0.5` | sway | test | ±22.5 mm at 0.5 Hz | 0.8 |
| `sway__amp0.0240m__f0.5` | sway | test (v9x) | ±24.0 mm at 0.5 Hz | 0.8 |
| `sway__amp0.0275m__f1.0` | sway | test | ±27.5 mm at 1.0 Hz | 1.6 |
| `sway__amp0.0285m__f1.0` | sway | test (v9x) | ±28.5 mm at 1.0 Hz | 1.6 |
| `sway__amp0.0325m__f0.5` | sway | test | ±32.5 mm at 0.5 Hz | 1.2 |
| `head__shake_a1__slow` | head | train | shake ×1.0 at 0.5 Hz | 2.0 |
| `head__tilt_a1__fast` | head | train | tilt ×1.0 at 1.0 Hz | 1.9 |
| `head__tilt_a1__slow` | head | train | tilt ×1.0 at 0.5 Hz | 1.2 |
| `head__look_around_a1__slow` | head | val | look around ×1.0 at 0.5 Hz | 1.3 |
| `head__nod_a0.7__fast` | head | val | nod ×0.7 at 1.0 Hz | 1.8 |
| `head__shake_a0.7__slow` | head | val | shake ×0.7 at 0.5 Hz | 1.4 |
| `head__look_around_a0.9__fast` | head | test (v9x) | look around ×0.9 at 1.0 Hz | 1.8 |
| `head__look_tilt_a0.8__fast` | head | test (v9x) | look tilt ×0.8 at 1.0 Hz | 1.6 |
| `head__look_tilt_a1__fast` | head | test | look tilt ×1.0 at 1.0 Hz | 2.0 |
| `head__nod_a0.85__slow` | head | test | nod ×0.85 at 0.5 Hz | 1.4 |
| `head__nod_a0.9__fast` | head | test (v9x) | nod ×0.9 at 1.0 Hz | 2.3 |
| `head__nod_tilt_a0.8__slow` | head | test (v9x) | nod tilt ×0.8 at 0.5 Hz | 1.3 |
| `head__nod_tilt_a1__slow` | head | test | nod tilt ×1.0 at 0.5 Hz | 1.6 |
| `head__shake_a0.75__slow` | head | test (v9x) | shake ×0.75 at 0.5 Hz | 1.5 |
| `head__shake_a0.85__fast` | head | test | shake ×0.85 at 1.0 Hz | 2.7 |
| `head__shake_a0.9__slow` | head | test (v9x) | shake ×0.9 at 0.5 Hz | 1.8 |
| `head__tilt_a0.7__fast` | head | test | tilt ×0.7 at 1.0 Hz | 1.3 |
| `head__tilt_a0.9__slow` | head | test (v9x) | tilt ×0.9 at 0.5 Hz | 1.1 |
| `hop__h0.004_n2` | hop | train | h 0.004, n 2 | 5.5 |
| `hop__h0.005_n1` | hop | train | h 0.005, n 1 | 5.5 |
| `hop__h0.008_n1` | hop | train | h 0.008, n 1 | 5.5 |
| `hop__h0.0045_n1` | hop | val | h 0.0045, n 1 | 5.5 |
| `hop__h0.0055_n2` | hop | val | h 0.0055, n 2 | 5.5 |
| `hop__h0.0085_n1` | hop | val | h 0.0085, n 1 | 5.5 |
| `hop__h0.0035_n2` | hop | test | h 0.0035, n 2 | 5.5 |
| `hop__h0.0042_n1` | hop | test (v9x) | h 0.0042, n 1 | 5.5 |
| `hop__h0.0048_n2` | hop | test (v9x) | h 0.0048, n 2 | 5.5 |
| `hop__h0.0052_n2` | hop | test (v9x) | h 0.0052, n 2 | 5.5 |
| `hop__h0.0058_n1` | hop | test (v9x) | h 0.0058, n 1 | 5.5 |
| `hop__h0.0065_n2` | hop | test | h 0.0065, n 2 | 5.5 |
| `hop__h0.0068_n2` | hop | test (v9x) | h 0.0068, n 2 | 5.5 |
| `hop__h0.006_n1` | hop | test | h 0.006, n 1 | 5.5 |
| `hop__h0.0072_n1` | hop | test (v9x) | h 0.0072, n 1 | 5.5 |
| `hop__h0.0075_n1` | hop | test | h 0.0075, n 1 | 5.5 |
| `hop__h0.0082_n2` | hop | test (v9x) | h 0.0082, n 2 | 5.5 |
| `hop__h0.0095_n1` | hop | test | h 0.0095, n 1 | 5.5 |
| `dance__f1.5_a0.5` | dance | train | f 1.5, a 0.5 | 1.2 |
| `dance__f2.5_a0.5` | dance | train | f 2.5, a 0.5 | 1.9 |
| `dance__f2_a0.6` | dance | train | f 2, a 0.6 | 1.9 |
| `dance__f1.25_a0.6` | dance | val | f 1.25, a 0.6 | 1.2 |
| `dance__f1.5_a0.7` | dance | val | f 1.5, a 0.7 | 1.6 |
| `dance__f2.25_a0.5` | dance | val | f 2.25, a 0.5 | 1.7 |
| `dance__f1.1_a0.55` | dance | test (v9x) | f 1.1, a 0.55 | 0.9 |
| `dance__f1.25_a0.55` | dance | test | f 1.25, a 0.55 | 1.1 |
| `dance__f1.3_a0.75` | dance | test (v9x) | f 1.3, a 0.75 | 1.5 |
| `dance__f1.4_a0.65` | dance | test (v9x) | f 1.4, a 0.65 | 1.4 |
| `dance__f1.6_a0.55` | dance | test (v9x) | f 1.6, a 0.55 | 1.4 |
| `dance__f1.75_a0.5` | dance | test | f 1.75, a 0.5 | 1.4 |
| `dance__f1.9_a0.7` | dance | test (v9x) | f 1.9, a 0.7 | 2.1 |
| `dance__f1_a0.75` | dance | test | f 1, a 0.75 | 1.2 |
| `dance__f2.1_a0.55` | dance | test (v9x) | f 2.1, a 0.55 | 1.8 |
| `dance__f2.25_a0.65` | dance | test | f 2.25, a 0.65 | 2.3 |
| `dance__f2.4_a0.6` | dance | test (v9x) | f 2.4, a 0.6 | 2.2 |
| `dance__f2_a0.45` | dance | test | f 2, a 0.45 | 1.4 |
| `headbang__f1_a0.5` | headbang | train | f 1, a 0.5 | 3.1 |
| `headbang__f2_a0.25` | headbang | train | f 2, a 0.25 | 3.1 |
| `headbang__f3_a0.25` | headbang | train | f 3, a 0.25 | 4.6 |
| `headbang__f1.5_a0.25` | headbang | val | f 1.5, a 0.25 | 2.3 |
| `headbang__f1_a0.35` | headbang | val | f 1, a 0.35 | 2.2 |
| `headbang__f2.5_a0.3` | headbang | val | f 2.5, a 0.3 | 4.6 |
| `headbang__f1.25_a0.3` | headbang | test (v9x) | f 1.25, a 0.3 | 2.3 |
| `headbang__f1.25_a0.45` | headbang | test (v9x) | f 1.25, a 0.45 | 3.5 |
| `headbang__f1.5_a0.35` | headbang | test | f 1.5, a 0.35 | 3.3 |
| `headbang__f1.75_a0.3` | headbang | test (v9x) | f 1.75, a 0.3 | 3.3 |
| `headbang__f1.75_a0.4` | headbang | test (v9x) | f 1.75, a 0.4 | 4.4 |
| `headbang__f1_a0.4` | headbang | test | f 1, a 0.4 | 2.5 |
| `headbang__f2.25_a0.25` | headbang | test (v9x) | f 2.25, a 0.25 | 3.5 |
| `headbang__f2.25_a0.4` | headbang | test (v9x) | f 2.25, a 0.4 | 5.6 |
| `headbang__f2.5_a0.2` | headbang | test | f 2.5, a 0.2 | 3.1 |
| `headbang__f2.75_a0.25` | headbang | test (v9x) | f 2.75, a 0.25 | 4.2 |
| `headbang__f2_a0.35` | headbang | test | f 2, a 0.35 | 4.4 |
| `headbang__f3_a0.2` | headbang | test | f 3, a 0.2 | 3.7 |
| `twist__f0.5_a0.3` | twist | train | f 0.5, a 0.3 | 1.2 |
| `twist__f1.5_a0.3` | twist | train | f 1.5, a 0.3 | 2.8 |
| `twist__f1_a0.25` | twist | train | f 1, a 0.25 | 1.6 |
| `twist__f0.6_a0.25` | twist | val | f 0.6, a 0.25 | 1.1 |
| `twist__f1.25_a0.25` | twist | val | f 1.25, a 0.25 | 2.0 |
| `twist__f1_a0.2` | twist | val | f 1, a 0.2 | 1.3 |
| `twist__f0.5_a0.2` | twist | test | f 0.5, a 0.2 | 0.8 |
| `twist__f0.6_a0.2` | twist | test (v9x) | f 0.6, a 0.2 | 0.9 |
| `twist__f0.75_a0.25` | twist | test | f 0.75, a 0.25 | 1.2 |
| `twist__f0.7_a0.175` | twist | test (v9x) | f 0.7, a 0.175 | 0.8 |
| `twist__f0.8_a0.3` | twist | test (v9x) | f 0.8, a 0.3 | 1.5 |
| `twist__f0.9_a0.15` | twist | test (v9x) | f 0.9, a 0.15 | 0.8 |
| `twist__f1.1_a0.25` | twist | test (v9x) | f 1.1, a 0.25 | 1.7 |
| `twist__f1.25_a0.15` | twist | test | f 1.25, a 0.15 | 1.2 |
| `twist__f1.2_a0.2` | twist | test (v9x) | f 1.2, a 0.2 | 1.5 |
| `twist__f1.4_a0.25` | twist | test (v9x) | f 1.4, a 0.25 | 2.2 |
| `twist__f1.5_a0.2` | twist | test | f 1.5, a 0.2 | 1.9 |
| `twist__f1_a0.3` | twist | test | f 1, a 0.3 | 1.9 |
