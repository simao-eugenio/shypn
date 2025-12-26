#!/usr/bin/env python3
"""
Add UV damage arc A50 to enable DNA damage simulation
Creates UV_Source place and connects to T21
"""

import sys
sys.path.insert(0, 'src')
from shypn.data.canvas.document_model import DocumentModel

print("="*80)
print("ADD UV DAMAGE ARC (A50)")
print("="*80)

# Load model
model_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
print(f"\n📂 Loading: {model_path}")
model = DocumentModel.load_from_file(model_path)

print(f"✓ Loaded: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")

# Find T21 (DNA_Damage_UV)
t21 = next((t for t in model.transitions if t.name == 'DNA_Damage_UV'), None)
if not t21:
    print("\n❌ ERROR: T21 (DNA_Damage_UV) not found!")
    sys.exit(1)

print(f"\n✓ Found T21 (DNA_Damage_UV)")

# Find P15 (DNA_Damage)
p15 = next((p for p in model.places if p.name == 'DNA_Damage'), None)
if not p15:
    print("\n❌ ERROR: P15 (DNA_Damage) not found!")
    sys.exit(1)

print(f"✓ Found P15 (DNA_Damage)")

# ============================================================================
# Step 1: Create UV_Source place
# ============================================================================
print(f"\n{'='*80}")
print("STEP 1: Create UV_Source Place")
print(f"{'='*80}")

# Find next available place ID
max_place_id = max(int(p.id[1:]) for p in model.places)
uv_source_id = f"P{max_place_id + 1}"

print(f"\nCreating {uv_source_id} (UV_Source):")
print(f"  Initial marking: 100.0 (constant UV source)")
print(f"  Is signal: False (environmental constant)")
print(f"  Color: Yellow (environmental factor)")

from shypn.data.canvas.document_model import Place

uv_source = Place(
    id=uv_source_id,
    name='UV_Source',
    initial_marking=100.0,
    is_signal_place=False,
    position=[100.0, 100.0],  # Will be repositioned in GUI
    border_color=[0.9, 0.7, 0.0],  # Yellow
    fill_color=[1.0, 0.95, 0.7]
)

model.places.append(uv_source)
print(f"✓ Created {uv_source_id} (UV_Source)")

# ============================================================================
# Step 2: Create A50 arc (UV_Source → T21)
# ============================================================================
print(f"\n{'='*80}")
print("STEP 2: Create A50 Arc (UV_Source → T21)")
print(f"{'='*80}")

from shypn.data.canvas.document_model import Arc

a50 = Arc(
    id='A50',
    source=uv_source.id,
    target=t21.id,
    weight=1.0,
    arc_type='test',  # Test arc - doesn't consume tokens
    threshold=0.1
)

model.arcs.append(a50)
print(f"\n✓ Created A50: {uv_source_id} --test(threshold=0.1)--> T21")
print(f"  Arc type: test (UV_Source remains constant)")
print(f"  Weight: 1.0")
print(f"  Effect: T21 can now fire when UV_Source > 0.1")

# ============================================================================
# Step 3: Check/fix T21 output arc to DNA_Damage
# ============================================================================
print(f"\n{'='*80}")
print("STEP 3: Check T21 → DNA_Damage Connection")
print(f"{'='*80}")

# Check if T21 produces DNA_Damage
t21_output = next((arc for arc in model.arcs if arc.source == t21.id and arc.target == p15.id), None)

if not t21_output:
    print(f"\n⚠️ Missing: T21 → P15 (DNA_Damage) arc")
    print(f"Creating output arc...")
    
    # Find next available arc ID
    arc_numbers = [int(a.id[1:]) for a in model.arcs if a.id.startswith('A') and a.id[1:].isdigit()]
    next_arc_id = f"A{max(arc_numbers) + 1}"
    
    output_arc = Arc(
        id=next_arc_id,
        source=t21.id,
        target=p15.id,
        weight=5.0,  # Produces 5 DNA damage per firing
        arc_type='normal'
    )
    
    model.arcs.append(output_arc)
    print(f"✓ Created {next_arc_id}: T21 --[weight=5.0]--> P15 (DNA_Damage)")
else:
    print(f"\n✓ T21 output arc already exists: {t21_output.id}")
    print(f"  Weight: {t21_output.weight}")

# ============================================================================
# Summary
# ============================================================================
print(f"\n{'='*80}")
print("UV DAMAGE PATHWAY")
print(f"{'='*80}")

print(f"\nComplete pathway:")
print(f"  1. UV_Source (P{uv_source.id}) [initial=100.0, constant]")
print(f"  2. A50: UV_Source --test--> T21 (DNA_Damage_UV)")
print(f"  3. T21 fires stochastically based on rate")
print(f"  4. T21 → P15 (DNA_Damage) [produces damage]")
print(f"  5. P15 → T22 (RecA_Activation)")
print(f"  6. T22 → P14 (RecA_Active)")
print(f"\nExpected behavior:")
print(f"  - UV_Source constant at 100 → T21 fires continuously")
print(f"  - DNA_Damage accumulates")
print(f"  - RecA activates (P14 increases)")
print(f"  - RecA blocks CII via inhibition term: 1/(1+(P14/10)^2)")
print(f"  - Low CII → weak CI → Cro dominates → LYTIC")

# Save model
print(f"\n{'='*80}")
print("SAVING MODEL")
print(f"{'='*80}")

model.save_to_file(model_path)
print(f"\n✓ Saved: {model_path}")
print(f"  {len(model.places)} places (+1)")
print(f"  {len(model.transitions)} transitions")
print(f"  {len(model.arcs)} arcs (+1 or +2)")

print(f"\n{'='*80}")
print("NEXT STEPS")
print(f"{'='*80}")

print(f"\n1. Run simulation with UV damage enabled")
print(f"2. Verify RecA_Active increases (should reach ~86)")
print(f"3. Verify CII_Protein blocked (should stay <1)")
print(f"4. Verify lytic outcome: Cro >> CI")
print(f"5. Compare to NO UV simulation (A50 deleted)")
print(f"6. Validate hierarchical priority: RecA overrides metabolism")

print(f"\n{'='*80}")
