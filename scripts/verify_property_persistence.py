#!/usr/bin/env python3
"""
Verification Script: Property Dialog Persistence and Metadata Synchronization

This script verifies that:
1. Transition adaptive properties are persisted to JSON
2. Place spatial properties are persisted to JSON
3. Properties are correctly synchronized between UI → Object → JSON
4. Metadata dict is properly synchronized with object attributes

Usage:
    python verify_property_persistence.py workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy
"""

import json
import sys
from pathlib import Path


def verify_transition_properties(data: dict) -> tuple[bool, list[str]]:
    """Verify transition properties persistence.
    
    Returns:
        (success, messages): Success flag and list of verification messages
    """
    messages = []
    success = True
    
    transitions = data.get('transitions', [])
    messages.append(f"\n📊 Found {len(transitions)} transitions")
    
    # Find adaptive transitions
    adaptive_transitions = [t for t in transitions if t.get('transition_type') == 'adaptive']
    messages.append(f"✅ Found {len(adaptive_transitions)} adaptive transitions")
    
    if not adaptive_transitions:
        messages.append("⚠️  WARNING: No adaptive transitions found!")
        success = False
        return success, messages
    
    # Verify each adaptive transition has properties
    for trans in adaptive_transitions:
        trans_id = trans.get('id', 'UNKNOWN')
        trans_name = trans.get('name', trans_id)
        messages.append(f"\n🔍 Checking {trans_id} ({trans_name}):")
        
        # Check transition_type is 'adaptive'
        if trans.get('transition_type') != 'adaptive':
            messages.append(f"   ❌ FAIL: transition_type = {trans.get('transition_type')} (expected 'adaptive')")
            success = False
        else:
            messages.append(f"   ✅ transition_type = 'adaptive'")
        
        # Check properties dict exists
        properties = trans.get('properties')
        if not properties:
            messages.append(f"   ❌ FAIL: No properties dict found!")
            success = False
            continue
        
        messages.append(f"   ✅ properties dict exists")
        
        # Check adaptive_filter
        adaptive_filter = properties.get('adaptive_filter')
        if not adaptive_filter:
            messages.append(f"   ❌ FAIL: adaptive_filter missing!")
            success = False
        elif adaptive_filter not in ['inputs_only', 'outputs_only', 'all_places']:
            messages.append(f"   ⚠️  WARNING: adaptive_filter = '{adaptive_filter}' (unusual value)")
        else:
            messages.append(f"   ✅ adaptive_filter = '{adaptive_filter}'")
        
        # Check volume_threshold
        volume_threshold = properties.get('volume_threshold')
        if volume_threshold is None:
            messages.append(f"   ❌ FAIL: volume_threshold missing!")
            success = False
        elif not isinstance(volume_threshold, (int, float)):
            messages.append(f"   ⚠️  WARNING: volume_threshold = {volume_threshold} (not numeric)")
        elif volume_threshold <= 0:
            messages.append(f"   ⚠️  WARNING: volume_threshold = {volume_threshold} (should be > 0)")
        else:
            messages.append(f"   ✅ volume_threshold = {volume_threshold} fL")
    
    return success, messages


def verify_place_properties(data: dict) -> tuple[bool, list[str]]:
    """Verify place spatial properties persistence.
    
    Returns:
        (success, messages): Success flag and list of verification messages
    """
    messages = []
    success = True
    
    places = data.get('places', [])
    messages.append(f"\n📊 Found {len(places)} places")
    
    # Find places with spatial properties
    spatial_properties = [
        'compartment_volume',
        'diffusion_coefficient',
        'boundary_type',
        'module_id',
        'gradient_vector',
        'spatial_position',
        'neighbor_compartments'
    ]
    
    places_with_spatial = []
    for place in places:
        has_any_spatial = any(place.get(prop) is not None for prop in spatial_properties)
        if has_any_spatial:
            places_with_spatial.append(place)
    
    messages.append(f"✅ Found {len(places_with_spatial)} places with spatial properties")
    
    if not places_with_spatial:
        messages.append("⚠️  WARNING: No places with spatial properties found!")
        # This might be OK if model doesn't use spatial features
    
    # Verify each place with spatial properties
    for place in places_with_spatial:
        place_id = place.get('id', 'UNKNOWN')
        place_name = place.get('name', place_id)
        messages.append(f"\n🔍 Checking {place_id} ({place_name}):")
        
        # Check compartment_volume
        volume = place.get('compartment_volume')
        if volume is not None:
            if not isinstance(volume, (int, float)):
                messages.append(f"   ⚠️  WARNING: compartment_volume = {volume} (not numeric)")
            elif volume <= 0:
                messages.append(f"   ⚠️  WARNING: compartment_volume = {volume} (should be > 0)")
            else:
                messages.append(f"   ✅ compartment_volume = {volume} fL")
        
        # Check diffusion_coefficient
        diff_coeff = place.get('diffusion_coefficient')
        if diff_coeff is not None:
            if not isinstance(diff_coeff, (int, float)):
                messages.append(f"   ⚠️  WARNING: diffusion_coefficient = {diff_coeff} (not numeric)")
            elif diff_coeff < 0:
                messages.append(f"   ⚠️  WARNING: diffusion_coefficient = {diff_coeff} (should be >= 0)")
            else:
                messages.append(f"   ✅ diffusion_coefficient = {diff_coeff} μm²/s")
        
        # Check boundary_type
        boundary = place.get('boundary_type')
        if boundary is not None:
            if boundary not in ['PERMEABLE', 'SELECTIVE', 'IMPERMEABLE']:
                messages.append(f"   ⚠️  WARNING: boundary_type = '{boundary}' (unusual value)")
            else:
                messages.append(f"   ✅ boundary_type = '{boundary}'")
        
        # Check module_id
        module_id = place.get('module_id')
        if module_id is not None:
            messages.append(f"   ✅ module_id = '{module_id}'")
        
        # Check gradient_vector
        gradient = place.get('gradient_vector')
        if gradient is not None:
            if not isinstance(gradient, list) or len(gradient) != 3:
                messages.append(f"   ❌ FAIL: gradient_vector = {gradient} (should be [dx, dy, dz])")
                success = False
            else:
                messages.append(f"   ✅ gradient_vector = {gradient}")
        
        # Check spatial_position
        position = place.get('spatial_position')
        if position is not None:
            if not isinstance(position, list) or len(position) != 3:
                messages.append(f"   ❌ FAIL: spatial_position = {position} (should be [x, y, z])")
                success = False
            else:
                messages.append(f"   ✅ spatial_position = {position} μm")
        
        # Check neighbor_compartments
        neighbors = place.get('neighbor_compartments')
        if neighbors is not None:
            if not isinstance(neighbors, list):
                messages.append(f"   ❌ FAIL: neighbor_compartments = {neighbors} (should be list)")
                success = False
            else:
                messages.append(f"   ✅ neighbor_compartments = {neighbors} ({len(neighbors)} neighbors)")
    
    return success, messages


