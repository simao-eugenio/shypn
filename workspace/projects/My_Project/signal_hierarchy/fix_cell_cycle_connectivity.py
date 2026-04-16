#!/usr/bin/env python3
"""
Fix Cell Cycle Module Connectivity in Lambda Hierarchical v3
Connects P27 (Cell_Cycle_Phase) signal to the decision network.
"""

import sys
sys.path.insert(0, 'src')
from shypn.data.canvas.document_model import DocumentModel

print("="*70)
print("Fixing Cell Cycle Module Connectivity - Lambda Hierarchical v3")
print("="*70)

# Load v3 model
model_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
print(f"\n📂 Loading: {model_path}")
doc = DocumentModel.load_from_file(model_path)
print(f"✓ Loaded: {len(doc.places)} places, {len(doc.transitions)} transitions, {len(doc.arcs)} arcs")

# Find the cell cycle phase signal place and target transitions
p27 = [p for p in doc.places if p.id == 'P27'][0]  # Cell_Cycle_Phase
p27.name = 'Cell_Cycle_Phase'  # Fix name while we're at it

# Also fix other unnamed places
for p in doc.places:
    if p.id == 'P25' and p.name == 'P25':
        p.name = 'DnaA'
    elif p.id == 'P26' and p.name == 'P26':
        p.name = 'FtsZ'
    elif p.id == 'P28' and p.name == 'P28':
        p.name = 'CIII_Protein'
    elif p.id == 'P29' and p.name == 'P29':
        p.name = 'CI_Cleaved'

print(f"\n🔧 Fixed place names")

# Find transitions to connect
t1 = [t for t in doc.transitions if t.id == 'T1'][0]   # CI_Transcription
t29 = [t for t in doc.transitions if t.id == 'T29'][0] # CII_Transcription

print(f"\n🔗 Adding cell cycle → decision connections:")
print(f"   Biological logic:")
print(f"   - Early cell cycle (high P27) → favor lysogeny (more time to integrate)")
print(f"   - Late cell cycle (low P27) → favor lysis (maximize progeny before division)")

# Connection 1: Cell cycle phase activates CII transcription
# High P27 (early cycle) → more CII → more CI → lysogeny
arc1 = doc.create_arc(source=p27, target=t29, weight=1, arc_type='test')
arc1.threshold = 0.5  # Activate when cell cycle phase > 0.5 (early cycle)
print(f"\n✓ Added: P27 (Cell_Cycle_Phase) → T29 (CII_Transcription)")
print(f"  Type: test arc, threshold=0.5")
print(f"  Effect: Early cell cycle boosts CII → favors lysogeny")

# Connection 2: Cell cycle phase activates CI transcription  
# High P27 (early cycle) → more CI directly
arc2 = doc.create_arc(source=p27, target=t1, weight=1, arc_type='test')
arc2.threshold = 0.6  # Activate when clearly in early cycle
print(f"\n✓ Added: P27 (Cell_Cycle_Phase) → T1 (CI_Transcription)")
print(f"  Type: test arc, threshold=0.6")
print(f"  Effect: Early cell cycle directly boosts CI → favors lysogeny")

print(f"\n📊 Updated Statistics:")
print(f"  Places:      {len(doc.places)}")
print(f"  Transitions: {len(doc.transitions)}")
print(f"  Arcs:        {len(doc.arcs)} (was 54, added 2)")

# Verify connectivity
print(f"\n🔍 Verifying P27 connectivity:")
p27_outgoing = [a for a in doc.arcs if a.source.id == 'P27']
print(f"  P27 outgoing arcs: {len(p27_outgoing)}")
for a in p27_outgoing:
    tgt_name = a.target.name if hasattr(a.target, 'name') else a.target.id
    print(f"    → {tgt_name} ({a.target.id}) [{a.arc_type}, threshold={getattr(a, 'threshold', 'N/A')}]")

# Save updated model
output_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
doc.save_to_file(output_path)
print(f"\n💾 Saved: {output_path}")

print("\n✅ Cell Cycle Module Integration Complete!")
print("\n📝 Summary:")
print("  The cell cycle module is now connected to the decision network:")
print("  - Early cycle (high DnaA, high P27) → boosts CII & CI → lysogeny")
print("  - Late cycle (high FtsZ, low P27) → less CII & CI → lysis")
print("  This makes biological sense: integrate early, lyse late in cell cycle")
