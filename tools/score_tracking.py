import json, os, sys, numpy as np
names = sys.argv[2:] or ["best2", "ours172M", "ours193M", "ours258M", "ours279M", "ours300M"]
segs = ["fwd", "back", "left", "right", "yaw_l", "yaw_r", "fwd_yaw"]
print("policy      no-backlash  backlash   mean   (mean |achieved-cmd|/|cmd| over 7 commands; lower = better; 1.0 = no motion)")
for n in names:
    d = json.load(open(n if n.endswith(".json") else f"{sys.argv[1]}/{n}.json"))
    out = []
    for sc in ["scene_flat_terrain.xml", "scene_flat_terrain_backlash.xml"]:
        errs = []
        for s in segs:
            seg = d["scenes"][sc]["segments"][s]
            cmd = np.array(seg["cmd"])
            got = np.array([[r["vx"], r["vy"], r["wz"]] for r in seg["runs"] if r["survived"]]).mean(0)
            m = cmd != 0
            errs.append(np.mean(np.abs(got[m] - cmd[m]) / np.abs(cmd[m])))
        out.append(np.mean(errs))
    print(f"{os.path.basename(n).replace('.json', ''):10s} {out[0]:12.3f} {out[1]:9.3f} {np.mean(out):7.3f}")
