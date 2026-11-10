#!/bin/bash
# Run training jobs one after another on one GPU, after an existing PID exits (owner's order).
#   queue_runs.sh <gpu> <wait_pid|0> <queue_file>
# queue_file lines (blank lines and # comments ignored):
#   GROUP <name>                      start of a group of dependent jobs
#   <run_name> <num_timesteps> [runner args...]
#   GATE <command...>                 must exit 0, or the rest of its group is skipped
# Each launch goes through launch_train.sh (nvidia-smi, walker_waiting, gpu lock, trap). A refused launch (walker_waiting,
# busy GPU, lock held: rc 2/3/4) retries every 5 min. A failed run or gate skips only the rest of its group.
GPU=$1; WAIT_PID=$2; QUEUE=$3
ROOT=${OPENDUCK_ROOT:-$HOME/OpenDuck}
log() { echo "$(date -Is) $*" | tee -a $ROOT/queue.log; }
log "queue start: gpu=$GPU waiting for pid $WAIT_PID; queue $QUEUE"
while [ "$WAIT_PID" != "0" ] && kill -0 "$WAIT_PID" 2>/dev/null; do sleep 60; done
[ "$WAIT_PID" != "0" ] && log "pid $WAIT_PID exited"
SKIP=""
mapfile -t LINES < <(grep -v '^\s*\(#\|$\)' "$QUEUE")
for LINE in "${LINES[@]}"; do
  read -r RUN STEPS ARGS <<< "$LINE"
  if [ "$RUN" = "GROUP" ]; then SKIP=""; log "group $STEPS $ARGS"; continue; fi
  if [ -n "$SKIP" ]; then log "skip ($SKIP): $LINE"; continue; fi
  if [ "$RUN" = "GATE" ]; then
    log "gate: $STEPS $ARGS"
    (cd $ROOT && eval "$STEPS $ARGS") 2>&1 | tee -a $ROOT/queue.log
    if [ "${PIPESTATUS[0]}" != "0" ]; then SKIP="gate failed"; log "gate FAILED; skipping the rest of this group"; fi
    continue
  fi
  while true; do
    log "launch $RUN $STEPS $ARGS"
    ALLOW_BUSY_GPU=${ALLOW_BUSY_GPU:-0} $ROOT/tools/launch_train.sh "$GPU" "$RUN" "$STEPS" $ARGS < /dev/null
    RC=$?
    case $RC in
      0) log "$RUN finished rc=0"; break ;;
      2|3|4) log "$RUN refused (rc=$RC), retry in 5 min"; sleep 300 ;;
      *) log "$RUN failed rc=$RC; skipping the rest of this group"; SKIP="$RUN failed"; break ;;
    esac
  done
done
log "queue done"
