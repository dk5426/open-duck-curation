"""CPU check of the getup_back2 env before a GPU launch: reset and step a small batch, report the start mix and the
feet_under term at standing home vs in the sitting starts.
  cd Open_Duck_Playground && JAX_PLATFORMS=cpu .venv/bin/python ../tools/check_getup_back2.py
"""

import os
import sys

import jax
import jax.numpy as jp
import numpy as np

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import getup_back2  # noqa: E402

env = getup_back2.GetupBack2()
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
st = np.asarray(s.metrics["stood_up"]) > 0
print(f"after 0.5 s of zero action: feet_under standing {fu[st].mean():.2f} (n={st.sum()}), "
      f"not standing {fu[~st].mean():.2f} (n={(~st).sum()}); reward finite {bool(np.isfinite(s.reward).all())}")

# the sitting bank itself, held still
sit = np.load(getup_back2.SIT_BANK_PATH)["qpos"]
print(f"sit bank {sit.shape}, base height median {np.median(sit[:, 2]):.3f}")
