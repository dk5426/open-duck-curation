"""Build the reference-clip library (S2.1-S2.6): gait clips from the reference generator's raw recordings, crouch clips
by inverse kinematics, train/val/test split by SOURCE before variants, kinematic checks, one npz + manifest.

Clip format (every clip resampled to 50 Hz, padded to the longest clip; `length` says how many frames are real):
  q        (N, T, 14)  joint targets, model actuator order
  qd       (N, T, 14)  joint velocities
  base_pos (N, T, 3)   base position in the clip's world frame (start at x = y = 0)
  base_quat(N, T, 4)   base orientation, MuJoCo order (w, x, y, z)
  lin_vel  (N, T, 3)   base linear velocity in the BODY frame
  ang_vel  (N, T, 3)   base angular velocity in the BODY frame (yaw rate recomputed from orientation: the upstream
                       generator's stored angular velocity is ~40x too small)
  contacts (N, T, 2)   left / right foot contact
  keypts   (N, T, K, 3) body-frame keypoints (KEYPOINTS below), from forward kinematics of q
  length   (N,)        frames per clip
Manifest (json): per clip id, category, source id, split, parameters, length, and the kinematic check report.

  cd Open_Duck_Playground && .venv/bin/python ../open-duck-curation/curation/clips/make_library.py \
      --recordings ../Open_Duck_reference_motion_generator/recordings --out ../open-duck-curation/data/clips_v1
"""

import argparse
import json
import os
import sys

import mujoco
import numpy as np
from etils import epath

sys.path.insert(0, os.getcwd())
from playground.open_duck_mini_v2 import base  # noqa: E402

SCENE = "playground/open_duck_mini_v2/xmls/scene_flat_terrain_backlash.xml"
FPS = 50
CLIP_S = 4.0
KEYPOINTS = [("site", "left_foot"), ("site", "right_foot"), ("body", "knee_and_ankle_assembly"),
             ("body", "knee_and_ankle_assembly_3"), ("body", "head_assembly")]
KEYPOINT_NAMES = ["left_foot", "right_foot", "left_knee", "right_knee", "head"]
SERVO_MAX_SPEED = 4.7  # rad/s: STS3215 7.4 V no-load 0.222 s / 60 deg (datasheet); measured peak on the robot ~4 rad/s

# Gait sources come from curation/clips/gen_gaits.sh (Placo, joint-limit-respecting settings): one SOURCE per walking
# direction (13), two VARIANTS per source (styles "normal" and "gentle"). Splits are drawn per source.
# Crouch: one SOURCE per depth (fraction of the deepest reachable crouch), two VARIANTS per source (fast / slow).
CROUCH_DEPTHS = [0.25, 0.5, 0.75, 1.0]
CROUCH_STYLES = {"fast": (0.8, 1.0), "slow": (1.5, 0.5)}  # (down / up duration s, hold s)
# Split by source, stratified by category; seeded and recorded in the manifest. Each category keeps >= 1 train source.
SPLIT_SEED = 7


def load_model():
    m = mujoco.MjModel.from_xml_string(epath.Path(SCENE).read_text(), assets=base.get_assets())
    return m, mujoco.MjData(m)


def quat_xyzw_to_wxyz(q):
    return np.concatenate([q[..., 3:4], q[..., :3]], axis=-1)


def quat_to_mat(q):  # wxyz
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat_log(R):
    c = np.clip((np.trace(R) - 1) / 2, -1, 1)
    th = np.arccos(c)
    if th < 1e-9:
        return np.zeros(3)
    return th / (2 * np.sin(th)) * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])


def body_velocities(pos, quat):
    """Body-frame linear and angular velocity from world positions and wxyz quaternions (central differences)."""
    T = len(pos)
    lin, ang = np.zeros((T, 3)), np.zeros((T, 3))
    for k in range(T):
        a, b = max(0, k - 1), min(T - 1, k + 1)
        dt = (b - a) / FPS
        R = quat_to_mat(quat[k])
        lin[k] = R.T @ (pos[b] - pos[a]) / dt
        ang[k] = mat_log(quat_to_mat(quat[a]).T @ quat_to_mat(quat[b])) / dt  # body frame
    return lin, ang


