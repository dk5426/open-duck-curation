"""FastTD3 (Seo et al. 2025, github.com/younggyoseo/FastTD3) on the tracking env, for Phase 2.

FastTD3's own train.py runs unchanged; only its MuJoCo Playground bridge (environments/mujoco_playground_env.make_env)
is replaced by one that builds our Tracking env with the Phase 1 clip list (CURATION_CLIPS), randomizer, episode length
and auto-reset. The actor sees "state" (152), the critic "privileged_state", as in FastTD3's Playground mode. The bridge
also records each episode's last observation before the auto-reset ("raw_obs"), which FastTD3's fork of
mujoco_playground adds and our pinned version lacks.

Runs in its own venv (torch 2.8 + our pinned jax / mujoco / brax + FastTD3's code), started by train_alt.py
--learner fasttd3. After training, the final actor and its observation normalizer are written as
<output_dir>/<date>_<env steps>/fasttd3_actor.npz, which train_alt.load_alt_policy runs in JAX for eval_clips.py.

Hyperparameters: FastTD3's MuJoCo Playground defaults (num_envs 1024, gamma 0.97, v_min / v_max -10 / 10, batch 32768,
2 updates per step, distributional clipped double-Q critic 1024 wide, actor 512-256-128), with the replay buffer cut to
2048 steps per env and 256 evaluation envs to fit the 16 GB GPUs, no rendering and no wandb, and torch.compile off
(Triton fails to compile its kernels on these RTX A4000s, "PassManager::run failed").
"""

import argparse
import functools
import glob
import json
import os
import sys
import time
import types
from datetime import datetime

import numpy as np

sys.path.insert(0, os.getcwd())


def make_env_factory(task, num_envs_default):
    import jax
    import jax.numpy as jp
    import torch
    from brax.envs.wrappers import training as brax_training
    from torch.utils import dlpack as tpack
    from mujoco_playground._src import wrapper
    from playground.open_duck_mini_v2 import tracking

    j2t = lambda x: tpack.from_dlpack(x)  # noqa: E731
    t2j = lambda x: jax.dlpack.from_dlpack(x.contiguous())  # noqa: E731
    ep = tracking.PPO_OVERRIDES["episode_length"]

    class RawObsAutoReset(wrapper.BraxAutoResetWrapper):
        """BraxAutoResetWrapper that also keeps the observation the episode ended on (info['raw_obs'])."""

        def reset(self, rng):
            s = super().reset(rng)
            s.info["raw_obs"] = s.obs
            return s

        def step(self, state, action):
            if "steps" in state.info:
                state.info.update(steps=jp.where(state.done, jp.zeros_like(state.info["steps"]), state.info["steps"]))
            state = state.replace(done=jp.zeros_like(state.done))
            state = self.env.step(state, action)
            state.info["raw_obs"] = state.obs
            pick = lambda x, y: jp.where(jp.reshape(state.done, [x.shape[0]] + [1] * (x.ndim - 1)), x, y)  # noqa: E731
            return state.replace(data=jax.tree.map(pick, state.info["first_state"], state.data),
                                 obs=jax.tree.map(pick, state.info["first_obs"], state.obs))

    class TrainEnv:
        asymmetric_obs = True

        def __init__(self, num_envs, seed):
            raw = tracking.Tracking(task=task)
            k_reset, k_rand = jax.random.split(jax.random.PRNGKey(seed))
            rfn = functools.partial(tracking.make_randomizer(raw.mj_model), rng=jax.random.split(k_rand, num_envs))
            env = wrapper.BraxDomainRandomizationVmapWrapper(raw, rfn)
            env = brax_training.EpisodeWrapper(env, ep, 1)
            self.env = RawObsAutoReset(env)
            self.num_envs = num_envs
            self.num_obs = int(raw.observation_size["state"][0])
            self.num_privileged_obs = int(raw.observation_size["privileged_state"][0])
            self.num_actions = raw.action_size
            self.max_episode_steps = ep
            self.key_reset = jax.random.split(k_reset, num_envs)
            self.reset_fn, self.step_fn = jax.jit(self.env.reset), jax.jit(self.env.step)
            self.state = None

        def reset(self):
            self.state = self.reset_fn(self.key_reset)
            return j2t(self.state.obs["state"])

        def reset_with_critic_obs(self):
            self.state = self.reset_fn(self.key_reset)
            return j2t(self.state.obs["state"]), j2t(self.state.obs["privileged_state"])

        def step(self, action):
            self.state = self.step_fn(self.state, t2j(torch.clip(action, -1.0, 1.0)))
            s, raw = self.state, self.state.info["raw_obs"]
            info = {"time_outs": j2t(s.info["truncation"]),
                    "observations": {"critic": j2t(s.obs["privileged_state"]),
                                     "raw": {"obs": j2t(raw["state"]), "critic_obs": j2t(raw["privileged_state"])}},
                    "log": {}}
            return j2t(s.obs["state"]), j2t(s.reward), j2t(s.done), info

    class EvalEnv:
        """No randomization and no auto-reset, as FastTD3's Playground evaluation env."""

        def __init__(self, num_envs, seed):
            self.env = tracking.Tracking(task=task)
            self.num_envs, self.max_episode_steps, self.asymmetric_obs = num_envs, ep, True
            self.key_reset = jax.random.split(jax.random.PRNGKey(seed), num_envs)
            self.jit_reset = jax.jit(jax.vmap(self.env.reset))
            self.jit_step = jax.jit(jax.vmap(self.env.step))

        def reset(self):
            self.state = self.jit_reset(self.key_reset)
            return j2t(self.state.obs["state"])

        def step(self, actions):
            self.state = self.jit_step(self.state, t2j(actions))
            return j2t(self.state.obs["state"]), j2t(self.state.reward), j2t(self.state.done), None

    def make_env(env_name, seed, num_envs, num_eval_envs, device_rank, **_):
        return TrainEnv(num_envs, seed), EvalEnv(num_eval_envs, seed), None

    return make_env


