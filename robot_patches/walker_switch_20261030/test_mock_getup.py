"""Get-up mode in the patched v2_rl_walk_mujoco.py with every hardware module stubbed and a fake clock. No robot.
  python test_mock_getup.py
"""

import importlib.util
import os
import sys
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch",
         "head_yaw", "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
HOME = [0.002, 0.053, -0.63, 1.368, -0.784, 0, 0, 0, 0, -0.003, -0.065, 0.635, 1.379, -0.796]


class World:
    accel = np.array([9.8, 0.0, 0.0])  # lying on its side
    pos = np.array(HOME) + 0.6
    obs_sizes = []
    writes = 0


class FakeHWI:
    def __init__(self, *a, **k):
        self.init_pos = dict(zip(NAMES, HOME))
        self.joints = {n: i for i, n in enumerate(NAMES)}

    def set_kps(self, k): pass
    def set_kds(self, k): pass
    def turn_on(self): pass
    def get_present_positions(self, ignore=None): return list(World.pos)
    def get_present_velocities(self, ignore=None): return [0.0] * 14

    def set_position_all(self, d):
        World.writes += 1
        World.pos = np.array([d[n] for n in NAMES])  # joints follow their targets instantly

    def go_soft_home(self): return set()
    def stiffen_home(self): return set()
    def _format_servos(self, ids): return str(ids)


class FakePolicy:
    def __init__(self, path, awd=True):
        self.path = path

    def infer(self, obs):
        World.obs_sizes.append(len(obs))
        return np.zeros(14)  # "go to home"


class FakeImu:
    def __init__(self, *a, **k): pass
    def get_data(self): return {"gyro": np.zeros(3), "accelero": World.accel.copy()}


def load():
    def cls(name):
        return type(name, (), {"__init__": lambda self, *a, **k: None})

    class DuckConfig:
        def __init__(self, *a, **k):
            self.start_paused, self.imu_upside_down, self.phase_frequency_factor_offset = True, False, 0.0
            self.eyes = self.projector = self.speaker = self.antennas = False

    feet = cls("FeetContacts")
    feet.get = lambda self: [True, True]
    mods = {
        "mini_bdx_runtime.rustypot_position_hwi": {"HWI": FakeHWI},
        "mini_bdx_runtime.onnx_infer": {"OnnxInfer": FakePolicy},
        "mini_bdx_runtime.rl_utils": {"make_action_dict": lambda a, order: {order[i]: v for i, v in enumerate(a)},
                                      "LowPassActionFilter": None},
        "mini_bdx_runtime.raw_imu": {"Imu": FakeImu},
        "mini_bdx_runtime.poly_reference_motion": {"PolyReferenceMotion": cls("PRM")},
        "mini_bdx_runtime.xbox_controller": {"XBoxController": cls("XBoxController")},
        "mini_bdx_runtime.controller_shutdown": {"HoldToShutdown": cls("HoldToShutdown"), "stop_and_poweroff": None},
        "mini_bdx_runtime.keyboard_controller": {"KeyboardController": cls("KeyboardController")},
        "mini_bdx_runtime.feet_contacts": {"FeetContacts": feet},
        "mini_bdx_runtime.eyes": {"Eyes": cls("Eyes")},
        "mini_bdx_runtime.sounds": {"Sounds": cls("Sounds")},
        "mini_bdx_runtime.antennas": {"Antennas": cls("Antennas")},
        "mini_bdx_runtime.projector": {"Projector": cls("Projector")},
        "mini_bdx_runtime.duck_config": {"DuckConfig": DuckConfig},
    }
    pkg = types.ModuleType("mini_bdx_runtime")
    pkg.__path__ = []
    sys.modules["mini_bdx_runtime"] = pkg
    for name, attrs in mods.items():
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m
    spec = importlib.util.spec_from_file_location("walk", os.path.join(HERE, "patched/scripts/v2_rl_walk_mujoco.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Clock:
    t = 1000.0


class Pad:
    def __init__(self):
        self.buttons = {}

    def get_raw_button_sample(self, i):
        return self.buttons.get(i, False), Clock.t


def make(mod):
    os.environ["DUCK_GETUP_ONNX_MODEL"] = __file__  # any existing file: FakePolicy ignores it
    w = mod.RLWalk("walk.onnx", commands=True)
    w.command_controller = Pad()
    w.paused = False
    w.last_action = np.ones(14)
    w.imitation_i = 9
    return w


def press(w, idx, steps=1):
    w.command_controller.buttons[idx] = True
    for _ in range(steps):
        w._check_getup_button()
        w._check_reset_button()
    w.command_controller.buttons[idx] = False
    w._check_getup_button()
    w._check_reset_button()


def run_steps(w, n):
    for _ in range(n):
        if not w.getup_active:
            return
        w._getup_step()
        Clock.t += 0.02


def main():
    mod = load()
    mod.time.sleep = lambda s: None
    mod.time.monotonic = lambda: Clock.t
    ok = True

    # 1. lying -> button -> stands after 0.6 s -> 1 s upright -> 0.5 s settle -> paused, fresh walker state
    World.accel, World.pos, World.obs_sizes = np.array([9.8, 0, 0]), np.array(HOME) + 0.6, []
    w = make(mod)
    press(w, 11, steps=5)  # held for 5 samples: must start once
    started = w.getup_active
    run_steps(w, 30)
    World.accel = np.array([0, 0, 9.8])  # policy got it upright
    run_steps(w, 200)
    case1 = started and not w.getup_active and w.paused and not w.last_action.any() and w.imitation_i == 0
    case1 &= set(World.obs_sizes) == {92} and np.allclose(World.pos, HOME, atol=1e-6)
    print(f"1. fallen -> get-up button -> standing -> settle -> paused, walker state reset: {'PASS' if case1 else 'FAIL'}"
          f"  (policy obs size {sorted(set(World.obs_sizes))}, joints at home {np.allclose(World.pos, HOME, atol=1e-6)})")
    ok &= case1

    # 2. never gets up -> timeout after 10 s, paused, walker state NOT reset (it is still lying)
    World.accel, World.pos = np.array([9.8, 0, 0]), np.array(HOME) + 0.6
    w = make(mod)
    press(w, 11)
    t0 = Clock.t
    run_steps(w, 1000)
    case2 = not w.getup_active and w.paused and 9.9 < Clock.t - t0 < 10.2
    print(f"2. never upright -> stops after {Clock.t - t0:.2f} s, paused: {'PASS' if case2 else 'FAIL'}")
    ok &= case2

    # 3. RB during a get-up cancels it and starts the soft reset
    World.accel = np.array([9.8, 0, 0])
    w = make(mod)
    press(w, 11)
    run_steps(w, 10)
    w.command_controller.buttons[7] = True
    w._check_getup_button()
    w._check_reset_button()
    case3 = not w.getup_active and w.resetting and w.paused
    print(f"3. RB during get-up -> get-up cancelled, soft reset running: {'PASS' if case3 else 'FAIL'}")
    ok &= case3

    # 4. no get-up policy file -> button does nothing
    os.environ["DUCK_GETUP_ONNX_MODEL"] = "/nonexistent.onnx"
    w = mod.RLWalk("walk.onnx", commands=True)
    w.command_controller = Pad()
    press(w, 11)
    case4 = not w.getup_active
    print(f"4. no get-up policy installed -> button ignored: {'PASS' if case4 else 'FAIL'}")
    ok &= case4

    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
