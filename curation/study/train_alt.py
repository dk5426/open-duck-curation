"""Phase 2 learners (PREREG v2 §4) on the tracking env: same env, clip list (CURATION_CLIPS), randomization and
observation as the Phase 1 PPO runs; only the learner changes.

  ppo_noff  PPO exactly as Phase 1 (common/runner.py) with ref_feedforward=False: targets = home + 0.25 * action
  sac       brax SAC on the actor observation ("state", 152); the critic sees the same observation (brax SAC has no
            asymmetric critic). Actor and critic 512-256-128, as PPO's networks. Hyperparameters: MuJoCo Playground's
            brax SAC config (num_envs 128, batch 512, lr 1e-3, 8 gradient updates per step, min replay 8192,
            q-network layer norm) with PPO's discount 0.97 and episode length 200; replay 1M (the config's 4M does not fit
            the 16 GB GPUs)
  ars       brax ARS (Mania et al. 2018): linear policy on the normalized actor observation, 60 directions, top 20,
            step 0.015, noise 0.025
  dagger    brax online DAgger (bc.train): the student (PPO's policy network, 512-256-128 on "state") imitates the
            teacher's mean action (L2 on tanh(loc)) on states the student visits; the teacher acts only in the first
            DAgger iteration. Teacher = the Phase 1 PPO final policy of the SAME condition (clip list) and seed
            (--teacher), so the student only sees the clips its teacher was trained on
  fasttd3   FastTD3's own train.py in its own torch venv, on this env (fasttd3_duck.py)
  fastsac   Holosoma's FastSAC (ported, Apache-2.0) in FastTD3's torch venv, on the same env bridge (fastsac_duck.py)

Every learner runs under launch_train.sh (TRAIN_ENTRY=<this file>) and writes, like PPO, checkpoint dirs
<output_dir>/<date>_<step> plus learner.json, which eval_clips.py reads to rebuild the policy (load_alt_policy) and
the env (TRACKING_OVERRIDES), so Phase 2 policies are tested by the Phase 1 evaluator unchanged.

  cd Open_Duck_Playground && uv run <this file> --learner sac --num_timesteps N --output_dir <run> --env tracking
"""

import argparse
import functools
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.getcwd())

HIDDEN = (512, 256, 128)
FF_OFF = {"ref_feedforward": False}


def _set_overrides(extra):
    over = {**json.loads(os.environ.get("TRACKING_OVERRIDES", "{}")), **extra}
    os.environ["TRACKING_OVERRIDES"] = json.dumps(over)
    return over


def _save(out, step, params):
    from flax.training import orbax_utils
    from orbax import checkpoint as ocp
    path = os.path.join(out, f"{datetime.now().strftime('%Y_%m_%d_%H%M%S')}_{int(step)}")
    ocp.PyTreeCheckpointer().save(path, params, force=True, save_args=orbax_utils.save_args_from_target(params))
    print(f"Saving checkpoint (step: {step}): {path}", flush=True)
    return path


def state_obs(env):
    """Expose only the actor observation as a flat array (brax SAC / ARS take no observation dicts)."""
    from mujoco_playground._src import wrapper

    class StateObs(wrapper.Wrapper):
        def reset(self, rng):
            s = self.env.reset(rng)
            return s.replace(obs=s.obs["state"])

        def step(self, state, action):
            s = self.env.step(state, action)
            return s.replace(obs=s.obs["state"])

        @property
        def observation_size(self):
            return int(self.env.observation_size["state"][0])

    return StateObs(env)


def _progress(t0, log):
    def fn(step, metrics):
        r = metrics.get("eval/episode_reward", float("nan"))
        line = f"STEP: {int(step)} reward: {float(r):.3f} elapsed_s: {time.time() - t0:.0f}"
        print(line, flush=True)
        log.append({"step": int(step), "elapsed_s": time.time() - t0, "reward": float(r)})
    return fn