def keypoints(m, d, qadr, q):
    out = np.zeros((len(q), len(KEYPOINTS), 3))
    for k, qk in enumerate(q):
        d.qpos[:] = m.keyframe("home").qpos
        d.qpos[0:3] = 0
        d.qpos[3:7] = [1, 0, 0, 0]
        d.qpos[qadr] = qk
        mujoco.mj_kinematics(m, d)
        for i, (kind, name) in enumerate(KEYPOINTS):
            out[k, i] = d.site_xpos[m.site(name).id] if kind == "site" else d.xpos[m.body(name).id]
    return out


def resample(arr, rate, T):
    """Sample a 50 Hz array at times k * rate / 50 (k < T), linear interpolation."""
    src_t = np.arange(len(arr))
    t = np.arange(T) * rate
    t = np.clip(t, 0, len(arr) - 1)
    flat = arr.reshape(len(arr), -1)
    out = np.stack([np.interp(t, src_t, flat[:, j]) for j in range(flat.shape[1])], axis=1)
    return out.reshape((T,) + arr.shape[1:])


def gait_files(gait_dir):
    """{source_id: {style: path}} from gen_gaits.sh output names: <cat>__dx.._dy.._dth..__<style>_<vx>_<vy>_<wz>.json"""
    out = {}
    for f in sorted(os.listdir(gait_dir)):
        if not f.endswith(".json") or "__" not in f:
            continue
        cat, dirtag, rest = f[:-5].split("__")
        style = rest.split("_")[0]
        out.setdefault((cat, f"{cat}__{dirtag}"), {})[style] = os.path.join(gait_dir, f)
    return out


def gait_file(rec_dir, dx, dy, dth):
    for f in os.listdir(rec_dir):
        parts = f[:-5].split("_")
        if len(parts) == 4 and parts[0].isdigit():
            try:
                v = tuple(float(x) for x in parts[1:])
            except ValueError:
                continue
            if np.allclose(v, (dx, dy, dth), atol=1e-6):
                return os.path.join(rec_dir, f)
    raise FileNotFoundError((dx, dy, dth))


def gait_clip(m, d, qadr, path, rate):
    rec = json.load(open(path))
    off, fr = rec["Frame_offset"][0], np.array(rec["Frames"])
    j16 = fr[:, off["joints_pos"]: off["joints_pos"] + 16]
    q = np.concatenate([j16[:, 0:9], j16[:, 11:16]], axis=1)  # drop the antennas
    q[:, 5:9] = m.keyframe("home").ctrl[5:9]  # head at home (the generator holds its own fixed head pose)
    pos = fr[:, off["root_pos"]: off["root_pos"] + 3]
    quat = quat_xyzw_to_wxyz(fr[:, off["root_quat"]: off["root_quat"] + 4])
    contacts = fr[:, off["foot_contacts"]: off["foot_contacts"] + 2]
    T = int(CLIP_S * FPS)
    q, pos, contacts = resample(q, rate, T), resample(pos, rate, T), resample(contacts, rate, T) > 0.5
    quat = resample(quat, rate, T)
    quat /= np.linalg.norm(quat, axis=1, keepdims=True)
    pos = pos - np.array([pos[0, 0], pos[0, 1], 0.0])
    pos[:, 2] = grounded_height(m, d, qadr, q, quat, contacts)
    return q, pos, quat, contacts.astype(np.float32), rec["Placo"]


