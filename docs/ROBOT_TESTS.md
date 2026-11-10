# Tests that need the robot

Everything here needs the robot and a person at it. Everything else runs in simulation or on recorded logs.

**For every test:**
- duck on its stand;
- battery full;
- the recorder on (it is installed and logs every walker and get-up step to `~/duck_logs`).

| id | Test | Why | How | Time | Plan task |
|---|---|---|---|---|---|
| R1 | **Foot-switch mapping and polarity** | Robot logs suggest the left and right switches are **swapped**: agreement with kinematic stance is 46% as wired, 74% swapped (`results/foot_switch_check.md`). The deployed walker reads contacts, so a swap feeds it mirrored data | Runtime stopped. Run `feet_contacts.py` (prints `[left, right]` every 50 ms). Press the left sole, then the right; note which value changes and whether pressed reads `True` | 5 min | S1.3 |
| R2 | **Weigh the robot** | The model is 2.107 kg; the real mass was never measured. If they differ by more than 10%, the link masses get scaled | Kitchen scale: the whole robot; if easy, also the battery and the head | 10 min | S1.1 |
| R3 | **Joint ranges by hand** | The model limits the knee to ±1.57 rad, but the real knee reached 1.66 rad in the logs. This limit decides how deep a crouch the dataset can ask for (now only 8 mm) | Torque off (soft RB reset, or runtime stopped). Move each leg joint gently to its mechanical stops and read the positions (a read-only script prints all 14 at 10 Hz) | 20 min | S1.1 / S2.3 |
| R4 | **Single-joint step and chirp response** | Dead time, rise time and peak speed per joint group, compared with the same commands in sim. The core of "compare simulated vs measured joint responses" | A test script commands one joint group at a time with the duck hanging on the stand: steps of 0.1 / 0.3 rad, and a 0.5–5 Hz chirp. Recorded at 50 Hz; analysed against sim | 45 min | S1.2 |
| R5 | **IMU orientation check** | At the home pose the robot's accelerometer reads 17.5° away from the model's and 8% low. Unclear whether that is the mount or a calibration | Duck on a level surface at home, then rotated 90° nose-down, then 90° on its side; 5 s still in each. Read the raw IMU | 15 min | S1.1 |
| R6 | **Joint-offset calibration** (optional) | All 14 offsets in `duck_config.json` are 0.0 | Upstream `find_soft_offsets.py` | 20 min | S1.7 |
| R7 | **Hardware demo** (stretch, after the study) | Completion, joint tracking and loop timing on 2–3 conservative clips (slow walk, shallow crouch) | Deploy the tracking policy; record with the recorder | 1 h | S5.6 |

**Order for Wednesday:** R1, R2, R3, R5 (all quick and read-only or torque-off), then R4, the only one that moves
motors. R6 only if there is time. Scripts for R3 and R4 will be ready in `curation/robot/` before then.
