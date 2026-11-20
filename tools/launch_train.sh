#!/bin/bash
# Launch one Open Duck Playground training run on one GPU under the shared lock protocol.
#   launch_train.sh <gpu> <run_name> <num_timesteps> [extra runner.py args...]
# Env: ALLOW_BUSY_GPU=1 skips the "no process on the GPU" check (owner allowed GPU 0, which hosts another user's job).
#      TRAIN_ENTRY=<script> trains with another entry point taking the same arguments (Phase 2: train_alt.py).
# Refuses if $LOCKS/walker_waiting exists, the GPU lock is held, or the run is already live in its folder (rc 4).
# A lock whose holder process is gone is reclaimed. Removes only its own lock.
set -u
GPU=$1; RUN=$2; STEPS=$3; shift 3
ROOT=${OPENDUCK_ROOT:-$HOME/OpenDuck}
LOCKS=${OPENDUCK_LOCKS:-/var/tmp/$USER/gpu_locks}
LOCK=$LOCKS/gpu$GPU
OUT=$ROOT/runs/$RUN
export PATH=$HOME/.local/bin:$PATH

if [ -e "$LOCKS/walker_waiting" ]; then echo "walker_waiting present; not launching"; exit 2; fi
BUSY=$(nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader | wc -l)
nvidia-smi -i "$GPU" --query-compute-apps=pid,used_memory --format=csv,noheader
if [ "$BUSY" != "0" ] && [ "${ALLOW_BUSY_GPU:-0}" != "1" ]; then echo "GPU $GPU has $BUSY process(es); not launching"; exit 3; fi
# alive <tag>: the tag's pid is running and its command line names the tag's run (guards against pid reuse)
alive() { set -- $1; [ -n "${4:-}" ] && ps -p "$4" -o args= 2>/dev/null | grep -q -- "$2"; }
if [ -f "$OUT/.lock_tag" ] && alive "$(cat $OUT/.lock_tag)"; then
  echo "$RUN is already running ($(cat $OUT/.lock_tag)); not launching a duplicate"; exit 4
fi
if ! mkdir "$LOCK" 2>/dev/null; then
  INFO=$(cat $LOCK/info 2>/dev/null)
  if [ -n "$INFO" ] && ! alive "$INFO"; then
    echo "reclaiming stale lock $LOCK ($INFO: process gone)"; rm -rf "$LOCK"
  fi
  mkdir "$LOCK" 2>/dev/null || { echo "lock $LOCK held: $(cat $LOCK/info 2>/dev/null)"; exit 4; }
fi

TAG="openduck $RUN pid $$"
echo "$TAG" > "$LOCK/info"
cleanup() { [ "$(cat $LOCK/info 2>/dev/null)" = "$(cat $OUT/.lock_tag 2>/dev/null)" ] && rm -rf "$LOCK"; }
trap cleanup EXIT
trap 'kill $CHILD 2>/dev/null; exit 130' INT TERM

mkdir -p "$OUT"
cd $ROOT/Open_Duck_Playground
export CUDA_VISIBLE_DEVICES=$GPU XLA_PYTHON_CLIENT_PREALLOCATE=false XLA_PYTHON_CLIENT_MEM_FRACTION=${MEM_FRACTION:-0.75}
git rev-parse HEAD > "$OUT/git_head.txt"; git diff > "$OUT/git_diff.patch"
cp playground/open_duck_mini_v2/data/polynomial_coefficients.pkl "$OUT/"
echo "$(date -Is) start gpu=$GPU steps=$STEPS args=$*" >> "$OUT/launch.txt"
uv run "${TRAIN_ENTRY:-playground/open_duck_mini_v2/runner.py}" --task flat_terrain_backlash --num_timesteps "$STEPS" --output_dir "$OUT" "$@" \
  > "$OUT/train.log" 2>&1 &
CHILD=$!
TAG="openduck $RUN pid $CHILD"
echo "$TAG" > "$LOCK/info"; echo "$TAG" > "$OUT/.lock_tag"
echo "launched $TAG"
wait $CHILD; RC=$?
echo "$(date -Is) exit rc=$RC" >> "$OUT/launch.txt"
exit $RC
