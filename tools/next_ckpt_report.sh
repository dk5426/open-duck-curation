#!/bin/bash
# Wait until run <run> has written <skip> more ONNX checkpoints (or exited), then evaluate the newest one on CPU with
# a GIF and print the tensorboard eval curve. One-shot: re-run it for the next report.
#   next_ckpt_report.sh <run> <pid> [skip=2]
RUN=$1; PID=$2; SKIP=${3:-2}
ROOT=${OPENDUCK_ROOT:-$HOME/OpenDuck}
D=$ROOT/runs/$RUN
n0=$(ls $D/*.onnx 2>/dev/null | wc -l)
while kill -0 "$PID" 2>/dev/null && [ "$(ls $D/*.onnx | wc -l)" -lt $((n0 + SKIP)) ]; do sleep 60; done
date
kill -0 "$PID" 2>/dev/null && echo "RUN STATUS: running" || { echo "RUN STATUS: exited"; cat $D/launch.txt; }
ONNX=$(ls $D/*.onnx | tail -1)  # names start with a timestamp, so ls order is time order
STEP=$(basename "$ONNX" .onnx | awk -F_ '{print $NF}')
M=$((STEP / 1000000))
cd $ROOT/Open_Duck_Playground
.venv/bin/python -c "
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator as E
e=E('$D'); e.Reload()
for tag in ['eval/episode_reward','eval/avg_episode_length','eval/episode_reward/tracking_lin_vel','eval/episode_reward/tracking_ang_vel','eval/episode_reward/imitation']:
    print(tag, [(round(s.step/1e6), round(s.value,1)) for s in e.Scalars(tag)])
" 2>&1 | grep "^eval"
MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES= $HOME/.local/bin/uv run python \
  ../tools/duck_eval.py -o "$ONNX" --scenes scene_flat_terrain_backlash.xml --seeds 2 \
  --out ../results/${RUN}_${M}M.json --gif ../results/${RUN}_${M}M.gif --title "Our $RUN @ ${M}M steps  [backlash scene]" \
  2>&1 | grep -A12 "^== "
echo "GIF: results/${RUN}_${M}M.gif"
