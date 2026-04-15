#!/usr/bin/env python3
"""
Build Lambda Phage Hierarchical Model v3 - Phase 2: Multi-Signal Integration
Adds metabolic sensor, cell cycle sensor, CIII, and CI cleavage mechanisms.
"""

import sys
sys.path.insert(0, 'src')
import json
from shypn.data.canvas.document_model import DocumentModel

print("="*70)
print("Building Lambda Hierarchical v3 - Phase 2: Multi-Signal Integration")
print("="*70)

# Load base model (v2)
base_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v2.shy'
print(f"\n📂 Loading base model: {base_path}")
doc = DocumentModel.load_from_file(base_path)

print(f"✓ Loaded: {len(doc.places)} places, {len(doc.transitions)} transitions, {len(doc.arcs)} arcs")

# First, fix CII module names (P19-P21, T29-T31)
print("\n🔧 Renaming CII module components...")
for p in doc.places:
    if p.id == 'P19':
        p.name = 'CII_Gene'
        print(f"  P19 → CII_Gene")
    elif p.id == 'P20':
        p.name = 'CII_mRNA'
        print(f"  P20 → CII_mRNA")
    elif p.id == 'P21':
        p.name = 'CII_Protein'
        print(f"  P21 → CII_Protein [SIGNAL]")

for t in doc.transitions:
    if t.id == 'T29':
        t.name = 'CII_Transcription'
        print(f"  T29 → CII_Transcription")
    elif t.id == 'T30':
        t.name = 'CII_Translation'
        print(f"  T30 → CII_Translation")
    elif t.id == 'T31':
        t.name = 'CII_Degradation'
        print(f"  T31 → CII_Degradation")

# ============================================================================
# STEP 1: Metabolic Sensor Module (L0-C1B)
# ============================================================================
print("\n" + "="*70)
print("STEP 1: Adding Metabolic Sensor Module (L0-C1B)")
print("="*70)

# P22: cAMP (cyclic AMP, high when glucose low)
p22 = doc.create_place(x=100, y=550, label="cAMP")
p22.name = "cAMP"
p22.initial_marking = 5.0  # Basal level
p22.tokens = 5.0
print(f"✓ Created {p22.id}: {p22.name} (basal cAMP)")

# P23: ppGpp (stringent response, high under amino acid starvation)
p23 = doc.create_place(x=200, y=550, label="ppGpp")
p23.name = "ppGpp"
p23.initial_marking = 2.0  # Low stress initially
p23.tokens = 2.0
print(f"✓ Created {p23.id}: {p23.name} (low stress)")

# P24: Metabolic_Health (signal place)
p24 = doc.create_place(x=150, y=650, label="Metabolic_Health")
p24.name = "Metabolic_Health"
p24.initial_marking = 1.0  # Neutral health
p24.tokens = 1.0
p24.is_signal_place = True
p24.signal_type = "Ψ_metabolic"
p24.color = (0.0, 0.4, 0.8)  # Blue for signal places
print(f"✓ Created {p24.id}: {p24.name} [SIGNAL - metabolic state]")

# T32: Calculate Metabolic Health
# Health = f(cAMP, ppGpp) = (1 - ppGpp/10) * (1 + cAMP/10)
# This is a continuous calculation, we'll use mass action for simplicity
t32 = doc.create_transition(x=150, y=600, label="Metabolic_Health_Update")
t32.transition_type = "mass_action"
t32.rate = "1.0"  # Frequent updates
print(f"✓ Created {t32.id}: {t32.name}")

# Arcs for metabolic health calculation (test arcs)
# In reality, this would be a calculation, but we'll use test arcs for signal flow
arc1 = doc.create_arc(source=p22, target=t32, weight=1, arc_type='test')
arc2 = doc.create_arc(source=p23, target=t32, weight=1, arc_type='test')
arc3 = doc.create_arc(source=t32, target=p24, weight=1, arc_type='normal')
print(f"✓ Created metabolic health calculation arcs")

# ============================================================================
# STEP 2: Cell Cycle Sensor Module (L0-C1C) 
# ============================================================================
print("\n" + "="*70)
print("STEP 2: Adding Cell Cycle Sensor Module (L0-C1C)")
print("="*70)

