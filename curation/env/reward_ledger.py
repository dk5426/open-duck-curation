"""S3.4 reward ledger + CPU check of the tracking env (playground/open_duck_mini_v2/tracking.py).

For every clip, the per-step reward (before dt) the env would pay for
  perfect  the robot exactly on the reference (joints, base pose and velocities from the clip),
  stand    the robot standing still at the home pose while the clip plays,
  fall     the termination step,
averaged over the clip's frames, then per category. "Do the clip" must beat "stand still" clearly (plan: by >= 30%),
or the policy is paid to stand. Also: one batched reset/step on CPU with random actions (shapes, finite rewards).

  cd Open_Duck_Playground && JAX_PLATFORMS=cpu .venv/bin/python ../open-duck-curation/curation/env/reward_ledger.py
"""

import json
import os
import sys

import jax
import jax.numpy as jp
import numpy as np

sys.path.insert(0, os.getcwd())
from mujoco_playground._src import mjx_env  # noqa: E402
from mujoco.mjx._src import math  # noqa: E402

from playground.open_duck_mini_v2 import tracking  # noqa: E402


def main():
    lib, man = tracking.load_library()
    all_ids = [c["id"] for c in man["clips"]]
    env = tracking.Tracking(clip_ids=all_ids)
    print(f"clips {env._n_clips}, frames {env._T}; obs {env.observation_size}")
    sc = env._config.reward_config.scales

    def state_at(clip, k, stand):
        ref = env._ref(clip, k)
        if stand:
            qpos = env._home_q
            qvel = jp.zeros(env.mjx_model.nv)
        else:
            qpos = env._home_q.at[0:3].set(ref["pos"]).at[3:7].set(ref["quat"])
            qpos = env.set_actuator_joints_qpos(ref["q"], qpos)
            Rw = math.quat_to_mat(ref["quat"])
            qvel = env.set_floating_base_qvel(jp.concatenate([Rw @ ref["lin"], Rw @ ref["ang"]]), jp.zeros(env.mjx_model.nv))
            qvel = env.set_actuator_joints_qvel(ref["qd"], qvel)
        data = mjx_env.init(env.mjx_model, qpos=qpos, qvel=qvel, ctrl=env.get_actuator_joints_qpos(qpos))
        return data, ref

    def reward_at(clip, k, stand):
        data, ref = state_at(clip, k, stand)
        prev_ref = env._ref(clip, jp.maximum(k - 1, 0))
        info = {"last_act": jp.zeros(env._nu), "frame": k, "clip": clip,
                "prev_feet": data.site_xpos[env._feet_site_id] if stand else data.site_xpos[env._feet_site_id]}
        contact = env._feet_contact(data)
        terms, errs, fell = env._terms(data, jp.zeros(env._nu), info, ref, contact)
        terms = dict(terms)
        terms["foot_slip"] = jp.zeros(())  # needs two consecutive states; zero for both rows
        terms["torques"] = jp.zeros(())
        r = sum(terms[k2] * sc[k2] for k2 in terms if k2 != "termination")
        return r, terms

    import functools
    fp = jax.jit(jax.vmap(functools.partial(reward_at, stand=False), in_axes=(None, 0)))
    fs = jax.jit(jax.vmap(functools.partial(reward_at, stand=True), in_axes=(None, 0)))
    rows = []
    for ci, c in enumerate(man["clips"]):
        ks = jp.arange(0, c["length"] - 1, 2)
        rp, tp = fp(ci, ks)
        rs, ts = fs(ci, ks)
        rows.append((c["category"], c["id"], float(rp.mean()), float(rs.mean()),
                     {k: float(v.mean()) for k, v in tp.items()}, {k: float(v.mean()) for k, v in ts.items()}))
    fall = float(sc["termination"])
    print(f"\nper-step reward (x dt = 0.02 in training); falling costs {fall:+.1f} once")
    print(f"{'category':14s} {'perfect':>8s} {'stand':>8s} {'perfect/stand':>13s}  clips")
    out = {}
    for cat in sorted(set(r[0] for r in rows)):
        rr = [r for r in rows if r[0] == cat]
        p, s = np.mean([r[2] for r in rr]), np.mean([r[3] for r in rr])
        worst = min(rr, key=lambda r: r[2] / max(r[3], 1e-6))
        out[cat] = {"perfect": p, "stand": s, "ratio": p / s, "worst_clip": worst[1], "worst_ratio": worst[2] / worst[3]}
        print(f"{cat:14s} {p:8.2f} {s:8.2f} {p / s:12.2f}x  {len(rr)} (worst {worst[2] / worst[3]:.2f}x {worst[1]})")
    terms = list(rows[0][4].keys())
    print("\nterm values (perfect / stand), averaged over gait clips and over crouch clips:")
    for grp, sel in [("gaits", lambda r: r[0] != "crouch"), ("crouch", lambda r: r[0] == "crouch")]:
        rr = [r for r in rows if sel(r)]
        print(f"  {grp:6s} " + "  ".join(f"{t} {np.mean([r[4][t] for r in rr]):.2f}/{np.mean([r[5][t] for r in rr]):.2f}"
                                       for t in terms if t not in ("termination", "foot_slip", "torques", "alive")))
    json.dump(out, open(os.environ.get("LEDGER_OUT", "/tmp/ledger.json"), "w"), indent=1)

    # batched reset/step with random actions
    reset, step = jax.jit(jax.vmap(env.reset)), jax.jit(jax.vmap(env.step))
    st = reset(jax.random.split(jax.random.PRNGKey(0), 32))
    for i in range(30):
        st = step(st, 0.3 * jax.random.normal(jax.random.PRNGKey(i), (32, env.action_size)))
    print(f"\nreset/step: obs {st.obs['state'].shape} privileged {st.obs['privileged_state'].shape}; "
          f"reward finite {bool(np.isfinite(np.asarray(st.reward)).all())}; done after 30 random steps "
          f"{int(np.asarray(st.done).sum())}/32")


if __name__ == "__main__":
    main()
