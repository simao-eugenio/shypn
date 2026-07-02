"""Verify F1 leak is caused by is_source=true on regen transitions.

Patches Source_ATP_regen and Source_ATP_stationary to is_source=false
and re-traces ATP/ADP for 60 s.
"""
import sys
import json
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

SRC = "workspace/projects/thesis/models/bacillus_sporulation_v4_thesis.shy"

m = json.loads(Path(SRC).read_text())
patched = 0
for t in m['transitions']:
    if t['name'] in ('Source_ATP_regen', 'Source_ATP_stationary'):
        if t.get('is_source'):
            t['is_source'] = False
            patched += 1
print(f"Patched {patched} transitions: is_source true → false")

with tempfile.NamedTemporaryFile("w", suffix=".shy", delete=False) as f:
    json.dump(m, f)
    tmp = f.name

model = DocumentModel.load_from_file(tmp)
atp = next(p for p in model.places if p.name == "ATP_pool")
adp = next(p for p in model.places if p.name == "ADP_pool")
print(f"Initial: ATP={atp.tokens}, ADP={adp.tokens}, sum={atp.tokens + adp.tokens}")

ctrl = SimulationController(model)
duration, dt = 60.0, 0.5
n = int(duration / dt)
prev = atp.tokens + adp.tokens
print(f"\n{'t(s)':>6} {'ATP':>10} {'ADP':>10} {'sum':>12} {'Δsum':>10}")
print("-" * 56)
for i in range(n):
    ctrl.step(time_step=dt)
    s = atp.tokens + adp.tokens
    if i % 10 == 0 or i == n - 1:
        print(f"{(i+1)*dt:>6.1f} {atp.tokens:>10.2f} {adp.tokens:>10.2f} {s:>12.2f} {s - prev:>+10.3f}")
    prev = s
print(f"\nFinal sum: {atp.tokens + adp.tokens:.2f}  (initial 5995)")
print(f"Drift: {atp.tokens + adp.tokens - 5995:+.3f}  ({(atp.tokens + adp.tokens - 5995)/5995*100:+.2f}%)")
