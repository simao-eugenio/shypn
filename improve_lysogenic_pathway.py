#!/usr/bin/env python3
"""
Improve lysogenic pathway strength:
1. Boost CII transcription regulation
2. Add CI_Intact seed for faster lysogeny establishment
3. Add RecA inhibition of CII transcription
"""

import sys
sys.path.insert(0, 'src')
import json
from shypn.data.canvas.document_model import DocumentModel

print("="*80)
print("IMPROVING LYSOGENIC PATHWAY STRENGTH")
print("="*80)

# Load model
model_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
print(f"\n📂 Loading: {model_path}")
model = DocumentModel.load_from_file(model_path)

print(f"✓ Loaded: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")

# ============================================================================
# CORRECTION 1: Boost CII transcription
# ============================================================================
print(f"\n{'='*80}")
print("CORRECTION 1: Boost CII Transcription")
print(f"{'='*80}")

t29 = next((t for t in model.transitions if t.name == 'CII_Transcription'), None)
if t29:
    old_rate = t29.rate
    # Change from: 1.0 * P7 / (2.0 + P7)
    # To: 3.0 * P7 / (1.0 + P7) - stronger activation, lower saturation
    t29.rate = "3.0 * P7 / (1.0 + P7)"
    print(f"✓ {t29.id} ({t29.name}):")
    print(f"  Old rate: {old_rate}")
    print(f"  New rate: {t29.rate}")
    print(f"  Effect: 3x stronger, saturates at lower P7 for faster CII production")

# ============================================================================
# CORRECTION 2: Add CI_Intact seed
# ============================================================================
print(f"\n{'='*80}")
print("CORRECTION 2: Add CI_Intact Seed")
print(f"{'='*80}")

p3 = next((p for p in model.places if p.id == 'P3'), None)
if p3:
    old_marking = p3.initial_marking
    p3.initial_marking = 0.5
    p3.tokens = 0.5
    print(f"✓ {p3.id} ({p3.name}):")
    print(f"  Old initial marking: {old_marking}")
    print(f"  New initial marking: {p3.initial_marking}")
    print(f"  Effect: Small CI seed enables faster dimerization when conditions favor lysogeny")

# ============================================================================
# CORRECTION 3: Add RecA inhibition of CII transcription
# ============================================================================
print(f"\n{'='*80}")
print("CORRECTION 3: Add RecA Inhibition of CII")
print(f"{'='*80}")

# Find T29 and P14
t29 = next((t for t in model.transitions if t.name == 'CII_Transcription'), None)
p14 = next((p for p in model.places if p.id == 'P14'), None)

if t29 and p14:
    # Check if inhibitor arc already exists
    existing_inhibitor = next((a for a in model.arcs if a.source.id == 'P14' and a.target.id == t29.id and a.arc_type == 'inhibitor'), None)
    
    if not existing_inhibitor:
        # Update rate to include RecA inhibition term
        old_rate = t29.rate
        # Add Hill inhibition by RecA: / (1 + (RecA_Active / 10)**2)
        t29.rate = "3.0 * P7 / (1.0 + P7) / (1 + (P14 / 10)**2)"
        print(f"✓ {t29.id} ({t29.name}):")
        print(f"  Old rate: {old_rate}")
        print(f"  New rate: {t29.rate}")
        print(f"  Effect: RecA_Active > 10 strongly inhibits CII transcription (n=2)")
        
        # Could also add inhibitor arc, but rate expression is sufficient
        print(f"  Note: Inhibition via rate expression (Hill function)")
    else:
        print(f"✓ RecA inhibition already exists via arc {existing_inhibitor.id}")

# ============================================================================
# CORRECTION 4: Strengthen CI positive autoregulation
# ============================================================================
print(f"\n{'='*80}")
print("CORRECTION 4: Strengthen CI Positive Autoregulation")
print(f"{'='*80}")

t1 = next((t for t in model.transitions if t.name == 'CI_Transcription'), None)
if t1:
    old_rate = t1.rate
    # Change from: 2.0 * (1 + 0.5 * CI_Dimer / (5 + CI_Dimer)) / (1 + (Cro_Dimer / 15)**2)
    # To: 2.0 * (1 + 1.0 * CI_Dimer / (3 + CI_Dimer)) / (1 + (Cro_Dimer / 15)**2)
    # Stronger positive feedback (0.5 → 1.0) and lower saturation (5 → 3)
    t1.rate = "2.0 * (1 + 1.0 * CI_Dimer / (3 + CI_Dimer)) / (1 + (Cro_Dimer / 15)**2)"
    print(f"✓ {t1.id} ({t1.name}):")
    print(f"  Old rate: {old_rate}")
    print(f"  New rate: {t1.rate}")
    print(f"  Effect: 2x stronger positive feedback, activates at lower CI_Dimer levels")

# Save model
print(f"\n{'='*80}")
print("SAVING MODEL")
print(f"{'='*80}")

model.save_to_file(model_path)
print(f"✓ Saved to: {model_path}")

# Update initial marking in raw file
print(f"\n{'='*80}")
print("UPDATING RAW FILE")
print(f"{'='*80}")

with open(model_path, 'r') as f:
    data = json.load(f)

for place in data['places']:
    if place['id'] == 'P3':
        place['initial_marking'] = 0.5
        place['tokens'] = 0.5
        print(f"✓ Updated P3 initial_marking in raw file: 0.5")

with open(model_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n{'='*80}")
print("LYSOGENIC PATHWAY IMPROVEMENTS COMPLETE")
print(f"{'='*80}")

print(f"\n✅ Summary of changes:")
print(f"\n1. CII Transcription (T29):")
print(f"   - Rate: 1.0 * P7 / (2.0 + P7) → 3.0 * P7 / (1.0 + P7)")
print(f"   - Added RecA inhibition: / (1 + (P14 / 10)**2)")
print(f"   - Effect: 3x stronger, responds faster, blocked by DNA damage")

print(f"\n2. CI_Intact Seed (P3):")
print(f"   - Initial: 0.0 → 0.5 mM")
print(f"   - Effect: Faster CI_Dimer formation when lysogeny favored")

print(f"\n3. CI Transcription (T1):")
print(f"   - Positive feedback: 0.5 → 1.0 coefficient")
print(f"   - Saturation: 5 → 3 (activates earlier)")
print(f"   - Effect: Stronger lysogenic commitment once CI starts accumulating")

print(f"\n4. RecA-CII Inhibition:")
print(f"   - High RecA (>10) blocks CII production")
print(f"   - Hierarchical priority: DNA damage overrides lysogeny signals")

print(f"\nExpected outcomes:")
print(f"  WITH UV (RecA high):  Lytic (as before)")
print(f"  NO UV (RecA=0):       Strong Lysogenic (CI >> Cro)")
print(f"\n{'='*80}")
