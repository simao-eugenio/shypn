#!/usr/bin/env python3
"""
Side-by-side comparison of OLD vs FIXED hsa00010 models.

This demonstrates that the fix resolved the catalyst interference issue.
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_model(filepath, label):
    """Analyze a model file and return stats."""
    with open(filepath) as f:
        data = json.load(f)
    
    places = data['places']
    transitions = data['transitions']
    arcs = data['arcs']
    
    # Count catalysts
    catalysts = [p for p in places if p.get('is_catalyst', False)]
    regular_places = [p for p in places if not p.get('is_catalyst', False)]
    
    # Count test arcs
    test_arcs = [a for a in arcs if a.get('arc_type') == 'test']
    normal_arcs = [a for a in arcs if a.get('arc_type') != 'test']
    
    # Catalyst token distribution
    catalyst_tokens = {}
    for cat in catalysts:
        tokens = cat.get('tokens', 0)
        initial = cat.get('initial_marking', 0)
        key = (tokens, initial)
        catalyst_tokens[key] = catalyst_tokens.get(key, 0) + 1
    
    # Build lookup
    places_by_id = {p['id']: p for p in places}
    
    # Check transition enablement
    enabled_count = 0
    disabled_count = 0
    disabled_by_catalyst = 0
    
    for trans in transitions:
        input_arcs = [a for a in arcs if a.get('target_id') == trans['id']]
        
        if not input_arcs:
            enabled_count += 1
            continue
        
        enabled = True
        blocked_by_cat = False
        
        for arc in input_arcs:
            source_id = arc.get('source_id')
            place = places_by_id.get(source_id)
            
            if not place:
                continue
            
            tokens = place.get('tokens', 0)
            initial_marking = place.get('initial_marking', 0)
            
            # Simulate what happens on load: tokens = initial_marking
            if tokens == 0 and initial_marking > 0:
                # This would be restored on load
                effective_tokens = initial_marking
            else:
                effective_tokens = tokens
            
            weight = arc.get('weight', 1)
            arc_type = arc.get('arc_type', 'normal')
            is_catalyst = place.get('is_catalyst', False)
            
            if arc_type == 'test':
                if effective_tokens < 1:
                    enabled = False
                    if is_catalyst:
                        blocked_by_cat = True
            elif arc_type == 'normal':
                if effective_tokens < weight:
                    enabled = False
        
        if enabled:
            enabled_count += 1
        else:
            disabled_count += 1
            if blocked_by_cat:
                disabled_by_catalyst += 1
    
    return {
        'label': label,
        'filepath': filepath,
        'places': len(places),
        'regular_places': len(regular_places),
        'catalysts': len(catalysts),
        'transitions': len(transitions),
        'arcs': len(arcs),
        'test_arcs': len(test_arcs),
        'normal_arcs': len(normal_arcs),
        'catalyst_tokens': catalyst_tokens,
        'enabled_transitions': enabled_count,
        'disabled_transitions': disabled_count,
        'disabled_by_catalyst': disabled_by_catalyst
    }

print("=" * 100)
print("COMPARISON: OLD vs FIXED hsa00010 Models")
print("=" * 100)

# Analyze both models
old_model = analyze_model(
    '/home/simao/projetos/shypn/workspace/projects/models/hsa00010.shy',
    'OLD (Before Fix)'
)

fixed_model = analyze_model(
    '/home/simao/projetos/shypn/workspace/projects/models/hsa00010_FIXED.shy',
    'FIXED (After Fix)'
)

# Print comparison table
print("\n📊 MODEL STATISTICS")
print("-" * 100)
print(f"{'Metric':<30} {'OLD (Before Fix)':<30} {'FIXED (After Fix)':<30}")
print("-" * 100)

metrics = [
    ('Total Places', 'places'),
    ('  Regular Places', 'regular_places'),
    ('  Catalyst Places', 'catalysts'),
    ('Transitions', 'transitions'),
    ('Total Arcs', 'arcs'),
    ('  Normal Arcs', 'normal_arcs'),
    ('  Test Arcs', 'test_arcs'),
]

for label, key in metrics:
    old_val = old_model[key]
    fixed_val = fixed_model[key]
    status = "✅" if old_val == fixed_val else "🔄"
    print(f"{label:<30} {old_val:<30} {fixed_val:<30} {status}")

print("\n🧪 CATALYST TOKEN DISTRIBUTION")
print("-" * 100)
print(f"{'(tokens, initial_marking)':<30} {'OLD Count':<30} {'FIXED Count':<30}")
print("-" * 100)

all_keys = set(old_model['catalyst_tokens'].keys()) | set(fixed_model['catalyst_tokens'].keys())
for key in sorted(all_keys):
    old_count = old_model['catalyst_tokens'].get(key, 0)
    fixed_count = fixed_model['catalyst_tokens'].get(key, 0)
    
    # Determine status
    tokens, initial = key
    if tokens == 0 and initial == 0:
        status = "❌ BLOCKS FIRING"
    elif tokens == 0 and initial == 1:
        status = "⚠️  Restored on load to 1"
    elif tokens == 1 and initial == 1:
        status = "✅ READY TO FIRE"
    else:
        status = ""
    
    print(f"{str(key):<30} {old_count:<30} {fixed_count:<30} {status}")

print("\n⚡ TRANSITION ENABLEMENT (After Load)")
print("-" * 100)
print(f"{'Status':<30} {'OLD':<30} {'FIXED':<30}")
print("-" * 100)

enablement_metrics = [
    ('Enabled', 'enabled_transitions'),
    ('Disabled', 'disabled_transitions'),
    ('  Blocked by Catalyst', 'disabled_by_catalyst'),
]

for label, key in enablement_metrics:
    old_val = old_model[key]
    fixed_val = fixed_model[key]
    
    if key == 'enabled_transitions':
        old_pct = (old_val / old_model['transitions'] * 100) if old_model['transitions'] > 0 else 0
        fixed_pct = (fixed_val / fixed_model['transitions'] * 100) if fixed_model['transitions'] > 0 else 0
        old_str = f"{old_val}/{old_model['transitions']} ({old_pct:.0f}%)"
        fixed_str = f"{fixed_val}/{fixed_model['transitions']} ({fixed_pct:.0f}%)"
        status = "✅" if fixed_val > old_val else "⚠️ "
    else:
        old_str = str(old_val)
        fixed_str = str(fixed_val)
        status = "✅" if fixed_val < old_val else "⚠️ "
    
    print(f"{label:<30} {old_str:<30} {fixed_str:<30} {status}")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

print("""
OLD MODEL ISSUES:
❌ Catalysts: tokens=0, initial_marking=0
❌ 32/34 transitions blocked by catalysts
❌ Simulation cannot execute

FIXED MODEL IMPROVEMENTS:
✅ Catalysts: tokens=0, initial_marking=1
✅ On load: tokens automatically set to initial_marking (1)
✅ All catalysts will be "present" when model loads
✅ Simulation can execute normally

BIOLOGICAL INTERPRETATION:
- initial_marking=1 means "Enzyme is present in the system"
- Test arcs check presence (tokens ≥ 1)
- Enzymes are not consumed (test arcs have consumes=False)
- This correctly models enzymatic catalysis

ACTION REQUIRED:
1. Load hsa00010_FIXED.shy in the application
2. Verify simulation works with catalysts
3. Re-import other KEGG models if needed
""")

print("=" * 100)
