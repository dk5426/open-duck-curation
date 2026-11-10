"""Recorder in the patched v2_rl_walk_mujoco.py, no robot: a get-up through the real _getup_step writes one npz with
the 92-input observations; walker-style rows split into segments on a pause gap; DUCK_RECORD=0 writes nothing.
  python test_mock_recorder.py
"""

import glob
import os
import sys
import tempfile
import threading

import numpy as np

import test_mock_getup as T

import time as _time

REAL = {"monotonic": _time.monotonic, "sleep": _time.sleep, "strftime": _time.strftime}  # the tests patch these
tmp = tempfile.mkdtemp()
os.environ["DUCK_RECORD_DIR"] = tmp


def wait_writes():
    for th in threading.enumerate():
        if th is not threading.current_thread() and th.daemon:
            th.join(timeout=5)


def main():
    mod = T.load()
    clock = T.Clock  # the pad's sample times use the same clock
    mod.time.sleep = lambda s: None
    mod.time.monotonic = lambda: clock.t
    ok = True

    # 1. a get-up: fallen, button, 40 policy steps, then stop
    T.World.accel, T.World.pos = np.array([9.8, 0, 0]), np.array(T.HOME) + 0.6
    w = T.make(mod)
    T.press(w, 11)
    assert w.getup_active, "get-up did not start"
    for _ in range(40):
        w._getup_step()
        clock.t += 0.02
    w.rec.close()
    wait_writes()
    files = sorted(glob.glob(os.path.join(tmp, "*_getup.npz")))
    d = np.load(files[-1]) if files else None
    case1 = d is not None and d["obs"].shape == (40, 92) and d["action"].shape == (40, 14) and \
        d["targets"].shape == (40, 14) and d["acc_raw"].shape == (40, 3) and str(d["mode"]) == "getup" and \
        "action_scale" in str(d["meta"])
    print(f"1. get-up recorded: {'PASS' if case1 else 'FAIL'}  ({files[-1] if files else 'no file'}: "
          f"{ {k: d[k].shape for k in d.files} if d is not None else ''})")
    ok &= case1

    # 2. walker rows: 30 steps, 1 s pause (idle closes the segment), 20 steps -> two walk files
    for f in glob.glob(os.path.join(tmp, "*")):
        os.remove(f)
    rec = w.rec
    for n in (30, 20):
        for _ in range(n):
            rec.add("walk", obs=np.zeros(101), action=np.zeros(14), targets=np.zeros(14), gyro_raw=np.zeros(3),
                    acc_raw=np.zeros(3), commands=np.zeros(7), took=0.01)
            clock.t += 0.02
        clock.t += 1.0
        rec.idle()
        clock.t += 1.0  # new file name second
        mod.time.strftime = (lambda c=clock.t: (lambda fmt: f"t{int(c)}"))()
    wait_writes()
    lens = sorted(len(np.load(f)["t"]) for f in glob.glob(os.path.join(tmp, "*_walk.npz")))
    case2 = lens == [20, 30]
    print(f"2. pause splits walker segments: {'PASS' if case2 else 'FAIL'}  (segment lengths {lens})")
    ok &= case2

    # 3. DUCK_RECORD=0 -> nothing written
    for f in glob.glob(os.path.join(tmp, "*")):
        os.remove(f)
    os.environ["DUCK_RECORD"] = "0"
    w = T.make(mod)
    T.press(w, 11)
    for _ in range(10):
        w._getup_step()
        clock.t += 0.02
    w.rec.close()
    wait_writes()
    case3 = not os.listdir(tmp)
    print(f"3. DUCK_RECORD=0 writes nothing: {'PASS' if case3 else 'FAIL'}")
    ok &= case3
    os.environ["DUCK_RECORD"] = "1"

    # 4. timing: 100 s of walker-sized rows in a real 50 Hz loop (real clock); worst add() incl. 30 s part flushes,
    #    parts are deleted when the segment closes and the final file has every row
    for f in glob.glob(os.path.join(tmp, "*")):
        os.remove(f)
    mod.time.monotonic, mod.time.sleep, mod.time.strftime = REAL["monotonic"], REAL["sleep"], REAL["strftime"]
    _t = mod.time
    rec = mod.StepRecorder({"x": 1})
    rec.FLUSH_S = 3.0  # part flushes every 3 s instead of 30 s so the test sees several
    worst, n_steps, spin = 0.0, 1500, np.random.default_rng(0)
    periods, prev, slow = [], None, []
    for k in range(n_steps):
        t0 = _t.perf_counter()
        if prev is not None:
            periods.append(t0 - prev)
        prev = t0
        rec.add("walk", obs=spin.normal(size=101), action=spin.normal(size=14), targets=np.zeros(14),
                gyro_raw=np.zeros(3), acc_raw=np.zeros(3), commands=np.zeros(7), took=0.01)
        took = _t.perf_counter() - t0
        worst = max(worst, took)
        slow.append(took) if took > 0.002 else None
        _t.sleep(max(0.0, 0.02 - (_t.perf_counter() - t0)))
    parts_seen = len(rec.parts)
    rec.close()
    wait_writes()
    final = glob.glob(os.path.join(tmp, "*_walk.npz"))
    left = glob.glob(os.path.join(tmp, "*.part*"))
    nrows = len(np.load(final[0])["t"]) if len(final) == 1 else -1
    # the walk loop has 20 ms and the policy step takes ~8 ms on the Pi, so a 10 ms worst case never makes a step late
    case4 = worst < 0.010 and max(periods) < 0.025 and parts_seen >= 5 and not left and nrows == n_steps
    print(f"   add() over 2 ms: {len(slow)} times ({', '.join(f'{1000 * x:.1f}' for x in slow[:12])} ms)")
    print(f"   loop period: median {1000 * np.median(periods):.1f} ms, max {1000 * max(periods):.1f} ms")
    print(f"4. worst add() {1000 * worst:.2f} ms over {n_steps} steps with {parts_seen} part flushes; final file "
          f"{nrows} rows; parts left {len(left)}: {'PASS' if case4 else 'FAIL'}")
    ok &= case4
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
