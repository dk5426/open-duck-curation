"""S3.7 per-clip evaluator for tracking policies (and S4.2 scoring).

Runs the training env itself (playground/open_duck_mini_v2/tracking.py, same observations, physics, noise and action
delay) with a trained checkpoint, deterministic actions, every requested clip from frame 0, R rollouts per clip
(different seeds: domain randomization off by default, observation noise and action delay on). Per clip:
  completion   mean fraction of the clip played before a fall
  falls        rollouts that fell
  legs_rms / head_rms (rad), keypoints (m, mean body-frame distance), lin_vel (m/s), yaw_rate (rad/s): means over the
               frames played
  torque_sat   fraction of steps with any actuator at >= 95% of its torque limit
  joint_lim    fraction of steps with any joint within 0.02 rad of its range end
  score        PREREG P.2 draft: mean over the WHOLE clip of (legs_rms / tau_dof + keypoints / tau_key); each frame after a
               fall counts E_FAIL. Lower is better.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/eval/eval_clips.py \
      --ckpt <run>/<checkpoint dir> --clips all|train|val|test|<ids.json> --rollouts 10 --out scores.json
"""

import argparse
import functools
import json
import os
import sys

import jax
import jax.numpy as jp
import numpy as np

sys.path.insert(0, os.getcwd())
from brax.training.agents.ppo import networks as ppo_networks  # noqa: E402
from mujoco_playground.config import locomotion_params  # noqa: E402
from orbax import checkpoint as ocp  # noqa: E402

from playground.open_duck_mini_v2 import tracking  # noqa: E402

TAU_DOF, TAU_KEY, E_FAIL = 0.10, 0.02, 3.0
PUSH_T = 1.5  # s, P.7


def clip_ids(man, which):
    if which in ("all", "train", "val", "test"):
        return [c["id"] for c in man["clips"] if which == "all" or c["split"] == which]
    return json.load(open(which))


def restore_params(ckpt):
    """Restore a brax PPO checkpoint saved on a GPU onto whatever device this process has (CPU included)."""
    path = os.path.abspath(ckpt)
    ckptr = ocp.PyTreeCheckpointer()
    meta = ckptr.metadata(path)
    meta = getattr(meta, "item_metadata", meta)
    meta = getattr(meta, "tree", meta)
    shard = jax.sharding.SingleDeviceSharding(jax.devices()[0])
    is_leaf = lambda x: hasattr(x, "shape") and hasattr(x, "dtype")  # noqa: E731
    rargs = jax.tree_util.tree_map(lambda m: ocp.ArrayRestoreArgs(sharding=shard), meta, is_leaf=is_leaf)
    return ckptr.restore(path, restore_args=rargs)


def load_policy(ckpt, env):
    ppo = locomotion_params.brax_ppo_config("BerkeleyHumanoidJoystickFlatTerrain")
    nets = ppo_networks.make_ppo_networks(env.observation_size, env.action_size,
                                          preprocess_observations_fn=__import__("brax.training.acme.running_statistics",
                                                                                fromlist=["normalize"]).normalize,
                                          **ppo.network_factory)
    params = restore_params(ckpt)
    from brax.training.acme import running_statistics
    norm = params[0]
    if isinstance(norm, dict):  # restored without a target: rebuild the normalizer state object
        norm = running_statistics.RunningStatisticsState(**norm)
    make = ppo_networks.make_inference_fn(nets)
    return make((norm, params[1]), deterministic=True)


