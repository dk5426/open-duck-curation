"""CPU check of the getup_real env before a GPU launch: head-vs-body collision bits, head gains, the torque
randomizer, and a batched reset/step with the randomized models; a head pushed into the trunk must make contact.
  cd Open_Duck_Playground && JAX_PLATFORMS=cpu .venv/bin/python ../tools/check_getup_real.py
"""

import os
import sys

import jax
import jax.numpy as jp
import mujoco
import numpy as np

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import getup_real  # noqa: E402

env = getup_real.GetupReal()
m = env.mj_model
head = [m.geom(n).id for n in getup_real.HEAD_BOXES]
print("head boxes contype/conaffinity:", [(int(m.geom_contype[g]), int(m.geom_conaffinity[g])) for g in head])
print("trunk box:", int(m.geom_contype[m.geom("col_trunk_assembly").id]), int(m.geom_conaffinity[m.geom("col_trunk_assembly").id]))
kp = m.actuator_gainprm[:, 0]
print("kp legs", np.unique(np.round(kp[[0, 1, 2, 3, 4, 9, 10, 11, 12, 13]], 3)), "head", np.unique(np.round(kp[5:9], 3)))
print("mjx ncon (contacts allocated):", env.mjx_model.ngeom, "geoms")

# a pose with the head folded into the trunk: neck/head pitch to the limit, check head-trunk contact in plain MuJoCo
d = mujoco.MjData(m)
mujoco.mj_resetDataKeyframe(m, d, m.keyframe("home").id)
adr = {m.actuator(i).name: m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)}
best = 0
for npv in np.linspace(m.jnt_range[m.joint("neck_pitch").id][0], m.jnt_range[m.joint("neck_pitch").id][1], 15):
    for hp in np.linspace(m.jnt_range[m.joint("head_pitch").id][0], m.jnt_range[m.joint("head_pitch").id][1], 15):
        d.qpos[adr["neck_pitch"]], d.qpos[adr["head_pitch"]] = npv, hp
        mujoco.mj_forward(m, d)
        n = sum(1 for c in d.contact[: d.ncon] if (c.geom1 in head) != (c.geom2 in head)
                and m.geom(c.geom1).name.startswith("col_") and m.geom(c.geom2).name.startswith("col_"))
        best = max(best, n)
print("head-vs-body contacts possible over the neck/head pitch range:", best)

rand = getup_real.make_randomizer(m)
rng = jax.random.split(jax.random.PRNGKey(0), 64)
mb, axes = rand(env.mjx_model, rng)
fr = np.asarray(mb.actuator_forcerange)
print("randomized forcerange shape", fr.shape, "scale min/max", round(float(fr[:, 0, 1].min() / m.actuator_forcerange[0, 1]), 2),
      round(float(fr[:, 0, 1].max() / m.actuator_forcerange[0, 1]), 2))
print("kp after DR (head/legs ratio):", round(float(np.median(np.asarray(mb.actuator_gainprm)[:, 6, 0] / np.asarray(mb.actuator_gainprm)[:, 2, 0])), 3))


def one(model, key):
    e = env
    st = jax.jit(e.reset)(key)
    return st


reset = jax.jit(jax.vmap(env.reset))
step = jax.jit(jax.vmap(env.step))
s = reset(jax.random.split(jax.random.PRNGKey(1), 32))
for _ in range(10):
    s = step(s, jp.zeros((32, env.action_size)))
print("reset/step ok, reward finite:", bool(np.isfinite(np.asarray(s.reward)).all()))
