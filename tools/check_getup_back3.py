"""CPU check of the getup_back3 env before a GPU launch: reset and step a small batch, report the start mix and the
feet_under and roll_front terms by pose.
  cd Open_Duck_Playground && JAX_PLATFORMS=cpu .venv/bin/python ../tools/check_getup_back3.py
"""

import os
import sys

import jax
import jax.numpy as jp
import numpy as np

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import getup_back3  # noqa: E402

env = getup_back3.GetupBack3()
reset, step = jax.jit(jax.vmap(env.reset)), jax.jit(jax.vmap(env.step))
n = 256
s = reset(jax.random.split(jax.random.PRNGKey(0), n))
h = np.asarray(s.data.qpos[:, 2])
fallen = np.asarray(s.info["start_fallen"]) > 0
print(f"starts: fallen {fallen.mean():.2f}, base height median fallen {np.median(h[fallen]):.3f} "
      f"standing {np.median(h[~fallen]):.3f}; obs {s.obs['state'].shape}")
for _ in range(25):
    s = step(s, jp.zeros((n, env.action_size)))
fu = np.asarray(s.metrics["reward/feet_under"])
rf = np.asarray(s.metrics["reward/roll_front"])
st = np.asarray(s.metrics["stood_up"]) > 0
fwd_z = np.asarray(s.data.xmat[:, env._base_body_id, 2, 0])
print(f"after 0.5 s of zero action: feet_under standing {fu[st].mean():.2f} (n={st.sum()}), "
      f"not standing {fu[~st].mean():.2f}; reward finite {bool(np.isfinite(s.reward).all())}")
for name, sel in [("standing", st), ("on back (fwd_z > 0.6)", ~st & (fwd_z > 0.6)),
                  ("on belly (fwd_z < -0.6)", ~st & (fwd_z < -0.6)), ("side/other", ~st & (np.abs(fwd_z) <= 0.6))]:
    if sel.any():
        print(f"  roll_front {name:24s} {rf[sel].mean():.2f} (n={sel.sum()})")

# the sitting bank itself, held still
sit = np.load(getup_back3.getup_back2.SIT_BANK_PATH)["qpos"]
print(f"sit bank {sit.shape}, base height median {np.median(sit[:, 2]):.3f}")
