#!/usr/bin/env python3
"""
Test hierarchical exploration on E. coli core metabolism model.

This script loads the real E. coli core model and analyzes:
1. Signal layer detection (if signals are present)
2. Transition partitioning by layer
3. Model statistics and structure

The E. coli core model is a real biological network with:
- 72 metabolic species (places)
- 95 reactions (transitions)
- Central metabolism pathways
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.topology.behavioral.exploration import (
    SignalLayerDetector,
    TransitionPartitioner
)


class SHYPlace:
    """Place wrapper for .shy model format."""
    def __init__(self, data: Dict[str, Any]):
        self.id = data['id']
        self.name = data.get('name', self.id)
        self.label = data.get('label', self.name)
        self.tokens = data.get('tokens', 0)
        self.capacity = data.get('capacity', float('inf'))
        
        # Check for signal place designation
        metadata = data.get('metadata', {})
        self.is_signal_place = metadata.get('is_signal_place', False)
        self.signal_type = metadata.get('signal_type', None)


class SHYTransition:
    """Transition wrapper for .shy model format."""
    def __init__(self, data: Dict[str, Any]):
        self.id = data['id']
        self.name = data.get('name', self.id)
        self.label = data.get('label', self.name)


class SHYArc:
    """Arc wrapper for .shy model format."""
    def __init__(self, data: Dict[str, Any], places, transitions):
        self.id = data['id']
        self.weight = data.get('weight', 1)
        
        # Determine arc type (check both direct field and metadata)
        self.type = data.get('arc_type', 'normal')
        if self.type == 'normal':
            self.type = 'regular'
        
        # Resolve source and target
        source_id = data.get('source_id', data.get('source'))
        target_id = data.get('target_id', data.get('target'))
        
        self.source = places.get(source_id, transitions.get(source_id))
        self.target = transitions.get(target_id, places.get(target_id))


class SHYModel:
    """Model wrapper for .shy format."""
    def __init__(self, model_data: Dict[str, Any]):
        self.metadata = model_data.get('metadata', {})
        
        # Load places
        self.places = {}
        for p in model_data.get('places', []):
            place = SHYPlace(p)
            self.places[place.id] = place
        
        # Load transitions
        self.transitions = {}
        for t in model_data.get('transitions', []):
            trans = SHYTransition(t)
            self.transitions[trans.id] = trans
        
        # Load arcs
        self.arcs = []
        for a in model_data.get('arcs', []):
            arc = SHYArc(a, self.places, self.transitions)
            self.arcs.append(arc)


def load_shy_model(file_path: str) -> SHYModel:
    """Load a .shy format model."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return SHYModel(data)


