#!/bin/bash
# Launch one Open Duck Playground training run on one GPU under the shared lock protocol.
#   launch_train.sh <gpu> <run_name> <num_timesteps> [extra runner.py args...]
# Env: ALLOW_BUSY_GPU=1 skips the "no process on the GPU" check (owner allowed GPU 0, which hosts another user's job).
# Refuses if $LOCKS/walker_waiting exists or the GPU lock is held. Removes only its own lock.
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
mkdir "$LOCK" 2>/dev/null || { echo "lock $LOCK held: $(cat $LOCK/info 2>/dev/null)"; exit 4; }

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
uv run playground/open_duck_mini_v2/runner.py --task flat_terrain_backlash --num_timesteps "$STEPS" --output_dir "$OUT" "$@" \
  > "$OUT/train.log" 2>&1 &
CHILD=$!
TAG="openduck $RUN pid $CHILD"
echo "$TAG" > "$LOCK/info"; echo "$TAG" > "$OUT/.lock_tag"
echo "launched $TAG"
wait $CHILD; RC=$?
echo "$(date -Is) exit rc=$RC" >> "$OUT/launch.txt"
exit $RC
