#!/usr/bin/env python3
"""Generate comprehensive arc type test battery with correct SHYPN model format.

Creates test models for verifying arc transformation behaviors and visual properties.
All models saved to workspace/projects/My_Project/arcs/
"""

import json
import os
from datetime import datetime

def create_place(id, name, x, y, marking=0.0, is_signal=False):
    """Create a place object with standard SHYPN format."""
    return {
        "id": id,
        "name": name,
        "label": "",
        "object_type": "place",
        "x": float(x),
        "y": float(y),
        "radius": 40.0,
        "marking": float(marking),
        "initial_marking": float(marking),
        "capacity": "Infinity",
        "border_color": [0.0, 0.0, 1.0] if is_signal else [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "is_catalyst": False,
        "is_signal_place": is_signal,
        "signal_type": "control" if is_signal else None,
        "is_compartment_place": False,
        "is_regulatory_place": False,
        "diffusion_coefficient": None,
        "boundary_type": None,
        "gradient_vector": None,
        "compartment_volume": None,
        "neighbor_compartments": [],
        "spatial_position": None
    }

def create_transition(id, name, x, y):
    """Create a transition object with standard SHYPN format."""
    return {
        "id": id,
        "name": name,
        "label": "",
        "object_type": "transition",
        "x": float(x),
        "y": float(y),
        "width": 60.0,
        "height": 12.0,
        "angle_degrees": 0.0,
        "border_color": [0.0, 0.0, 0.0],
        "fill_color": [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "is_source": False,
        "is_sink": False,
        "timing": {
            "type": "immediate",
            "priority": 1
        }
    }

def create_arc(id, name, source_id, source_type, target_id, target_type, weight=1.0, arc_type="normal", threshold=None, label=""):
    """Create an arc object with standard SHYPN format."""
    # Color based on arc type
    if arc_type == "test":
        color = [0.0, 0.0, 1.0]  # Blue
    elif arc_type == "signal_flow":
        color = [0.7, 0.7, 0.7]  # Gray
    else:  # normal or inhibitor
        color = [0.0, 0.0, 0.0]  # Black
    
    arc = {
        "id": id,
        "name": name,
        "label": label,
        "object_type": "arc",
        "arc_type": arc_type,
        "source_id": source_id,
        "source_type": source_type,
        "target_id": target_id,
        "target_type": target_type,
        "weight": float(weight),
        "threshold": threshold,
        "color": color,
        "is_curved": False,
        "curve_control_x": None,
        "curve_control_y": None
    }
    
    return arc

def create_model_template(name, description):
    """Create base model structure."""
    return {
        "version": "2.0",
        "metadata": {
            "created": datetime.now().isoformat(),
            "source": "test_battery",
            "model_type": "Petri Net",
            "name": name,
            "description": description,
            "author": "Test Battery"
        },
        "view_state": {
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "transformations": {
                "rotation": {
                    "type": "rotation",
                    "angle_degrees": 0.0,
                    "enabled": True
                }
            }
        },
        "thermodynamic_settings": {
            "ph": 7.0,
            "temperature": 298.15,
            "ionic_strength": 0.1,
            "tolerance": 0.5,
            "enable_validation": False,
            "preset": "biochemical_standard"
        },
        "compound_mappings": {},
        "places": [],
        "transitions": [],
        "arcs": [],
        "modules": []
    }

# Test 1: Basic Arc Types
def create_basic_arc_types_test():
    """Create model with all 4 arc types for visual comparison."""
    
    model = create_model_template(
        "Arc Types - Basic Test",
        "Visual test of all 4 arc types with default weights."
    )
    
    # Row 1: Normal Arcs
    model["places"].extend([
        create_place("P1", "Substrate_1", 100, 100, 100.0),
        create_place("P2", "Catalyst_1", 100, 200, 10.0),
        create_place("P3", "Product_1", 300, 100, 0.0),
    ])
    model["transitions"].append(create_transition("T1", "Normal_React", 200, 100))
    model["arcs"].extend([
        create_arc("A1", "A1", "P1", "place", "T1", "transition", 1.0, "normal"),
        create_arc("A2", "A2", "P2", "place", "T1", "transition", 1.0, "normal"),
        create_arc("A3", "A3", "T1", "transition", "P3", "place", 1.0, "normal"),
    ])
    
    # Row 2: Test Arcs
    model["places"].extend([
        create_place("P4", "Substrate_2", 500, 100, 100.0),
        create_place("P5", "Catalyst_2", 500, 200, 10.0),
        create_place("P6", "Product_2", 700, 100, 0.0),
    ])
    model["transitions"].append(create_transition("T2", "Test_React", 600, 100))
    model["arcs"].extend([
        create_arc("A4", "A4", "P4", "place", "T2", "transition", 1.0, "normal"),
        create_arc("A5", "A5", "P5", "place", "T2", "transition", 1.0, "test", label="TEST"),
        create_arc("A6", "A6", "T2", "transition", "P6", "place", 1.0, "normal"),
    ])
    
    # Row 3: Inhibitor Arcs
    model["places"].extend([
        create_place("P7", "Substrate_3", 100, 350, 100.0),
        create_place("P8", "Inhibitor_3", 100, 450, 10.0),
        create_place("P9", "Product_3", 300, 350, 0.0),
    ])
    model["transitions"].append(create_transition("T3", "Inhibitor_React", 200, 350))
    model["arcs"].extend([
        create_arc("A7", "A7", "P7", "place", "T3", "transition", 1.0, "normal"),
        create_arc("A8", "A8", "P8", "place", "T3", "transition", 1.0, "inhibitor", threshold=5.0, label="INHIBITOR"),
        create_arc("A9", "A9", "T3", "transition", "P9", "place", 1.0, "normal"),
    ])
    
    # Row 4: Signal Flow Arcs
    model["places"].extend([
        create_place("P10", "Substrate_4", 500, 350, 100.0),
        create_place("P11", "Signal_4", 500, 450, 10.0, is_signal=True),
        create_place("P12", "Product_4", 700, 350, 0.0),
    ])
    model["transitions"].append(create_transition("T4", "Signal_React", 600, 350))
    model["arcs"].extend([
        create_arc("A10", "A10", "P10", "place", "T4", "transition", 1.0, "normal"),
        create_arc("A11", "A11", "P11", "place", "T4", "transition", 1.0, "signal_flow", label="SIGNAL"),
        create_arc("A12", "A12", "T4", "transition", "P12", "place", 1.0, "normal"),
    ])
    
    return model

# Test 2: Arc Weights
def create_arc_weights_test():
    """Create model testing different arc weights (1, 2, 5, 10)."""
    
    model = create_model_template(
        "Arc Weights Test",
        "Test arc transformations with different weights."
    )
    
    weights = [1, 2, 5, 10]
    y_positions = [100, 220, 340, 460]
    
    for i, weight in enumerate(weights):
        y = y_positions[i]
        p_idx = i * 3
        
        model["places"].extend([
            create_place(f"P{p_idx+1}", f"Sub_W{weight}", 100, y, 100.0),
            create_place(f"P{p_idx+2}", f"Cat_W{weight}", 100, y+60, 20.0),
            create_place(f"P{p_idx+3}", f"Prod_W{weight}", 300, y, 0.0),
        ])
        
        model["transitions"].append(create_transition(f"T{i+1}", f"React_W{weight}", 200, y))
        
        a_base = i * 3
        model["arcs"].extend([
            create_arc(f"A{a_base+1}", f"A{a_base+1}", f"P{p_idx+1}", "place", f"T{i+1}", "transition", weight, "normal"),
            create_arc(f"A{a_base+2}", f"A{a_base+2}", f"P{p_idx+2}", "place", f"T{i+1}", "transition", weight, "normal", label=f"W={weight}"),
            create_arc(f"A{a_base+3}", f"A{a_base+3}", f"T{i+1}", "transition", f"P{p_idx+3}", "place", weight, "normal"),
        ])
    
    return model

# Test 3: Transformation Test
def create_transformation_test():
    """Create model specifically for testing successive arc transformations."""
    
    model = create_model_template(
        "Arc Transformation Test",
        "Testing ground for successive arc transformations."
    )
    
    model["places"].extend([
        create_place("P1", "Substrate", 100, 200, 100.0),
        create_place("P2", "Catalyst_TRANSFORM", 200, 100, 10.0),
        create_place("P3", "Product", 300, 200, 0.0),
    ])
    
    model["transitions"].append(create_transition("T1", "Reaction", 200, 200))
    
    model["arcs"].extend([
        create_arc("A1", "A1", "P1", "place", "T1", "transition", 1.0, "normal"),
        create_arc("A2", "A2", "P2", "place", "T1", "transition", 1.0, "normal", label="TRANSFORM THIS"),
        create_arc("A3", "A3", "T1", "transition", "P3", "place", 1.0, "normal"),
    ])
    
    return model

# Test 4: Threshold Expressions
def create_threshold_test():
    """Create model testing threshold expressions on inhibitor arcs."""
    
    model = create_model_template(
        "Arc Threshold Expressions",
        "Test inhibitor arcs with different threshold expressions."
    )
    
    # Test 1: threshold = 5
    model["places"].extend([
        create_place("P1", "Sub_T5", 100, 100, 50.0),
        create_place("P2", "Inh_T5", 100, 180, 7.0),
        create_place("P3", "Prod_T5", 300, 100, 0.0),
    ])
    model["transitions"].append(create_transition("T1", "React_T5", 200, 100))
    model["arcs"].extend([
        create_arc("A1", "A1", "P1", "place", "T1", "transition", 1.0, "normal"),
        create_arc("A2", "A2", "P2", "place", "T1", "transition", 1.0, "inhibitor", threshold=5.0, label="T=5"),
        create_arc("A3", "A3", "T1", "transition", "P3", "place", 1.0, "normal"),
    ])
    
    # Test 2: threshold = 10
    model["places"].extend([
        create_place("P4", "Sub_T10", 500, 100, 50.0),
        create_place("P5", "Inh_T10", 500, 180, 15.0),
        create_place("P6", "Prod_T10", 700, 100, 0.0),
    ])
    model["transitions"].append(create_transition("T2", "React_T10", 600, 100))
    model["arcs"].extend([
        create_arc("A4", "A4", "P4", "place", "T2", "transition", 1.0, "normal"),
        create_arc("A5", "A5", "P5", "place", "T2", "transition", 1.0, "inhibitor", threshold=10.0, label="T=10"),
        create_arc("A6", "A6", "T2", "transition", "P6", "place", 1.0, "normal"),
    ])
    
    return model

# Test 5: Visual Properties
def create_visual_properties_test():
    """Create model for verifying arc visual properties."""
    
    model = create_model_template(
        "Arc Visual Properties",
        "Verify visual properties after arc transformations."
    )
    
    model["places"].extend([
        create_place("P1", "CENTER", 300, 300, 50.0),
        create_place("P2", "Normal", 100, 200, 10.0),
        create_place("P3", "Test", 100, 400, 10.0),
        create_place("P4", "Inhibitor", 500, 200, 10.0),
        create_place("P5", "Signal", 500, 400, 10.0, is_signal=True),
    ])
    
    model["transitions"].append(create_transition("T1", "T_Center", 300, 300))
    
    model["arcs"].extend([
        create_arc("A1", "A1", "P2", "place", "T1", "transition", 1.0, "normal", label="Normal"),
        create_arc("A2", "A2", "P3", "place", "T1", "transition", 1.0, "test", label="Test"),
        create_arc("A3", "A3", "P4", "place", "T1", "transition", 1.0, "inhibitor", threshold=5.0, label="Inhibitor"),
        create_arc("A4", "A4", "P5", "place", "T1", "transition", 1.0, "signal_flow", label="Signal"),
    ])
    
    return model


def save_model(model, filename):
    """Save model to JSON file."""
    filepath = os.path.join("/home/simao/projetos/shypn/workspace/projects/My_Project/arcs", filename)
    with open(filepath, 'w') as f:
        json.dump(model, f, indent=2)
    print(f"✓ Created: {filename}")


if __name__ == "__main__":
    print("=" * 70)
    print("GENERATING ARC TEST BATTERY (Correct SHYPN Format)")
    print("=" * 70)
    print()
    
    # Generate all test models
    save_model(create_basic_arc_types_test(), "01_arc_types_basic.shy")
    save_model(create_arc_weights_test(), "02_arc_weights.shy")
    save_model(create_transformation_test(), "03_transformation_test.shy")
    save_model(create_threshold_test(), "04_threshold_expressions.shy")
    save_model(create_visual_properties_test(), "05_visual_properties.shy")
    
    print()
    print("=" * 70)
    print("✅ TEST BATTERY COMPLETE - Ready to load in SHYPN!")
    print("=" * 70)
    print()
    print("Format corrections:")
    print("  ✓ IDs: P1/P2/P3, T1/T2, A1/A2/A3")
    print("  ✓ Arcs use source_id/target_id")
    print("  ✓ All metadata included")
    print("  ✓ Correct color mappings")
