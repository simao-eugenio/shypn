#!/usr/bin/env python3
"""Diagnose why transitions aren't firing when they should be enabled.

This script checks:
1. Which transitions have sufficient input tokens
2. Test arc (catalyst) requirements
3. Guard conditions
4. Source/sink flags
5. Transition types and their enabling logic
"""

import json
import sys
from pathlib import Path

def load_model(model_path):
    """Load model from JSON file."""
    with open(model_path, 'r') as f:
        return json.load(f)

def analyze_firing_readiness(model_path):
    """Analyze which transitions should be able to fire."""
    
    print(f"{'='*80}")
    print(f"FIRING READINESS ANALYSIS: {Path(model_path).name}")
    print(f"{'='*80}\n")
    
    data = load_model(model_path)
    
    places = {p['id']: p for p in data.get('places', [])}
    transitions = {t['id']: t for t in data.get('transitions', [])}
    arcs = data.get('arcs', [])
    
    print(f"📊 MODEL SUMMARY")
    print(f"   Places: {len(places)}")
    print(f"   Transitions: {len(transitions)}")
    print(f"   Arcs: {len(arcs)}\n")
    
    # Group arcs by transition
    transition_inputs = {t_id: [] for t_id in transitions}
    transition_outputs = {t_id: [] for t_id in transitions}
    
    for arc in arcs:
        source_id = arc.get('source_id') or arc.get('source')
        target_id = arc.get('target_id') or arc.get('target')
        
        # Place → Transition (input arc)
        if source_id in places and target_id in transitions:
            transition_inputs[target_id].append(arc)
        
        # Transition → Place (output arc)
        elif source_id in transitions and target_id in places:
            transition_outputs[source_id].append(arc)
    
    # Find places with tokens
    places_with_tokens = {p_id: p for p_id, p in places.items() 
                         if p.get('tokens', 0) > 0}
    
    print(f"🎯 PLACES WITH TOKENS ({len(places_with_tokens)})")
    for p_id, p in places_with_tokens.items():
        name = p.get('label', p.get('name', f'P{p_id}'))
        tokens = p.get('tokens', 0)
        is_catalyst = p.get('is_catalyst', False) or p.get('metadata', {}).get('is_catalyst', False)
        catalyst_marker = " (CATALYST)" if is_catalyst else ""
        print(f"   • {name}: {tokens} tokens{catalyst_marker}")
    print()
    
    # Check each transition
    print(f"🔍 TRANSITION ANALYSIS\n")
    
    enabled_count = 0
    disabled_count = 0
    
    for t_id, t in transitions.items():
        t_name = t.get('label', t.get('name', f'T{t_id}'))
        input_arcs = transition_inputs[t_id]
        output_arcs = transition_outputs[t_id]
        
        # Check if transition is enabled
        is_enabled = True
        blocking_reasons = []
        
        # Check input arc requirements
        for arc in input_arcs:
            source_id = arc.get('source_id') or arc.get('source')
            place = places.get(source_id)
            
            if not place:
                blocking_reasons.append(f"Missing place {source_id}")
                is_enabled = False
                continue
            
            place_name = place.get('label', place.get('name', f'P{source_id}'))
            tokens = place.get('tokens', 0)
            weight = arc.get('weight', 1)
            
            # Check if it's a test arc (catalyst)
            arc_kind = arc.get('kind', arc.get('properties', {}).get('kind', 'normal'))
            arc_type = arc.get('arc_type', 'normal')
            consumes = arc.get('consumes', True)
            is_test_arc = arc_kind == 'test' or arc_type == 'test' or consumes == False
            
            is_catalyst = place.get('is_catalyst', False) or place.get('metadata', {}).get('is_catalyst', False)
            
            if is_test_arc or is_catalyst:
                # Test arcs just check presence, don't consume
                if tokens < weight:
                    blocking_reasons.append(f"Catalyst {place_name}: {tokens} < {weight} (test arc)")
                    is_enabled = False
            else:
                # Normal arc - must have tokens to consume
                if tokens < weight:
                    blocking_reasons.append(f"{place_name}: {tokens} < {weight} tokens")
                    is_enabled = False
        
        # Check source/sink flags
        is_source = t.get('is_source', False)
        is_sink = t.get('is_sink', False)
        
        # Check transition type
        t_type = t.get('type', 'immediate')
        
        # Output status
        if is_enabled:
            enabled_count += 1
            print(f"✅ {t_name} (id={t_id})")
            print(f"   Type: {t_type}")
            if is_source:
                print(f"   Source: YES (always enabled)")
            print(f"   Input arcs: {len(input_arcs)}")
            for arc in input_arcs:
                source_id = arc.get('source_id') or arc.get('source')
                place = places.get(source_id)
                place_name = place.get('label', place.get('name', f'P{source_id}'))
                tokens = place.get('tokens', 0)
                weight = arc.get('weight', 1)
                arc_kind = arc.get('kind', arc.get('properties', {}).get('kind', 'normal'))
                
                if arc_kind == 'test':
                    print(f"     ← {place_name}: {tokens} tokens (test arc ✓)")
                else:
                    print(f"     ← {place_name}: {tokens} ≥ {weight} ✓")
            
            print(f"   Output arcs: {len(output_arcs)}")
            for arc in output_arcs[:3]:  # Show first 3
                target_id = arc.get('target_id') or arc.get('target')
                place = places.get(target_id)
                place_name = place.get('label', place.get('name', f'P{target_id}'))
                print(f"     → {place_name}")
            print()
        else:
            disabled_count += 1
            print(f"❌ {t_name} (id={t_id}) - BLOCKED")
            print(f"   Type: {t_type}")
            print(f"   Reasons:")
            for reason in blocking_reasons:
                print(f"     • {reason}")
            print()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Enabled transitions: {enabled_count}")
    print(f"❌ Disabled transitions: {disabled_count}")
    
    if enabled_count > 0 and places_with_tokens:
        print(f"\n⚠️  WARNING: {enabled_count} transitions are ENABLED but may not be firing!")
        print(f"   Possible causes:")
        print(f"   1. Simulation not running")
        print(f"   2. Simulation paused")
        print(f"   3. Transition type mismatch (immediate vs timed vs continuous)")
        print(f"   4. Guard conditions preventing firing")
        print(f"   5. Timing windows not open (for timed transitions)")
        print(f"   6. Rate functions evaluating to zero (for continuous)")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        # Default to most recent model
        model_path = "./workspace/projects/Interactive/models/hsa00010.shy"
    
    try:
        analyze_firing_readiness(model_path)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
