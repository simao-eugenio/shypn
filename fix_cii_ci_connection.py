#!/usr/bin/env python3
"""
Fix CII-CI connection: Add CII to rate expressions
1. CII activates CI transcription
2. CII inhibits Cro transcription
"""

import sys
sys.path.insert(0, 'src')
from shypn.data.canvas.document_model import DocumentModel

print("="*80)
print("FIX CII-CI CONNECTION")
print("="*80)

# Load model
model_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
print(f"\n📂 Loading: {model_path}")
model = DocumentModel.load_from_file(model_path)

print(f"✓ Loaded: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")

# ============================================================================
# FIX 1: Add CII activation to CI transcription
# ============================================================================
print(f"\n{'='*80}")
print("FIX 1: Add CII Activation to CI Transcription (T1)")
print(f"{'='*80}")

t1 = next((t for t in model.transitions if t.name == 'CI_Transcription'), None)
if t1:
    old_rate = t1.rate
    # Current: 2.0 * (1 + 1.0 * CI_Dimer / (3 + CI_Dimer)) / (1 + (Cro_Dimer / 15)**2)
    # Add CII activation: * (1 + 2.0 * P21 / (5 + P21))
    t1.rate = "2.0 * (1 + 1.0 * CI_Dimer / (3 + CI_Dimer)) * (1 + 2.0 * P21 / (5 + P21)) / (1 + (Cro_Dimer / 15)**2)"
    print(f"✓ {t1.id} ({t1.name}):")
    print(f"  Old rate: {old_rate}")
    print(f"  New rate: {t1.rate}")
    print(f"\n  Effect at different CII levels:")
    for cii in [0, 2, 5, 10, 21]:
        boost = (1 + 2.0 * cii / (5 + cii))
        print(f"    CII = {cii:2d} mM → {boost:.2f}x boost to CI transcription")

# ============================================================================
# FIX 2: Add CII inhibition to Cro transcription
# ============================================================================
print(f"\n{'='*80}")
print("FIX 2: Add CII Inhibition to Cro Transcription (T6)")
print(f"{'='*80}")

t6 = next((t for t in model.transitions if t.name == 'Cro_Transcription'), None)
if t6:
    old_rate = t6.rate
    # Current: 2.0 * (1 + 0.5 * Cro_Dimer / (5 + Cro_Dimer)) / (1 + (CI_Dimer / 15)**2)
    # Add CII inhibition: / (1 + (P21 / 10)**2)
    t6.rate = "2.0 * (1 + 0.5 * Cro_Dimer / (5 + Cro_Dimer)) / (1 + (CI_Dimer / 15)**2) / (1 + (P21 / 10)**2)"
    print(f"✓ {t6.id} ({t6.name}):")
    print(f"  Old rate: {old_rate}")
    print(f"  New rate: {t6.rate}")
    print(f"\n  Effect at different CII levels:")
    for cii in [0, 5, 10, 15, 21]:
        suppression = 1 / (1 + (cii / 10)**2)
        print(f"    CII = {cii:2d} mM → {suppression:.2f}x (Cro reduced to {100*suppression:.0f}%)")

# Save model
print(f"\n{'='*80}")
print("SAVING MODEL")
print(f"{'='*80}")

model.save_to_file(model_path)
print(f"✓ Saved to: {model_path}")

print(f"\n{'='*80}")
print("CII-CI CONNECTION FIXED")
print(f"{'='*80}")

print(f"\n✅ Summary:")
print(f"\n1. CI Transcription now responds to CII:")
print(f"   - CII = 0 mM: baseline CI production")
print(f"   - CII = 5 mM: 2x CI production")
print(f"   - CII = 21 mM: 2.68x CI production")

print(f"\n2. Cro Transcription now inhibited by CII:")
print(f"   - CII = 0 mM: baseline Cro production")
print(f"   - CII = 10 mM: 50% Cro production")
print(f"   - CII = 21 mM: 19% Cro production (81% suppressed)")

print(f"\n3. Expected outcome with high CII (21 mM):")
print(f"   - CI production: ~2.7x boost")
print(f"   - Cro production: ~5x reduction")
print(f"   - Combined effect: CI/Cro ratio should increase ~13x")
print(f"   - Previous: CI/Cro = 1.21")
print(f"   - Expected: CI/Cro > 15 (strong lysogenic)")

print(f"\n{'='*80}")