# P25: DnaA (replication initiator, high at cell birth)
p25 = doc.create_place(x=350, y=550, label="DnaA")
p25.initial_marking = 80.0  # High at start (early cycle)
p25.tokens = 80.0
print(f"✓ Created {p25.id}: {p25.name} (high at cell birth)")

# P26: FtsZ (division ring protein, low initially)
p26 = doc.create_place(x=450, y=550, label="FtsZ")
p26.initial_marking = 10.0  # Low at start
p26.tokens = 10.0
print(f"✓ Created {p26.id}: {p26.name} (low at start)")

# P27: Cell_Cycle_Phase (signal place)
# Value represents phase: high = early (favor lysogeny), low = late (favor lysis)
p27 = doc.create_place(x=400, y=650, label="Cell_Cycle_Phase")
p27.initial_marking = 0.8  # Early cycle
p27.tokens = 0.8
p27.is_signal_place = True
p27.signal_type = "Ψ_cell_cycle"
p27.color = (0.0, 0.4, 0.8)  # Blue for signal places
print(f"✓ Created {p27.id}: {p27.name} [SIGNAL - cell cycle state]")

# T33: DnaA Decay (decays over cell cycle)
t33 = doc.create_transition(x=350, y=600, label="DnaA_Decay")
t33.transition_type = "mass_action"
t33.rate = "0.05"  # Slow decay
arc4 = doc.create_arc(source=p25, target=t33, weight=1, arc_type='normal')
print(f"✓ Created {t33.id}: {t33.name}")

# T34: FtsZ Production (increases over cell cycle)
t34 = doc.create_transition(x=450, y=600, label="FtsZ_Production")
t34.transition_type = "mass_action"
t34.rate = "0.1"  # Ramps up
arc5 = doc.create_arc(source=t34, target=p26, weight=1, arc_type='normal')
print(f"✓ Created {t34.id}: {t34.name}")

# T35: Cell Cycle Phase Calculation
# Phase = DnaA / (DnaA + FtsZ + 1)
t35 = doc.create_transition(x=400, y=600, label="Cell_Cycle_Phase_Update")
t35.transition_type = "mass_action"
t35.rate = "1.0"
arc6 = doc.create_arc(source=p25, target=t35, weight=1, arc_type='test')
arc7 = doc.create_arc(source=p26, target=t35, weight=1, arc_type='test')
arc8 = doc.create_arc(source=t35, target=p27, weight=1, arc_type='normal')
print(f"✓ Created {t35.id}: {t35.name}")

# ============================================================================
# STEP 3: CIII Protease Inhibitor (L1-C2A Enhancement)
# ============================================================================
print("\n" + "="*70)
print("STEP 3: Adding CIII Protease Inhibitor (CII Stability Control)")
print("="*70)

# P28: CIII Protein (protease inhibitor for CII)
p28 = doc.create_place(x=650, y=400, label="CIII_Protein")
p28.initial_marking = 10.0  # Moderate level initially
p28.tokens = 10.0
print(f"✓ Created {p28.id}: {p28.name} (stabilizes CII)")

# T36: CIII Synthesis (activated by metabolic health)
t36 = doc.create_transition(x=650, y=450, label="CIII_Synthesis")
t36.transition_type = "mass_action"
t36.rate = "2.0"  # Base rate, modulated by metabolic health
arc9 = doc.create_arc(source=t36, target=p28, weight=1, arc_type='normal')
# Test arc from metabolic health to activate CIII synthesis
arc10 = doc.create_arc(source=p24, target=t36, weight=1, arc_type='test')
print(f"✓ Created {t36.id}: {t36.name} (metabolic health dependent)")

# T37: CIII Degradation
t37 = doc.create_transition(x=650, y=500, label="CIII_Degradation")
t37.transition_type = "mass_action"
t37.rate = "0.5"
arc11 = doc.create_arc(source=p28, target=t37, weight=1, arc_type='normal')
print(f"✓ Created {t37.id}: {t37.name}")

# Modify T31 (CII_Degradation) to be inhibited by CIII
# This requires adding a test arc from P28 (CIII) to T31
# In practice, we'll add inhibitor arc
for t in doc.transitions:
    if t.id == 'T31':  # CII_Degradation
        # Add test arc from CIII to inhibit degradation
        arc12 = doc.create_arc(source=p28, target=t, weight=5, arc_type='inhibitor')
        print(f"✓ Added CIII inhibition to CII_Degradation (threshold=5)")
        break