def grounded_height(m, d, qadr, q, quat, contacts):
    """Base height that puts the lowest sole of the feet in contact on the floor (z = 0), frame by frame. The
    generator's root frame is not the model's base origin, so its root height cannot be used directly."""
    soles = [m.site("left_foot").id, m.site("right_foot").id]
    z = np.zeros(len(q))
    for k in range(len(q)):
        d.qpos[:] = m.keyframe("home").qpos
        d.qpos[0:3] = 0
        d.qpos[3:7] = quat[k]
        d.qpos[qadr] = q[k]
        mujoco.mj_kinematics(m, d)
        sz = np.array([d.site_xpos[s][2] for s in soles])
        down = contacts[k] > 0.5
        z[k] = -(sz[down].min() if down.any() else sz.min())
    return z


def solve_crouch_legs(m, d, qadr, drop, iters=60):
    """Joint angles for the base lowered by `drop` (m) with the trunk upright and both soles fixed where they are at
    home (position and orientation): damped least squares on each leg's hip pitch, knee and ankle."""
    home = m.keyframe("home").qpos.copy()
    d.qpos[:] = home
    mujoco.mj_kinematics(m, d)
    mujoco.mj_comPos(m, d)
    sites = [m.site("left_foot").id, m.site("right_foot").id]
    tgt_p = [d.site_xpos[s].copy() for s in sites]
    tgt_R = [d.site_xmat[s].reshape(3, 3).copy() for s in sites]
    names = {0: ["left_hip_pitch", "left_knee", "left_ankle"], 1: ["right_hip_pitch", "right_knee", "right_ankle"]}
    q = home.copy()
    q[2] -= drop
    for _ in range(iters):
        d.qpos[:] = q
        mujoco.mj_kinematics(m, d)
        mujoco.mj_comPos(m, d)
        done = True
        for leg, s in enumerate(sites):
            dofs = [m.jnt_dofadr[m.joint(n).id] for n in names[leg]]
            qa = [m.jnt_qposadr[m.joint(n).id] for n in names[leg]]
            ep = tgt_p[leg] - d.site_xpos[s]
            eR = mat_log(tgt_R[leg] @ d.site_xmat[s].reshape(3, 3).T)
            e = np.concatenate([ep, eR])
            if np.linalg.norm(e) > 1e-6:
                done = False
            jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
            mujoco.mj_jacSite(m, d, jp, jr, s)
            J = np.vstack([jp, jr])[:, dofs]
            dq = np.linalg.solve(J.T @ J + 1e-6 * np.eye(3), J.T @ e)
            q[qa] += dq
        if done:
            break
    return q[qadr].copy(), q, float(np.linalg.norm(e))


def crouch_clip(m, d, qadr, depth, t_move, t_hold, max_drop):
    drop = depth * max_drop
    T = int(CLIP_S * FPS)
    t = np.arange(T) / FPS
    t0 = 0.4  # stand still first
    def minjerk(s):
        s = np.clip(s, 0, 1)
        return 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5
    down = minjerk((t - t0) / t_move)
    up = minjerk((t - t0 - t_move - t_hold) / t_move)
    frac = down - up
    q, pos = np.zeros((T, 14)), np.zeros((T, 3))
    home = m.keyframe("home").qpos
    cache = {}
    for k in range(T):
        key = round(float(frac[k]) * drop, 5)
        if key not in cache:
            cache[key] = solve_crouch_legs(m, d, qadr, key)
        qk, qfull, _ = cache[key]
        q[k] = qk
        pos[k] = [0, 0, home[2] - key]
    quat = np.tile(home[3:7], (T, 1))
    contacts = np.ones((T, 2), dtype=np.float32)
    return q, pos, quat, contacts, {"depth_m": drop, "depth_frac": depth, "move_s": t_move, "hold_s": t_hold}


def max_crouch_drop(m, d, qadr, margin=0.05):
    """Deepest drop whose IK solution keeps every joint `margin` rad inside its range."""
    lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
    best = 0.0
    for drop in np.arange(0.002, 0.12, 0.002):
        qk, _, err = solve_crouch_legs(m, d, qadr, drop)
        if err > 1e-3 or np.any(qk < lo + margin) or np.any(qk > hi - margin):
            break
        best = drop
    return best


