"""Read-only: firmware / model version registers 0-4 of the duck's 14 servos (no writes)."""
import rustypot

io = rustypot.Sts3215PyController("/dev/ttyACM0", 1000000, 0.05)
names = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch",
         "head_yaw", "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
ids = [20, 21, 22, 23, 24, 30, 31, 32, 33, 10, 11, 12, 13, 14]
print(f"{'joint':16s} {'id':>3s}  {'regs 0-4':24s} {'firmware':>9s} {'servo':>6s}  read_model")
for n, i in zip(names, ids):
    try:
        raw = list(io.read_raw_data(i, 0, 5))
        fw, sv = f"{raw[0]}.{raw[1]}", f"{raw[3]}.{raw[4]}"
    except Exception as e:
        raw, fw, sv = f"ERR {e}", "-", "-"
    try:
        mdl = io.read_model(i)
    except Exception as e:
        mdl = f"ERR {e}"
    print(f"{n:16s} {i:3d}  {str(raw):24s} {fw:>9s} {sv:>6s}  {mdl}")