def verify_metadata_sync(data: dict) -> tuple[bool, list[str]]:
    """Verify metadata synchronization.
    
    Checks that metadata dict is consistent with object attributes.
    
    Returns:
        (success, messages): Success flag and list of verification messages
    """
    messages = []
    success = True
    
    messages.append("\n🔄 Verifying Metadata Synchronization:")
    
    # Check places
    places = data.get('places', [])
    for place in places:
        place_id = place.get('id', 'UNKNOWN')
        metadata = place.get('metadata', {})
        
        # Check if metadata contradicts object attributes
        # Example: metadata['signal_type'] vs is_signal_place flag
        if metadata.get('signal_type') and not place.get('is_signal_place'):
            messages.append(f"   ⚠️  {place_id}: metadata has signal_type but is_signal_place=False")
        
        # Spatial properties should be in object attributes, not metadata
        spatial_in_metadata = any(key in metadata for key in [
            'compartment_volume', 'diffusion_coefficient', 'boundary_type'
        ])
        if spatial_in_metadata:
            messages.append(f"   ⚠️  {place_id}: Spatial properties in metadata (should be in object attributes)")
    
    # Check transitions
    transitions = data.get('transitions', [])
    for trans in transitions:
        trans_id = trans.get('id', 'UNKNOWN')
        
        # Adaptive properties should be in properties dict, not top-level or metadata
        if trans.get('transition_type') == 'adaptive':
            if trans.get('adaptive_filter'):  # Top-level attribute
                messages.append(f"   ⚠️  {trans_id}: adaptive_filter at top level (should be in properties dict)")
                success = False
            
            if trans.get('volume_threshold'):  # Top-level attribute
                messages.append(f"   ⚠️  {trans_id}: volume_threshold at top level (should be in properties dict)")
                success = False
    
    if success:
        messages.append("   ✅ No metadata conflicts detected")
    
    return success, messages


def main():
    """Main verification routine."""
    if len(sys.argv) < 2:
        print("Usage: python verify_property_persistence.py <model.shy>")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    
    if not filepath.exists():
        print(f"❌ ERROR: File not found: {filepath}")
        sys.exit(1)
    
    print(f"🔍 Verifying Property Persistence: {filepath.name}")
    print("=" * 80)
    
    # Load JSON
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Failed to load JSON: {e}")
        sys.exit(1)
    
    # Verify version
    version = data.get('version', 'UNKNOWN')
    print(f"📄 Model version: {version}")
    
    # Run verifications
    all_success = True
    
    # 1. Verify transitions
    trans_success, trans_messages = verify_transition_properties(data)
    for msg in trans_messages:
        print(msg)
    all_success = all_success and trans_success
    
    # 2. Verify places
    place_success, place_messages = verify_place_properties(data)
    for msg in place_messages:
        print(msg)
    all_success = all_success and place_success
    
    # 3. Verify metadata sync
    metadata_success, metadata_messages = verify_metadata_sync(data)
    for msg in metadata_messages:
        print(msg)
    all_success = all_success and metadata_success
    
    # Summary
    print("\n" + "=" * 80)
    if all_success:
        print("✅ ALL VERIFICATIONS PASSED")
        print("\n🎉 Property dialogs are correctly persisted and synchronized!")
        sys.exit(0)
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("\n⚠️  Please check the issues above and update the model.")
        sys.exit(1)


if __name__ == '__main__':
    main()
