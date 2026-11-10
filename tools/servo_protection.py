"""Feetech STS3215 overload protection, as set on the duck's servos (read 2026-10-30, all 14 identical):
overload torque 80 %, protection time 200 x 10 ms = 2 s, protective torque 20 %.

Model (per servo, per 50 Hz control step):
- overloaded while |actuator force| >= 80 % of the servo's torque limit; a servo overloaded continuously for 2 s
  enters protection;
- in protection its torque is capped at 20 % of the limit. For a position servo (force = kp (target - q)) the cap is
  applied by clipping the target to q +- cap / kp;
- ASSUMED recovery (the registers do not say): it leaves protection once the torque it is asked for,
  |kp (target - q)|, has stayed below the 20 % cap for 0.5 s.
NumPy version for the CPU evaluation tools; playground/open_duck_mini_v2/getup_real2.py has the JAX one.
"""

import numpy as np

OVERLOAD, PROT_TIME, PROTECTIVE, RELEASE_TIME = 0.80, 2.0, 0.20, 0.5


class ServoProtection:
    def __init__(self, nu, dt=0.02):
        self.dt = dt
        self.over_t = np.zeros(nu)
        self.calm_t = np.zeros(nu)
        self.protected = np.zeros(nu, dtype=bool)

    def reset(self):
        self.over_t[:] = 0
        self.calm_t[:] = 0
        self.protected[:] = False

    def limit_targets(self, targets, q, kp, tau_max):
        """Clip the targets of protected servos so that their torque stays under the protective cap."""
        cap = PROTECTIVE * tau_max / kp
        return np.where(self.protected, np.clip(targets, q - cap, q + cap), targets)

    def update(self, actuator_force, demanded, tau_max):
        """After the physics step: actuator_force = applied torque, demanded = |kp (target - q)| unclipped."""
        over = np.abs(actuator_force) >= OVERLOAD * tau_max
        self.over_t = np.where(over, self.over_t + self.dt, 0.0)
        calm = demanded < PROTECTIVE * tau_max
        self.calm_t = np.where(self.protected & calm, self.calm_t + self.dt, 0.0)
        self.protected = (self.protected | (self.over_t >= PROT_TIME)) & ~(self.calm_t >= RELEASE_TIME)
