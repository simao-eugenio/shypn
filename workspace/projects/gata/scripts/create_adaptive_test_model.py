"""
Create a simple gene expression model to test adaptive transition switching.

Model structure:
  Gene (1 copy, constant)
  ↓ Transcription (adaptive, stochastic when gene count=1)
  mRNA (0-10 copies, low count region)
  ↓ Translation (adaptive, switches at ~10 copies threshold)
  Protein (0-1000 copies, high count region)

All transitions are set to 'adaptive' mode, which should:
- Use stochastic (Gillespie) when reactant counts are low (<20-50)
- Use deterministic (ODE) when reactant counts are high (>50)
"""

import json
import os

def create_adaptive_test_model():
    """Create simple gene expression model with adaptive transitions."""
    
    model = {
        "version": "1.0",
        "model_name": "Adaptive_Test_GeneExpression",
        "description": "Simple model to test adaptive transition switching behavior",
        
        "places": [
            {
                "id": "P1",
                "name": "Gene",
                "label": "Gene",
                "object_type": "place",
                "x": 100.0,
                "y": 100.0,
                "width": 60.0,
                "height": 60.0,
                "tokens": 1,  # Always 1 copy (stochastic regime)
                "capacity": -1,
                "fill_color": [0.2, 0.6, 0.2],
                "border_color": [0.0, 0.0, 0.0],
                "border_width": 2.0,
                "properties": {}
            },
            {
                "id": "P2",
                "name": "mRNA",
                "label": "mRNA",
                "object_type": "place",
                "x": 100.0,
                "y": 250.0,
                "width": 60.0,
                "height": 60.0,
                "tokens": 0,  # Starts empty, grows to 5-15 (low-medium counts)
                "capacity": -1,
                "fill_color": [0.2, 0.4, 0.8],
                "border_color": [0.0, 0.0, 0.0],
                "border_width": 2.0,
                "properties": {}
            },
            {
                "id": "P3",
                "name": "Protein",
                "label": "Protein",
                "object_type": "place",
                "x": 100.0,
                "y": 400.0,
                "width": 60.0,
                "height": 60.0,
                "tokens": 0,  # Starts empty, can grow to 100-1000 (high counts)
                "capacity": -1,
                "fill_color": [0.8, 0.2, 0.2],
                "border_color": [0.0, 0.0, 0.0],
                "border_width": 2.0,
                "properties": {}
            }
        ],
        
        "transitions": [
            {
                "id": "T1",
                "name": "Transcription",
                "label": "Transcription",
                "object_type": "transition",
                "x": 250.0,
                "y": 175.0,
                "width": 60.0,
                "height": 20.0,
                "horizontal": True,
                "enabled": True,
                "fill_color": [0.0, 0.0, 0.0],
                "border_color": [0.0, 0.0, 0.0],
                "border_width": 3.0,
                "transition_type": "adaptive",  # Should stay stochastic (Gene=1)
                "rate_function": "5.0 * Gene",  # 5 transcripts per time unit
                "guard": "1",
                "properties": {}
            },
            {
                "id": "T2",
                "name": "Translation",
                "label": "Translation",
                "object_type": "transition",
                "x": 250.0,
                "y": 325.0,
                "width": 60.0,
                "height": 20.0,
                "horizontal": True,
                "enabled": True,
                "fill_color": [0.0, 0.0, 0.0],
                "border_color": [0.0, 0.0, 0.0],
                "border_width": 3.0,
                "transition_type": "adaptive",  # Should switch: stochastic->deterministic
                "rate_function": "10.0 * mRNA",  # 10 proteins per mRNA per time unit
                "guard": "1",
                "properties": {}
            },
            {
                "id": "T3",
                "name": "mRNA_degradation",
                "label": "mRNA_deg",
                "object_type": "transition",
                "x": 400.0,
                "y": 250.0,
                "width": 60.0,
                "height": 20.0,
                "horizontal": True,
                "enabled": True,
                "fill_color": [0.0, 0.0, 0.0],
                "border_color": [0.0, 0.0, 0.0],
                "border_width": 3.0,
                "transition_type": "adaptive",  # Should stay stochastic (low mRNA)
                "rate_function": "1.0 * mRNA",  # Half-life control
                "guard": "1",
                "properties": {}
            },
            {
                "id": "T4",
                "name": "Protein_degradation",
                "label": "Protein_deg",
                "object_type": "transition",
                "x": 400.0,
                "y": 400.0,
                "width": 60.0,
                "height": 20.0,
                "horizontal": True,
                "enabled": True,
                "fill_color": [0.0, 0.0, 0.0],
                "border_color": [0.0, 0.0, 0.0],
                "border_width": 3.0,
                "transition_type": "adaptive",  # Should switch to deterministic (high Protein)
                "rate_function": "0.1 * Protein",  # Slow degradation
                "guard": "1",
                "properties": {}
            }
        ],
        
        "arcs": [
            # Transcription: Gene ->T1 (read) and T1->mRNA (produce)
            {
                "id": "A1",
                "source": "P1",
                "target": "T1",
                "arc_type": "signal_flow",  # Read-only (gene not consumed)
                "weight": 1.0,
                "properties": {}
            },
            {
                "id": "A2",
                "source": "T1",
                "target": "P2",
                "arc_type": "normal",  # Produce mRNA
                "weight": 1.0,
                "properties": {}
            },
            
            # Translation: mRNA ->T2 (read) and T2->Protein (produce)
            {
                "id": "A3",
                "source": "P2",
                "target": "T2",
                "arc_type": "signal_flow",  # Read-only (mRNA not consumed during translation)
                "weight": 1.0,
                "properties": {}
            },
            {
                "id": "A4",
                "source": "T2",
                "target": "P3",
                "arc_type": "normal",  # Produce Protein
                "weight": 1.0,
                "properties": {}
            },
            
            # mRNA degradation: mRNA ->T3 (consume)
            {
                "id": "A5",
                "source": "P2",
                "target": "T3",
                "arc_type": "normal",  # Consume mRNA
                "weight": 1.0,
                "properties": {}
            },
            
            # Protein degradation: Protein ->T4 (consume)
            {
                "id": "A6",
                "source": "P3",
                "target": "T4",
                "arc_type": "normal",  # Consume Protein
                "weight": 1.0,
                "properties": {}
            }
        ],
        
        "metadata": {
            "author": "Adaptive Test Model Generator",
            "created": "2026-02-20",
            "notes": [
                "Test model for adaptive transition switching behavior",
                "",
                "Expected behavior:",
                "- Transcription (T1): Always stochastic (Gene=1)",
                "- mRNA_degradation (T3): Always stochastic (mRNA=5-15)",
                "- Translation (T2): Starts stochastic, switches to deterministic as mRNA grows",
                "- Protein_degradation (T4): Switches to deterministic when Protein>50",
                "",
                "Steady state (approximate):",
                "- Gene: 1 (constant)",
                "- mRNA: ~5 copies (production/degradation = 5/1)",
                "- Protein: ~500 copies (production/degradation = 10*5/0.1)"
            ]
        }
    }
    
    return model


if __name__ == "__main__":
    # Create the model
    model = create_adaptive_test_model()
    
    # Save to file
    output_dir = "workspace/projects/gata/models"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "adaptive_test_simple.shy")
    
    with open(output_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"✓ Created adaptive test model: {output_path}")
    print()
    print("Model structure:")
    print("  Gene (1 copy) -- [Transcription] --> mRNA (5-15 copies)")
    print("                                         |")
    print("                                    [Translation]")
    print("                                         |")
    print("                                         v")
    print("                                   Protein (0-500 copies)")
    print()
    print("Transitions (all adaptive):")
    print("  T1: Transcription     - rate 5.0  (always stochastic, Gene=1)")
    print("  T2: Translation       - rate 10.0 (switches stochastic->deterministic)")
    print("  T3: mRNA degradation  - rate 1.0  (always stochastic, low mRNA)")
    print("  T4: Protein deg.      - rate 0.1  (switches to deterministic)")
    print()
    print("To test:")
    print("  1. Load model in Shypn")
    print("  2. Set simulation mode: Adaptive Hybrid")
    print("  3. Run for 50-100 time units")
    print("  4. Watch transitions switch between stochastic/deterministic")
    print("  5. Check adaptation log in console/debug output")
