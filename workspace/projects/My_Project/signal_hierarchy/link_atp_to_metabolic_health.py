#!/usr/bin/env python3
"""
Link P12 (Energy_ATP) to P24 (Metabolic_Health) - Make ATP dynamic
ATP production rate driven by metabolic health
"""

import sys
sys.path.insert(0, 'src')
from shypn.data.canvas.document_model import DocumentModel

print("="*80)
print("LINKING P12 (Energy_ATP) TO P24 (Metabolic_Health)")
print("="*80)

# Load model
model_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
print(f"\n📂 Loading: {model_path}")
model = DocumentModel.load_from_file(model_path)

print(f"✓ Loaded: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")

# Find P12 and P24
p12 = next((p for p in model.places if p.id == 'P12'), None)
p24 = next((p for p in model.places if p.id == 'P24'), None)

if not p12 or not p24:
    print("ERROR: Could not find P12 or P24!")
    sys.exit(1)

print(f"\n✓ Found {p12.id} ({p12.name}): {p12.tokens} tokens")
print(f"✓ Found {p24.id} ({p24.name}): {p24.tokens} tokens")

# Step 1: Make P12 a signal place with blue border
print(f"\n{'='*80}")
print("STEP 1: Configure P12 as Signal Place")
print(f"{'='*80}")

p12.is_signal_place = True
p12.signal_type = "Ψ_energy"
# Set blue border (will update in raw file)
print(f"✓ Set P12 as signal place (Ψ_energy)")

# Step 2: Create ATP production transition (driven by P24)
print(f"\n{'='*80}")
print("STEP 2: Create ATP Production (driven by Metabolic_Health)")
print(f"{'='*80}")

# T48: ATP_Production - rate proportional to P24 (Metabolic_Health)
t48 = model.create_transition(x=250, y=700, label="ATP_Production")
t48.name = "ATP_Production"
t48.transition_type = "stochastic"
t48.rate = "5.0 * P24"  # Higher metabolic health → more ATP
print(f"✓ Created {t48.id}: {t48.name}")
print(f"  Type: {t48.transition_type}")
print(f"  Rate: {t48.rate} (proportional to Metabolic_Health)")

# Arc: P24 (test) → T48 (senses metabolic health)
arc_p24_t48 = model.create_arc(source=p24, target=t48, weight=0.1, arc_type='test')
print(f"✓ Created {arc_p24_t48.id}: {p24.id} --test--> {t48.id} (threshold=0.1)")

# Arc: T48 → P12 (produces ATP)
arc_t48_p12 = model.create_arc(source=t48, target=p12, weight=10.0, arc_type='normal')
print(f"✓ Created {arc_t48_p12.id}: {t48.id} --10--> {p12.id} (produces ATP)")

# Step 3: Create ATP consumption transition (basal ATP usage)
print(f"\n{'='*80}")
print("STEP 3: Create ATP Consumption (basal usage)")
print(f"{'='*80}")

# T49: ATP_Consumption - constant drain
t49 = model.create_transition(x=350, y=700, label="ATP_Consumption")
t49.name = "ATP_Consumption"
t49.transition_type = "stochastic"
t49.rate = "0.5 * P12"  # Proportional to ATP level
print(f"✓ Created {t49.id}: {t49.name}")
print(f"  Type: {t49.transition_type}")
print(f"  Rate: {t49.rate} (basal consumption)")

# Arc: P12 → T49 (consumes ATP)
arc_p12_t49 = model.create_arc(source=p12, target=t49, weight=10.0, arc_type='normal')
print(f"✓ Created {arc_p12_t49.id}: {p12.id} --10--> {t49.id} (consumes ATP)")

# Step 4: Adjust P12 initial marking
print(f"\n{'='*80}")
print("STEP 4: Adjust P12 Initial Conditions")
print(f"{'='*80}")

old_tokens = p12.tokens
p12.tokens = 50.0  # Start at moderate level
p12.initial_marking = 50.0
print(f"✓ Changed P12 initial marking: {old_tokens} → {p12.tokens}")

# Save model
print(f"\n{'='*80}")
print("SAVING MODEL")
print(f"{'='*80}")

model.save_to_file(model_path)
print(f"✓ Saved to: {model_path}")

# Update border color in raw file (property not accessible via DocumentModel)
print(f"\n{'='*80}")
print("UPDATING P12 BORDER COLOR (blue for signal)")
print(f"{'='*80}")

import json
with open(model_path, 'r') as f:
    data = json.load(f)

for place in data['places']:
    if place['id'] == 'P12':
        old_color = place.get('border_color', [0.4, 0.0, 0.6])
        place['border_color'] = [0.0, 0.4, 0.8]  # Blue
        place['is_signal_place'] = True
        place['signal_type'] = 'Ψ_energy'
        print(f"✓ Updated P12 border color: {old_color} → [0.0, 0.4, 0.8] (blue)")
        print(f"✓ Set is_signal_place = True")
        break

with open(model_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n{'='*80}")
print("ATP DYNAMICS LINKED TO METABOLIC HEALTH")
print(f"{'='*80}")

print(f"\n✅ COMPLETE!")
print(f"\nFinal model:")
print(f"  Places: {len(model.places)}")
print(f"  Transitions: {len(model.transitions)}")
print(f"  Arcs: {len(model.arcs)}")

print(f"\nP12 (Energy_ATP) now:")
print(f"  ✓ Signal place with blue border")
print(f"  ✓ Dynamic: Production driven by P24 (Metabolic_Health)")
print(f"  ✓ Consumption: Basal ATP usage")
print(f"  ✓ Initial level: 50.0 mM")

print(f"\nMechanism:")
print(f"  High P24 (good metabolism) → High ATP production → High P12")
print(f"  Low P24 (poor metabolism) → Low ATP production → Low P12")
print(f"  P12 gates CI/Cro transcription (existing test arcs A24, A25)")

print(f"\n{'='*80}")
