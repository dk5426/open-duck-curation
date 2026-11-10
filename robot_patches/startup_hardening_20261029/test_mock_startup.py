"""Mock test of HWI.turn_on(): a fake STS3215 bus with injected faults, run against the original and the patched
rustypot_position_hwi.py. No hardware, no robot. Run with any Python that has numpy:

  python test_mock_startup.py

Fake bus model: a servo whose torque is off does not move; a servo moves to its goal only if its kp is >= 5 (the start-up kp 2
is too soft to lift the leg; the head runs at 8); a 'stuck' servo stops 0.3 rad short of its goal; a 'flaky' servo fails its first N
writes; a 'dead' servo fails every write.
"""

import importlib.util
import io
import os
import sys
import time
import types
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))


class FakeBus:
    def __init__(self, faults):
        self.faults = faults
        self.torque, self.kp, self.goal, self.pos, self.writes = {}, {}, {}, {}, {}
        for sid in [20, 21, 22, 23, 24, 30, 31, 32, 33, 10, 11, 12, 13, 14]:
            self.torque[sid] = faults.get("torque_off_at_start", False) is False
            self.kp[sid], self.goal[sid], self.pos[sid], self.writes[sid] = 0, 0.0, 0.0, 0

    def _write(self, sid):
        self.writes[sid] += 1
        if sid in self.faults.get("dead", ()):
            raise IOError(f"timeout servo {sid}")
        if self.writes[sid] <= self.faults.get("flaky", {}).get(sid, 0):
            raise IOError(f"crc error servo {sid}")

    def _settle(self):
        for sid in self.pos:
            if self.torque[sid] and self.kp[sid] >= 5:
                short = 0.3 if sid in self.faults.get("stuck", ()) else 0.0
                self.pos[sid] = self.goal[sid] - short

    # new rustypot API used by FeetechSTS3215Adapter
    def sync_write_p_coefficient(self, ids, values):
        for sid, v in zip(ids, values):
            self._write(sid)
            self.kp[sid] = v
        self._settle()

    def sync_write_d_coefficient(self, ids, values):
        for sid in ids:
            self._write(sid)

    def sync_write_goal_position(self, ids, values):
        for sid, v in zip(ids, values):
            self._write(sid)
            self.goal[sid] = v
        self._settle()

    def write_goal_position(self, sid, value):
        self.sync_write_goal_position([sid], [value])

    def sync_write_torque_enable(self, ids, values):
        for sid, v in zip(ids, values):
            self._write(sid)
            self.torque[sid] = bool(v)
        self._settle()

    def sync_read_present_position(self, ids):
        for sid in ids:
            if sid in self.faults.get("dead", ()):
                raise IOError(f"timeout servo {sid}")
        return [self.pos[sid] for sid in ids]


def load_hwi(path, bus):
    rustypot = types.ModuleType("rustypot")
    rustypot.Sts3215PyController = lambda *a, **k: bus
    sys.modules["rustypot"] = rustypot
    pkg = types.ModuleType("mini_bdx_runtime")
    pkg.__path__ = []
    dc = types.ModuleType("mini_bdx_runtime.duck_config")
    dc.DuckConfig = object
    sys.modules["mini_bdx_runtime"], sys.modules["mini_bdx_runtime.duck_config"] = pkg, dc
    spec = importlib.util.spec_from_file_location("hwi_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Cfg:
    joints_offset = {n: 0.0 for n in ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
                                      "neck_pitch", "head_pitch", "head_yaw", "head_roll", "right_hip_yaw",
                                      "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]}


def run(variant, faults):
    bus = FakeBus(faults)
    mod = load_hwi(os.path.join(HERE, variant, "mini_bdx_runtime/mini_bdx_runtime/rustypot_position_hwi.py"), bus)
    mod.time.sleep = lambda s: None  # fast
    hwi = mod.HWI(Cfg(), "/dev/fake")
    kps = [22] * 14
    kps[5:9] = [8, 8, 8, 8]  # as RLWalk.start()
    out = io.StringIO()
    err = None
    with redirect_stdout(out):
        try:
            hwi.set_kps(kps)
            hwi.turn_on()
        except Exception as e:
            err = e
    limp = [n for n, sid in hwi.joints.items() if bus.kp[sid] < 5 or not bus.torque[sid]]
    off = [n for n, sid in hwi.joints.items() if abs(bus.pos[sid] - hwi.init_pos[n]) > 0.15]
    log = [l for l in out.getvalue().splitlines() if any(t in l for t in ("WARN", "FATAL", "pose", "ERROR"))]
    return err, limp, off, log


CASES = {
    "healthy bus": {},
    "torque left off by `run_duck.sh stop`": {"torque_off_at_start": True},
    "flaky left_knee (fails 4 writes)": {"flaky": {23: 4}},
    "dead right_ankle": {"dead": (14,)},
    "left_ankle stuck 0.3 rad short": {"stuck": (24,)},
}

if __name__ == "__main__":
    for case, faults in CASES.items():
        print(f"\n### {case}")
        for variant in ["original", "patched"]:
            err, limp, off, log = run(variant, faults)
            outcome = f"ABORTS: {str(err)[:60]}" if err else "starts"
            print(f"  {variant:8s} {outcome:70s} limp joints: {limp or '-'}  off pose: {off or '-'}")
            for line in log[:4]:
                print(f"           | {line[:110]}")


def reset_cycle():
    """Reset button against the fake bus: start, knock joints off pose, go soft, stiffen."""
    bus = FakeBus({})
    mod = load_hwi(os.path.join(HERE, "patched", "mini_bdx_runtime/mini_bdx_runtime/rustypot_position_hwi.py"), bus)
    mod.time.sleep = lambda s: None
    hwi = mod.HWI(Cfg(), "/dev/fake")
    kps = [22] * 14
    kps[5:9] = [8, 8, 8, 8]
    with redirect_stdout(io.StringIO()):
        hwi.set_kps(kps)
        hwi.turn_on()
    for sid in bus.pos:  # the duck fell: every joint somewhere else, torque cut
        bus.pos[sid] += 0.7
        bus.torque[sid] = False
    soft_failed = hwi.go_soft_home()
    soft = {n: bus.kp[sid] for n, sid in hwi.joints.items()}
    out = io.StringIO()
    with redirect_stdout(out):
        stiff_failed = hwi.stiffen_home()
    off = [n for n, sid in hwi.joints.items() if abs(bus.pos[sid] - hwi.init_pos[n]) > 0.15]
    print("\n### reset button on the fake bus (patched HWI)")
    print(f"  soft step: all kp = {sorted(set(soft.values()))}, torque on = {all(bus.torque.values())}, failures = {soft_failed or '-'}")
    print(f"  stiff step: failures = {stiff_failed or '-'}, joints off pose = {off or '-'}; {out.getvalue().strip().splitlines()[-1]}")


reset_cycle()
