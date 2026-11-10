#!/bin/bash
# Queue helper: copy a run's last orbax checkpoint to a fixed path, so a later queue line can warm-start from it.
#   latest_ckpt.sh <run_dir> <dest>
set -e
SRC=$(for d in "$1"/*/; do n=${d%/}; echo "${n##*_} $d"; done | sort -n | tail -1 | cut -d' ' -f2)  # by step count
rm -rf "$2"; cp -r "$SRC" "$2"
echo "latest checkpoint $SRC -> $2"
