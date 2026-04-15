#!/usr/bin/env python3
"""Analyze why adaptive transitions are not at full capability in GATA1/PU.1 model.

This script examines the current adaptive configuration and explains what "full capability" would mean.
"""

import json
from pathlib import Path

# Load model
model_path = Path("workspace/projects/gata/models/phase3a_spatial.shy")
with open(model_path) as f:
    model = json.load(f)

print("=" * 80)
print("WHY ADAPTIVE TRANSITIONS ARE NOT AT FULL CAPABILITY")
print("=" * 80)
print()

# Get compartment volumes
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║                         COMPARTMENT VOLUMES                                 ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")
print()

compartment_volumes = {}
for place in model['places']:
    comp_vol = place.get('compartment_volume')
    if comp_vol:
        comp = place.get('compartment', 'unknown')
        if comp not in compartment_volumes:
            compartment_volumes[comp] = comp_vol

for comp, vol in sorted(compartment_volumes.items()):
    print(f"  {comp:20s}: {vol:6.1f} fL")
print()

# Analyze current adaptive configuration
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║                    CURRENT ADAPTIVE CONFIGURATION                           ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")
print()

adaptive_transitions = []
continuous_transitions = []
stochastic_transitions = []

for trans in model['transitions']:
    ttype = trans.get('transition_type', 'stochastic')
    comp = trans.get('compartment', 'unknown')
    props = trans.get('properties', {})
    
    trans_info = {
        'name': trans['name'],
        'type': ttype,
        'compartment': comp,
        'rate_function': props.get('rate_function', 'N/A'),
        'volume_threshold': props.get('volume_threshold'),
        'adaptive_filter': props.get('adaptive_filter')
    }
    
    if ttype == 'adaptive':
        adaptive_transitions.append(trans_info)
    elif ttype == 'continuous':
        continuous_transitions.append(trans_info)
    else:
        stochastic_transitions.append(trans_info)

print(f"✅ **ADAPTIVE transitions**: {len(adaptive_transitions)} (dynamic stochastic/continuous switching)")
for t in adaptive_transitions:
    comp_vol = compartment_volumes.get(t['compartment'], 'unknown')
    threshold = t['volume_threshold']
    would_be = 'stochastic' if comp_vol != 'unknown' and comp_vol < threshold else 'continuous'
    print(f"   • {t['name']}")
    print(f"     Compartment: {t['compartment']} ({comp_vol} fL)")
    print(f"     Threshold: {threshold} fL → Currently runs in {would_be.upper()} mode")
    print(f"     Filter: {t['adaptive_filter']}")
print()

print(f"🔄 **CONTINUOUS transitions**: {len(continuous_transitions)} (always deterministic ODE)")
for t in continuous_transitions[:5]:  # Show first 5
    comp_vol = compartment_volumes.get(t['compartment'], 'unknown')
    print(f"   • {t['name']} ({t['compartment']}, {comp_vol} fL)")
if len(continuous_transitions) > 5:
    print(f"   ... and {len(continuous_transitions) - 5} more")
print()

print(f"🎲 **STOCHASTIC transitions**: {len(stochastic_transitions)} (always discrete SSA/τ-leaping)")
for t in stochastic_transitions[:5]:  # Show first 5
    comp_vol = compartment_volumes.get(t['compartment'], 'unknown')
    print(f"   • {t['name']} ({t['compartment']}, {comp_vol} fL)")
if len(stochastic_transitions) > 5:
    print(f"   ... and {len(stochastic_transitions) - 5} more")
print()

# Explain what "full capability" means
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║                   WHAT IS 'FULL CAPABILITY'?                                ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")
print()

print("The adaptive mode has several configuration dimensions:")
print()

print("1️⃣ **Number of adaptive transitions**:")
print(f"   Current: {len(adaptive_transitions)}/{len(model['transitions'])} transitions are adaptive")
print(f"   Full capability: More transitions could be adaptive (currently {len(continuous_transitions)} continuous, {len(stochastic_transitions)} stochastic)")
print()

print("2️⃣ **Volume threshold**:")
print("   Current: 1.0 fL (standard threshold)")
print("   Key insight:")
print(f"     • Nucleus: {compartment_volumes.get('nucleus', 'N/A')} fL < 1.0 fL → Transcription is STOCHASTIC ✅")
print(f"     • Cytoplasm: {compartment_volumes.get('cytoplasm', 'N/A')} fL > 1.0 fL → (would be continuous)")
print(f"     • Extracellular: {compartment_volumes.get('extracellular', 'N/A')} fL > 1.0 fL → (would be continuous)")
print()
print("   This is actually well-configured! Gene expression noise is captured.")
print()

print("3️⃣ **Adaptive filter** (which places determine the mode):")
print("   Current: 'inputs_only' for transcription")
print("   Options:")
print("     • 'inputs_only': Only input place volumes matter (current)")
print("     • 'outputs_only': Only output place volumes matter")
print("     • 'all': Both inputs and outputs")
print("     • 'spatial_only': Only places with compartment_volume set")
print()
print("   Current choice makes sense: transcription rate depends on input (TF proteins in nucleus).")
print()

print("4️⃣ **Which transitions should be adaptive?**")
print("   Current adaptive transitions:")
for t in adaptive_transitions:
    print(f"     ✅ {t['name']} ({t['compartment']})")
print()

print("   Candidate transitions for adaptive mode:")
print("   ──────────────────────────────────────")
print()

# Identify candidates by compartment
nucleus_continuous = [t for t in continuous_transitions if t['compartment'] == 'nucleus']
cytoplasm_continuous = [t for t in continuous_transitions if t['compartment'] == 'cytoplasm']