# ============================================================================
# STEP 4: CI Cleavage Mechanism (L1-C2B)
# ============================================================================
print("\n" + "="*70)
print("STEP 4: Adding CI Cleavage Mechanism (RecA-dependent)")
print("="*70)

# Split P3 (CI_Protein) → P3 (CI_Intact) + P29 (CI_Cleaved)
# We'll keep P3 as CI_Intact and create P29 for cleaved fragments
p3 = [p for p in doc.places if p.id == 'P3'][0]
p3_original_name = p3.name
p3.name = "CI_Intact"
print(f"✓ Renamed P3: {p3_original_name} → CI_Intact")

# P29: CI_Cleaved (inactive fragments)
p29 = doc.create_place(x=p3.x + 100, y=p3.y, label="CI_Cleaved")
p29.initial_marking = 0.0  # None initially
p29.tokens = 0.0
print(f"✓ Created {p29.id}: {p29.name} (inactive CI fragments)")

# T38: CI_Cleavage (RecA-dependent proteolysis)
t38 = doc.create_transition(x=p3.x + 50, y=p3.y - 50, label="CI_Cleavage")
t38.transition_type = "mass_action"
t38.rate = "0.05"  # RecA-dependent rate
arc13 = doc.create_arc(source=p3, target=t38, weight=1, arc_type='normal')
arc14 = doc.create_arc(source=t38, target=p29, weight=1, arc_type='normal')
# Test arc from RecA_Active to activate cleavage
p14 = [p for p in doc.places if p.id == 'P14'][0]  # RecA_Active
arc15 = doc.create_arc(source=p14, target=t38, weight=10, arc_type='test')
print(f"✓ Created {t38.id}: {t38.name} (RecA-dependent, threshold=10)")

# T39: Cleaved CI Degradation (remove fragments)
t39 = doc.create_transition(x=p29.x, y=p29.y + 50, label="CI_Cleaved_Decay")
t39.transition_type = "mass_action"
t39.rate = "1.0"  # Fast removal
arc16 = doc.create_arc(source=p29, target=t39, weight=1, arc_type='normal')
print(f"✓ Created {t39.id}: {t39.name}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "="*70)
print("MODEL CONSTRUCTION COMPLETE")
print("="*70)

print(f"\n📊 Final Statistics:")
print(f"  Places:      {len(doc.places)} (was 15, added 8)")
print(f"  Transitions: {len(doc.transitions)} (was 20, added 8)")
print(f"  Arcs:        {len(doc.arcs)} (was 38, added ~16)")

print(f"\n🏗️  Model Structure:")
print(f"  Layer 0 (Environmental Sensors):")
print(f"    - L0-C1A: RecA (DNA damage)         - P13,P14,P15")
print(f"    - L0-C1B: Metabolic (cAMP, ppGpp)   - P22,P23,P24 [NEW]")
print(f"    - L0-C1C: Cell Cycle (DnaA, FtsZ)   - P25,P26,P27 [NEW]")
print(f"  Layer 1 (Signal Integration):")
print(f"    - L1-C2A: CII Module (with CIII)    - P19,P20,P21,P28 [ENHANCED]")
print(f"    - L1-C2B: CI Cleavage               - P3,P29 [NEW]")
print(f"  Layer 2 (Decision Core):")
print(f"    - L2-C3: CI-Cro Bistable Switch     - P1-P8,P12")

print(f"\n🔵 Signal Places (6 total):")
signal_places = [p for p in doc.places if hasattr(p, 'is_signal_place') and p.is_signal_place]
for p in signal_places:
    signal_type = getattr(p, 'signal_type', 'unknown')
    print(f"  {p.id}: {p.name:25s} ({signal_type})")

# Save as v3
output_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
doc.save_to_file(output_path)
print(f"\n💾 Saved: {output_path}")

print("\n✅ Phase 2 Model Construction Complete!")
print("\n📝 Next Steps:")
print("  1. Open lambda_hierarchical_v3.shy in SHYpn GUI")
print("  2. Adjust positions/layout for clarity")
print("  3. Test with neutral conditions (all sensors at baseline)")
print("  4. Run multi-signal integration experiments")
print("  5. Calculate information flow through all layers")

EOF
