#!/bin/bash
# Contamination sweep: wait for a study to finish, then one study per contaminated library (full + curated, seeds
# 0 1), in the order given. Stops at the first failure. Log: $OPENDUCK_ROOT/sweep.log
#   OPENDUCK_ROOT=<dir> GPUS="1 2" setsid nohup bash run_sweep.sh <tag to wait for> <tag>:<library> ... > /dev/null 2>&1 &
# e.g. run_sweep.sh cs30smoke cs30:clips_v5c30 camb:clips_v5amb cs50:clips_v5c50
set -u
R=$OPENDUCK_ROOT; C=$R/open-duck-curation; PY=$R/Open_Duck_Playground/.venv/bin/python
GPUS=${GPUS:-1 2}
WAIT=$1; shift
LOG=$R/sweep.log
say() { echo "$(date '+%m-%d %H:%M:%S') $*" >> $LOG; }
say "waiting for results/$WAIT/DONE; then: $*"
while [ ! -f $C/results/$WAIT/DONE ]; do
  [ -f $C/results/$WAIT/FAILED ] && { say "$WAIT FAILED; sweep not started"; exit 1; }
  sleep 300
done
say "$WAIT done"
for job in "$@"; do
  tag=${job%%:*}; lib=${job#*:}
  say "start $tag ($lib)"
  OPENDUCK_ROOT=$R $PY $C/curation/study/run_study.py --gpus $GPUS --tag $tag --lib $C/data/$lib \
      --conds full curated --seeds 0 1 >> $R/$tag.out 2>&1
  if [ -f $C/results/$tag/DONE ]; then say "done $tag"; else say "FAILED $tag (see $R/$tag.out)"; exit 1; fi
done
say "SWEEP DONE"