def check_clip(m, d, qadr, q, qd, pos, quat, contacts):
    """Kinematic validity (S2.4): joint-limit margin, joint speed vs servo, sole penetration / float while in
    contact, foot-to-foot gap (self-collision proxy), hip-roll demand."""
    lo, hi = m.jnt_range[m.actuator_trnid[:, 0], 0], m.jnt_range[m.actuator_trnid[:, 0], 1]
    margin = float(np.min(np.minimum(q - lo, hi - q)))
    speed = float(np.max(np.abs(qd)))
    soles = [m.site("left_foot").id, m.site("right_foot").id]
    feet = [m.body("foot_assembly").id, m.body("foot_assembly_2").id]
    zs, gap = [], []
    for k in range(len(q)):
        d.qpos[:] = m.keyframe("home").qpos
        d.qpos[0:3] = pos[k]
        d.qpos[3:7] = quat[k]
        d.qpos[qadr] = q[k]
        mujoco.mj_kinematics(m, d)
        zs.append([d.site_xpos[s][2] for s in soles])
        gap.append(np.linalg.norm(d.xpos[feet[0]][:2] - d.xpos[feet[1]][:2]))
    zs = np.array(zs)
    stance_z = zs[contacts > 0.5]
    hr = [names_index("left_hip_roll"), names_index("right_hip_roll")]
    hip_roll = float(np.max(np.abs(q[:, hr] - m.keyframe("home").ctrl[hr])))
    rep = {
        "joint_limit_margin_rad": round(margin, 4),
        "peak_joint_speed_rad_s": round(speed, 3),
        "speed_vs_servo": round(speed / SERVO_MAX_SPEED, 3),
        "stance_sole_z_min_mm": round(1000 * float(stance_z.min() - zs[0].min()), 2) if len(stance_z) else None,
        "stance_sole_z_max_mm": round(1000 * float(stance_z.max() - zs[0].min()), 2) if len(stance_z) else None,
        "min_foot_gap_m": round(float(np.min(gap)), 4),
        "peak_hip_roll_dev_rad": round(hip_roll, 4),
    }
    stance_dev = float(np.max(np.abs(stance_z - np.median(stance_z)))) if len(stance_z) else 0.0
    rep["stance_sole_z_spread_mm"] = round(1000 * stance_dev, 2)
    # hard checks: every joint inside its range, foot gap (self-collision), stance soles neither sinking nor floating (> 5 mm);
    # joint speed above the servo's is reported, not rejected: dynamic trackability is what the scoring measures
    rep["pass"] = bool(margin > 0.0 and np.min(gap) > 0.08 and stance_dev < 0.005)
    rep["fast_for_servo"] = bool(speed > SERVO_MAX_SPEED)
    return rep


ACT = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch",
       "head_yaw", "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]


def names_index(n):
    return ACT.index(n)


