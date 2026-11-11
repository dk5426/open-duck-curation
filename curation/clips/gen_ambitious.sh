#!/bin/bash
# Ambitious gait sources for the contamination sweep: the same generator and joint-limit-respecting settings as
# gen_gaits.sh, but speeds, step sizes and turn rates beyond the dataset's range, and a quicker step style
# (single support 0.22 s, foot lift 3.5 cm). Kept only if they pass the library's kinematic checks (make_ambitious.py).
#   gen_ambitious.sh <reference_motion_generator dir> <out dir>
set -e
GEN=$1; OUT=$2; mkdir -p $OUT/presets
BASE=$GEN/open_duck_reference_motion_generator/robots/open_duck_mini_v2/placo_presets/medium.json
DIRS="walk_fwd:0.07:0:0 walk_fwd:0.08:0:0 walk_back:-0.06:0:0 walk_back:-0.08:0:0 side_step:0:0.04:0
side_step:0:-0.04:0 side_step:0:0.05:0 side_step:0:-0.05:0 turn_in_place:0:0:0.45 turn_in_place:0:0:-0.45
turn_in_place:0:0:0.6 turn_in_place:0:0:-0.6 walk_turn:0.05:0:0.3 walk_turn:0.05:0:-0.3 walk_turn:0.06:0:0.4
walk_turn:0.06:0:-0.4"
STYLES="normal:0.30:0.025:15 quick:0.22:0.035:11"
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
cd $GEN
cat $OUT/names.txt | xargs -P 8 -I{} sh -c "timeout 600 .venv/bin/python open_duck_reference_motion_generator/gait_generator.py --duck open_duck_mini_v2 --preset $OUT/presets/{}.json --name {} --output_dir $OUT > $OUT/{}.log 2>&1 || echo 'FAILED {}'"
ls $OUT/*.json | grep -v presets | wc -l
