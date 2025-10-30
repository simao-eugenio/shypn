#!/usr/bin/env python3
"""
Diagnostic script to analyze why transitions don't fire in BIOMD0000000061.

This script checks:
1. Transition enablement conditions
2. Rate function evaluation
3. Token availability
4. Arc connectivity
5. Formula parameters
"""

import sys
import json
sys.path.insert(0, 'src')

from pathlib import Path
from shypn.data.canvas.document_model import DocumentModel


def diagnose_model(model_path: str):
    """Diagnose why transitions might not fire."""
    
    print(f"\n{'='*80}")
    print(f"BIOMD0000000061 Transition Firing Diagnosis")
    print(f"{'='*80}")
    print(f"\nModel: {model_path}\n")
    
    # Load model
    document = DocumentModel.load_from_file(model_path)
    
    print(f"📊 Model Structure:")
    print(f"   Places: {len(document.places)}")
    print(f"   Transitions: {len(document.transitions)}")
    print(f"   Arcs: {len(document.arcs)}")
    
    # Analyze places
    print(f"\n{'='*80}")
    print(f"1️⃣  PLACE ANALYSIS (Token Availability)")
    print(f"{'='*80}\n")
    
    places_with_tokens = []
    places_without_tokens = []
    
    for place in document.places:
        if place.tokens > 0:
            places_with_tokens.append((place, place.tokens))
        else:
            places_without_tokens.append(place)
    
    print(f"Places WITH tokens: {len(places_with_tokens)}")
    for place, tokens in places_with_tokens[:10]:  # Show first 10
        print(f"   ✓ {place.name}: {tokens} tokens")
    
    if len(places_with_tokens) > 10:
        print(f"   ... and {len(places_with_tokens) - 10} more")
    
    print(f"\nPlaces WITHOUT tokens: {len(places_without_tokens)}")
    for place in places_without_tokens[:5]:  # Show first 5
        print(f"   ⚠️  {place.name}: 0 tokens")
    
    # Analyze transitions
    print(f"\n{'='*80}")
    print(f"2️⃣  TRANSITION ANALYSIS")
    print(f"{'='*80}\n")
    
    continuous_transitions = []
    stochastic_transitions = []
    
    for t in document.transitions:
        if t.transition_type == 'continuous':
            continuous_transitions.append(t)
        elif t.transition_type == 'stochastic':
            stochastic_transitions.append(t)
    
    print(f"Continuous transitions: {len(continuous_transitions)}")
    print(f"Stochastic transitions: {len(stochastic_transitions)}")
    
    # Analyze continuous transitions with formulas
    print(f"\n{'='*80}")
    print(f"3️⃣  CONTINUOUS TRANSITION DETAILS")
    print(f"{'='*80}\n")
    
    for t in continuous_transitions[:5]:  # Show first 5
        print(f"\n{'─'*60}")
        print(f"Transition: {t.name} ({t.label})")
        print(f"  Type: {t.transition_type}")
        print(f"  Enabled: {t.enabled}")
        
        # Check for rate function
        if hasattr(t, 'properties') and 'rate_function' in t.properties:
            formula = t.properties['rate_function']
            print(f"  Formula: {formula[:80]}...")
            
            # Check for parameters
            if hasattr(t, 'kinetic_metadata') and t.kinetic_metadata:
                params = t.kinetic_metadata.parameters
                print(f"  Parameters: {len(params)} defined")
                # Show first few
                param_names = list(params.keys())[:5]
                for pname in param_names:
                    print(f"    • {pname} = {params[pname]}")
        else:
            print(f"  ⚠️  No rate_function property!")
        
        # Check input arcs
        input_arcs = [arc for arc in document.arcs if arc.target == t]
        print(f"  Input arcs: {len(input_arcs)}")
        for arc in input_arcs:
            place = arc.source
            print(f"    ← {place.name}: {place.tokens} tokens (weight={arc.weight})")
        
        # Check output arcs
        output_arcs = [arc for arc in document.arcs if arc.source == t]
        print(f"  Output arcs: {len(output_arcs)}")
        for arc in output_arcs[:3]:  # Show first 3
            place = arc.target
            print(f"    → {place.name} (weight={arc.weight})")
    
    # Check enablement conditions
    print(f"\n{'='*80}")
    print(f"4️⃣  ENABLEMENT ANALYSIS")
    print(f"{'='*80}\n")
    
    enabled_transitions = []
    disabled_transitions = []
    
    for t in continuous_transitions:
        # Check if all input places have tokens
        input_arcs = [arc for arc in document.arcs if arc.target == t]
        
        can_fire = True
        blocking_place = None
        
        for arc in input_arcs:
            place = arc.source
            # Continuous requires tokens > 0
            if place.tokens <= 0:
                can_fire = False
                blocking_place = place
                break
        
        if can_fire:
            enabled_transitions.append(t)
        else:
            disabled_transitions.append((t, blocking_place))
    
    print(f"Enabled continuous transitions: {len(enabled_transitions)}")
    for t in enabled_transitions[:5]:
        print(f"   ✓ {t.name}: {t.label}")
    
    print(f"\nDisabled continuous transitions: {len(disabled_transitions)}")
    for t, blocking_place in disabled_transitions[:5]:
        print(f"   ✗ {t.name}: {t.label}")
        if blocking_place:
            print(f"     Blocked by: {blocking_place.name} (0 tokens)")
    
    # Check for common issues
    print(f"\n{'='*80}")
    print(f"5️⃣  COMMON ISSUES CHECK")
    print(f"{'='*80}\n")
    
    issues_found = []
    
    # Issue 1: Transitions without formulas
    no_formula = []
    for t in continuous_transitions:
        if not hasattr(t, 'properties') or 'rate_function' not in t.properties:
            no_formula.append(t)
    
    if no_formula:
        issues_found.append("no_formula")
        print(f"⚠️  Issue 1: Transitions without rate_function")
        print(f"   {len(no_formula)} transitions have no rate_function property")
        for t in no_formula[:3]:
            print(f"     • {t.name}")
    
    # Issue 2: Empty places blocking transitions
    if disabled_transitions:
        issues_found.append("empty_places")
        print(f"\n⚠️  Issue 2: Empty places blocking transitions")
        print(f"   {len(disabled_transitions)} transitions blocked by empty input places")
        blocking_places = set()
        for _, place in disabled_transitions:
            if place:
                blocking_places.add(place.name)
        print(f"   Blocking places: {', '.join(list(blocking_places)[:5])}")
    
    # Issue 3: Missing parameters in formulas
    missing_params = []
    for t in continuous_transitions:
        if hasattr(t, 'properties') and 'rate_function' in t.properties:
            formula = t.properties['rate_function']
            # Check if formula has undefined variables
            if hasattr(t, 'kinetic_metadata') and t.kinetic_metadata:
                params = t.kinetic_metadata.parameters
                # Simple check: look for common parameter patterns
                if 'k0' in formula and 'k0' not in params:
                    missing_params.append((t, 'k0'))
    
    if missing_params:
        issues_found.append("missing_params")
        print(f"\n⚠️  Issue 3: Missing parameters in formulas")
        print(f"   {len(missing_params)} transitions may have undefined parameters")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📋 DIAGNOSIS SUMMARY")
    print(f"{'='*80}\n")
    
    if not issues_found:
        print(f"✅ No obvious issues detected!")
        print(f"\nPossible reasons transitions don't fire:")
        print(f"  1. Simulation not running (need to start simulation)")
        print(f"  2. Time step too large (continuous transitions need small dt)")
        print(f"  3. Rate functions evaluate to zero")
        print(f"  4. Formula evaluation errors (check terminal for warnings)")
    else:
        print(f"❌ Issues detected:")
        if "no_formula" in issues_found:
            print(f"  • Some transitions lack rate_function property")
        if "empty_places" in issues_found:
            print(f"  • Many input places have 0 tokens (need initialization)")
        if "missing_params" in issues_found:
            print(f"  • Some formulas may reference undefined parameters")
        
        print(f"\n💡 Recommended Actions:")
        if "empty_places" in issues_found:
            print(f"  1. Set initial markings for input places")
            print(f"  2. Add source transitions to generate tokens")
        if "no_formula" in issues_found:
            print(f"  3. Verify SBML import completed successfully")
        print(f"  4. Run simulation with small time steps (dt=0.01)")
        print(f"  5. Check terminal output for formula evaluation errors")
    
    # Specific check for BIOMD61
    print(f"\n{'='*80}")
    print(f"🧬 BIOMD0000000061 SPECIFIC CHECKS")
    print(f"{'='*80}\n")
    
    # Check key species
    key_species = ['GlcX', 'Glc', 'ATP', 'G6P', 'ADP']
    print(f"Key metabolite concentrations:")
    for place in document.places:
        place_label = place.label if hasattr(place, 'label') else place.name
        for species in key_species:
            if species.lower() in place_label.lower():
                print(f"  • {place_label}: {place.tokens} tokens")
                break
    
    # Check if converted transitions are present
    converted = [t for t in document.transitions 
                 if hasattr(t, 'properties') 
                 and 'enrichment_reason' in t.properties
                 and 'Converted from stochastic' in t.properties['enrichment_reason']]
    
    if converted:
        print(f"\n✓ Auto-converted transitions detected: {len(converted)}")
        for t in converted:
            print(f"  • {t.name}: {t.label}")
    
    return document


if __name__ == '__main__':
    model_file = "workspace/projects/SBML/models/BIOMD0000000061.shy"
    
    if not Path(model_file).exists():
        print(f"❌ Model file not found: {model_file}")
        sys.exit(1)
    
    document = diagnose_model(model_file)
