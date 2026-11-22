"""FastSAC (Amazon FAR Holosoma, github.com/amazon-far/holosoma) on the tracking env, for Phase 2.

Networks and update rule ported from Holosoma's src/holosoma/holosoma/agents/fast_sac/{fast_sac.py, fast_sac_agent.py,
fast_sac_utils.py} (Copyright Amazon.com, Inc. or its affiliates, Apache License 2.0; modified: single-GPU, flat
observations, no symmetry / CNN / n-step paths, no logging helper or ONNX export). Holosoma's agent is tied to its own
env manager, so unlike FastTD3 its training loop cannot run unchanged; the port keeps its loop and update order:
  actor   tanh-squashed Gaussian, 512-256-128 Linear + LayerNorm + SiLU, mean and log_std heads zero-initialised,
          log_std = -5 + 2.5 (tanh(h) + 1) in [-5, 0], deterministic action tanh(mean)
  critic  ensemble of 2 distributional (C51) Q-networks, 768-384-192 Linear + LayerNorm + SiLU, 501 atoms on
          [-20, 20]; target from the target critics with the soft-value term -gamma * alpha * log pi(a'|s');
          the actor maximises the ensemble MEAN of the Q values minus alpha * log pi
  alpha   autotuned (log alpha, init 0.001), target entropy -0.5 * n_act, updated after every critic update
  updates per env step: one batch of num_updates * batch sampled and normalised once, then num_updates critic +
          alpha updates, the actor on every policy_frequency-th of them (i % 2 == 1), soft target update (tau) after
          each; AdamW (betas 0.9 / 0.95, weight decay 0.001), lr 3e-4 everywhere, no grad clipping, bf16 autocast
  obs     separate empirical normalisers (eps 1e-2) for the actor and critic observations, updated on every sampled
          batch, frozen when acting; learning starts after 10 env steps
Environment exactly as FastTD3's (fasttd3_duck.make_env_factory: our Tracking env, CURATION_CLIPS, randomizer,
episode length 200, auto-reset with the pre-reset observation kept for truncated transitions); the actor sees "state"
(152), the critic "privileged_state". Reference feed-forward stays on (the env default).

Hyperparameters: Holosoma's g1_29dof_wbt_fast_sac recipe (gamma 0.99, num_updates 4, num_atoms 501, policy_frequency 2,
target_entropy_ratio 0.5, tau 0.05, v_min / v_max -20 / 20, batch 8192, buffer 1024 per env, critic 768 / actor 512,
lr 3e-4, symmetry off) with these departures:
  num_envs 1024 (theirs 4096): a 4096 x 1024 replay of 152 + 2 x privileged observations does not fit the 16 GB GPUs
      next to MJX; 1024 is also FastTD3's env count here. Kept: batch 8192 global (8 per env) and 1024 steps per env,
      so the replay holds 1M transitions (theirs 4M) and each env step feeds 32 samples (theirs 8)
  action_scale 1, bias 0: Holosoma scales tanh to each joint's limit range; our env maps [-1, 1] itself (as for PPO
      and FastTD3), so the actor outputs [-1, 1]
  torch.compile off (Triton fails on these RTX A4000s, "PassManager::run failed"); bf16 AMP kept
  evaluation: every 1/5 of training, 256 envs without randomization, deterministic, one 200-step episode (FastTD3's
      evaluate()), logged as "STEP: <env steps> reward: <mean return>" into learner.json's progress
ALT_OVERRIDES_JSON (a JSON dict) updates any of the hyperparameters below, num_envs included; learner.json records the
final values. After training the actor and its observation normaliser are written as
<output_dir>/<date>_<env steps>/fastsac_actor.npz, which train_alt.load_alt_policy replays in JAX for eval_clips.py;
the full torch checkpoint (Holosoma's save_params layout) goes to <output_dir>/models/fastsac_final.pt.
"""

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.amp import GradScaler, autocast

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fasttd3_duck import make_env_factory  # noqa: E402

torch.set_float32_matmul_precision("high")