def assign_splits(sources):
    """sources: list of (category, source_id). Per category, seeded shuffle; then 1 val and 1 test when the category
    has >= 3 sources, else 1 test when it has 2; the rest train."""
    rng = np.random.default_rng(SPLIT_SEED)
    split = {}
    cats = sorted(set(c for c, _ in sources))
    for c in cats:
        ids = [s for cc, s in sources if cc == c]
        rng.shuffle(ids)
        n = len(ids)
        n_val = 1 if n >= 3 else 0
        n_test = 1 if n >= 2 else 0
        if n >= 6:
            n_val, n_test = 2, 2
        for i, s in enumerate(ids):
            split[s] = "val" if i < n_val else ("test" if i < n_val + n_test else "train")
    return split


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gaits", required=True, help="output folder of gen_gaits.sh")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    m, d = load_model()
    qadr = np.array([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)])
    assert [m.actuator(i).name for i in range(m.nu)] == ACT

    gaits = gait_files(a.gaits)
    sources = list(gaits.keys())
    max_drop = max_crouch_drop(m, d, qadr, margin=0.03)
    print(f"deepest crouch keeping every joint 0.03 rad inside its range: {1000 * max_drop:.1f} mm")
    for dep in CROUCH_DEPTHS:
        sources.append(("crouch", f"crouch__depth{dep:.2f}"))
    split = assign_splits(sources)

    clips = []
    for cat, sid in sources:
        if cat == "crouch":
            dep = float(sid.split("depth")[1])
            variants = [(f"__{sty}", crouch_clip(m, d, qadr, dep, tm, th, max_drop))
                        for sty, (tm, th) in CROUCH_STYLES.items()]
        else:
            variants = [(f"__{sty}", gait_clip(m, d, qadr, path, 1.0)) for sty, path in sorted(gaits[(cat, sid)].items())]
        for suffix, (q, pos, quat, contacts, params) in variants:
            qd = np.gradient(q, 1 / FPS, axis=0)
            lin, ang = body_velocities(pos, quat)
            kp = keypoints(m, d, qadr, q)
            rep = check_clip(m, d, qadr, q, qd, pos, quat, contacts)
            prm = {k: v for k, v in params.items() if isinstance(v, (int, float, str))} if cat != "crouch" else params
            if cat != "crouch":
                prm = {"dx": prm.get("dx"), "dy": prm.get("dy"), "dtheta": prm.get("dtheta"), "style": suffix[2:],
                       "single_support_s": prm.get("single_support_duration"), "foot_lift_m": prm.get("walk_foot_height"),
                       "mean_vx": round(float(lin[:, 0].mean()), 4),
                       "mean_vy": round(float(lin[:, 1].mean()), 4), "mean_yaw_rate": round(float(ang[:, 2].mean()), 4)}
            clips.append(dict(id=sid + suffix, category=cat, source=sid, split=split[sid], params=prm, check=rep,
                              arrays=dict(q=q, qd=qd, base_pos=pos, base_quat=quat, lin_vel=lin, ang_vel=ang,
                                          contacts=contacts, keypts=kp)))
            print(f"  {split[sid]:5s} {sid + suffix:50s} {'pass' if rep['pass'] else 'FAIL'} "
                  f"margin {rep['joint_limit_margin_rad']:.3f} speed {rep['peak_joint_speed_rad_s']:5.2f}"
                  f"{'*' if rep['fast_for_servo'] else ' '} gap {rep['min_foot_gap_m']:.3f} "
                  f"stance spread {rep['stance_sole_z_spread_mm']:.1f} mm")

    kept = [c for c in clips if c["check"]["pass"]]
    T = max(len(c["arrays"]["q"]) for c in kept)
    def stack(key):
        arrs = [c["arrays"][key] for c in kept]
        out = np.zeros((len(arrs), T) + arrs[0].shape[1:], dtype=np.float32)
        for i, x in enumerate(arrs):
            out[i, : len(x)] = x
            out[i, len(x):] = x[-1]
        return out
    np.savez_compressed(os.path.join(a.out, "library.npz"), **{k: stack(k) for k in kept[0]["arrays"]},
                        length=np.array([len(c["arrays"]["q"]) for c in kept], dtype=np.int32))
    manifest = {
        "fps": FPS, "joints": ACT, "keypoints": KEYPOINT_NAMES, "split_seed": SPLIT_SEED,
        "max_crouch_drop_m": max_drop, "servo_max_speed_rad_s": SERVO_MAX_SPEED,
        "clips": [{k: c[k] for k in ("id", "category", "source", "split", "params", "check")} | {"index": i,
                  "length": len(c["arrays"]["q"])} for i, c in enumerate(kept)],
        "dropped_by_checks": [c["id"] for c in clips if not c["check"]["pass"]],
    }
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    splits = {s: split[s] for _, s in sources}
    json.dump(splits, open(os.path.join(a.out, "splits.json"), "w"), indent=1)
    n = {sp: sum(c["split"] == sp for c in kept) for sp in ("train", "val", "test")}
    print(f"library: {len(kept)} clips ({n}), {len(clips) - len(kept)} dropped by checks; {T} frames each (padded)")


if __name__ == "__main__":
    main()
