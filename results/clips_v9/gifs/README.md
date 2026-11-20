# Dataset v9: every clip, labelled

One GIF per motion type ([`docs/DATASET_V9.md`](../../../docs/DATASET_V9.md) has the full clip list and the evidence
for each broken clip). Kinematic replay of the reference (no physics), full body in frame, real time. Tiles are ordered
train, broken train, val, test. The label line gives the split in green (TRAIN), blue (VAL) or yellow (TEST); a red
bar **BROKEN: &lt;kind&gt;** marks a broken train copy.

| type | train clean | train broken | val | test | GIF size |
|---|---|---|---|---|---|
| [walk_fwd](walk_fwd.gif) | 6 | 2 (shove, noise) | 3 | 5 | 7.2 MB |
| [walk_back](walk_back.gif) | 6 | 2 (shove, glitch) | 3 | 5 | 7.1 MB |
| [side_step](side_step.gif) | 6 | 1 (foot_skate) | 3 | 5 | 6.1 MB |
| [turn_in_place](turn_in_place.gif) | 6 | 2 (speed, noise) | 3 | 5 | 7.0 MB |
| [walk_turn](walk_turn.gif) | 6 | 2 (speed, speed) | 3 | 5 | 7.0 MB |
| [leg_lift](leg_lift.gif) | 6 | 2 (one_foot_long, joint_limit) | 3 | 5 | 5.3 MB |
| [crouch](crouch.gif) | 6 | 2 (shove, glitch) | 3 | 5 | 1.9 MB |
| [bow](bow.gif) | 6 | 1 (shove) | 3 | 5 | 3.4 MB |
| [sway](sway.gif) | 6 | 2 (one_foot_long, foot_skate) | 3 | 5 | 4.3 MB |
| [head](head.gif) | 6 | 2 (shove, one_foot_long) | 3 | 5 | 3.1 MB |
| [hop](hop.gif) | 6 | 2 (takeoff, takeoff) | 3 | 5 | 2.3 MB |
| [dance](dance.gif) | 6 | 2 (joint_limit, foot_skate) | 3 | 5 | 5.5 MB |
| [headbang](headbang.gif) | 6 | 2 (joint_limit, glitch) | 3 | 5 | 3.8 MB |
| [twist](twist.gif) | 6 | 1 (noise) | 3 | 5 | 3.1 MB |

Broken kinds: impossible (physics-verified) = shove, joint_limit, takeoff, speed, one_foot_long; corrupted (by
construction) = noise, glitch, foot_skate.

Regenerate (cluster, Open_Duck_Playground venv):

    MUJOCO_GL=osmesa .venv/bin/python ../open-duck-curation/curation/clips/render_clips.py \
        --lib ../open-duck-curation/data/clips_v9 --out ../open-duck-curation/results/clips_v9/gifs \
        --cols 4 --cam-z 0.2 --cam-dist 0.95 --tile 240 208 --step 3 --colors 64 --by-split
