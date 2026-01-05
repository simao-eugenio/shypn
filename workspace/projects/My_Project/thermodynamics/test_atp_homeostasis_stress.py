#!/usr/bin/env python3
"""
Test ATP Homeostasis Achievement in Stress Model
================================================

Validates that the stress model achieves ATP homeostasis with the same
adjustments applied to the normal model:

1. T20 (Source_ATP_regen) rate function: 4.4 * Nutrients / (10 + Nutrients)
2. A9 (T_septation): Weight reduced from 50 → 40 mM
3. A22 (T_forespore_formation): Weight reduced from 30 → 24 mM  
4. A24 (T_mother_cell_formation): Weight reduced from 30 → 24 mM

Expected outcomes:
- ATP_pool should remain stable around 300 mM (stress initial value)
- Sporulation pathway should function despite stress conditions
- T20 should fire consistently to regenerate ATP
"""

import sys
import os
import json

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

def verify_adjustments(model):
    """Verify that all ATP homeostasis adjustments are present in the model."""
    
    print("=" * 80)
    print("VERIFYING ATP HOMEOSTASIS ADJUSTMENTS IN STRESS MODEL")
    print("=" * 80)
    
    # 1. Verify T20 rate function
    t20 = None
    for transition in model.transitions:
        if transition.name == 'Source_ATP_regen':
            t20 = transition
            break
    
    expected_rate = "4.4 * Nutrients / (10 + Nutrients)"
    actual_rate = t20.rate_function if t20 else "NOT FOUND"
    
    print(f"\n1. T20 (Source_ATP_regen) Rate Function:")
    print(f"   Expected: {expected_rate}")
    print(f"   Actual:   {actual_rate}")
    print(f"   Status:   {'✓ CORRECT' if actual_rate == expected_rate else '✗ INCORRECT'}")
    
    # 2. Verify arc weights
    adjustments = [
        ('A9', 40.0, 'T_septation ATP consumption'),
        ('A22', 24.0, 'T_forespore_formation ATP consumption'),
        ('A24', 24.0, 'T_mother_cell_formation ATP consumption')
    ]
    
    print("\n2. Arc Weight Adjustments:")
    all_correct = True
    
    for arc_id, expected_weight, description in adjustments:
        arc = None
        for a in model.arcs:
            if a.id == arc_id:
                arc = a
                break
        
        actual_weight = arc.weight if arc else "NOT FOUND"
        correct = (actual_weight == expected_weight)
        all_correct = all_correct and correct
        
        print(f"   {arc_id} ({description}):")
        print(f"      Expected: {expected_weight} mM")
        print(f"      Actual:   {actual_weight} mM")
        print(f"      Status:   {'✓ CORRECT' if correct else '✗ INCORRECT'}")
    
    return all_correct

def run_simulation(model):
    """Run simulation and monitor ATP homeostasis."""
    
    print("\n" + "=" * 80)
    print("RUNNING SIMULATION TO TEST ATP HOMEOSTASIS")
    print("=" * 80)
    
    # Get initial ATP level
    atp_place = None
    for place in model.places:
        if place.name == 'ATP_pool':
            atp_place = place
            break
    
    initial_atp = atp_place.marking
    
    print(f"\nInitial ATP level: {initial_atp} mM")
    print("\nSimulation parameters:")
    print("  - Duration: 60 seconds")
    print("  - Time step: 0.006 s")
    print("  - Steps: 10,000")
    
    # Run simulation
    controller = SimulationController(model)
    
    # Track key metrics
    t20_fire_count = 0
    atp_samples = []
    
    print("\nSimulating...", end='', flush=True)
    
    target_time = 60.0
    step_count = 0
    while controller.time < target_time and step_count < 10001:
        # Track T20 firing
        for transition in model.transitions:
            if transition.name == 'Source_ATP_regen' and transition.enabled:
                t20_fire_count += 1
                break
        
        # Sample ATP every 100 steps
        if step_count % 100 == 0:
            atp_samples.append(atp_place.marking)
            if step_count % 1000 == 0:
                print(".", end='', flush=True)
        
        controller.step()
        step_count += 1
    
    print(" Done!\n")
    
    # Get final state
    final_atp = atp_place.marking
    
    # Calculate statistics
    min_atp = min(atp_samples)
    max_atp = max(atp_samples)
    avg_atp = sum(atp_samples) / len(atp_samples)
    atp_retention = (final_atp / initial_atp) * 100
    
    # Check sporulation progress
    mature_spore_place = None
    for place in model.places:
        if place.name == 'Mature_spore':
            mature_spore_place = place
            break
    
    mature_spores = mature_spore_place.marking if mature_spore_place else 0
    
    print("=" * 80)
    print("SIMULATION RESULTS")
    print("=" * 80)
    
    print(f"\nATP Dynamics:")
    print(f"  Initial ATP:  {initial_atp:.2f} mM")
    print(f"  Final ATP:    {final_atp:.2f} mM")
    print(f"  Min ATP:      {min_atp:.2f} mM")
    print(f"  Max ATP:      {max_atp:.2f} mM")
    print(f"  Average ATP:  {avg_atp:.2f} mM")
    print(f"  Retention:    {atp_retention:.1f}%")
    
    print(f"\nT20 Firing Rate:")
    print(f"  Enabled steps: {t20_fire_count} / {step_count}")
    print(f"  Fire rate:     {(t20_fire_count/step_count)*100:.1f}%")
    
    print(f"\nSporulation Progress:")
    print(f"  Mature spores formed: {int(mature_spores)}")
    
    # Determine if homeostasis was achieved
    homeostasis_achieved = (atp_retention > 85.0 and final_atp > initial_atp * 0.8)
    
    print(f"\n{'=' * 80}")
    if homeostasis_achieved:
        print("✓ ATP HOMEOSTASIS ACHIEVED")
        print(f"  ATP maintained above 85% of initial value")
    else:
        print("✗ ATP HOMEOSTASIS NOT ACHIEVED")
        print(f"  ATP dropped below critical threshold")
    print("=" * 80)
    
    return homeostasis_achieved

def main():
    """Main test routine."""
    
    # Load the stress model
    model_path = 'bacillus_sporulation_stress.shy'
    
    print(f"Loading stress model: {model_path}")
    model = DocumentModel.load_from_file(model_path)
    
    # Restore tokens
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    for place_data in model_data.get('places', []):
        place_id = place_data['id']
        for place in model.places:
            if place.id == place_id:
                place.marking = place_data.get('marking', 0)
                break
    
    # Verify adjustments
    adjustments_correct = verify_adjustments(model)
    
    if not adjustments_correct:
        print("\n✗ ERROR: Not all adjustments are correctly applied!")
        print("Please check the model file.")
        sys.exit(1)
    
    print("\n✓ All adjustments verified correctly!")
    
    # Run simulation
    homeostasis_achieved = run_simulation(model)
    
    if homeostasis_achieved:
        print("\n✓ STRESS MODEL TEST PASSED")
        print("The stress model achieves ATP homeostasis with the applied adjustments.")
        sys.exit(0)
    else:
        print("\n✗ STRESS MODEL TEST FAILED")
        print("The stress model does not maintain ATP homeostasis.")
        sys.exit(1)

if __name__ == "__main__":
    main()