def analyze_ecoli_core():
    """Analyze E. coli core metabolism model."""
    
    print("=" * 80)
    print("E. coli Core Metabolism - Hierarchical Analysis")
    print("=" * 80)
    print()
    
    # Load model
    model_path = Path(__file__).parent.parent / "workspace/projects/My_Project/models/e_coli_core.shy"
    
    print(f"Loading model: {model_path.name}")
    model = load_shy_model(str(model_path))
    
    print()
    print("Model Statistics:")
    print(f"  Model ID: {model.metadata.get('model_id', 'N/A')}")
    print(f"  Source: {model.metadata.get('data_source', 'N/A')}")
    print(f"  Places: {len(model.places)}")
    print(f"  Transitions: {len(model.transitions)}")
    print(f"  Arcs: {len(model.arcs)}")
    
    # Check compartments
    compartments = model.metadata.get('compartments', [])
    print(f"  Compartments: {', '.join(compartments) if compartments else 'N/A'}")
    print()
    
    # Analyze signal places
    signal_places = [p for p in model.places.values() if p.is_signal_place]
    print(f"Signal Places: {len(signal_places)}")
    
    if signal_places:
        print()
        for sp in signal_places:
            print(f"  - {sp.id} ({sp.label})")
            print(f"    Type: {sp.signal_type}")
        print()
        
        # Run hierarchical analysis
        print("=" * 80)
        print("Hierarchical Analysis")
        print("=" * 80)
        print()
        
        # Step 1: Detect layers
        print("Step 1: Detecting signal layers...")
        detector = SignalLayerDetector(model)
        
        start_time = time.time()
        layer_assignment = detector.detect_layers()
        detection_time = time.time() - start_time
        
        print(f"  Detection time: {detection_time:.6f}s")
        print(f"  Layers detected: {len(set(layer_assignment.values()))}")
        print()
        
        for layer in sorted(set(layer_assignment.values())):
            places_in_layer = [(pid, model.places[pid].signal_type) 
                              for pid, l in layer_assignment.items() if l == layer]
            print(f"  Layer {layer}: {len(places_in_layer)} signal(s)")
            for pid, sig_type in sorted(places_in_layer):
                place = model.places[pid]
                print(f"    - {pid} ({place.label}) - {sig_type}")
        print()
        
        # Step 2: Partition transitions
        print("Step 2: Partitioning transitions by layer...")
        partitioner = TransitionPartitioner(model, layer_assignment)
        
        start_time = time.time()
        layer_transitions = partitioner.partition_transitions()
        partition_time = time.time() - start_time
        
        print(f"  Partitioning time: {partition_time:.6f}s")
        print()
        
        for layer in sorted(layer_transitions.keys()):
            trans_list = layer_transitions[layer]
            print(f"  Layer {layer}: {len(trans_list)} transition(s)")
            if len(trans_list) <= 10:
                for trans in sorted(trans_list, key=lambda t: t.id)[:10]:
                    print(f"    - {trans.id} ({trans.label})")
            else:
                print(f"    (showing first 10 of {len(trans_list)})")
                for trans in sorted(trans_list, key=lambda t: t.id)[:10]:
                    print(f"    - {trans.id} ({trans.label})")
        print()
        
    else:
        print("  No signal places found in model.")
        print()
        print("Note: This is a standard metabolic model without signal hierarchy.")
        print("Signal places can be added to represent:")
        print("  - Energy availability (ATP/ADP ratio)")
        print("  - Redox state (NADH/NAD+ ratio)")
        print("  - Regulatory signals (allosteric control)")
        print("  - Compartment-specific conditions")
        print()
        print("To enable hierarchical exploration, annotate key metabolites as")
        print("signal places with appropriate signal_type metadata.")
        print()
    
    # Analyze model structure
    print("=" * 80)
    print("Model Structure Analysis")
    print("=" * 80)
    print()
    
    # Count arc types
    arc_types = {}
    for arc in model.arcs:
        arc_type = arc.type
        arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
    
    print("Arc Types:")
    for arc_type, count in sorted(arc_types.items()):
        print(f"  {arc_type}: {count}")
    print()
    
    # Sample places
    print("Sample Places (first 10):")
    for i, (pid, place) in enumerate(list(model.places.items())[:10]):
        print(f"  {pid}: {place.label} (tokens={place.tokens})")
    print()
    
    # Sample transitions
    print("Sample Transitions (first 10):")
    for i, (tid, trans) in enumerate(list(model.transitions.items())[:10]):
        print(f"  {tid}: {trans.label}")
    print()
    
    # Pathway analysis
    print("=" * 80)
    print("Biological Context")
    print("=" * 80)
    print()
    
    print("E. coli Core Metabolism Pathways:")
    print("  - Glycolysis (glucose → pyruvate)")
    print("  - TCA cycle (citric acid cycle)")
    print("  - Pentose phosphate pathway")
    print("  - Oxidative phosphorylation")
    print("  - Amino acid biosynthesis (partial)")
    print("  - Biomass production")
    print()
    
    print("Potential Signal Hierarchy:")
    print("  Layer 0 (ENERGY): ATP, GTP availability")
    print("  Layer 1 (SPATIAL): Membrane transport, compartmentalization")
    print("  Layer 2 (METABOLIC): Redox state, cofactor availability")
    print("  Layer 3 (REGULATORY): Allosteric control, feedback inhibition")
    print()
    
    print("To demonstrate hierarchical exploration on this model:")
    print("  1. Annotate ATP/GTP as ENERGY signals")
    print("  2. Annotate NADH/NAD+ as METABOLIC signals")
    print("  3. Annotate key intermediates as REGULATORY signals")
    print("  4. Add signal_flow arcs for known regulatory interactions")
    print()
    
    print("=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    analyze_ecoli_core()