def evaluate(ckpt, ids, rollouts, seed=0, push=0.0, friction=1.0):
    """push: lateral base-velocity kick (m/s) at t = PUSH_T, +y on even rollouts and -y on odd ones (P.7);
    friction: scale on every geom's friction."""
    env = tracking.Tracking(clip_ids=ids)
    if friction != 1.0:
        env._mjx_model = env._mjx_model.replace(geom_friction=env._mjx_model.geom_friction.at[:, 0].multiply(friction))
    policy = load_policy(ckpt, env)
    n = len(ids)
    clips = jp.repeat(jp.arange(n), rollouts)
    keys = jax.random.split(jax.random.PRNGKey(seed), n * rollouts)
    reset = jax.jit(jax.vmap(lambda k, c: env.reset_to(k, c, 0)))
    T = env._T

    m = env._mj_model
    fmax = jp.array(m.actuator_forcerange[:, 1])
    lo, hi = env._ctrl_lo, env._ctrl_hi

    kick = jp.where(jp.arange(n * rollouts) % 2 == 0, push, -push)
    k_push = int(round(PUSH_T / env.dt))

    def one_step(carry, t):
        st, alive, key = carry
        qvel = st.data.qvel.at[:, 1].add(jp.where(t == k_push, kick, 0.0))
        st = st.replace(data=st.data.replace(qvel=qvel))
        key, kp = jax.random.split(key)
        act, _ = jax.vmap(policy)(st.obs, jax.random.split(kp, st.obs["state"].shape[0]))
        nst = jax.vmap(env.step)(st, act)
        q = jax.vmap(env.get_actuator_joints_qpos)(nst.data.qpos)
        rec = {k: nst.metrics[k] for k in ("err/legs_rms", "err/head_rms", "err/keypoints", "err/lin_vel", "err/yaw_rate")}
        rec["fell"] = nst.metrics["cost/termination"]
        rec["torque_sat"] = jp.any(jp.abs(nst.data.actuator_force) >= 0.95 * fmax, axis=-1).astype(jp.float32)
        rec["joint_lim"] = jp.any((q < lo + 0.02) | (q > hi - 0.02), axis=-1).astype(jp.float32)
        rec["alive"] = alive
        alive = alive * (1.0 - nst.done)
        return (nst, alive, key), rec

    st = reset(keys, clips)
    run = jax.jit(lambda st: jax.lax.scan(one_step, (st, jp.ones(n * rollouts), jax.random.PRNGKey(seed + 1)), jp.arange(T - 1))[1])
    rec = jax.tree_util.tree_map(np.asarray, run(st))  # (T-1, n*R)
    L = np.asarray(env._ref_len)[np.asarray(clips)] - 1
    out = {}
    for ci, cid in enumerate(ids):
        sel = np.where(np.asarray(clips) == ci)[0]
        per = []
        for r in sel:
            Lr = int(L[r])
            alive = rec["alive"][:Lr, r] > 0.5
            played = int(alive.sum())
            fell = bool(rec["fell"][:Lr, r][alive].max() > 0.5) if played else True
            e = rec["err/legs_rms"][:Lr, r] / TAU_DOF + rec["err/keypoints"][:Lr, r] / TAU_KEY
            e = np.where(alive, e, E_FAIL)
            if fell:  # the fall step itself and everything after it
                e[max(played - 1, 0):] = E_FAIL
            per.append(dict(completion=played / Lr, fell=fell, score=float(e.mean()),
                            **{k.split("/")[-1]: float(rec[k][:Lr, r][alive].mean()) if played else float("nan")
                               for k in ("err/legs_rms", "err/head_rms", "err/keypoints", "err/lin_vel", "err/yaw_rate")},
                            torque_sat=float(rec["torque_sat"][:Lr, r][alive].mean()) if played else float("nan"),
                            joint_lim=float(rec["joint_lim"][:Lr, r][alive].mean()) if played else float("nan")))
        agg = {k: float(np.nanmean([p[k] for p in per])) for k in per[0] if k != "fell"}
        agg["falls"] = int(sum(p["fell"] for p in per))
        agg["rollouts"] = len(per)
        out[cid] = agg
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", required=True)
    p.add_argument("--clips", default="all")
    p.add_argument("--rollouts", type=int, default=10)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--push", type=float, default=0.0, help="lateral kick (m/s) at t = 1.5 s (P.7)")
    p.add_argument("--friction", type=float, default=1.0, help="friction scale (P.7: 0.6)")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    _, man = tracking.load_library()
    ids = clip_ids(man, a.clips)
    res = evaluate(a.ckpt, ids, a.rollouts, a.seed, a.push, a.friction)
    cat = {c["id"]: (c["category"], c["split"]) for c in man["clips"]}
    print(f"{'clip':52s} {'split':5s} {'compl':>6s} {'falls':>5s} {'legs':>6s} {'kp cm':>6s} {'vel':>6s} {'yaw':>6s} {'score':>6s}")
    for cid, r in sorted(res.items(), key=lambda kv: kv[1]["score"]):
        print(f"{cid[:52]:52s} {cat[cid][1]:5s} {r['completion']:6.2f} {r['falls']:3d}/{r['rollouts']:<2d} {r['legs_rms']:6.3f} "
              f"{100 * r['keypoints']:6.2f} {r['lin_vel']:6.3f} {r['yaw_rate']:6.3f} {r['score']:6.2f}")
    json.dump({"ckpt": "/".join(os.path.abspath(a.ckpt).split("/")[-2:]), "tau_dof": TAU_DOF, "tau_key": TAU_KEY, "e_fail": E_FAIL,
               "rollouts": a.rollouts, "push_m_s": a.push, "friction_scale": a.friction, "clips": res}, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
