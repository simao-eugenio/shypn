"""Trace ATP/ADP marking on actual v4 model for first 60 s.

Tracks every transition firing's net effect on ATP_pool + ADP_pool
to localize the F1 leak source.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

MODEL = "workspace/projects/thesis/models/bacillus_sporulation_v4_thesis.shy"

model = DocumentModel.load_from_file(MODEL)
atp = next(p for p in model.places if p.name == "ATP_pool")
adp = next(p for p in model.places if p.name == "ADP_pool")

print(f"Initial: ATP={atp.tokens}, ADP={adp.tokens}, sum={atp.tokens + adp.tokens}")

ctrl = SimulationController(model)

# Run for 60 s in 1 s chunks, printing ATP/ADP each step
duration = 60.0
dt = 0.5
n_steps = int(duration / dt)

prev_sum = atp.tokens + adp.tokens
print(f"\n{'t(s)':>6} {'ATP':>10} {'ADP':>10} {'sum':>12} {'Δsum':>10}")
print("-" * 56)
for i in range(n_steps):
    ctrl.step(time_step=dt)
    s = atp.tokens + adp.tokens
    delta = s - prev_sum
    if i % 4 == 0 or abs(delta) > 1.0:
        print(f"{(i+1)*dt:>6.1f} {atp.tokens:>10.2f} {adp.tokens:>10.2f} {s:>12.2f} {delta:>+10.3f}")
    prev_sum = s

print(f"\nFinal sum: {atp.tokens + adp.tokens:.2f}  (initial 5995, expected ~5995 for conservation)")
