"""Robot test R3 (read only): record the mechanical range of every joint, moved BY HAND.

Run on the duck with the runtime STOPPED and torque off (`sudo systemctl stop open-duck-runtime` switches torque off).
This script never writes to the servos: it only reads present positions (radians, same offsets as the runtime) at
10 Hz and keeps each joint's minimum and maximum. Move each leg joint gently to both of its stops, then Ctrl-C.

  cd ~/open_duck_mini_runtime && /home/duck/.venv/bin/python joint_range_reader.py --out ~/joint_ranges.json

NOT YET RUN ON THE ROBOT (written 2026-11-09).
"""

import argparse
import json
import sys
import time

sys.path.insert(0, "mini_bdx_runtime")
from mini_bdx_runtime.duck_config import DuckConfig  # noqa: E402
from mini_bdx_runtime.rustypot_position_hwi import HWI  # noqa: E402

MODEL_RANGE = {  # model (MJCF) ranges, rad, for comparison
    "hip_yaw": (-0.52, 0.52), "hip_roll": (-0.44, 0.44), "knee": (-1.57, 1.57), "ankle": (-1.57, 1.57),
    "left_hip_pitch": (-1.22, 0.52), "right_hip_pitch": (-0.52, 1.22),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="joint_ranges.json")
    a = p.parse_args()
    hwi = HWI(DuckConfig())
    names = list(hwi.joints.keys())
    lo, hi = {n: 9.0 for n in names}, {n: -9.0 for n in names}
    print("Reading positions (no writes). Move each joint to its stops by hand; Ctrl-C to finish.")
    try:
        while True:
            pos = hwi.get_present_positions(ignore=["left_antenna", "right_antenna"])
            if pos is not None:
                for n, v in zip([n for n in names if "antenna" not in n], pos):
                    lo[n], hi[n] = min(lo[n], float(v)), max(hi[n], float(v))
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    print(f"\n{'joint':18s} {'min':>8s} {'max':>8s}   model range")
    for n in names:
        if "antenna" in n:
            continue
        key = n if n in MODEL_RANGE else n.split("_", 1)[1]
        mr = MODEL_RANGE.get(key, ("", ""))
        print(f"{n:18s} {lo[n]:+8.3f} {hi[n]:+8.3f}   {mr}")
    json.dump({n: [lo[n], hi[n]] for n in names if "antenna" not in n}, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
