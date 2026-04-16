#!/usr/bin/env python3
"""
Diagnostic Script: Why Isn't My Adaptive Transition Firing?

This script checks common issues that prevent adaptive transitions from firing:
1. Missing properties (adaptive_filter, volume_threshold)
2. Missing compartment_volume on connected places
3. Rate not set or rate = 0
4. No input places connected
5. Input places have 0 tokens

Usage:
    python diagnose_adaptive_transition.py <model.shy> <transition_id>
    
Example:
    python diagnose_adaptive_transition.py my_model.shy T1
"""

import json
import sys
from pathlib import Path


def diagnose_adaptive_transition(model_path: str, transition_id: str):
    """Diagnose why adaptive transition isn't firing."""
    
    # Load model
    try:
        with open(model_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Cannot load model: {e}")
        return
    
    print(f"🔍 Diagnosing Adaptive Transition: {transition_id}")
    print("=" * 80)
    
    # Find transition
    transitions = data.get('transitions', [])
    transition = None
    for t in transitions:
        if t.get('id') == transition_id:
            transition = t
            break
    
    if not transition:
        print(f"❌ ERROR: Transition '{transition_id}' not found!")
        print(f"Available transitions: {', '.join(t.get('id') for t in transitions)}")
        return
    
    print(f"\n📊 Transition Info:")
    print(f"   ID: {transition.get('id')}")
    print(f"   Name: {transition.get('name', 'N/A')}")
    print(f"   Type: {transition.get('transition_type', 'N/A')}")
    
    issues = []
    warnings = []
    
    # Check 1: Is it actually adaptive?
    if transition.get('transition_type') != 'adaptive':
        issues.append(f"❌ CRITICAL: transition_type = '{transition.get('transition_type')}' (not 'adaptive')")
    else:
        print(f"   ✅ Type is 'adaptive'")
    
    # Check 2: Has properties dict?
    properties = transition.get('properties', {})
    if not properties:
        issues.append("❌ CRITICAL: No 'properties' dict found!")
    else:
        print(f"   ✅ Has properties dict")
        
        # Check adaptive_filter
        adaptive_filter = properties.get('adaptive_filter')
        if not adaptive_filter:
            warnings.append("⚠️  WARNING: adaptive_filter not set (will default to 'inputs_only')")
        else:
            print(f"   ✅ adaptive_filter = '{adaptive_filter}'")
        
        # Check volume_threshold
        volume_threshold = properties.get('volume_threshold')
        if volume_threshold is None:
            warnings.append("⚠️  WARNING: volume_threshold not set (will default to 1.0 fL)")
        else:
            print(f"   ✅ volume_threshold = {volume_threshold} fL")
    
    # Check 3: Has rate set?
    rate = transition.get('rate')
    if rate is None:
        issues.append("❌ CRITICAL: No 'rate' set!")
    elif rate == 0:
        warnings.append("⚠️  WARNING: rate = 0 (transition will never fire)")
    else:
        print(f"   ✅ rate = {rate}")
    
    # Check 4: Find connected places
    arcs = data.get('arcs', [])
    input_arcs = [a for a in arcs if a.get('target_id') == transition_id]
    output_arcs = [a for a in arcs if a.get('source_id') == transition_id]
    
    print(f"\n🔗 Connectivity:")
    print(f"   Input arcs: {len(input_arcs)}")
    print(f"   Output arcs: {len(output_arcs)}")
    
    if not input_arcs:
        issues.append("❌ CRITICAL: No input arcs! Transition has nothing to consume.")
    
    # Check 5: Analyze input places
    places = data.get('places', [])
    place_map = {p.get('id'): p for p in places}
    
    print(f"\n📍 Input Places Analysis:")
    for arc in input_arcs:
        place_id = arc.get('source_id')
        place = place_map.get(place_id)
        
        if not place:
            issues.append(f"❌ CRITICAL: Input place '{place_id}' not found!")
            continue
        
        place_name = place.get('name', place_id)
        marking = place.get('marking', 0)
        volume = place.get('compartment_volume')
        
        print(f"\n   Place: {place_id} ({place_name})")
        print(f"      Marking: {marking}")
        
        if marking == 0:
            warnings.append(f"⚠️  WARNING: Place '{place_id}' has 0 tokens (transition not enabled)")
        else:
            print(f"      ✅ Has {marking} tokens")
        
        if volume is None:
            issues.append(f"❌ ISSUE: Place '{place_id}' has NO compartment_volume set!")
            print(f"      ❌ compartment_volume = None")
        else:
            print(f"      ✅ compartment_volume = {volume} fL")
    
    # Determine expected mode
    print(f"\n🎯 Mode Selection Analysis:")
    
    # Get volumes from input places (inputs_only is default)
    input_volumes = []
    for arc in input_arcs:
        place_id = arc.get('source_id')
        place = place_map.get(place_id)
        if place:
            volume = place.get('compartment_volume')
            if volume is not None:
                input_volumes.append(volume)
    
    if not input_volumes:
        print(f"   ⚠️  No compartment_volume set on input places")
        print(f"   → Mode: CONTINUOUS (default when no volumes)")
        print(f"   → Behavior: Uses integrate_step() not fire()")
        print(f"   → Visual: NO discrete firings visible (smooth flow)")
        issues.append("❌ KEY ISSUE: Adaptive defaults to CONTINUOUS mode without volumes")
        issues.append("   → Solution: Set compartment_volume on input places")
    else:
        threshold = properties.get('volume_threshold', 1.0)
        min_volume = min(input_volumes)
        
        if min_volume < threshold:
            print(f"   ✅ min_volume ({min_volume} fL) < threshold ({threshold} fL)")
            print(f"   → Mode: STOCHASTIC")
            print(f"   → Behavior: Discrete burst firing via fire()")
            print(f"   → Visual: Discrete firings visible")
        else:
            print(f"   ⚠️  min_volume ({min_volume} fL) ≥ threshold ({threshold} fL)")
            print(f"   → Mode: CONTINUOUS")
            print(f"   → Behavior: Smooth integration via integrate_step()")
            print(f"   → Visual: NO discrete firings visible")
            warnings.append(f"Mode is CONTINUOUS - visual firings only happen in STOCHASTIC mode")
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 DIAGNOSIS SUMMARY:")
    print("=" * 80)
    
    if not issues and not warnings:
        print("✅ No issues found! Transition should work correctly.")
    else:
        if issues:
            print(f"\n🔴 CRITICAL ISSUES ({len(issues)}):")
            for issue in issues:
                print(f"   {issue}")
        
        if warnings:
            print(f"\n🟡 WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"   {warning}")
    
    # Solutions
    print("\n" + "=" * 80)
    print("💡 SOLUTIONS:")
    print("=" * 80)
    
    if "No compartment_volume" in str(issues) or "No compartment_volume" in str(warnings):
        print("\n1. Add compartment_volume to input places:")
        print("   - Open place property dialog")
        print("   - Go to 'Spatial Properties' tab")
        print("   - Set 'Compartment Volume (fL)' to a value < 1.0")
        print("   - Example: 0.5 fL for stochastic mode")
        print("   - Save and run simulation again")
    
    if "rate" in str(issues).lower():
        print("\n2. Set transition rate:")
        print("   - Open transition property dialog")
        print("   - Set 'Rate' field to a positive value")
        print("   - Example: 1.0 or 10.0")
        print("   - Save and run simulation again")
    
    if "0 tokens" in str(warnings):
        print("\n3. Add tokens to input places:")
        print("   - Open place property dialog")
        print("   - Set 'Marking' to > 0")
        print("   - Example: 10 or 100")
        print("   - Save and run simulation again")
    
    if "CONTINUOUS" in str(issues):
        print("\n4. To see VISUAL FIRINGS:")
        print("   Option A: Add compartment volumes < threshold:")
        print("      - Set input place volumes to 0.1 - 0.9 fL")
        print("      - This forces STOCHASTIC mode")
        print("      - Discrete firings will be visible")
        print("")
        print("   Option B: Change type to 'stochastic':")
        print("      - Open transition property dialog")
        print("      - Change type from 'adaptive' to 'stochastic'")
        print("      - Discrete firings always visible")
        print("")
        print("   Option C: Accept continuous behavior:")
        print("      - Adaptive IS working correctly")
        print("      - It's using continuous mode (smooth flow)")
        print("      - Check token counts - they should change smoothly")
        print("      - Visual firing animation only for discrete events")


def main():
    if len(sys.argv) < 3:
        print("Usage: python diagnose_adaptive_transition.py <model.shy> <transition_id>")
        print("Example: python diagnose_adaptive_transition.py my_model.shy T1")
        sys.exit(1)
    
    model_path = sys.argv[1]
    transition_id = sys.argv[2]
    
    if not Path(model_path).exists():
        print(f"❌ ERROR: File not found: {model_path}")
        sys.exit(1)
    
    diagnose_adaptive_transition(model_path, transition_id)


if __name__ == '__main__':
    main()
