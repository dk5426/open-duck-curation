#!/bin/bash
# Contamination sweep: wait for a running study to finish, smoke-test the sweep path, then one study per contamination
# level (full + curated, seeds 0 1). Stops at the first failure. Log: $OPENDUCK_ROOT/sweep.log
#   OPENDUCK_ROOT=<dir> setsid nohup bash run_sweep.sh <tag to wait for, e.g. st7> [gpu ...] > /dev/null 2>&1 &
set -u
R=$OPENDUCK_ROOT; C=$R/open-duck-curation; PY=$R/Open_Duck_Playground/.venv/bin/python
WAIT=$1; shift; GPUS=${*:-1 2}
LOG=$R/sweep.log
say() { echo "$(date '+%m-%d %H:%M:%S') $*" >> $LOG; }
study() {  # tag lib [extra args]
  local tag=$1 lib=$2; shift 2
  say "start $tag ($lib)"
  OPENDUCK_ROOT=$R $PY $C/curation/study/run_study.py --gpus $GPUS --tag $tag --lib $C/data/$lib \
      --conds full curated --seeds 0 1 "$@" >> $R/$tag.out 2>&1
  if [ -f $C/results/$tag/DONE ]; then say "done $tag"; else say "FAILED $tag (see $R/$tag.out)"; exit 1; fi
}
say "waiting for results/$WAIT/DONE"
while [ ! -f $C/results/$WAIT/DONE ]; do
  [ -f $C/results/$WAIT/FAILED ] && { say "$WAIT FAILED; sweep not started"; exit 1; }
  sleep 300
done
say "$WAIT done"
study cs30smoke clips_v5c30 --seeds 0 --score-steps 2000000 --tau-steps 1000000 --final-steps 1000000
for lv in 30 50 15; do study cs$lv clips_v5c$lv; done
say "SWEEP DONE"
