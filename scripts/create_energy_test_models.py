#!/usr/bin/env python3
"""Minimal Test Model for Energy Loss Investigation.

This script creates a simple ATP ↔ ADP + Pi cycle model to isolate
the energy conservation issue observed in the drug discovery model.

Test Hypothesis:
    Signal flow arcs in adaptive hybrid mode may cause token loss
    during continuous ↔ stochastic mode switches.

Model Structure:
    - 3 places: ATP, ADP, Pi (each starts at 5.0 mM)
    - 2 transitions: ATP_synthesis, ATPase (both adaptive)
    - ATP_synthesis output uses signal_flow arc (suspected issue)
    - Compartment volumes properly set to trigger adaptive behavior
    
Expected:
    Total pool (ATP + ADP + Pi) = 15.0 mM (conserved)
    
Observed in full model:
    Total decreases by ~26% over 300s
"""

import json
from pathlib import Path


def create_minimal_energy_test_model(
    arc_type_variant: str = "signal_flow_output",
    volume_scenario: str = "adaptive"
) -> dict:
    """Create minimal ATP cycle model for testing.
    
    Args:
        arc_type_variant: Which arcs to make signal_flow
            - "all_normal": All arcs are normal (baseline control)
            - "signal_flow_output": ATP_synthesis output is signal_flow (matches drug model)
            - "signal_flow_input": ATPase input is signal_flow
            - "signal_flow_both": Both ATP_synthesis output and ATPase input
        
        volume_scenario: Compartment volume configuration
            - "adaptive": Small volume (0.5 fL) → triggers stochastic mode
            - "continuous": Large volume (100 fL) → triggers continuous mode
            - "mixed": ATP small (0.5 fL), ADP/Pi large (100 fL) → mixed behavior
    
    Returns:
        Model dictionary ready for .shy format
    """
    
    # Determine arc types based on variant
    synth_output_type = "signal_flow" if "output" in arc_type_variant or "both" in arc_type_variant else "normal"
    atpase_input_type = "signal_flow" if "input" in arc_type_variant or "both" in arc_type_variant else "normal"
    
    # Determine volumes based on scenario
    if volume_scenario == "adaptive":
        # Small volumes → stochastic mode (below 1.0 fL threshold)
        atp_volume = 0.5  # Will trigger stochastic
        adp_volume = 0.5
        pi_volume = 0.5
    elif volume_scenario == "continuous":
        # Large volumes → continuous mode (above 1.0 fL threshold)
        atp_volume = 100.0  # Will trigger continuous
        adp_volume = 100.0
        pi_volume = 100.0
    elif volume_scenario == "mixed":
        # Mixed volumes → tests mode switching behavior
        atp_volume = 0.5   # Small (stochastic)
        adp_volume = 100.0  # Large (continuous)
        pi_volume = 100.0   # Large (continuous)
    else:
        raise ValueError(f"Unknown volume_scenario: {volume_scenario}")
    
    model = {
        "model_type": "bio_petri_net",
        "name": f"ATP_Cycle_Test_{arc_type_variant}_{volume_scenario}",
        "description": f"Minimal energy conservation test - {arc_type_variant} - {volume_scenario}",
        "version": "1.0",
        
        "places": [
            {
                "id": "P1",
                "name": "ATP_pool",
                "tokens": 5.0,
                "x": 100,
                "y": 100,
                "compartment_volume": atp_volume,  # Set based on volume_scenario
                "compound_id": None,
                "is_signal_place": (synth_output_type == "signal_flow" or atpase_input_type == "signal_flow"),
                "color": [1.0, 0.0, 0.0],
                "properties": {
                    "volume_unit": "fL"
                }
            },
            {
                "id": "P2",
                "name": "ADP_pool",
                "tokens": 5.0,
                "x": 300,
                "y": 100,
                "compartment_volume": adp_volume,  # Set based on volume_scenario
                "compound_id": None,
                "is_signal_place": False,
                "color": [0.0, 1.0, 0.0],
                "properties": {
                    "volume_unit": "fL"
                }
            },
            {
                "id": "P3",
                "name": "Pi_pool",
                "tokens": 5.0,
                "x": 300,
                "y": 200,
                "compartment_volume": pi_volume,  # Set based on volume_scenario
                "compound_id": None,
                "is_signal_place": False,
                "color": [0.0, 0.0, 1.0],
                "properties": {
                    "volume_unit": "fL"
                }
            }
        ],
        
        "transitions": [
            {
                "id": "T1",
                "name": "ATP_synthesis",
                "transition_type": "adaptive",  # Use adaptive to test mode switching
                "x": 200,
                "y": 150,
                "properties": {
                    "rate": 10.0,  # 10 Hz baseline
                    "stochastic_burst_min": 1,
                    "stochastic_burst_max": 1,
                    "volume_threshold": 1.0,  # 1.0 fL threshold (matches drug model)
                    "prefer_continuous": True,
                    "adaptive_filter": "inputs_only"  # Check input volumes (ADP, Pi)
                },
                "color": [0.0, 0.0, 0.0]
            },
            {
                "id": "T2",
                "name": "ATPase",
                "transition_type": "adaptive",  # Use adaptive to test mode switching
                "x": 200,
                "y": 50,
                "properties": {
                    "rate": 10.0,  # Balanced with synthesis
                    "stochastic_burst_min": 1,
                    "stochastic_burst_max": 1,
                    "volume_threshold": 1.0,  # 1.0 fL threshold
                    "prefer_continuous": True,
                    "adaptive_filter": "inputs_only"  # Check input volume (ATP)
                },
                "color": [0.0, 0.0, 0.0]
            }
        ],
        
        "arcs": [
            # ATP_synthesis: ADP + Pi → ATP
            {
                "id": "A1",
                "name": "adp_to_synth",
                "source_id": "P2",
                "source_type": "place",
                "target_id": "T1",
                "target_type": "transition",
                "arc_type": "normal",
                "weight": 1.0,
                "color": [0.0, 0.0, 0.0]
            },
            {
                "id": "A2",
                "name": "pi_to_synth",
                "source_id": "P3",
                "source_type": "place",
                "target_id": "T1",
                "target_type": "transition",
                "arc_type": "normal",
                "weight": 1.0,
                "color": [0.0, 0.0, 0.0]
            },
            {
                "id": "A3",
                "name": "synth_to_atp",
                "source_id": "T1",
                "source_type": "transition",
                "target_id": "P1",
                "target_type": "place",
                "arc_type": synth_output_type,  # ← VARIABLE
                "weight": 1.0,
                "color": [0.7, 0.7, 0.7] if synth_output_type == "signal_flow" else [0.0, 0.0, 0.0]
            },
            
            # ATPase: ATP → ADP + Pi
            {
                "id": "A4",
                "name": "atp_to_atpase",
                "source_id": "P1",
                "source_type": "place",
                "target_id": "T2",
                "target_type": "transition",
                "arc_type": atpase_input_type,  # ← VARIABLE
                "weight": 1.0,
                "color": [0.7, 0.7, 0.7] if atpase_input_type == "signal_flow" else [0.0, 0.0, 0.0]
            },
            {
                "id": "A5",
                "name": "atpase_to_adp",
                "source_id": "T2",
                "source_type": "transition",
                "target_id": "P2",
                "target_type": "place",
                "arc_type": "normal",
                "weight": 1.0,
                "color": [0.0, 0.0, 0.0]
            },
            {
                "id": "A6",
                "name": "atpase_to_pi",
                "source_id": "T2",
                "source_type": "transition",
                "target_id": "P3",
                "target_type": "place",
                "arc_type": "normal",
                "weight": 1.0,
                "color": [0.0, 0.0, 0.0]
            }
        ]
    }
    
    return model


