#!/usr/bin/env python3
"""Test thermodynamic diagnosis on MAPK model to check for errors."""

import json
from pathlib import Path
from shypn.thermodynamics.simulation_integration import ThermodynamicSimulationValidator

# Load MAPK model
mapk_file = Path("mapk/models/erk_cascade_oscillation_timed.shy")
with open(mapk_file) as f:
    model_data = json.load(f)

print("=" * 80)
print("MAPK Thermodynamic Diagnosis")
print("=" * 80)

# Check compound mappings
compound_mappings = model_data.get("compound_mappings", {})
print(f"\n1. Compound Mappings: {len(compound_mappings)} entries")
if compound_mappings:
    for place_name, compound_id in compound_mappings.items():
        print(f"   {place_name} → {compound_id}")
else:
    print("   ⚠️  WARNING: No compound mappings found!")

# Check places
places = model_data.get("places", [])
print(f"\n2. Places ({len(places)} total):")
for place in places[:10]:  # Show first 10
    print(f"   ID: {place['id']}, Name: {place['name']}, Label: {place['label'][:20]}...")

# Check for reversible transitions
transitions = model_data.get("transitions", [])
reversible = [t for t in transitions if t.get("properties", {}).get("is_reversible", False)]
print(f"\n3. Reversible Transitions: {len(reversible)} out of {len(transitions)}")
for t in reversible:
    print(f"   - {t['name']} (k_forward={t.get('rate_forward')}, k_reverse={t.get('rate_reverse')})")

# Check rate functions
rate_functions = []
for t in transitions:
    if "rate_function" in t:
        rate_functions.append((t['name'], t['rate_function']))

print(f"\n4. Rate Functions: {len(rate_functions)} transitions with rate functions")
for name, func in rate_functions[:5]:  # Show first 5
    print(f"   {name}: {func[:60]}...")

# Try to validate (will fail without mappings)
print(f"\n5. Attempting Thermodynamic Validation:")
print("   " + "-" * 70)

validator = ThermodynamicSimulationValidator()

# Mock transition object for testing
if reversible:
    trans = reversible[0]
    print(f"\n   Testing: {trans['name']}")
    print(f"   k_forward = {trans.get('rate_forward')}")
    print(f"   k_reverse = {trans.get('rate_reverse')}")
    print(f"   Issue: Need compound_mapping to map place names to KEGG IDs")
    print(f"   Example: {{'ATP': 'C00002', 'ADP': 'C00008', ...}}")

# Summary
print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)

if not compound_mappings:
    print("❌ CRITICAL ISSUE: Empty compound_mappings")
    print("   - Thermodynamic validation requires mapping place NAMES to KEGG/ChEBI IDs")
    print("   - Place names like 'ATP', 'Raf_inactive', etc. must map to 'C00002', etc.")
    print("   - Rate functions can use place names (Growth_Factor) - that's OK!")
    print("\n✅ SOLUTION:")
    print("   1. Add compound_mappings to model file")
    print("   2. Map biochemical compounds to KEGG IDs:")
    print("      'ATP' → 'C00002'")
    print("      'ADP' → 'C00008'")
    print("      'Raf_inactive' → 'C#####' (if available)")
    print("   3. Non-biochemical places (like Growth_Factor) don't need mapping")
else:
    print("✅ Compound mappings found!")
    biochemical = [cid for cid in compound_mappings.values() if cid.startswith('C')]
    protein = [cid for cid in compound_mappings.values() if cid.startswith('PROTEIN')]
    signal = [cid for cid in compound_mappings.values() if cid.startswith('SIGNAL')]
    
    print(f"   - Biochemical compounds: {len(biochemical)} (KEGG IDs: {', '.join(biochemical)})")
    print(f"   - Protein/enzyme placeholders: {len(protein)}")
    print(f"   - Signal placeholders: {len(signal)}")
    
    if reversible:
        print(f"\n⚠️  Note: {len(reversible)} reversible transitions detected")
        print(f"   Thermodynamic validation will check:")
        print(f"   - k_forward/k_reverse ratios")
        print(f"   - Consistency with ΔG° (from KEGG database)")
        print(f"   - Only ATP (C00002) and ADP (C00008) have database entries")
    else:
        print(f"\n⚠️  No reversible transitions detected")
        print(f"   Thermodynamic validation only applies to reversible reactions")
        print(f"   To test: Set transition property 'is_reversible=true'")
    
    print("\n📊 Thermodynamic Validation Ready!")
    print("   Run validation in SHYPN:")
    print("   1. Open model")
    print("   2. Pathway Operations → THERMODYNAMICS category")
    print("   3. Topology Analysis → Thermodynamic Validation")

print("=" * 80)
