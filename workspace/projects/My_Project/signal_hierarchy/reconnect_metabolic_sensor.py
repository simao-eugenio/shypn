#!/usr/bin/env python3
"""
Reconnect P22 (cAMP) and P23 (ppGpp) to create functional metabolic sensor.

Adds:
- T40: cAMP_Production (source → P22)
- T41: ppGpp_Production (source → P23)  
- T32: Metabolic_Health_Update (P22, P23 test arcs → P24)
- T42: Metabolic_Health_Decay (P24 → sink)
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

# Find the metabolic sensor places
p22 = next(p for p in model.places if p.id == 'P22')  # cAMP
p23 = next(p for p in model.places if p.id == 'P23')  # ppGpp
p24 = next(p for p in model.places if p.id == 'P24')  # Metabolic_Health

print(f"Found metabolic sensor places:")
print(f"  P22: {p22.name} (tokens={p22.tokens})")
print(f"  P23: {p23.name} (tokens={p23.tokens})")
print(f"  P24: {p24.name} (tokens={p24.tokens})")

# Create T40: cAMP_Production (source)
print(f"\n✓ Creating T40 (cAMP_Production)...")
t40 = model.create_transition(x=150, y=350, label="cAMP_Production")
# ID is auto-generated, just update name and label
t40.name = "cAMP_Production"
t40.transition_type = "stochastic"
t40.rate = "0.5"  # Constant production
t40.is_source = True
print(f"  {t40.id}: source transition, rate=0.5")

# Arc: T40 → P22 (create_arc makes normal arcs by default)
arc_t40_p22 = model.create_arc(t40, p22)
print(f"  Arc {arc_t40_p22.id}: {t40.id} → P22 (normal, weight=1)")

# Create T41: ppGpp_Production (source)
print(f"\n✓ Creating T41 (ppGpp_Production)...")
t41 = model.create_transition(x=150, y=450, label="ppGpp_Production")
t41.name = "ppGpp_Production"
t41.transition_type = "stochastic"
t41.rate = "0.3"  # Constant production (lower than cAMP)
t41.is_source = True
print(f"  {t41.id}: source transition, rate=0.3")

# Arc: T41 → P23
arc_t41_p23 = model.create_arc(t41, p23)
print(f"  Arc {arc_t41_p23.id}: {t41.id} → P23 (normal, weight=1)")

# Create T32: Metabolic_Health_Update
print(f"\n✓ Creating T32 (Metabolic_Health_Update)...")
t32 = model.create_transition(x=350, y=400, label="Metabolic_Health_Update")
t32.name = "Metabolic_Health_Update"
t32.transition_type = "stochastic"
# Rate: High cAMP (good) and low ppGpp (good) → high metabolic health
# Formula: rate = cAMP / (1 + ppGpp)
t32.rate = "P22 / (1.0 + P23)"
print(f"  {t32.id}: stochastic transition, rate = P22 / (1.0 + P23)")

# Test arcs: P22 → T32 and P23 → T32 (read levels without consuming)
arc_p22_t32 = model.create_arc(p22, t32, weight=0, arc_type='test')
print(f"  Arc {arc_p22_t32.id}: P22 → {t32.id} (test, threshold=0)")

arc_p23_t32 = model.create_arc(p23, t32, weight=0, arc_type='test')
print(f"  Arc {arc_p23_t32.id}: P23 → {t32.id} (test, threshold=0)")

# Normal arc: T32 → P24
arc_t32_p24 = model.create_arc(t32, p24)
print(f"  Arc {arc_t32_p24.id}: {t32.id} → P24 (normal, weight=1)")

# Create T42: Metabolic_Health_Decay (sink)
print(f"\n✓ Creating T42 (Metabolic_Health_Decay)...")
t42 = model.create_transition(x=550, y=400, label="Metabolic_Health_Decay")
t42.name = "Metabolic_Health_Decay"
t42.transition_type = "stochastic"
t42.rate = "0.1 * P24"  # First-order decay
t42.is_sink = True
print(f"  {t42.id}: sink transition, rate = 0.1 * P24")

# Arc: P24 → T42
arc_p24_t42 = model.create_arc(p24, t42)
print(f"  Arc {arc_p24_t42.id}: P24 → T42 (normal, weight=1)")

# Set initial conditions for metabolic sensor
print(f"\n✓ Setting initial conditions...")
p22.tokens = 10.0  # Moderate cAMP
p22.initial_marking = 10.0
p23.tokens = 5.0   # Moderate ppGpp  
p23.initial_marking = 5.0
p24.tokens = 2.0   # Will equilibrate based on P22/P23
p24.initial_marking = 2.0

print(f"  P22 (cAMP) = {p22.tokens}")
print(f"  P23 (ppGpp) = {p23.tokens}")
print(f"  P24 (Metabolic_Health) = {p24.tokens}")

# Save model
print(f"\n{'=' * 80}")
print(f"Saving updated model...")
model.save_to_file(model_path)

print(f"\n✅ Metabolic sensor reconnected successfully!")
print(f"\nFinal model: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")

print(f"\n{'=' * 80}")
print("METABOLIC SENSOR MODULE:")
print("  Production:")
print(f"    {t40.id}: source → P22 (cAMP), rate=0.5")
print(f"    {t41.id}: source → P23 (ppGpp), rate=0.3")
print("  Integration:")
print(f"    {t32.id}: P22, P23 (test) → P24, rate = P22/(1+P23)")
print("  Decay:")
print(f"    {t42.id}: P24 → sink, rate = 0.1*P24")
print(f"{'=' * 80}")
