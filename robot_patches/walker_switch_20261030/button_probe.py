#!/usr/bin/env python3
"""Read-only: print the pygame index of every controller button pressed (and D-pad / hat moves) for N seconds.
Never touches the servos. Safe to run while the walking runtime is running.
  /home/duck/.venv/bin/python button_probe.py [seconds]
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame  # noqa: E402

seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 20
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() < 1:
    sys.exit("no controller visible to pygame")
js = pygame.joystick.Joystick(0)
js.init()
print(f"{js.get_name()}: {js.get_numbuttons()} buttons, {js.get_numhats()} hats. Press buttons now ({seconds:g} s)...",
      flush=True)
prev_b = [False] * js.get_numbuttons()
prev_h = [(0, 0)] * js.get_numhats()
t0 = time.time()
while time.time() - t0 < seconds:
    pygame.event.pump()
    for i in range(js.get_numbuttons()):
        b = bool(js.get_button(i))
        if b and not prev_b[i]:
            print(f"  button index {i} pressed", flush=True)
        prev_b[i] = b
    for i in range(js.get_numhats()):
        h = js.get_hat(i)
        if h != prev_h[i] and h != (0, 0):
            print(f"  hat {i} -> {h}", flush=True)
        prev_h[i] = h
    time.sleep(0.01)
print("done")
