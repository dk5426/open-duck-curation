"""Robot test R4: single-joint step and chirp responses, for comparison with the same commands in sim.

The duck must HANG ON ITS STAND (feet off the ground), battery full, runtime STOPPED. For each chosen joint: hold the
home pose, then steps of +-0.1 and +-0.3 rad around home (1.5 s each), then a 0.5 -> 5 Hz chirp of 0.1 rad amplitude
(10 s), commanded at 50 Hz like the runtime; targets are clipped 0.05 rad inside the model's range. Present positions
are read every step and saved with the commanded targets and timestamps. After each joint the duck returns to home;
Ctrl-C stops, holds home and switches torque off.

  cd ~/open_duck_mini_runtime && /home/duck/.venv/bin/python joint_step_test.py --joints left_knee left_hip_pitch \
      --kp 22 --out ~/step_test.npz

NOT YET RUN ON THE ROBOT (written 2026-11-09). First run: one joint (left_knee), owner watching.
"""

import argparse
import sys
import time

import numpy as np

sys.path.insert(0, "mini_bdx_runtime")
from mini_bdx_runtime.duck_config import DuckConfig  # noqa: E402
from mini_bdx_runtime.rustypot_position_hwi import HWI  # noqa: E402

RANGE = {"left_hip_yaw": (-0.52, 0.52), "left_hip_roll": (-0.44, 0.44), "left_hip_pitch": (-1.22, 0.52),
         "left_knee": (-1.57, 1.57), "left_ankle": (-1.57, 1.57), "right_hip_yaw": (-0.52, 0.52),
         "right_hip_roll": (-0.44, 0.44), "right_hip_pitch": (-0.52, 1.22), "right_knee": (-1.57, 1.57),
         "right_ankle": (-1.57, 1.57), "neck_pitch": (-0.35, 1.13), "head_pitch": (-0.79, 0.79),
         "head_yaw": (-2.79, 2.79), "head_roll": (-0.52, 0.52)}
DT = 0.02


def profile(home):
    """Target offsets from home over time: steps then chirp."""
    seg = []
    for amp in (0.1, -0.1, 0.3, -0.3):
        seg += [0.0] * int(1.0 / DT) + [amp] * int(1.5 / DT)
    seg += [0.0] * int(1.0 / DT)
    t = np.arange(int(10.0 / DT)) * DT
    f = 0.5 + (5.0 - 0.5) * t / 10.0  # linear chirp
    phase = 2 * np.pi * np.cumsum(f) * DT
    seg += list(0.1 * np.sin(phase))
    seg += [0.0] * int(1.0 / DT)
    return np.array(seg)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--joints", nargs="+", required=True)
    p.add_argument("--kp", type=float, default=22)
    p.add_argument("--out", default="step_test.npz")
    a = p.parse_args()
    hwi = HWI(DuckConfig())
    names = [n for n in hwi.joints if "antenna" not in n]
    home = dict(hwi.init_pos)
    hwi.turn_on()
    kps = [a.kp] * 14
    kps[5:9] = [8, 8, 8, 8]
    hwi.set_kps(kps)
    logs = {}
    try:
        for j in a.joints:
            lo, hi = RANGE[j]
            offs = profile(home[j])
            tgt_log, pos_log, t_log = [], [], []
            t0 = time.monotonic()
            for k, o in enumerate(offs):
                tk = t0 + k * DT
                target = float(np.clip(home[j] + o, lo + 0.05, hi - 0.05))
                cmd = dict(home)
                cmd[j] = target
                hwi.set_position_all({n: cmd[n] for n in names})
                pos = hwi.get_present_positions(ignore=["left_antenna", "right_antenna"])
                tgt_log.append(target)
                pos_log.append(np.nan if pos is None else float(pos[names.index(j)]))
                t_log.append(time.monotonic() - t0)
                time.sleep(max(0.0, tk + DT - time.monotonic()))
            logs[j] = (np.array(t_log), np.array(tgt_log), np.array(pos_log))
            hwi.set_position_all({n: home[n] for n in names})
            time.sleep(1.0)
            print(f"{j}: {len(t_log)} steps, late steps {np.sum(np.diff(t_log) > 0.025)}")
    except KeyboardInterrupt:
        print("stopped: holding home")
        hwi.set_position_all({n: home[n] for n in names})
        time.sleep(1.0)
    finally:
        np.savez(a.out, **{f"{j}__{k}": v for j, (t, tg, ps) in logs.items() for k, v in (("t", t), ("target", tg),
                                                                                             ("pos", ps))},
                 kp=a.kp, home=np.array([home[n] for n in names]), names=np.array(names))
        print("wrote", a.out)
        hwi.turn_off()


if __name__ == "__main__":
    main()
