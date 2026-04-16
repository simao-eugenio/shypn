#!/usr/bin/env python3
"""Enable full adaptive capability in GATA1/PU.1 model.

This script converts transitions to adaptive mode for:
1. Nucleus degradation transitions (immediate biological realism)
2. Optionally all transitions (maximum parameter sweep flexibility)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
MODEL_PATH = Path("workspace/projects/gata/models/phase3a_spatial.shy")
BACKUP_SUFFIX = f".backup_before_full_adaptive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Adaptive configuration
VOLUME_THRESHOLD = 1.0  # fL
ADAPTIVE_FILTER = "inputs_only"  # Which places to check for volume

def backup_model():
    """Create timestamped backup."""
    backup_path = MODEL_PATH.parent / (MODEL_PATH.name + BACKUP_SUFFIX)
    shutil.copy2(MODEL_PATH, backup_path)
    print(f"✅ Backup created: {backup_path.name}")
    return backup_path

def load_model():
    """Load model from JSON."""
    with open(MODEL_PATH) as f:
        return json.load(f)

def save_model(model):
    """Save model to JSON."""
    with open(MODEL_PATH, 'w') as f:
        json.dump(model, f, indent=2)
    print(f"✅ Model saved: {MODEL_PATH}")

def convert_to_adaptive(transition, rationale=""):
    """Convert a transition to adaptive type.
    
    Args:
        transition: Transition dict
        rationale: Why this conversion makes sense
    
    Returns:
        True if converted, False if already adaptive
    """
    if transition.get('transition_type') == 'adaptive':
        return False
    
    old_type = transition.get('transition_type', 'stochastic')
    transition['transition_type'] = 'adaptive'
    
    # Ensure properties dict exists
    if 'properties' not in transition:
        transition['properties'] = {}
    
    # Set adaptive parameters
    props = transition['properties']
    props['volume_threshold'] = VOLUME_THRESHOLD
    props['adaptive_filter'] = ADAPTIVE_FILTER
    
    # Ensure rate_function exists (required for adaptive)
    if 'rate_function' not in props:
        props['rate_function'] = "1"  # Default
    
    print(f"   ✅ {transition['name']}")
    print(f"      {old_type} → adaptive")
    print(f"      Compartment: {transition.get('compartment', 'unknown')}")
    if rationale:
        print(f"      Rationale: {rationale}")
    
    return True

def analyze_compartments(model):
    """Get compartment volumes."""
    compartment_volumes = {}
    for place in model['places']:
        comp_vol = place.get('compartment_volume')
        if comp_vol:
            comp = place.get('compartment', 'unknown')
            if comp not in compartment_volumes:
                compartment_volumes[comp] = comp_vol
    return compartment_volumes

def mode_one_nucleus_degradation(model):
    """Mode 1: Convert nucleus degradation transitions only.
    
    This captures degradation stochasticity in small nucleus compartment.
    """
    print("\n" + "=" * 80)
    print("MODE 1: Convert Nucleus Degradation Transitions")
    print("=" * 80)
    print("\nTarget: 4 nucleus degradation transitions")
    print("Effect: Capture degradation noise in small nucleus (0.5 fL < 1.0 fL)")
    print()
    
    target_names = [
        'GATA1_mRNA_nuc_degradation',
        'PU1_mRNA_nuc_degradation',
        'GATA1_Protein_nuc_degradation',
        'PU1_Protein_nuc_degradation'
    ]
    
    converted = 0
    skipped = 0
    
    for trans in model['transitions']:
        if trans['name'] in target_names:
            if convert_to_adaptive(trans, "Degradation in small nucleus → stochastic noise"):
                converted += 1
            else:
                skipped += 1
                print(f"   ⏭️  {trans['name']} (already adaptive)")
    
    print(f"\n✅ Converted {converted} transitions")
    if skipped > 0:
        print(f"⏭️  Skipped {skipped} (already adaptive)")
    
    return converted

def mode_two_all_nucleus(model):
    """Mode 2: Convert all nucleus transitions to adaptive.
    
    This ensures all processes in small nucleus use stochastic dynamics.
    """
    print("\n" + "=" * 80)
    print("MODE 2: Convert All Nucleus Transitions")
    print("=" * 80)
    print("\nTarget: All transitions in nucleus compartment")
    print("Effect: All nucleus processes → stochastic (nucleus 0.5 fL < 1.0 fL)")
    print()
    
    compartments = analyze_compartments(model)
    nucleus_vol = compartments.get('nucleus', 'unknown')
    
    print(f"Nucleus volume: {nucleus_vol} fL")
    print(f"Threshold: {VOLUME_THRESHOLD} fL → Will run STOCHASTIC")
    print()
    
    converted = 0
    skipped = 0
    
    for trans in model['transitions']:
        if trans.get('compartment') == 'nucleus':
            if convert_to_adaptive(trans, f"Nucleus process → auto-stochastic ({nucleus_vol} fL < {VOLUME_THRESHOLD} fL)"):
                converted += 1
            else:
                skipped += 1
                print(f"   ⏭️  {trans['name']} (already adaptive)")
    
    print(f"\n✅ Converted {converted} transitions")
    if skipped > 0:
        print(f"⏭️  Skipped {skipped} (already adaptive)")
    
    return converted

def mode_three_all_transitions(model):
    """Mode 3: Convert ALL transitions to adaptive.
    
    Maximum flexibility for parameter sweeps.
    """
    print("\n" + "=" * 80)
    print("MODE 3: Convert ALL Transitions to Adaptive")
    print("=" * 80)
    print("\nTarget: All 28 transitions")
    print("Effect: Automatic stochastic/continuous based on compartment volume")
    print()
    
    compartments = analyze_compartments(model)
    
    print("Expected behavior after conversion:")
    for comp, vol in sorted(compartments.items()):
        mode = "stochastic" if vol < VOLUME_THRESHOLD else "continuous"
        print(f"  {comp:20s}: {vol:6.1f} fL → {mode.upper()}")
    print()
    
    # Group by compartment
    by_compartment = {}
    for trans in model['transitions']:
        comp = trans.get('compartment', 'unknown')
        if comp not in by_compartment:
            by_compartment[comp] = []
        by_compartment[comp].append(trans)
    
    total_converted = 0
    total_skipped = 0
    
    for comp in sorted(by_compartment.keys()):
        vol = compartments.get(comp, 'unknown')
        mode = "stochastic" if vol != 'unknown' and vol < VOLUME_THRESHOLD else "continuous"
        
        print(f"\n📍 {comp.upper()} ({vol} fL) → Will run {mode.upper()}:")
        
        converted = 0
        skipped = 0
        
        for trans in by_compartment[comp]:
            if convert_to_adaptive(trans, ""):
                converted += 1
            else:
                skipped += 1
                print(f"   ⏭️  {trans['name']} (already adaptive)")
        
        print(f"   Converted: {converted}, Skipped: {skipped}")
        total_converted += converted
        total_skipped += skipped
    
    print(f"\n✅ Total converted: {total_converted}")
    if total_skipped > 0:
        print(f"⏭️  Total skipped: {total_skipped} (already adaptive)")
    
    return total_converted

def show_summary(model):
    """Show summary of current configuration."""
    print("\n" + "=" * 80)
    print("FINAL MODEL CONFIGURATION")
    print("=" * 80)
    print()
    
    transition_types = {}
    for trans in model['transitions']:
        ttype = trans.get('transition_type', 'stochastic')
        transition_types[ttype] = transition_types.get(ttype, 0) + 1
    
    print("Transition types:")
    for ttype, count in sorted(transition_types.items()):
        print(f"  {ttype:15s}: {count:2d}")
    
    print()
    
    # Show adaptive transitions by compartment
    adaptive_by_comp = {}
    for trans in model['transitions']:
        if trans.get('transition_type') == 'adaptive':
            comp = trans.get('compartment', 'unknown')
            if comp not in adaptive_by_comp:
                adaptive_by_comp[comp] = []
            adaptive_by_comp[comp].append(trans['name'])
    
    compartments = analyze_compartments(model)
    
    print("Adaptive transitions by compartment:")
    for comp in sorted(adaptive_by_comp.keys()):
        vol = compartments.get(comp, 'unknown')
        mode = "stochastic" if vol != 'unknown' and vol < VOLUME_THRESHOLD else "continuous"
        print(f"\n  {comp} ({vol} fL) → Will run {mode.upper()}:")
        for name in adaptive_by_comp[comp]:
            print(f"    • {name}")
    
    print()

def main():
    """Main execution."""
    print("=" * 80)
    print("ENABLE FULL ADAPTIVE CAPABILITY")
    print("=" * 80)
    print()
    print(f"Model: {MODEL_PATH}")
    print(f"Threshold: {VOLUME_THRESHOLD} fL")
    print(f"Adaptive filter: {ADAPTIVE_FILTER}")
    print()
    
    # Load model
    model = load_model()
    
    # Show current state
    print("Current configuration:")
    transition_types = {}
    for trans in model['transitions']:
        ttype = trans.get('transition_type', 'stochastic')
        transition_types[ttype] = transition_types.get(ttype, 0) + 1
    
    for ttype, count in sorted(transition_types.items()):
        print(f"  {ttype}: {count}")
    print()
    
    # Get compartment info
    compartments = analyze_compartments(model)
    print("Compartment volumes:")
    for comp, vol in sorted(compartments.items()):
        mode = "stochastic" if vol < VOLUME_THRESHOLD else "continuous"
        print(f"  {comp:20s}: {vol:6.1f} fL → {mode} (if adaptive)")
    
    # Choose mode
    print("\n" + "=" * 80)
    print("CONVERSION MODES")
    print("=" * 80)
    print()
    print("1️⃣  **Nucleus degradation only** (recommended for immediate realism)")
    print("   • Converts 4 nucleus degradation transitions")
    print("   • Captures degradation noise in small nucleus")
    print("   • Minimal performance impact")
    print()
    print("2️⃣  **All nucleus transitions** (comprehensive nucleus stochasticity)")
    print("   • Converts all transitions in nucleus compartment")
    print("   • All nucleus processes → stochastic")
    print("   • Moderate performance impact")
    print()
    print("3️⃣  **All transitions** (maximum flexibility for parameter sweeps)")
    print("   • Converts all 28 transitions")
    print("   • Automatic mode switching based on volume")
    print("   • Current behavior preserved, enables volume sweeps")
    print()
    
    print("Select mode [1/2/3] or 'q' to quit:")
    choice = input("> ").strip()
    
    if choice.lower() == 'q':
        print("\n❌ Aborted. No changes made.")
        return
    
    # Create backup
    backup_path = backup_model()
    
    # Convert based on choice
    if choice == '1':
        converted = mode_one_nucleus_degradation(model)
    elif choice == '2':
        converted = mode_two_all_nucleus(model)
    elif choice == '3':
        converted = mode_three_all_transitions(model)
    else:
        print(f"\n❌ Invalid choice: {choice}")
        print(f"   Backup preserved: {backup_path.name}")
        return
    
    if converted == 0:
        print("\n⚠️  No transitions converted (already adaptive?)")
        print(f"   Backup: {backup_path.name}")
        return
    
    # Show summary
    show_summary(model)
    
    # Confirm save
    print("\n" + "=" * 80)
    print("SAVE CHANGES?")
    print("=" * 80)
    print(f"\n{converted} transitions converted to adaptive mode.")
    print(f"Backup: {backup_path.name}")
    print()
    print("Save model? [y/n]:")
    
    confirm = input("> ").strip().lower()
    
    if confirm == 'y':
        save_model(model)
        print("\n✅ SUCCESS!")
        print()
        print("Next steps:")
        print("  1. Load model in shypn to verify changes")
        print("  2. Run test simulation to confirm behavior")
        print("  3. Check simulation logs for mode switching messages")
        print()
        print("To verify adaptive behavior:")
        print("  • Look for 'AdaptiveHybridBehavior' messages in logs")
        print("  • Nucleus transitions should run stochastic")
        print("  • Cytoplasm transitions should run continuous")
        print()
    else:
        print("\n❌ Changes NOT saved.")
        print(f"   Model unchanged, backup preserved: {backup_path.name}")

if __name__ == '__main__':
    main()
