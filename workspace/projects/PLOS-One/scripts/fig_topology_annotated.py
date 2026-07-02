"""
Figure: B. subtilis SHyPN — App-exported topology with G_s/G_E layer annotations
==================================================================================
Loads the PDF exported directly from the SHyPN GUI, converts it to a high-res
raster, then overlays:
  - Coloured dashed rectangles marking the G_s (decision) and G_E (execution) layers
  - Layer labels
  - Arc-type legend
  - Critical PreemptionCheck bridge annotation

Coordinate mapping:
  The PDFExporter translates: pdf_xy = world_xy - (min_x, min_y) + padding
  padding = max(content_w, content_h) * padding_percent / 100
  We replicate this transform to place overlay patches in image-pixel coordinates.

Output:
  workspace/projects/thesis/manuscript/figures/fig_topology_annotated.pdf
  workspace/projects/thesis/manuscript/figures/fig_topology_annotated.png
"""

import json
import pathlib
import subprocess
import tempfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
import matplotlib.image as mpimg

REPO     = pathlib.Path(__file__).resolve().parents[4]
SHY_FILE = REPO / "workspace/projects/thesis/models/bacillus_sporulation_v7_thesis.shy"
PDF_IN   = REPO / "workspace/projects/thesis/manuscript/figures/bacillus_sporulation_v7_thesis.pdf"
OUT_DIR  = REPO / "workspace/projects/thesis/manuscript/figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. Rasterise the app PDF at 250 dpi ───────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    prefix = pathlib.Path(td) / "page"
    subprocess.run(
        ["pdftoppm", "-r", "150", "-png", str(PDF_IN), str(prefix)],
        check=True
    )
    png_path = sorted(pathlib.Path(td).glob("page*.png"))[0]
    canvas_img = mpimg.imread(str(png_path))

img_h, img_w = canvas_img.shape[:2]

# ── 2. Replicate the PDFExporter coordinate transform ─────────────────────
d = json.loads(SHY_FILE.read_text())

# Gather all object positions (matching BaseExporter.calculate_bounds logic)
# The exporter uses place radius and transition width/height for bounds.
# For simplicity we use the centre coords + a small margin.
PLACE_R  = 50   # world units (matches renderer default)
TRANS_W  = 30
TRANS_H  = 80

xs_min, xs_max = [], []
ys_min, ys_max = [], []

for p in d["places"]:
    x, y = p.get("x", 0), p.get("y", 0)
    r = p.get("radius", PLACE_R)
    xs_min.append(x - r); xs_max.append(x + r)
    ys_min.append(y - r); ys_max.append(y + r)

for t in d["transitions"]:
    x, y = t.get("x", 0), t.get("y", 0)
    w = t.get("width",  TRANS_W) / 2
    h = t.get("height", TRANS_H) / 2
    xs_min.append(x - w); xs_max.append(x + w)
    ys_min.append(y - h); ys_max.append(y + h)

min_x, max_x = min(xs_min), max(xs_max)
min_y, max_y = min(ys_min), max(ys_max)

content_w = max_x - min_x
content_h = max_y - min_y
PADDING_PCT = 10.0
padding = max(content_w, content_h) * PADDING_PCT / 100

pdf_w = content_w + 2 * padding
pdf_h = content_h + 2 * padding

# Scale: image pixels per PDF point (pdf points == world units here, zoom=1.0)
scale_x = img_w / pdf_w
scale_y = img_h / pdf_h

def world_to_img(wx, wy):
    """Convert world coordinates to image pixel coordinates."""
    px = (wx - min_x + padding) * scale_x
    py = (wy - min_y + padding) * scale_y
    return px, py

# ── 3. Compute G_s and G_E bounding boxes in world coords ─────────────────
GS_TRANSITION_IDS = {"T1", "T2", "T3", "T4", "T5", "T7"}
# G_s places: those connected to G_s transitions only (phosphorelay + KinA)
GS_PLACE_IDS = {"P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P14"}  # KinA, Spo0F/A, RapA, Spo0B, Septum

t_coords = {t["id"]: (t.get("x", 0), t.get("y", 0)) for t in d["transitions"]}
p_coords = {p["id"]: (p.get("x", 0), p.get("y", 0)) for p in d["places"]}

def region_bounds(ids, coord_dict, margin=120):
    xs = [coord_dict[i][0] for i in ids if i in coord_dict]
    ys = [coord_dict[i][1] for i in ids if i in coord_dict]
    return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin

gs_wx0, gs_wy0, gs_wx1, gs_wy1 = region_bounds(
    GS_TRANSITION_IDS | GS_PLACE_IDS, {**t_coords, **p_coords}, margin=130)