HP = dict(num_envs=1024, critic_learning_rate=3e-4, actor_learning_rate=3e-4, alpha_learning_rate=3e-4,
          buffer_size=1024, gamma=0.99, tau=0.05, batch_size=8192, learning_starts=10, policy_frequency=2,
          num_updates=4, target_entropy_ratio=0.5, num_atoms=501, v_min=-20.0, v_max=20.0, critic_hidden_dim=768,
          actor_hidden_dim=512, alpha_init=0.001, use_autotune=True, log_std_max=0.0, log_std_min=-5.0,
          use_layer_norm=True, num_q_networks=2, max_grad_norm=0.0, amp=True, amp_dtype="bf16", weight_decay=0.001,
          logging_interval=100, num_eval_envs=256, num_evals=6)


def mlp(n_in, hidden, ln, out=None):
    """Holosoma's trunk: hidden -> hidden/2 -> hidden/4, each Linear + LayerNorm + SiLU, optional linear head."""
    dims, layers = [n_in, hidden, hidden // 2, hidden // 4], []
    for i in range(3):
        layers += [nn.Linear(dims[i], dims[i + 1]), nn.LayerNorm(dims[i + 1]) if ln else nn.Identity(), nn.SiLU()]
    if out is not None:
        layers.append(nn.Linear(dims[-1], out))
    return nn.Sequential(*layers)


class Actor(nn.Module):
    def __init__(self, n_obs, n_act, hidden_dim, log_std_max, log_std_min, use_layer_norm=True):
        super().__init__()
        self.log_std_max, self.log_std_min = log_std_max, log_std_min
        self.net = mlp(n_obs, hidden_dim, use_layer_norm)
        self.fc_mu = nn.Sequential(nn.Linear(hidden_dim // 4, n_act))
        self.fc_logstd = nn.Linear(hidden_dim // 4, n_act)
        for m in (self.fc_mu[0], self.fc_logstd):
            nn.init.constant_(m.weight, 0.0)
            nn.init.constant_(m.bias, 0.0)
        self.register_buffer("action_scale", torch.ones(n_act))
        self.register_buffer("action_bias", torch.zeros(n_act))

    def forward(self, obs):
        x = self.net(obs)
        mean = self.fc_mu(x)
        log_std = torch.tanh(self.fc_logstd(x))
        log_std = self.log_std_min + 0.5 * (self.log_std_max - self.log_std_min) * (log_std + 1)  # SpinUp / Yarats
        return torch.tanh(mean) * self.action_scale + self.action_bias, mean, log_std

    def get_actions_and_log_probs(self, obs):
        _, mean, log_std = self(obs)
        dist = torch.distributions.Normal(mean, log_std.exp())
        raw = dist.rsample()
        tanh_action = torch.tanh(raw)
        log_prob = dist.log_prob(raw)
        log_prob -= torch.log(1 - tanh_action.pow(2) + 1e-6)  # tanh Jacobian
        log_prob -= torch.log(self.action_scale + 1e-6)  # scaling Jacobian
        return tanh_action * self.action_scale + self.action_bias, log_prob.sum(1)

    @torch.no_grad()
    def explore(self, obs, deterministic=False):
        _, mean, log_std = self(obs)
        if deterministic:
            return torch.tanh(mean) * self.action_scale + self.action_bias
        raw = torch.distributions.Normal(mean, log_std.exp()).rsample()
        return torch.tanh(raw) * self.action_scale + self.action_bias


class DistributionalQNetwork(nn.Module):
    def __init__(self, n_obs, n_act, num_atoms, v_min, v_max, hidden_dim, use_layer_norm=True):
        super().__init__()
        self.net = mlp(n_obs + n_act, hidden_dim, use_layer_norm, out=num_atoms)
        self.v_min, self.v_max, self.num_atoms = v_min, v_max, num_atoms

    def forward(self, obs, actions):
        return self.net(torch.cat([obs, actions], 1))

    def projection(self, obs, actions, rewards, bootstrap, discount, q_support):
        """C51 projection of r + bootstrap * discount * z onto the support (Holosoma, with its edge-atom fix)."""
        delta_z = (self.v_max - self.v_min) / (self.num_atoms - 1)
        batch_size = rewards.shape[0]
        target_z = rewards.unsqueeze(1) + bootstrap.unsqueeze(1) * discount.unsqueeze(1) * q_support
        target_z = target_z.clamp(self.v_min, self.v_max)
        b = (target_z - self.v_min) / delta_z
        lower, upper = torch.floor(b).long(), torch.ceil(b).long()
        is_integer = upper == lower
        lower_mask = torch.logical_and(lower > 0, is_integer)
        upper_mask = torch.logical_and(lower == 0, is_integer)
        lower = torch.where(lower_mask, lower - 1, lower)
        upper = torch.where(upper_mask, upper + 1, upper)
        next_dist = F.softmax(self(obs, actions), dim=1)
        offset = (torch.linspace(0, (batch_size - 1) * self.num_atoms, batch_size, device=rewards.device)
                  .unsqueeze(1).expand(batch_size, self.num_atoms).long())
        max_index = next_dist.numel() - 1
        lower_idx = torch.clamp((lower + offset).view(-1), 0, max_index)
        upper_idx = torch.clamp((upper + offset).view(-1), 0, max_index)
        proj = torch.zeros_like(next_dist)
        proj.view(-1).index_add_(0, lower_idx, (next_dist * (upper.float() - b)).view(-1))
        proj.view(-1).index_add_(0, upper_idx, (next_dist * (b - lower.float())).view(-1))
        return proj


class Critic(nn.Module):
    def __init__(self, n_obs, n_act, num_atoms, v_min, v_max, hidden_dim, use_layer_norm=True, num_q_networks=2):
        super().__init__()
        self.qnets = nn.ModuleList([DistributionalQNetwork(n_obs, n_act, num_atoms, v_min, v_max, hidden_dim,
                                                           use_layer_norm) for _ in range(num_q_networks)])
        self.register_buffer("q_support", torch.linspace(v_min, v_max, num_atoms))

    def forward(self, obs, actions):
        return torch.stack([q(obs, actions) for q in self.qnets], dim=0)

    def projection(self, obs, actions, rewards, bootstrap, discount):
        return torch.stack([q.projection(obs, actions, rewards, bootstrap, discount, self.q_support)
                            for q in self.qnets], dim=0)

    def get_value(self, probs):
        return torch.sum(probs * self.q_support, dim=-1)


class EmpiricalNormalization(nn.Module):
    """Running mean / variance normaliser (Holosoma's, single process): (x - mean) / (std + eps)."""

    def __init__(self, shape, eps=1e-2):
        super().__init__()
        self.eps = eps
        self.register_buffer("_mean", torch.zeros(shape).unsqueeze(0))
        self.register_buffer("_var", torch.ones(shape).unsqueeze(0))
        self.register_buffer("_std", torch.ones(shape).unsqueeze(0))
        self.register_buffer("count", torch.tensor(0, dtype=torch.long))

    @torch.no_grad()
    def forward(self, x, update=True):
        if self.training and update:
            self.update(x)
        return (x - self._mean) / (self._std + self.eps)

    def update(self, x):
        n = x.shape[0]
        batch_mean = torch.mean(x, dim=0, keepdim=True)
        batch_var = torch.var(x, dim=0, keepdim=True, unbiased=False)
        new_count = self.count + n
        self._mean.copy_(self._mean + (batch_mean - self._mean) * (n / new_count))
        delta2 = batch_mean - self._mean
        M2 = self._var * self.count + batch_var * n + delta2.pow(2) * (self.count * n / new_count)
        self._var.copy_(M2 / new_count)
        self._std.copy_(self._var.sqrt())
        self.count.copy_(new_count)


class ReplayBuffer:
    """Holosoma's SimpleReplayBuffer, 1-step returns: per-env circular buffers, batch_size samples from every env."""

    def __init__(self, n_env, size, n_obs, n_act, n_critic_obs, device):
        z = lambda *s, dt=torch.float: torch.zeros((n_env, size, *s), device=device, dtype=dt)  # noqa: E731
        self.n_env, self.size, self.ptr = n_env, size, 0
        self.obs, self.next_obs, self.act = z(n_obs), z(n_obs), z(n_act)
        self.cobs, self.next_cobs = z(n_critic_obs), z(n_critic_obs)
        self.rew, self.done, self.trunc = z(), z(dt=torch.long), z(dt=torch.long)

    def extend(self, obs, cobs, act, rew, next_obs, next_cobs, done, trunc):
        p = self.ptr % self.size
        for buf, x in ((self.obs, obs), (self.cobs, cobs), (self.act, act), (self.rew, rew), (self.next_obs, next_obs),
                       (self.next_cobs, next_cobs), (self.done, done), (self.trunc, trunc)):
            buf[:, p] = x
        self.ptr += 1

    @torch.no_grad()
    def sample(self, batch_size):
        idx = torch.randint(0, min(self.size, self.ptr), (self.n_env, batch_size), device=self.obs.device)

        def g(buf):
            if buf.ndim == 2:
                return torch.gather(buf, 1, idx).reshape(-1)
            return torch.gather(buf, 1, idx.unsqueeze(-1).expand(-1, -1, buf.shape[-1])).reshape(-1, buf.shape[-1])
        return dict(obs=g(self.obs), cobs=g(self.cobs), act=g(self.act), rew=g(self.rew), next_obs=g(self.next_obs),
                    next_cobs=g(self.next_cobs), done=g(self.done), trunc=g(self.trunc))


class FastSAC:
    def __init__(self, hp, n_obs, n_cobs, n_act, device):
        self.hp, self.device = hp, device
        self.actor = Actor(n_obs, n_act, hp["actor_hidden_dim"], hp["log_std_max"], hp["log_std_min"],
                           hp["use_layer_norm"]).to(device)
        mk = lambda: Critic(n_cobs, n_act, hp["num_atoms"], hp["v_min"], hp["v_max"], hp["critic_hidden_dim"],  # noqa
                            hp["use_layer_norm"], hp["num_q_networks"]).to(device)
        self.qnet, self.qnet_target = mk(), mk()
        self.qnet_target.load_state_dict(self.qnet.state_dict())
        self.obs_norm = EmpiricalNormalization(n_obs).to(device)
        self.critic_obs_norm = EmpiricalNormalization(n_cobs).to(device)
        self.log_alpha = torch.tensor([math.log(hp["alpha_init"])], requires_grad=True, device=device)
        adamw = lambda ps, lr, wd: optim.AdamW(ps, lr=lr, weight_decay=wd, fused=True, betas=(0.9, 0.95))  # noqa
        self.q_opt = adamw(list(self.qnet.parameters()), hp["critic_learning_rate"], hp["weight_decay"])
        self.actor_opt = adamw(list(self.actor.parameters()), hp["actor_learning_rate"], hp["weight_decay"])
        self.alpha_opt = adamw([self.log_alpha], hp["alpha_learning_rate"], 0.01)  # torch's AdamW default decay
        self.target_entropy = -n_act * hp["target_entropy_ratio"]
        self.scaler = GradScaler("cuda", enabled=hp["amp"])
        self.amp_dtype = torch.bfloat16 if hp["amp_dtype"] == "bf16" else torch.float16

    def amp(self):
        return autocast(device_type="cuda", dtype=self.amp_dtype, enabled=self.hp["amp"])

    def _step(self, loss, opt, params):
        hp, sc = self.hp, self.scaler
        opt.zero_grad(set_to_none=True)
        sc.scale(loss).backward()
        sc.unscale_(opt)
        gn = (torch.nn.utils.clip_grad_norm_(params, max_norm=hp["max_grad_norm"]) if hp["max_grad_norm"] > 0
              else torch.tensor(0.0, device=self.device))
        sc.step(opt)
        sc.update()
        return gn

    def update_main(self, d):
        hp = self.hp
        with self.amp():
            bootstrap = (d["trunc"].bool() | ~d["done"].bool()).float()
            with torch.no_grad():
                next_a, next_logp = self.actor.get_actions_and_log_probs(d["next_obs"])
                discount = torch.full_like(d["rew"], hp["gamma"])  # gamma ** effective_n_steps, n = 1
                target = self.qnet_target.projection(
                    d["next_cobs"], next_a, d["rew"] - discount * bootstrap * self.log_alpha.exp() * next_logp,
                    bootstrap, discount)
            q_log = F.log_softmax(self.qnet(d["cobs"], d["act"]), dim=-1)
            qf_loss = (-torch.sum(target * q_log, dim=-1)).mean(dim=1).sum(dim=0)
        self._step(qf_loss, self.q_opt, self.qnet.parameters())
        alpha_loss = torch.tensor(0.0, device=self.device)
        if hp["use_autotune"]:
            with self.amp():
                alpha_loss = (-self.log_alpha.exp() * (next_logp.detach() + self.target_entropy)).mean()
            self._step(alpha_loss, self.alpha_opt, [self.log_alpha])
        return qf_loss.detach(), alpha_loss.detach()

    def update_pol(self, d):
        with self.amp():
            actions, logp = self.actor.get_actions_and_log_probs(d["obs"])
            with torch.no_grad():
                action_std = self.actor(d["obs"])[2].exp().mean()
                entropy = -logp.mean()
            q = self.qnet.get_value(F.softmax(self.qnet(d["cobs"], actions), dim=-1)).mean(dim=0)
            actor_loss = (self.log_alpha.exp().detach() * logp - q).mean()
        self._step(actor_loss, self.actor_opt, self.actor.parameters())
        return actor_loss.detach(), entropy.detach(), action_std.detach()

    def updates(self, rb, num_envs, step):
        """Sample num_updates batches at once, normalise once (this updates the normalisers), update on each."""
        hp = self.hp
        per_env = max(hp["batch_size"] // num_envs, 1)
        big = rb.sample(per_env * hp["num_updates"])
        for k, norm in (("obs", self.obs_norm), ("next_obs", self.obs_norm), ("cobs", self.critic_obs_norm),
                        ("next_cobs", self.critic_obs_norm)):
            big[k] = norm(big[k])
        n = per_env * num_envs
        m = {}
        for i in range(hp["num_updates"]):
            d = {k: v[i * n:(i + 1) * n] for k, v in big.items()}
            m["qf_loss"], m["alpha_loss"] = self.update_main(d)
            if (i % hp["policy_frequency"] == 1 if hp["num_updates"] > 1 else step % hp["policy_frequency"] == 0):
                m["actor_loss"], m["entropy"], m["action_std"] = self.update_pol(d)
            with torch.no_grad():
                tgt = [p.data for p in self.qnet_target.parameters()]
                torch._foreach_mul_(tgt, 1.0 - hp["tau"])
                torch._foreach_add_(tgt, [p.data for p in self.qnet.parameters()], alpha=hp["tau"])
        return m

    def state(self, step):
        cpu = lambda m: {k: v.detach().cpu() for k, v in m.state_dict().items()}  # noqa: E731
        return {"actor_state_dict": cpu(self.actor), "qnet_state_dict": cpu(self.qnet),
                "qnet_target_state_dict": cpu(self.qnet_target), "log_alpha": self.log_alpha.detach().cpu(),
                "obs_normalizer_state": cpu(self.obs_norm), "critic_obs_normalizer_state": cpu(self.critic_obs_norm),
                "actor_optimizer_state_dict": self.actor_opt.state_dict(),
                "q_optimizer_state_dict": self.q_opt.state_dict(),
                "alpha_optimizer_state_dict": self.alpha_opt.state_dict(),
                "grad_scaler_state_dict": self.scaler.state_dict(), "args": dict(self.hp), "global_step": step}


def evaluate(agent, eval_env):
    """FastTD3's evaluate(): deterministic actions, mean return of one episode per eval env."""
    obs = eval_env.reset()
    ret = torch.zeros(eval_env.num_envs, device=obs.device)
    done_mask = torch.zeros(eval_env.num_envs, dtype=torch.bool, device=obs.device)
    for _ in range(eval_env.max_episode_steps):
        with torch.no_grad(), agent.amp():
            a = agent.actor.explore(agent.obs_norm(obs, update=False), deterministic=True)
        obs, r, d, _ = eval_env.step(a.float())
        ret = torch.where(done_mask, ret, ret + r)
        done_mask |= d.bool()
        if done_mask.all():
            break
    return ret.mean().item()


def export_actor(pt, out_dir, steps):
    """Actor + normaliser as numpy: W/b per Linear (3 trunk + fc_mu), LayerNorm g/beta, action scale / bias."""
    d = torch.load(pt, map_location="cpu", weights_only=False)
    sd, norm = d["actor_state_dict"], d["obs_normalizer_state"]
    lin = ["net.0", "net.3", "net.6", "fc_mu.0"]
    arrs = {f"W{i}": sd[k + ".weight"].float().numpy() for i, k in enumerate(lin)}
    arrs.update({f"b{i}": sd[k + ".bias"].float().numpy() for i, k in enumerate(lin)})
    if d["args"]["use_layer_norm"]:
        for i, k in enumerate(["net.1", "net.4", "net.7"]):
            arrs[f"ln_g{i}"], arrs[f"ln_b{i}"] = sd[k + ".weight"].float().numpy(), sd[k + ".bias"].float().numpy()
    arrs.update(mean=norm["_mean"].float().numpy()[0], std=norm["_std"].float().numpy()[0], eps=np.float32(1e-2),
                ln_eps=np.float32(1e-5), action_scale=sd["action_scale"].float().numpy(),
                action_bias=sd["action_bias"].float().numpy())
    path = os.path.join(out_dir, f"{datetime.now().strftime('%Y_%m_%d_%H%M%S')}_{int(steps)}")
    os.makedirs(path, exist_ok=True)
    np.savez(os.path.join(path, "fastsac_actor.npz"), **arrs)
    print(f"Saving checkpoint (step: {steps}): {path}", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--num_timesteps", type=int, required=True, help="env steps (num_envs per iteration)")
    p.add_argument("--output_dir", required=True)
    p.add_argument("--task", default="flat_terrain_backlash")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    hp = {**HP, **json.loads(os.environ.get("ALT_OVERRIDES_JSON", "{}"))}
    unknown = set(hp) - set(HP)
    assert not unknown, f"unknown FastSAC hyperparameters {unknown}"
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    device = torch.device("cuda")
    ne = hp["num_envs"]
    iters = -(-a.num_timesteps // ne)
    eval_every = max(iters // (hp["num_evals"] - 1), 1)
    env, eval_env, _ = make_env_factory(a.task, ne)("OpenDuckTracking", a.seed, ne, hp["num_eval_envs"], 0)
    agent = FastSAC(hp, env.num_obs, env.num_privileged_obs, env.num_actions, device)
    rb = ReplayBuffer(ne, hp["buffer_size"], env.num_obs, env.num_actions, env.num_privileged_obs, device)
    print(f"FastSAC: obs {env.num_obs}, critic obs {env.num_privileged_obs}, actions {env.num_actions}, "
          f"{iters} iterations x {ne} envs; {json.dumps(hp)}", flush=True)
    meta_f = os.path.join(a.output_dir, "learner.json")
    meta = json.load(open(meta_f))
    meta["hyperparameters"] = hp

    obs, cobs = env.reset_with_critic_obs()
    t0, log, m, n_upd = time.time(), [], {}, 0
    t_win, s_win, u_win = time.time(), 0, 0
    for step in range(iters + 1):
        if step % eval_every == 0 or step == iters:
            r = evaluate(agent, eval_env)
            log.append({"step": step * ne, "elapsed_s": time.time() - t0, "reward": r})
            print(f"STEP: {step * ne} reward: {r:.3f} elapsed_s: {time.time() - t0:.0f}", flush=True)
            if step == iters:
                break
            t_win, s_win, u_win = time.time(), 0, 0  # throughput windows exclude evaluation
        with torch.no_grad(), agent.amp():
            actions = agent.actor.explore(agent.obs_norm(obs, update=False))
        next_obs, rew, done, info = env.step(actions.float())
        trunc = info["time_outs"]
        next_cobs = info["observations"]["critic"]
        raw = info["observations"]["raw"]
        true_next_obs = torch.where(trunc[:, None] > 0, raw["obs"], next_obs)
        true_next_cobs = torch.where(trunc[:, None] > 0, raw["critic_obs"], next_cobs)
        rb.extend(obs, cobs, actions.float(), rew.float(), true_next_obs, true_next_cobs, done.long(), trunc.long())
        obs, cobs = next_obs, next_cobs
        s_win += ne
        if step > hp["learning_starts"]:
            m = agent.updates(rb, ne, step)
            n_upd += hp["num_updates"]
            u_win += hp["num_updates"]
        if step % hp["logging_interval"] == 0 and step > 0:
            torch.cuda.synchronize()
            dt = time.time() - t_win
            print(f"it {step} env_steps/s {s_win / dt:.0f} updates/s {u_win / dt:.1f} alpha "
                  f"{agent.log_alpha.exp().item():.2e} train_rew {rew.float().mean().item():.4f} "
                  + " ".join(f"{k} {v.item():.4f}" for k, v in m.items()), flush=True)
            t_win, s_win, u_win = time.time(), 0, 0

    os.makedirs(os.path.join(a.output_dir, "models"), exist_ok=True)
    pt = os.path.join(a.output_dir, "models", "fastsac_final.pt")
    torch.save(agent.state(iters), pt)
    wall = time.time() - t0
    meta.update(wall_clock_s=wall, vector_steps=iters, num_envs=ne, gradient_updates=n_upd, progress=log,
                env_steps_per_s=iters * ne / wall, updates_per_s=n_upd / wall)
    json.dump(meta, open(meta_f, "w"), indent=1)
    export_actor(pt, a.output_dir, iters * ne)


if __name__ == "__main__":
    main()
