"""Read-only: present bus voltage of the duck's 14 servos (no writes)."""
import rustypot

io = rustypot.Sts3215PyController("/dev/ttyACM0", 1000000, 0.05)
v = io.sync_read_present_voltage([20, 21, 22, 23, 24, 30, 31, 32, 33, 10, 11, 12, 13, 14])
print("bus voltage at rest (V):", sorted(set(round(x * 0.1, 1) for x in v)))
