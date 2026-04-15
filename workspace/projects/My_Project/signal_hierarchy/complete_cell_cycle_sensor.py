#!/usr/bin/env python3
"""
Complete the cell cycle sensor module by adding missing transitions.

Currently has:
- T34: FtsZ_Production (source)
- T33: DnaA_Decay (sink)

Needs to add:
- DnaA_Production (source → P25)
- FtsZ_Decay (P26 → sink)
- Cell_Cycle_Phase_Update (P25, P26 test arcs → P27)
- Cell_Cycle_Phase_Decay (P27 → sink)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel

# Load model
model_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
print(f"Loading model from {model_path}...")
model = DocumentModel.load_from_file(model_path)

print(f"Current model: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")
print("=" * 80)

# Find the cell cycle sensor places
p25 = next(p for p in model.places if p.id == 'P25')  # DnaA
p26 = next(p for p in model.places if p.id == 'P26')  # FtsZ
p27 = next(p for p in model.places if p.id == 'P27')  # Cell_Cycle_Phase

print(f"Found cell cycle sensor places:")
print(f"  P25: {p25.name} (tokens={p25.tokens})")
print(f"  P26: {p26.name} (tokens={p26.tokens})")
print(f"  P27: {p27.name} (tokens={p27.tokens})")

# Create DnaA_Production (source)
print(f"\n✓ Creating DnaA_Production...")
t_dnaa_prod = model.create_transition(x=650, y=350, label="DnaA_Production")
t_dnaa_prod.name = "DnaA_Production"
t_dnaa_prod.transition_type = "stochastic"
t_dnaa_prod.rate = "0.4"  # Constant production
t_dnaa_prod.is_source = True
print(f"  {t_dnaa_prod.id}: source transition, rate=0.4")

# Arc: DnaA_Production → P25
arc_dnaa = model.create_arc(t_dnaa_prod, p25)
print(f"  Arc {arc_dnaa.id}: {t_dnaa_prod.id} → P25 (normal)")

# Create FtsZ_Decay (sink)
print(f"\n✓ Creating FtsZ_Decay...")
t_ftsz_decay = model.create_transition(x=650, y=450, label="FtsZ_Decay")
t_ftsz_decay.name = "FtsZ_Decay"
t_ftsz_decay.transition_type = "stochastic"
t_ftsz_decay.rate = "0.05 * P26"  # First-order decay
t_ftsz_decay.is_sink = True
print(f"  {t_ftsz_decay.id}: sink transition, rate=0.05*P26")

# Arc: P26 → FtsZ_Decay
arc_ftsz = model.create_arc(p26, t_ftsz_decay)
print(f"  Arc {arc_ftsz.id}: P26 → {t_ftsz_decay.id} (normal)")

# Create Cell_Cycle_Phase_Update
print(f"\n✓ Creating Cell_Cycle_Phase_Update...")
t_cc_update = model.create_transition(x=850, y=400, label="Cell_Cycle_Phase_Update")
t_cc_update.name = "Cell_Cycle_Phase_Update"
t_cc_update.transition_type = "stochastic"
# Rate: High DnaA (early) and low FtsZ (early) → high P27 (early cycle signal)
# Formula: rate = DnaA / (1 + FtsZ)
t_cc_update.rate = "P25 / (1.0 + P26)"
print(f"  {t_cc_update.id}: stochastic transition, rate = P25 / (1.0 + P26)")

# Test arcs: P25 → update and P26 → update (read levels without consuming)
arc_p25_update = model.create_arc(p25, t_cc_update, weight=0, arc_type='test')
print(f"  Arc {arc_p25_update.id}: P25 → {t_cc_update.id} (test)")

arc_p26_update = model.create_arc(p26, t_cc_update, weight=0, arc_type='test')
print(f"  Arc {arc_p26_update.id}: P26 → {t_cc_update.id} (test)")

# Normal arc: update → P27
arc_update_p27 = model.create_arc(t_cc_update, p27)
print(f"  Arc {arc_update_p27.id}: {t_cc_update.id} → P27 (normal)")

# Create Cell_Cycle_Phase_Decay (sink)
print(f"\n✓ Creating Cell_Cycle_Phase_Decay...")
t_cc_decay = model.create_transition(x=1050, y=400, label="Cell_Cycle_Phase_Decay")
t_cc_decay.name = "Cell_Cycle_Phase_Decay"
t_cc_decay.transition_type = "stochastic"
t_cc_decay.rate = "0.1 * P27"  # First-order decay
t_cc_decay.is_sink = True
print(f"  {t_cc_decay.id}: sink transition, rate = 0.1 * P27")

# Arc: P27 → decay
arc_p27_decay = model.create_arc(p27, t_cc_decay)
print(f"  Arc {arc_p27_decay.id}: P27 → {t_cc_decay.id} (normal)")

# Set initial conditions for cell cycle sensor
print(f"\n✓ Setting initial conditions...")
p25.tokens = 8.0   # Early cycle (high DnaA)
p25.initial_marking = 8.0
p26.tokens = 2.0   # Early cycle (low FtsZ)
p26.initial_marking = 2.0
p27.tokens = 4.0   # Will equilibrate based on P25/P26
p27.initial_marking = 4.0

print(f"  P25 (DnaA) = {p25.tokens}")
print(f"  P26 (FtsZ) = {p26.tokens}")
print(f"  P27 (Cell_Cycle_Phase) = {p27.tokens}")

# Save model
print(f"\n{'=' * 80}")
print(f"Saving updated model...")
model.save_to_file(model_path)

print(f"\n✅ Cell cycle sensor completed successfully!")
print(f"\nFinal model: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")

print(f"\n{'=' * 80}")
print("CELL CYCLE SENSOR MODULE:")
print("  Production:")
print(f"    {t_dnaa_prod.id}: source → P25 (DnaA), rate=0.4")
print(f"    T34: source → P26 (FtsZ), rate=? [already exists]")
print("  Integration:")
print(f"    {t_cc_update.id}: P25, P26 (test) → P27, rate = P25/(1+P26)")
print("  Decay:")
print(f"    T33: P25 → sink [already exists]")
print(f"    {t_ftsz_decay.id}: P26 → sink, rate = 0.05*P26")
print(f"    {t_cc_decay.id}: P27 → sink, rate = 0.1*P27")
print(f"{'=' * 80}")
print("\nBiological interpretation:")
print("  High DnaA + Low FtsZ → High P27 (early cell cycle)")
print("  Low DnaA + High FtsZ → Low P27 (late cell cycle)")
print("=" * 80)
