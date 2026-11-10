#!/bin/bash
# S2.2: generate the gait sources with the Placo reference generator, joint-limit-respecting settings
# (walk_com_height 0.220 keeps the knee inside +-1.57 rad; the upstream 0.205 reaches 1.95).
#   gen_gaits.sh <reference_motion_generator dir> <out dir>
# Sources: 24 directions (v4: >= 3 passing per category so each has train, val and test); variants: 2 styles (normal: single support 0.30 s, foot lift 2.5 cm; gentle: 0.40 s, 1.5 cm).
set -e
GEN=$1; OUT=$2; mkdir -p $OUT/presets
BASE=$GEN/open_duck_reference_motion_generator/robots/open_duck_mini_v2/placo_presets/medium.json
DIRS="walk_fwd:0.02:0:0 walk_fwd:0.04:0:0 walk_fwd:0.06:0:0 walk_back:-0.02:0:0 walk_back:-0.03:0:0 walk_back:-0.04:0:0
side_step:0:0.015:0 side_step:0:-0.015:0 side_step:0:0.03:0 side_step:0:-0.03:0 turn_in_place:0:0:0.15
turn_in_place:0:0:-0.15 turn_in_place:0:0:0.30 turn_in_place:0:0:-0.30 walk_turn:0.04:0:0.15 walk_turn:0.04:0:-0.15
walk_turn:0.04:0:0.30 walk_turn:0.04:0:-0.30 walk_fwd:0.03:0:0 walk_fwd:0.05:0:0 walk_turn:0.02:0:0.15
walk_turn:0.02:0:-0.15 walk_turn:0.03:0:0.10 walk_turn:0.03:0:-0.10"
STYLES="normal:0.30:0.025:15 gentle:0.40:0.015:20"
for d in $DIRS; do for s in $STYLES; do
  IFS=: read cat dx dy dth <<< "$d"; IFS=: read sty ss fh sst <<< "$s"
  name="${cat}__dx${dx}_dy${dy}_dth${dth}__${sty}"
  python3 - "$BASE" "$OUT/presets/$name.json" $dx $dy $dth $ss $fh $sst <<'PY'
import json, sys
b = json.load(open(sys.argv[1]))
b.update(dx=float(sys.argv[3]), dy=float(sys.argv[4]), dtheta=float(sys.argv[5]), duration=10, walk_com_height=0.220,
         walk_foot_height=float(sys.argv[7]), single_support_duration=float(sys.argv[6]),
         single_support_timesteps=int(sys.argv[8]))
json.dump(b, open(sys.argv[2], "w"), indent=1)
PY
  echo "$name"
done; done > $OUT/names.txt
# March in place (no translation, no turn): sources = foot lift height, variants = single-support duration
for fh in 0.015 0.025 0.035; do for s in normal:0.30:15 gentle:0.40:20; do
  IFS=: read sty ss sst <<< "$s"
  name="march__lift${fh}__${sty}"
  python3 - "$BASE" "$OUT/presets/$name.json" 0 0 0 $ss $fh $sst <<'PY2'
import json, sys
b = json.load(open(sys.argv[1]))
b.update(dx=0.0, dy=0.0, dtheta=0.0, duration=10, walk_com_height=0.220, walk_foot_height=float(sys.argv[7]),
         single_support_duration=float(sys.argv[6]), single_support_timesteps=int(sys.argv[8]))
json.dump(b, open(sys.argv[2], "w"), indent=1)
PY2
  echo "$name" >> $OUT/names.txt
done; done
cd $GEN
cat $OUT/names.txt | xargs -P 16 -I{} sh -c "timeout 600 .venv/bin/python open_duck_reference_motion_generator/gait_generator.py --duck open_duck_mini_v2 --preset $OUT/presets/{}.json --name {} --output_dir $OUT > $OUT/{}.log 2>&1 || echo 'FAILED {}'"
ls $OUT/*.json | grep -v presets | wc -l