def export_actor(pt, out_dir, steps):
    import torch
    d = torch.load(pt, map_location="cpu", weights_only=False)
    sd, norm = d["actor_state_dict"], d["obs_normalizer_state"]
    lin = sorted({k.rsplit(".", 1)[0] for k in sd if k.endswith(".weight")},
                 key=lambda k: (["net", "fc_head", "fc_mu"].index(k.split(".")[0]), int(k.split(".")[1])))
    arrs = {f"W{i}": sd[k + ".weight"].float().numpy() for i, k in enumerate(lin)}
    arrs.update({f"b{i}": sd[k + ".bias"].float().numpy() for i, k in enumerate(lin)})
    arrs.update(mean=norm["_mean"].float().numpy()[0], std=norm["_std"].float().numpy()[0], eps=np.float32(1e-2))
    path = os.path.join(out_dir, f"{datetime.now().strftime('%Y_%m_%d_%H%M%S')}_{int(steps)}")
    os.makedirs(path, exist_ok=True)
    np.savez(os.path.join(path, "fasttd3_actor.npz"), **arrs)
    print(f"Saving checkpoint (step: {steps}): {path}", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--num_timesteps", type=int, required=True, help="env steps; FastTD3 counts vector steps")
    p.add_argument("--output_dir", required=True)
    p.add_argument("--task", default="flat_terrain_backlash")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--num_envs", type=int, default=1024)
    a = p.parse_args()
    src = os.environ["FASTTD3_SRC"]
    sys.path.insert(0, src)
    mod = types.ModuleType("environments.mujoco_playground_env")
    mod.make_env = make_env_factory(a.task, a.num_envs)
    import environments  # noqa: F401  (FastTD3's package; its Playground module is replaced below)
    sys.modules["environments.mujoco_playground_env"] = mod
    iters = -(-a.num_timesteps // a.num_envs)
    sys.argv = ["train.py", "--env_name", "OpenDuckTracking", "--exp_name", "phase2", "--seed", str(a.seed),
                "--num_envs", str(a.num_envs), "--num_eval_envs", "256", "--buffer_size", "2048",
                "--total_timesteps", str(iters), "--eval_interval", str(max(iters // 5, 1)), "--render_interval", "0",
                "--save_interval", str(max(iters // 5, 1)), "--no-use_wandb", "--no-compile"]
    os.makedirs(a.output_dir, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(a.output_dir)
    t0 = time.time()
    import train as fasttd3_train
    fasttd3_train.main()
    os.chdir(cwd)
    final = max(glob.glob(os.path.join(a.output_dir, "models", "*_final.pt")), key=os.path.getmtime)
    meta_f = os.path.join(a.output_dir, "learner.json")
    meta = json.load(open(meta_f))
    meta.update(wall_clock_s=time.time() - t0, vector_steps=iters, num_envs=a.num_envs, fasttd3_args=sys.argv[1:])
    json.dump(meta, open(meta_f, "w"), indent=1)
    export_actor(final, a.output_dir, iters * a.num_envs)


if __name__ == "__main__":
    main()
