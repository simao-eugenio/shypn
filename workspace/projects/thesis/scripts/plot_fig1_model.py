#!/usr/bin/env python3
"""Figure 1 — B. subtilis sporulation SHPN model topology (v9, 41 places).

Embeds the existing bacillus_sporulation_v9.pdf into a figure and adds a
top-level title suitable for publication.

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/plot_fig1_model.py

Output: workspace/projects/thesis/manuscript/figures/fig1_model.png
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import subprocess, tempfile, os

SRC = pathlib.Path("workspace/projects/thesis/manuscript/figures/bacillus_sporulation_v9.pdf")
OUT = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig1_model.png")

# Rasterise PDF at high resolution via pdftoppm
with tempfile.TemporaryDirectory() as tmp:
    prefix = os.path.join(tmp, "fig1")
    subprocess.run(["pdftoppm", "-png", "-r", "200", str(SRC), prefix], check=True)
    png_file = prefix + "-1.png"
    img = mpimg.imread(png_file)

fig, ax = plt.subplots(figsize=(14, 9))
ax.imshow(img)
ax.axis("off")
fig.suptitle(
    r"$\it{B.\,subtilis}$ sporulation — Signal Hierarchical Petri Net (SHPN), v9"
    "\n"
    "41 places (circle: biological, hexagon: signal, square: parameter)"
    " · 36 transitions · 114 arcs",
    fontsize=11, y=0.99, va="top"
)

plt.subplots_adjust(top=0.93, bottom=0.01, left=0.01, right=0.99)
OUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT, dpi=200, bbox_inches="tight")
print("Saved:", OUT)
