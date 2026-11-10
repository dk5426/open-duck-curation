"""Check RLWalk.__init__ ordering with every hardware module stubbed: in the patched script a failing IMU or controller
must raise BEFORE any motor command (HWI.turn_on) is sent; an optional feature failing must only disable itself.
No hardware, no robot.  python test_mock_init_order.py
"""

import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
CALLS = []


def stub_modules(fail=None):
    def cls(name, fail_here=False):
        def __init__(self, *a, **k):
            CALLS.append(name)
            if fail_here:
                raise RuntimeError(f"{name} init failed")
        return type(name, (), {"__init__": __init__})

    class HWI:
        def __init__(self, *a, **k):
            CALLS.append("HWI")
            self.init_pos = {f"j{i}": 0.0 for i in range(14)}

        def set_kps(self, k): pass
        def set_kds(self, k): pass
        def turn_on(self): CALLS.append("MOTORS turn_on")

    class DuckConfig:
        def __init__(self, *a, **k):
            self.start_paused, self.imu_upside_down, self.phase_frequency_factor_offset = True, False, 0.0
            self.eyes = self.projector = self.speaker = self.antennas = True

    mods = {
        "mini_bdx_runtime.rustypot_position_hwi": {"HWI": HWI},
        "mini_bdx_runtime.onnx_infer": {"OnnxInfer": cls("OnnxInfer")},
        "mini_bdx_runtime.rl_utils": {"make_action_dict": None, "LowPassActionFilter": None},
        "mini_bdx_runtime.raw_imu": {"Imu": cls("Imu", fail == "imu")},
        "mini_bdx_runtime.poly_reference_motion": {"PolyReferenceMotion": cls("PRM")},
        "mini_bdx_runtime.xbox_controller": {"XBoxController": cls("XBoxController", fail == "controller")},
        "mini_bdx_runtime.controller_shutdown": {"HoldToShutdown": cls("HoldToShutdown"), "stop_and_poweroff": None},
        "mini_bdx_runtime.keyboard_controller": {"KeyboardController": cls("KeyboardController")},
        "mini_bdx_runtime.feet_contacts": {"FeetContacts": cls("FeetContacts")},
        "mini_bdx_runtime.eyes": {"Eyes": cls("Eyes", fail == "eyes")},
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


def run(variant, fail):
    CALLS.clear()
    stub_modules(fail)
    path = os.path.join(HERE, variant, "scripts/v2_rl_walk_mujoco.py")
    spec = importlib.util.spec_from_file_location(f"walk_{variant}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.time.sleep = lambda s: None
    err = None
    try:
        mod.RLWalk("x.onnx", commands=True)
    except Exception as e:
        err = e
    return err, list(CALLS)


if __name__ == "__main__":
    for fail in ["imu", "controller", "eyes", None]:
        print(f"\n### failure in: {fail or 'nothing'}")
        for variant in ["original", "patched"]:
            err, calls = run(variant, fail)
            moved = "MOTORS turn_on" in calls
            print(f"  {variant:8s} motors moved: {'YES' if moved else 'no '}   "
                  f"{'crashed: ' + str(err) if err else 'started OK'}")
            print(f"           order: {' -> '.join(calls)}")
