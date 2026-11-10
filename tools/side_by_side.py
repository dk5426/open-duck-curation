"""Render two walker policies through the same showcase schedule (duck_eval.render_gif) and put them side by side.
  MUJOCO_GL=osmesa uv run python ../tools/side_by_side.py A.onnx "label A" B.onnx "label B" out.gif
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from duck_eval import Runner, render_gif  # noqa: E402

a, la, b, lb, out = sys.argv[1:6]
scene = "playground/open_duck_mini_v2/xmls/scene_flat_terrain_backlash.xml"
ref = "playground/open_duck_mini_v2/data/polynomial_coefficients.pkl"
tmp = []
for onnx, label in [(a, la), (b, lb)]:
    path = out.replace(".gif", f"_{len(tmp)}.gif")
    render_gif(Runner(scene, onnx, ref), path, label, fps=10, size=(400, 320))
    tmp.append(Image.open(path))
frames = []
for i in range(min(t.n_frames for t in tmp)):
    canvas = Image.new("RGB", (800, 320))
    for k, t in enumerate(tmp):
        t.seek(i)
        canvas.paste(t.convert("RGB"), (400 * k, 0))
    frames.append(canvas.quantize(colors=128))
frames[0].save(out, save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=True)
for t in tmp:
    os.remove(t.filename)
print("wrote", out, len(frames), "frames")