if nucleus_continuous:
    print(f"   🧬 **Nucleus ({compartment_volumes.get('nucleus', 'N/A')} fL < 1.0 fL)** - Would benefit from stochastic behavior:")
    for t in nucleus_continuous:
        print(f"      • {t['name']}")
        print(f"        Current: continuous (deterministic)")
        print(f"        If adaptive: Would run stochastic (captures noise)")
    print()

if cytoplasm_continuous:
    print(f"   🏭 **Cytoplasm ({compartment_volumes.get('cytoplasm', 'N/A')} fL > 1.0 fL)** - Already above threshold:")
    for t in cytoplasm_continuous[:3]:
        print(f"      • {t['name']}")
        print(f"        Current: continuous (deterministic)")
        print(f"        If adaptive: Would STAY continuous (no change)")
    if len(cytoplasm_continuous) > 3:
        print(f"      ... and {len(cytoplasm_continuous) - 3} more")
    print()
    print("   → Making these adaptive wouldn't change behavior (cytoplasm > threshold)")
    print()

# Stochastic transitions that could become adaptive
nucleus_stochastic = [t for t in stochastic_transitions if t['compartment'] == 'nucleus']
if nucleus_stochastic:
    print(f"   🎲 **Nucleus stochastic transitions** that could become adaptive:")
    for t in nucleus_stochastic:
        print(f"      • {t['name']}")
        print(f"        Current: always stochastic")
        print(f"        If adaptive: Would stay stochastic (nucleus < threshold)")
        print(f"        Benefit: Could switch to continuous if nucleus volume increases")
    print()

# Analysis conclusion
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║                          CONCLUSION                                         ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")
print()

print("🎯 **Why adaptive is not at 'full capability':**")
print()

print("1. **Only 2 transitions are adaptive** (transcription)")
print(f"   • {len(model['transitions']) - 2} other transitions are fixed (continuous or stochastic)")
print()

print("2. **Nucleus is already small (0.5 fL < 1.0 fL)**")
print("   • Transcription runs stochastic ✅ (good!)")
print("   • But other nucleus processes are forced continuous")
print("   • They would benefit from adaptive mode (automatic stochastic)")
print()

print("3. **Cytoplasm processes are all continuous**")
print("   • Makes sense (cytoplasm 4.5 fL > threshold)")
print("   • Making them adaptive wouldn't change behavior")
print("   • BUT: Enables future flexibility (if volume changes in sweeps)")
print()

print("4. **Design philosophy**:")
print("   • Current: Minimize stochastic transitions (only gene expression)")
print("   • Full capability: Make more transitions adaptive")
print("     → Nucleus processes automatically stochastic")
print("     → Cytoplasm processes automatically continuous")
print("     → Volume changes in parameter sweeps would trigger mode switches")
print()

print("=" * 80)
print("RECOMMENDATIONS FOR 'FULL CAPABILITY'")
print("=" * 80)
print()

print("🔧 **Option 1: Convert nucleus continuous → adaptive**")
print("   Transitions in nucleus that are currently continuous:")
for t in nucleus_continuous:
    print(f"     • {t['name']}")
print()
print("   Effect: These would become stochastic (nucleus < 1.0 fL)")
print("   Benefit: Captures intrinsic noise in small compartment")
print()

print("🔧 **Option 2: Convert cytoplasm continuous → adaptive**")
print(f"   {len(cytoplasm_continuous)} transitions in cytoplasm")
print("   Effect: Would STAY continuous (cytoplasm > 1.0 fL)")
print("   Benefit: Enables parameter sweeps of volume (responsive to changes)")
print()

print("🔧 **Option 3: Convert nucleus stochastic → adaptive**")
if nucleus_stochastic:
    for t in nucleus_stochastic:
        print(f"     • {t['name']}")
    print()
    print("   Effect: Would STAY stochastic (nucleus < 1.0 fL)")
    print("   Benefit: Could switch to continuous if volume increases")
else:
    print("   No nucleus stochastic transitions found")
print()

print("🎯 **Recommended approach for parameter sweeps:**")
print()
print("   Make ALL transitions adaptive with threshold 1.0 fL:")
print("     • Nucleus (0.5 fL < 1.0) → Automatically stochastic")
print("     • Cytoplasm (4.5 fL > 1.0) → Automatically continuous")
print("     • Extracellular (10 fL > 1.0) → Automatically continuous")
print()
print("   This gives maximum flexibility:")
print("     ✅ Current behavior preserved")
print("     ✅ Volume sweeps automatically adjust simulation mode")
print("     ✅ No manual intervention needed")
print()

print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print()
print("To enable full adaptive capability:")
print()
print("1️⃣ **For nucleus transitions** (capture stochasticity):")
print("   • Convert continuous → adaptive (set transition_type='adaptive')")
print("   • Keep volume_threshold=1.0 fL")
print("   • Set adaptive_filter='inputs_only' (or 'all')")
print()
print("2️⃣ **For cytoplasm transitions** (enable flexibility):")
print("   • Convert continuous → adaptive")
print("   • Keep volume_threshold=1.0 fL")
print("   • Behavior stays continuous (cytoplasm > threshold)")
print()
print("3️⃣ **For parameter sweeps:**")
print("   • Sweep volume_threshold (0.1-10.0 fL)")
print("   • Sweep compartment volumes")
print("   • Observe automatic mode switching")
print()

print("Would you like me to:")
print("  A) Show which transitions to convert")
print("  B) Generate model update script")
print("  C) Explain trade-offs (performance vs biological realism)")
print()