def train(a):
    meta = {"learner": a.learner, "num_timesteps": a.num_timesteps, "teacher": a.teacher,
            "clips": os.environ.get("CURATION_CLIPS"), "seed": a.seed}
    if a.learner == "ppo_noff":
        meta["tracking_overrides"] = _set_overrides(FF_OFF)
    elif os.environ.get("TRACKING_OVERRIDES"):
        meta["tracking_overrides"] = json.loads(os.environ["TRACKING_OVERRIDES"])
    os.makedirs(a.output_dir, exist_ok=True)
    json.dump(meta, open(os.path.join(a.output_dir, "learner.json"), "w"), indent=1)

    if a.learner == "ppo_noff":  # Phase 1's runner, unchanged
        from playground.open_duck_mini_v2.runner import OpenDuckMiniV2Runner
        os.environ["PPO_OVERRIDES_JSON"] = json.dumps({**json.loads(os.environ.get("PPO_OVERRIDES_JSON", "{}")),
                                                       "seed": a.seed})
        OpenDuckMiniV2Runner(argparse.Namespace(output_dir=a.output_dir, num_timesteps=a.num_timesteps, env="tracking",
                                                task=a.task, restore_checkpoint_path=None)).train()
        return
    if a.learner in ("fasttd3", "fastsac"):  # torch: FastTD3's venv (fasttd3_duck.py, fastsac_duck.py)
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(here, "..", "..", ".."))
        py = os.environ.get("FASTTD3_PY", os.path.join(root, "fasttd3", ".venv", "bin", "python"))
        os.environ.setdefault("FASTTD3_SRC", os.path.join(root, "fasttd3", "fast_td3"))
        os.execv(py, [py, os.path.join(here, f"{a.learner}_duck.py"), "--num_timesteps", str(a.num_timesteps),
                      "--output_dir", a.output_dir, "--task", a.task, "--seed", str(a.seed)])

    import jax
    from mujoco_playground import wrapper
    from playground.open_duck_mini_v2 import tracking

    env = tracking.Tracking(task=a.task)
    randomizer = tracking.make_randomizer(env.mj_model)
    ep = tracking.PPO_OVERRIDES["episode_length"]
    t0, log = time.time(), []
    prog = _progress(t0, log)

    if a.learner == "sac":
        from brax.training.agents.sac import networks as sac_networks, train as sac
        nets = functools.partial(sac_networks.make_sac_networks, hidden_layer_sizes=HIDDEN, q_network_layer_norm=True)
        hp = dict(num_envs=128, batch_size=512, learning_rate=1e-3, grad_updates_per_step=8, discounting=0.97,
                  max_replay_size=1048576, min_replay_size=8192, normalize_observations=True, reward_scaling=1.0,
                  num_evals=a.num_evals, episode_length=ep, action_repeat=1)
        hp.update(json.loads(os.environ.get("ALT_OVERRIDES_JSON", "{}")))
        meta["hyperparameters"] = hp
        _, params, _ = sac.train(environment=state_obs(env), eval_env=state_obs(tracking.Tracking(task=a.task)),
                                 num_timesteps=a.num_timesteps, seed=a.seed, network_factory=nets,
                                 wrap_env_fn=wrapper.wrap_for_brax_training, randomization_fn=randomizer,
                                 progress_fn=prog, **hp)
    elif a.learner == "ars":
        from brax.training.agents.ars import train as ars
        hp = dict(number_of_directions=60, top_directions=20, step_size=0.015, exploration_noise_std=0.025,
                  normalize_observations=True, num_evals=a.num_evals, episode_length=ep, num_eval_envs=128)
        hp.update(json.loads(os.environ.get("ALT_OVERRIDES_JSON", "{}")))
        meta["hyperparameters"] = hp
        _, params, _ = ars.train(environment=state_obs(env), eval_env=state_obs(tracking.Tracking(task=a.task)),
                                 num_timesteps=a.num_timesteps, seed=a.seed, wrap_env_fn=wrapper.wrap_for_brax_training,
                                 randomization_fn=randomizer, progress_fn=prog, **hp)
    elif a.learner == "dagger":
        from brax.training.acme import running_statistics
        from brax.training.agents.bc import networks as bc_networks, train as bc
        assert a.teacher, "--teacher <Phase 1 PPO checkpoint> is required"
        teacher = teacher_fn(a.teacher, env)
        hp = dict(num_envs=2048, demo_length=100, epochs=4, batch_size=2048, learning_rate=3e-4, num_evals=a.num_evals,
                  eval_length=ep, scramble_time=ep)
        hp.update(json.loads(os.environ.get("ALT_OVERRIDES_JSON", "{}")))
        per_iter = hp["num_envs"] * hp["demo_length"]
        n_iter = max(hp["num_evals"] - 1, 1)
        steps = int(-(-a.num_timesteps // (per_iter * n_iter)) * n_iter)  # DAgger iterations, divisible by evals - 1
        hp["dagger_steps"] = steps
        meta["hyperparameters"] = hp
        key = jax.random.split(jax.random.PRNGKey(a.seed), hp["num_envs"])
        wenv = wrapper.wrap_for_brax_training(env, episode_length=ep, action_repeat=1,
                                              randomization_fn=functools.partial(randomizer, rng=key))
        nets = functools.partial(bc_networks.make_bc_networks, policy_hidden_layer_sizes=HIDDEN, policy_obs_key="state")
        _, ts, _ = bc.train(env=wenv, teacher_inference_fn=teacher, network_factory=nets, seed=a.seed,
                            progress_fn=lambda s, m: prog(int(s) * per_iter, m), tanh_squash=True,
                            normalize_observations=True, num_eval_envs=hp["num_envs"], **hp)
        # [normalizer, policy]: the PPO evaluator's layout (bc.train returns that pair, not the TrainingState it documents)
        params = list(ts) if isinstance(ts, tuple) else [ts.normalizer_params, ts.params]
    else:
        raise ValueError(a.learner)

    meta["wall_clock_s"] = time.time() - t0
    meta["progress"] = log
    json.dump(meta, open(os.path.join(a.output_dir, "learner.json"), "w"), indent=1)
    _save(a.output_dir, log[-1]["step"] if log else a.num_timesteps, params)


def _ppo_policy_net(env):
    from brax.training.acme import running_statistics
    from brax.training.agents.ppo import networks as ppo_networks
    from mujoco_playground.config import locomotion_params
    cfg = locomotion_params.brax_ppo_config("BerkeleyHumanoidJoystickFlatTerrain").network_factory
    return ppo_networks.make_ppo_networks(env.observation_size, env.action_size,
                                          preprocess_observations_fn=running_statistics.normalize, **cfg)


def teacher_fn(ckpt, env):
    """The PPO policy's mean action and its pre-tanh mean, the form brax's BC loss expects."""
    from brax.training.acme import running_statistics
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval"))
    from eval_clips import restore_params
    nets = _ppo_policy_net(env)
    p = restore_params(ckpt)
    norm = p[0] if not isinstance(p[0], dict) else running_statistics.RunningStatisticsState(**p[0])
    nu = env.action_size

    def fn(obs, key):
        logits = nets.policy_network.apply(norm, p[1], obs)
        loc = logits[..., :nu]
        import jax.numpy as jp
        return jp.tanh(loc), {"loc": loc}
    return fn


def load_alt_policy(ckpt, env, meta):
    """Deterministic policy(obs dict, key) -> (action, extras) for a Phase 2 checkpoint (eval_clips.py)."""
    import jax
    import jax.numpy as jp
    import numpy as np
    from brax.training.acme import running_statistics
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval"))
    from eval_clips import restore_params
    n_obs, nu = int(env.observation_size["state"][0]), env.action_size
    if meta["learner"] in ("fasttd3", "fastsac"):
        p, norm = None, None
    else:
        p = restore_params(ckpt)
        norm = p[0] if not isinstance(p[0], dict) else running_statistics.RunningStatisticsState(**p[0])
    if meta["learner"] == "sac":
        from brax.training.agents.sac import networks as sac_networks
        nets = sac_networks.make_sac_networks(n_obs, nu, preprocess_observations_fn=running_statistics.normalize,
                                              hidden_layer_sizes=HIDDEN, q_network_layer_norm=True)
        pol = sac_networks.make_inference_fn(nets)((norm, p[1]), deterministic=True)
    elif meta["learner"] == "fasttd3":  # fasttd3_duck.py's export: normalizer, then Linear + ReLU layers, tanh out
        z = np.load(os.path.join(ckpt, "fasttd3_actor.npz"))
        n = sum(k.startswith("W") for k in z.files)
        W = [jp.asarray(z[f"W{i}"]) for i in range(n)]
        b = [jp.asarray(z[f"b{i}"]) for i in range(n)]
        mean, scale = jp.asarray(z["mean"]), jp.asarray(z["std"]) + float(z["eps"])

        def pol(obs, key):
            x = (obs - mean) / scale
            for i in range(n):
                x = x @ W[i].T + b[i]
                x = jp.tanh(x) if i == n - 1 else jax.nn.relu(x)
            return x, {}
    elif meta["learner"] == "fastsac":  # fastsac_duck.py's export: normalizer, 3 x (Linear, LayerNorm, SiLU), mean head
        z = np.load(os.path.join(ckpt, "fastsac_actor.npz"))
        n = sum(k.startswith("W") for k in z.files)
        W = [jp.asarray(z[f"W{i}"]) for i in range(n)]
        b = [jp.asarray(z[f"b{i}"]) for i in range(n)]
        ln = [(jp.asarray(z[f"ln_g{i}"]), jp.asarray(z[f"ln_b{i}"])) if f"ln_g{i}" in z.files else None
              for i in range(n - 1)]
        mean, scale, ln_eps = jp.asarray(z["mean"]), jp.asarray(z["std"]) + float(z["eps"]), float(z["ln_eps"])
        a_scale, a_bias = jp.asarray(z["action_scale"]), jp.asarray(z["action_bias"])
        hi = jax.lax.Precision.HIGHEST  # no TF32, so the replay matches the fp32 torch actor

        def pol(obs, key):
            x = (obs - mean) / scale
            for i in range(n - 1):
                x = jp.matmul(x, W[i].T, precision=hi) + b[i]
                if ln[i] is not None:
                    mu = x.mean(-1, keepdims=True)
                    x = (x - mu) / jp.sqrt(jp.square(x - mu).mean(-1, keepdims=True) + ln_eps) * ln[i][0] + ln[i][1]
                x = jax.nn.silu(x)
            mu_a = jp.matmul(x, W[n - 1].T, precision=hi) + b[n - 1]  # Gaussian mean; deterministic action tanh(mean)
            return jp.tanh(mu_a) * a_scale + a_bias, {}
    elif meta["learner"] == "ars":
        from brax.training.agents.ars import networks as ars_networks
        net = ars_networks.make_policy_network(n_obs, nu, preprocess_observations_fn=running_statistics.normalize)
        pol = ars_networks.make_inference_fn(net)((norm, p[1]))
    else:
        raise ValueError(meta["learner"])
    return lambda obs, key: (lambda r: (jp.clip(r[0], -1.0, 1.0), r[1]))(pol(obs["state"], key))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--learner", required=True, choices=["ppo_noff", "sac", "ars", "dagger", "fasttd3", "fastsac"])
    p.add_argument("--num_timesteps", type=int, required=True)
    p.add_argument("--output_dir", required=True)
    p.add_argument("--task", default="flat_terrain_backlash")
    p.add_argument("--env", default="tracking", choices=["tracking"])
    p.add_argument("--teacher", default=None, help="dagger: Phase 1 PPO checkpoint dir (same condition and seed)")
    p.add_argument("--seed", type=int, default=None, help="default: PPO_OVERRIDES_JSON's seed, as the scheduler sets it")
    p.add_argument("--num_evals", type=int, default=6)
    p.add_argument("--restore_checkpoint_path", default=None, help="unused; accepted for the launcher's interface")
    a = p.parse_args()
    if a.seed is None:
        a.seed = int(json.loads(os.environ.get("PPO_OVERRIDES_JSON", "{}")).get("seed", 0))
    train(a)


if __name__ == "__main__":
    main()
