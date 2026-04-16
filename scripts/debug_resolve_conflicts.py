#!/usr/bin/env python3
"""
Deep dive into _resolve_continuous_conflicts for Bacillus model
to see why transitions are being filtered out.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

# Load Bacillus model
model = DocumentModel.load_from_file('bacillus_sporulation_normal.shy')

# Restore tokens
with open('bacillus_sporulation_normal.shy', 'r') as f:
    model_data = json.load(f)

for place_data in model_data.get('places', []):
    place_id = place_data['id']
    for place in model.places:
        if place.id == place_id:
            place.marking = place_data.get('marking', 0)
            break

print("="*80)
print("DEBUGGING: _resolve_continuous_conflicts in Bacillus Model")
print("="*80)

# Patch _resolve_continuous_conflicts to see what's happening
import shypn.engine.simulation.controller as ctrl_module

original_resolve = ctrl_module.SimulationController._resolve_continuous_conflicts

call_count = [0]
conflict_log = []

def patched_resolve(self, continuous_enabled):
    call_count[0] += 1
    
    # Log input
    input_trans = [trans.id for trans, _, _, _ in continuous_enabled]
    
    # Call original
    result = original_resolve(self, continuous_enabled)
    
    # Log output
    output_trans = [trans.id for trans, _, _, _ in result]
    
    # Calculate what was filtered out
    filtered_out = [tid for tid in input_trans if tid not in output_trans]
    
    conflict_log.append({
        'call': call_count[0],
        'time': self.time,
        'input_count': len(continuous_enabled),
        'output_count': len(result),
        'input_trans': input_trans,
        'output_trans': output_trans,
        'filtered_out': filtered_out
    })
    
    # Print first few calls
    if call_count[0] <= 10:
        print(f"\nCall {call_count[0]} at t={self.time:.6f}s:")
        print(f"  Input: {len(continuous_enabled)} transitions")
        print(f"    {', '.join(input_trans)}")
        print(f"  Output: {len(result)} transitions")
        print(f"    {', '.join(output_trans)}")
        if filtered_out:
            print(f"  🔴 FILTERED OUT: {', '.join(filtered_out)}")
    
    return result

ctrl_module.SimulationController._resolve_continuous_conflicts = patched_resolve

# Run simulation
controller = SimulationController(model)

print(f"\nRunning 0.5s simulation...\n")

step_count = 0
while controller.time < 0.5 and step_count < 10:
    controller.step()
    step_count += 1

# Restore
ctrl_module.SimulationController._resolve_continuous_conflicts = original_resolve

print(f"\n{'='*80}")
print(f"ANALYSIS: First {min(10, call_count[0])} calls to _resolve_continuous_conflicts")
print(f"{'='*80}\n")

# Analyze filtering patterns
if conflict_log:
    # Count how often each transition was filtered
    filter_counts = {}
    total_calls = len(conflict_log)
    
    for log in conflict_log:
        for tid in log['filtered_out']:
            if tid not in filter_counts:
                filter_counts[tid] = 0
            filter_counts[tid] += 1
    
    print(f"FILTERING STATISTICS:")
    print("-"*80)
    print(f"Total _resolve_continuous_conflicts calls: {total_calls}")
    print()
    
    if filter_counts:
        print(f"{'Transition':<25} {'Filtered':<12} {'Kept':<12} {'Filter %'}")
        print("-"*80)
        
        for tid in sorted(filter_counts.keys(), key=lambda x: filter_counts[x], reverse=True):
            filtered = filter_counts[tid]
            kept = total_calls - filtered
            pct = filtered / total_calls * 100
            
            status = "🔴" if pct > 50 else "⚠️" if pct > 20 else "✓"
            print(f"{tid:<25} {filtered:>10}   {kept:>10}   {pct:>6.1f}% {status}")
    else:
        print("✓ NO TRANSITIONS WERE FILTERED OUT")
        print("  All continuous transitions passed through conflict resolution")
    
    # Check if there are actual conflicts (shared places)
    print(f"\n\nCONFLICT DETECTION:")
    print("-"*80)
    
    # Find continuous transitions
    cont_transitions = [t for t in model.transitions if t.transition_type == 'continuous']
    
    print(f"Continuous transitions in model: {len(cont_transitions)}")
    for trans in cont_transitions:
        is_source = getattr(trans, 'is_source', False)
        is_sink = getattr(trans, 'is_sink', False)
        source_marker = " [SOURCE]" if is_source else ""
        sink_marker = " [SINK]" if is_sink else ""
        print(f"  - {trans.label or trans.id:<30} {trans.id:<10}{source_marker}{sink_marker}")
    
    # Check for shared input places
    print(f"\nChecking for shared input places (conflicts):")
    
    input_places_map = {}  # place_id -> list of transition_ids
    
    for trans in cont_transitions:
        trans_id = trans.id
        
        # Find input arcs
        for arc in model.arcs:
            if arc.target_id == trans_id:
                # Arc going to this transition (input)
                place_id = arc.source_id
                
                if place_id not in input_places_map:
                    input_places_map[place_id] = []
                input_places_map[place_id].append(trans_id)
    
    # Find shared places
    conflicts_found = False
    for place_id, trans_list in input_places_map.items():
        if len(trans_list) > 1:
            conflicts_found = True
            
            # Get place name
            place_name = place_id
            for place in model.places:
                if place.id == place_id:
                    place_name = place.label or place.name or place_id
                    break
            
            print(f"  🔴 Place '{place_name}' ({place_id}) is input to:")
            for tid in trans_list:
                trans_name = tid
                for t in model.transitions:
                    if t.id == tid:
                        trans_name = t.label or t.name or tid
                        break
                print(f"      - {trans_name} ({tid})")
    
    if not conflicts_found:
        print("  ✓ No shared input places found")
        print("    All continuous transitions have independent inputs")

print(f"\n{'='*80}")
print("CONCLUSION:")
print("-"*80)

if filter_counts and any(count > total_calls * 0.3 for count in filter_counts.values()):
    print("🔴 BUG CONFIRMED!")
    print("   _resolve_continuous_conflicts is filtering out transitions")
    print("   even though they should fire on every step.")
    print()
    print("   Likely cause: Incorrect conflict detection logic")
    print("   treating independent transitions as conflicting.")
else:
    print("Need more investigation...")

print("="*80 + "\n")
