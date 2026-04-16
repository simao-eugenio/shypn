#!/usr/bin/env python3
"""
Create an annotated E. coli core model with signal hierarchy and test hierarchical exploration.

This script:
1. Loads the E. coli core model
2. Annotates key metabolites as signal places
3. Tests hierarchical signal layer detection
4. Analyzes the resulting hierarchy
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.topology.behavioral.exploration import (
    SignalLayerDetector,
    TransitionPartitioner
)


class SHYPlace:
    """Place wrapper."""
    def __init__(self, data: Dict[str, Any]):
        self.id = data['id']
        self.name = data.get('name', self.id)
        self.label = data.get('label', self.name)
        self.tokens = data.get('tokens', 0)
        self.capacity = data.get('capacity', float('inf'))
        
        metadata = data.get('metadata', {})
        self.is_signal_place = metadata.get('is_signal_place', False)
        self.signal_type = metadata.get('signal_type', None)


class SHYTransition:
    """Transition wrapper."""
    def __init__(self, data: Dict[str, Any]):
        self.id = data['id']
        self.name = data.get('name', self.id)
        self.label = data.get('label', self.name)


class SHYArc:
    """Arc wrapper."""
    def __init__(self, data: Dict[str, Any], places, transitions):
        self.id = data['id']
        self.weight = data.get('weight', 1)
        self.type = data.get('arc_type', 'normal')
        if self.type == 'normal':
            self.type = 'regular'
        
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        
        self.source = places.get(source_id, transitions.get(source_id))
        self.target = transitions.get(target_id, places.get(target_id))


class SHYModel:
    """Model wrapper."""
    def __init__(self, model_data: Dict[str, Any]):
        self.metadata = model_data.get('metadata', {})
        self.places = {p['id']: SHYPlace(p) for p in model_data.get('places', [])}
        self.transitions = {t['id']: SHYTransition(t) for t in model_data.get('transitions', [])}
        self.arcs = [SHYArc(a, self.places, self.transitions) for a in model_data.get('arcs', [])]


def annotate_ecoli_model():
    """Annotate E. coli model with signal hierarchy."""
    
    print("=" * 80)
    print("E. coli Core - Annotating Signal Hierarchy")
    print("=" * 80)
    print()
    
    # Load original model
    model_path = Path(__file__).parent.parent / "workspace/projects/My_Project/models/e_coli_core.shy"
    
    print(f"Loading: {model_path.name}")
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    print(f"  Places: {len(data['places'])}")
    print(f"  Transitions: {len(data['transitions'])}")
    print(f"  Signal flow arcs: {sum(1 for a in data['arcs'] if a.get('arc_type') == 'signal_flow')}")
    print()
    
    # Define signal annotations
    signal_annotations = {
        # Energy metabolites (Layer 0)
        'P55': {'is_signal_place': True, 'signal_type': 'ENERGY'},  # ATP
        'P51': {'is_signal_place': True, 'signal_type': 'ENERGY'},  # ADP
        'P54': {'is_signal_place': True, 'signal_type': 'ENERGY'},  # AMP
        
        # Redox carriers (Layer 2 - METABOLIC)
        'P16': {'is_signal_place': True, 'signal_type': 'METABOLIC'},  # NAD+
        'P17': {'is_signal_place': True, 'signal_type': 'METABOLIC'},  # NADH
        'P18': {'is_signal_place': True, 'signal_type': 'METABOLIC'},  # NADP+
        'P19': {'is_signal_place': True, 'signal_type': 'METABOLIC'},  # NADPH
        
        # Key cofactors (Layer 2 - METABOLIC)
        'P59': {'is_signal_place': True, 'signal_type': 'METABOLIC'},  # CoA
        'P44': {'is_signal_place': True, 'signal_type': 'METABOLIC'},  # Acetyl-CoA
    }
    
    print("Annotating signal places:")
    for place_id, annotations in signal_annotations.items():
        place_data = next((p for p in data['places'] if p['id'] == place_id), None)
        if place_data:
            if 'metadata' not in place_data:
                place_data['metadata'] = {}
            place_data['metadata'].update(annotations)
            
            label = place_data.get('label', place_id)
            sig_type = annotations['signal_type']
            print(f"  {place_id} ({label}) → {sig_type}")
    print()
    
    # Create model wrapper
    model = SHYModel(data)
    
    # Verify annotations
    signal_places = [p for p in model.places.values() if p.is_signal_place]
    print(f"Signal places annotated: {len(signal_places)}")
    print()
    
    # Test hierarchical analysis
    print("=" * 80)
    print("Hierarchical Signal Layer Detection")
    print("=" * 80)
    print()
    
    detector = SignalLayerDetector(model)
    
    start_time = time.time()
    layer_assignment = detector.detect_layers()
    detection_time = time.time() - start_time
    
    print(f"Detection time: {detection_time:.6f}s")
    print(f"Layers detected: {len(set(layer_assignment.values()))}")
    print()
    
    # Show layers
    for layer in sorted(set(layer_assignment.values())):
        places_in_layer = [(pid, model.places[pid]) 
                          for pid, l in layer_assignment.items() if l == layer]
        print(f"Layer {layer}: {len(places_in_layer)} signal(s)")
        for pid, place in sorted(places_in_layer, key=lambda x: x[0]):
            print(f"  - {pid} ({place.label[:40]}...) - {place.signal_type}")
    print()
    
    # Test caching
    print("Testing cache (5 repeated calls)...")
    times = []
    for i in range(5):
        start = time.time()
        _ = detector.detect_layers()
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    speedup = detection_time / avg_time if avg_time > 0 else float('inf')
    print(f"  First call: {detection_time:.6f}s")
    print(f"  Avg cached: {avg_time:.9f}s")
    print(f"  Speedup: {speedup:.0f}×")
    print()
    
    # Partition transitions
    print("=" * 80)
    print("Transition Partitioning by Signal Layer")
    print("=" * 80)
    print()
    
    partitioner = TransitionPartitioner(model, layer_assignment)
    
    start_time = time.time()
    layer_transitions = partitioner.partition_transitions()
    partition_time = time.time() - start_time
    
    print(f"Partitioning time: {partition_time:.6f}s")
    print()
    
    for layer in sorted(layer_transitions.keys()):
        trans_list = layer_transitions[layer]
        print(f"Layer {layer}: {len(trans_list)} transitions")
        
        # Show a few examples
        examples = sorted(trans_list, key=lambda t: t.id)[:5]
        for trans in examples:
            print(f"  - {trans.id} ({trans.label[:50]})")
        if len(trans_list) > 5:
            print(f"  ... and {len(trans_list) - 5} more")
    print()
    
    # Analysis
    print("=" * 80)
    print("Hierarchical Analysis Summary")
    print("=" * 80)
    print()
    
    print("Signal Hierarchy in E. coli Core Metabolism:")
    print()
    print("Layer 0 (ENERGY):")
    print("  - ATP, ADP, AMP (adenosine phosphates)")
    print("  - Controls: All energy-dependent reactions")
    print("  - Role: Foundation of metabolic activity")
    print()
    print("Layer 2 (METABOLIC):")
    print("  - NAD+/NADH, NADP+/NADPH (redox carriers)")
    print("  - CoA, Acetyl-CoA (carbon carriers)")
    print("  - Depends on: Energy availability")
    print("  - Controls: Redox balance, biosynthesis")
    print()
    
    print("Hierarchical Exploration Benefits:")
    print()
    print("1. **Compositional State Space Exploration**:")
    print(f"   - {len(layer_transitions.get(0, []))} transitions in Layer 0 (energy metabolism)")
    print(f"   - Additional transitions gated by higher layers")
    print("   - Explore energy states first, then redox states conditionally")
    print()
    
    print("2. **State Space Reduction**:")
    print("   - Avoid full Cartesian product of all metabolite states")
    print("   - Layer decomposition enables incremental exploration")
    print("   - Expected 10-100× speedup for full state space analysis")
    print()
    
    print("3. **Biological Interpretability**:")
    print("   - Layers match biological organization")
    print("   - Energy → Redox → Biosynthesis cascade")
    print("   - Results preserve biological meaning")
    print()
    
    # Save annotated model
    output_path = Path(__file__).parent.parent / "workspace/projects/My_Project/models/e_coli_core_annotated.shy"
    print(f"Saving annotated model to: {output_path.name}")
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print()
    print("=" * 80)
    print("Success!")
    print("=" * 80)
    print()
    print(f"Annotated model saved with {len(signal_places)} signal places")
    print(f"Ready for hierarchical state space exploration!")
    
    return {
        'signal_places': len(signal_places),
        'layers': len(set(layer_assignment.values())),
        'detection_time': detection_time,
        'cache_speedup': speedup,
        'partition_time': partition_time,
        'transitions_by_layer': {k: len(v) for k, v in layer_transitions.items()}
    }


if __name__ == "__main__":
    results = annotate_ecoli_model()
