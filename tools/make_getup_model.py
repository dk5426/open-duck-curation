"""Build the get-up model: upstream's backlash robot + one collision box per body, so the whole duck can touch the floor.

Upstream lets only the two foot soles collide. Here every body that carries visual meshes (except the two feet, whose
soles already collide) gets a box fitted to its mesh vertices in the body frame, shrunk slightly so it stays inside
the visual shell. Boxes use a separate collision bit: box contype 0 / conaffinity 2, floor contype 1 -> 3. Boxes touch
the floor only (never each other or the soles); the soles keep contype 1 / conaffinity 1 and still touch the floor.
Explicit <inertial> elements are untouched and the boxes have zero density, so mass and inertia are unchanged.

Writes into playground/open_duck_mini_v2/xmls/:
  open_duck_mini_v2_backlash_getup.xml   robot with collision boxes
  scene_getup_backlash.xml               flat-terrain backlash scene including it, floor contype 3

Run from Open_Duck_Playground:  uv run python ../tools/make_getup_model.py
"""

import re

import mujoco
import numpy as np
from etils import epath

from playground.open_duck_mini_v2 import base

XMLS = epath.Path("playground/open_duck_mini_v2/xmls")
SHRINK = 0.9
SKIP = {"base", "foot_assembly", "foot_assembly_2"}

m = mujoco.MjModel.from_xml_string((XMLS / "scene_flat_terrain_backlash.xml").read_text(), assets=base.get_assets())
boxes = {}
for b in range(1, m.nbody):
    name = m.body(b).name
    if name in SKIP or name == "floor":
        continue
    pts = []
    for g in np.where((m.geom_bodyid == b) & (m.geom_type == mujoco.mjtGeom.mjGEOM_MESH))[0]:
        mid = m.geom_dataid[g]
        v = m.mesh_vert[m.mesh_vertadr[mid]: m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
        R = np.zeros(9)
        mujoco.mju_quat2Mat(R, m.geom_quat[g])
        pts.append(v @ R.reshape(3, 3).T + m.geom_pos[g])
    if not pts:
        continue
    pts = np.concatenate(pts)
    lo, hi = pts.min(0), pts.max(0)
    half = np.maximum((hi - lo) / 2 * SHRINK, 0.004)
    boxes[name] = ((lo + hi) / 2, half)

src = (XMLS / "open_duck_mini_v2_backlash.xml").read_text()
out = src
for name, (c, h) in boxes.items():
    tag = re.search(r'<body name="%s"[^>]*>' % re.escape(name), out)
    geom = ('\n<geom name="col_%s" type="box" pos="%.5f %.5f %.5f" size="%.5f %.5f %.5f" contype="0" conaffinity="2" '
            'group="4" density="0" rgba="1 0.3 0.3 0.4"/>' % (name, *c, *h))
    out = out[: tag.end()] + geom + out[tag.end():]
(XMLS / "open_duck_mini_v2_backlash_getup.xml").write_text(out)

scene = (XMLS / "scene_flat_terrain_backlash.xml").read_text()
scene = scene.replace('<include file="open_duck_mini_v2_backlash.xml"/>',
                      '<include file="open_duck_mini_v2_backlash_getup.xml"/>')
scene = re.sub(r'(<geom name="floor"[^>]*?)contype="1"', r'\1contype="3"', scene)
(XMLS / "scene_getup_backlash.xml").write_text(scene)

m2 = mujoco.MjModel.from_xml_string((XMLS / "scene_getup_backlash.xml").read_text(), assets=base.get_assets())
print(f"added {len(boxes)} boxes; mass {m.body_subtreemass[1]:.4f} -> {m2.body_subtreemass[1]:.4f} kg;",
      f"floor contype {m2.geom_contype[m2.geom('floor').id]}; ngeom {m.ngeom} -> {m2.ngeom}")
for name, (c, h) in boxes.items():
    print(f"  {name:32s} half-size mm {np.round(h * 1000, 1)}")
