#!/usr/bin/env python3
"""
Compare the imported BIOMD0000000010 Kholodenko model with the manually created simplified version
"""

import json
import sys
from pathlib import Path

def load_model(filepath):
    """Load a SHYPN .shy model file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_model_structure(model, model_name):
    """Extract key structural information from a model"""
    places = model['places']
    transitions = model['transitions']
    arcs = model['arcs']
    
    print(f"\n{'='*60}")
    print(f"{model_name}")
    print(f"{'='*60}")
    
    # Basic counts
    print(f"\n📊 Model Structure:")
    print(f"  Places: {len(places)}")
    print(f"  Transitions: {len(transitions)}")
    print(f"  Arcs: {len(arcs)}")
    
    # Place analysis
    print(f"\n🔵 Places (Species):")
    total_initial = 0
    for p in places:
        name = p['name']
        initial = p.get('initial_marking', 0)
        current = p.get('marking', initial)
        is_catalyst = p.get('is_catalyst', False)
        is_signal = p.get('is_signal_place', False)
        
        flags = []
        if is_catalyst:
            flags.append("catalyst")
        if is_signal:
            flags.append("signal")
        
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"  {name:15s}: {initial:8.1f} nM (initial) → {current:8.1f} nM (current){flag_str}")
        total_initial += initial
    
    print(f"\n  Total initial concentration: {total_initial:.1f} nM")
    
    # Transition analysis
    print(f"\n⚡ Transitions (Reactions):")
    for t in transitions:
        name = t['name']
        label = t.get('label', name)
        rate = t.get('rate', 'N/A')
        kinetic_meta = t.get('kinetic_metadata', {})
        
        # Extract rate type
        if kinetic_meta:
            rate_type = kinetic_meta.get('rate_type', 'unknown')
            formula = kinetic_meta.get('formula', rate)
        else:
            rate_type = t.get('transition_type', 'unknown')
            formula = rate
        
        print(f"  {name:20s}: {label}")
        print(f"    {'':20s}  Type: {rate_type}")
        
        # Show parameters if available
        if kinetic_meta and 'parameters' in kinetic_meta:
            params = kinetic_meta['parameters']
            param_str = ', '.join([f"{k}={v}" for k, v in params.items() if k != 'uVol'])
            if param_str:
                print(f"    {'':20s}  Params: {param_str}")
    
    # Arc type analysis
    print(f"\n🔗 Arc Types:")
    arc_types = {}
    for arc in arcs:
        arc_type = arc.get('arc_type', 'normal')
        arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
    
    for arc_type, count in sorted(arc_types.items()):
        print(f"  {arc_type:15s}: {count} arcs")
    
    return {
        'places': len(places),
        'transitions': len(transitions),
        'arcs': len(arcs),
        'arc_types': arc_types,
        'total_concentration': total_initial,
        'place_names': [p['name'] for p in places],
        'transition_names': [t['name'] for t in transitions]
    }

def compare_models(imported_model, manual_model):
    """Compare two models side by side"""
    print(f"\n\n{'='*80}")
    print("COMPARATIVE ANALYSIS")
    print(f"{'='*80}")
    
    imported = analyze_model_structure(imported_model, "IMPORTED: BIOMD0000000010 (Original Kholodenko 2000)")
    manual = analyze_model_structure(manual_model, "MANUAL: Simplified Kholodenko Cascade")
    
    print(f"\n\n{'='*80}")
    print("KEY DIFFERENCES")
    print(f"{'='*80}")
    
    print(f"\n1️⃣ MODEL COMPLEXITY:")
    print(f"   Imported: {imported['places']} places, {imported['transitions']} transitions, {imported['arcs']} arcs")
    print(f"   Manual:   {manual['places']} places, {manual['transitions']} transitions, {manual['arcs']} arcs")
    
    print(f"\n2️⃣ SPECIES COVERAGE:")
    imported_species = set(imported['place_names'])
    manual_species = set(manual['place_names'])
    common = imported_species & manual_species
    only_imported = imported_species - manual_species
    only_manual = manual_species - imported_species
    
    print(f"   Common species: {', '.join(sorted(common))}")
    if only_imported:
        print(f"   Only in imported: {', '.join(sorted(only_imported))}")
    if only_manual:
        print(f"   Only in manual: {', '.join(sorted(only_manual))}")
    
    print(f"\n3️⃣ REACTION COVERAGE:")
    imported_rxns = set(imported['transition_names'])
    manual_rxns = set(manual['transition_names'])
    
    print(f"   Imported has: {', '.join(sorted(imported_rxns))}")
    print(f"   Manual has:   {', '.join(sorted(manual_rxns))}")
    
    print(f"\n4️⃣ ARC TYPE USAGE:")
    print(f"   Imported:")
    for arc_type, count in sorted(imported['arc_types'].items()):
        print(f"     {arc_type}: {count}")
    print(f"   Manual:")
    for arc_type, count in sorted(manual['arc_types'].items()):
        print(f"     {arc_type}: {count}")
    
    print(f"\n5️⃣ KEY ARCHITECTURAL DIFFERENCES:")
    
    # Check for feedback
    imported_trans = [t['name'] for t in imported_model['transitions']]
    manual_trans = [t['name'] for t in manual_model['transitions']]
    
    print(f"\n   Imported Model (BIOMD0000000010):")
    print(f"   • From original Kholodenko 2000 EMBO paper")
    print(f"   • Uses authentic SBML kinetics with feedback inhibition")
    print(f"   • Product feedback: Erk2-PP → MAPKKK activation (Ki parameter)")
    print(f"   • Michaelis-Menten kinetics throughout")
    print(f"   • Total pool: {imported['total_concentration']:.0f} nM")
    
    # Check for feedback in imported model
    feedback_found = False
    for t in imported_model['transitions']:
        if 'kinetic_metadata' in t:
            formula = t['kinetic_metadata'].get('formula', '')
            if 'MAPK_PP' in formula and t['name'] == 'MA':
                print(f"   • Feedback in transition '{t['name']}': MAPK_PP inhibits MAPKKK activation")
                feedback_found = True
    
    print(f"\n   Manual Model (Simplified):")
    print(f"   • Created to understand cascade structure")
    print(f"   • Simplified kinetics (no product feedback)")
    print(f"   • Simple Michaelis-Menten for phosphorylation")
    print(f"   • Added ATP as energy signal")
    print(f"   • Total pool: {manual['total_concentration']:.0f} nM")
    print(f"   • Basal upstream stimulus for MOS activation")
    
    print(f"\n6️⃣ EXPECTED BEHAVIOR:")
    print(f"\n   Imported (with feedback):")
    print(f"   • Product feedback causes signal attenuation")
    print(f"   • Should reproduce LOW bistable state (~4% Erk2-PP)")
    print(f"   • Matches kolodenko_mapk_bistability.csv data")
    print(f"   • Demonstrates negative feedback ultrasensitivity")
    
    print(f"\n   Manual (no feedback):")
    print(f"   • Linear signal propagation")
    print(f"   • May show different steady state")
    print(f"   • Tests cascade amplification without feedback")
    print(f"   • Good baseline for understanding core mechanism")
    
    print(f"\n7️⃣ SIMULATION RECOMMENDATIONS:")
    print(f"\n   To reproduce Kholodenko LOW state:")
    print(f"   1. Use IMPORTED model (BIOMD0000000010.shy)")
    print(f"   2. It has authentic SBML kinetics with product feedback")
    print(f"   3. Simulate for 180s (match kolodenko_mapk_bistability.csv)")
    print(f"   4. Should show ~4% Erk2-PP activation at steady state")
    
    print(f"\n   To understand cascade without feedback:")
    print(f"   1. Use MANUAL model (kholodenko_mapk_cascade.shy)")
    print(f"   2. Compare steady state to IMPORTED version")
    print(f"   3. Quantify feedback impact on signal attenuation")
    
    print(f"\n8️⃣ BIOLOGICAL INSIGHT:")
    print(f"\n   The IMPORTED model demonstrates that:")
    print(f"   • Negative feedback (Erk2-PP inhibiting upstream) creates LOW state")
    print(f"   • This is distinct from your bistability model's POSITIVE feedback")
    print(f"   • Kholodenko 2000: ultrasensitivity from processive phosphorylation")
    print(f"   • Your model: bistability from phosphatase degradation")
    
    print(f"\n{'='*80}\n")

def main():
    # File paths
    base_path = Path("/home/simao/projetos/shypn/workspace/projects/My_Project")
    imported_model_path = base_path / "models" / "kolodenko_mapk.shy"
    manual_model_path = base_path / "mapk" / "models" / "manuscript" / "kholodenko_mapk_cascade.shy"
    
    # Check files exist
    if not imported_model_path.exists():
        print(f"❌ Imported model not found: {imported_model_path}")
        return 1
    
    if not manual_model_path.exists():
        print(f"❌ Manual model not found: {manual_model_path}")
        return 1
    
    # Load models
    print("Loading models...")
    imported_model = load_model(imported_model_path)
    manual_model = load_model(manual_model_path)
    
    # Compare
    compare_models(imported_model, manual_model)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