def _predict_mode(volume_scenario: str) -> str:
    """Predict which execution mode will be used."""
    if volume_scenario == "adaptive":
        return "stochastic (vol < 1.0 fL)"
    elif volume_scenario == "continuous":
        return "continuous (vol ≥ 1.0 fL)"
    elif volume_scenario == "mixed":
        return "hybrid (switches based on input volumes)"
    return "unknown"


def save_test_models(output_dir: str = "workspace/projects/My_Project/energy_test"):
    """Generate all test model variants."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    arc_variants = ["all_normal", "signal_flow_output", "signal_flow_input", "signal_flow_both"]
    volume_scenarios = ["adaptive", "continuous", "mixed"]
    
    print("=" * 80)
    print("  CREATING MINIMAL ENERGY CONSERVATION TEST MODELS")
    print("=" * 80)
    
    model_count = 0
    for arc_variant in arc_variants:
        for vol_scenario in volume_scenarios:
            model = create_minimal_energy_test_model(arc_variant, vol_scenario)
            filename = f"atp_cycle_{arc_variant}_{vol_scenario}.shy"
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(model, f, indent=2)
            
            atp_place = model['places'][0]
            adp_place = model['places'][1]
            pi_place = model['places'][2]
            
            print(f"\n✅ Created: {filename}")
            print(f"   Arc variant: {arc_variant}")
            print(f"   Volume scenario: {vol_scenario}")
            print(f"   ATP_synthesis output: {model['arcs'][2]['arc_type']}")
            print(f"   ATPase input: {model['arcs'][3]['arc_type']}")
            print(f"   ATP volume: {atp_place['compartment_volume']} fL (signal={atp_place['is_signal_place']})")
            print(f"   ADP volume: {adp_place['compartment_volume']} fL")
            print(f"   Pi volume: {pi_place['compartment_volume']} fL")
            print(f"   Expected mode: {_predict_mode(vol_scenario)}")
            
            model_count += 1
    
    print("\n" + "=" * 80)
    print(f"Total models created: {model_count}")
    print("=" * 80)


if __name__ == "__main__":
    save_test_models()
    print("\n✅ Test models ready!")
    print("   Location: workspace/projects/My_Project/energy_test/")
    print("   12 models: 4 arc variants × 3 volume scenarios")