# G_E: continuous transitions (excluding housekeeping sources T19-T23)
GE_TRANSITION_IDS = {"T6","T8","T9","T10","T11","T12","T13","T14","T15","T16","T17","T18"}
GE_PLACE_IDS = {"P13","P15","P16","P17","P18","P19","P20","P21","P22","P23","P24"}
ge_wx0, ge_wy0, ge_wx1, ge_wy1 = region_bounds(
    GE_TRANSITION_IDS | GE_PLACE_IDS, {**t_coords, **p_coords}, margin=130)

# Convert to image pixels
gs_ix0, gs_iy0 = world_to_img(gs_wx0, gs_wy0)
gs_ix1, gs_iy1 = world_to_img(gs_wx1, gs_wy1)
ge_ix0, ge_iy0 = world_to_img(ge_wx0, ge_wy0)
ge_ix1, ge_iy1 = world_to_img(ge_wx1, ge_wy1)

# ── 4. Build figure ────────────────────────────────────────────────────────
DPI = 100
fig, ax = plt.subplots(figsize=(img_w / DPI, img_h / DPI), dpi=DPI)
ax.imshow(canvas_img, origin="upper")
ax.axis("off")
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Helper: draw annotation rectangle in image-pixel coords
def img_rect(x0, y0, x1, y1, color, alpha_fill=0.08, lw=2.5, ls="--"):
    w = x1 - x0
    h = y1 - y0
    ax.add_patch(mpatches.FancyBboxPatch(
        (x0, y0), w, h,
        boxstyle="round,pad=8",
        fc=color, ec=color, alpha=alpha_fill,
        lw=0, zorder=3
    ))
    ax.add_patch(mpatches.FancyBboxPatch(
        (x0, y0), w, h,
        boxstyle="round,pad=8",
        fc="none", ec=color, lw=lw, ls=ls, zorder=4
    ))

# G_s region (orange)
img_rect(gs_ix0, gs_iy0, gs_ix1, gs_iy1, "#e65100", alpha_fill=0.07)
ax.text((gs_ix0 + gs_ix1) / 2, gs_iy0 - 18,
        r"$G_s$  — Decision layer  (stochastic)",
        ha="center", va="bottom", fontsize=10, fontweight="bold",
        color="#e65100", zorder=5)

# G_E region (blue)
img_rect(ge_ix0, ge_iy0, ge_ix1, ge_iy1, "#1565c0", alpha_fill=0.07)
ax.text((ge_ix0 + ge_ix1) / 2, ge_iy0 - 18,
        r"$G_E$  — Execution layer  (continuous)",
        ha="center", va="bottom", fontsize=10, fontweight="bold",
        color="#1565c0", zorder=5)

# PreemptionCheck bridge annotation (Septum → σF gate)
sept_ix, sept_iy = world_to_img(*p_coords["P14"])
sigf_ix, sigf_iy = world_to_img(*p_coords["P15"])
ax.annotate("", xy=(sigf_ix, sigf_iy), xytext=(sept_ix, sept_iy),
            arrowprops=dict(arrowstyle="-|>", color="#bf360c", lw=2.2,
                            connectionstyle="arc3,rad=-0.35"),
            zorder=6)
mid_ix = (sept_ix + sigf_ix) / 2 - 55
mid_iy = (sept_iy + sigf_iy) / 2 - 30
ax.text(mid_ix, mid_iy, "PreemptionCheck\n(Septum → $G_E$)",
        fontsize=7.5, color="#bf360c", ha="center", va="center",
        fontweight="bold", style="italic", zorder=7)

# ── 5. Legend ──────────────────────────────────────────────────────────────
handles = [
    mpatches.Patch(fc="#fff3e0", ec="#e65100", ls="--", lw=1.5,
                   label=r"$G_s$  decision layer"),
    mpatches.Patch(fc="#e3f2fd", ec="#1565c0", ls="--", lw=1.5,
                   label=r"$G_E$  execution layer"),
    Line2D([0], [0], color="#bf360c", lw=2.0, label="PreemptionCheck bridge"),
]
ax.legend(handles=handles,
          loc="lower center",
          bbox_to_anchor=(0.5, 0.01),
          ncol=3, fontsize=9,
          framealpha=0.95, edgecolor="0.65",
          handlelength=2.0, borderpad=0.7)

# ── 6. Save ────────────────────────────────────────────────────────────────
for ext in ("png",):   # PDF blocked by .gitignore; PNG is enough
    out = OUT_DIR / f"fig_topology_annotated.{ext}"
    fig.savefig(out, dpi=DPI, bbox_inches="tight", pad_inches=0)
    print(f"Saved: {out}")

plt.close(fig)
