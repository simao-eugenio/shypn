#!/usr/bin/env python3
"""
Test hierarchical exploration on a realistic biological model.

This script creates a more complex biological model (Lambda phage lysogeny decision)
and compares sequential vs parallel hierarchical exploration performance.

Model: Lambda Phage Lysogeny Decision
- 30 places (15 metabolites, 5 signals, 10 regulatory)
- 20 transitions
- 4 signal layers (ENERGY, SPATIAL, QUORUM, REGULATORY)
- Demonstrates: Energy-dependent quorum sensing driving lysis/lysogeny decision
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.topology.behavioral.exploration import (
    SignalLayerDetector,
    TransitionPartitioner,
    HierarchicalExplorer
)


def create_lambda_phage_model() -> Dict[str, Any]:
    """
    Create a realistic Lambda phage lysogeny decision model.
    
    Signal hierarchy:
    - Layer 0 (ENERGY): ATP, GTP (energy availability)
    - Layer 1 (SPATIAL): cI_location (membrane/cytoplasm localization)
    - Layer 2 (QUORUM): autoinducer (cell density signal)
    - Layer 3 (REGULATORY): cro_active, cI_active (genetic switches)
    
    Returns:
        Dict-format Petri net model
    """
    
    places = [
        # Layer 0: Energy metabolites (baseline)
        {"id": "ATP", "tokens": 5, "capacity": 10},
        {"id": "ADP", "tokens": 5, "capacity": 10},
        {"id": "GTP", "tokens": 3, "capacity": 10},
        {"id": "GDP", "tokens": 3, "capacity": 10},
        
        # Layer 0: Signal places - Energy
        {"id": "energy_high", "tokens": 1, "capacity": 1, "is_signal_place": True, "signal_type": "ENERGY"},
        {"id": "energy_low", "tokens": 0, "capacity": 1, "is_signal_place": True, "signal_type": "ENERGY"},
        
        # Layer 1: DNA and protein substrates
        {"id": "cI_gene", "tokens": 2, "capacity": 5},
        {"id": "cro_gene", "tokens": 2, "capacity": 5},
        {"id": "cI_protein", "tokens": 0, "capacity": 10},
        {"id": "cro_protein", "tokens": 0, "capacity": 10},
        
        # Layer 1: Signal places - Spatial
        {"id": "cI_location", "tokens": 0, "capacity": 1, "is_signal_place": True, "signal_type": "SPATIAL"},
        
        # Layer 2: Quorum sensing components
        {"id": "autoinducer_gene", "tokens": 1, "capacity": 3},
        {"id": "autoinducer_internal", "tokens": 0, "capacity": 10},
        {"id": "autoinducer_external", "tokens": 0, "capacity": 20},
        {"id": "receptor", "tokens": 2, "capacity": 5},
        {"id": "receptor_bound", "tokens": 0, "capacity": 5},
        
        # Layer 2: Signal places - Quorum
        {"id": "autoinducer", "tokens": 0, "capacity": 1, "is_signal_place": True, "signal_type": "QUORUM"},
        {"id": "quorum_reached", "tokens": 0, "capacity": 1, "is_signal_place": True, "signal_type": "QUORUM"},
        
        # Layer 3: Regulatory network
        {"id": "cI_mRNA", "tokens": 0, "capacity": 10},
        {"id": "cro_mRNA", "tokens": 0, "capacity": 10},
        {"id": "cI_promoter_free", "tokens": 1, "capacity": 1},
        {"id": "cI_promoter_bound", "tokens": 0, "capacity": 1},
        {"id": "cro_promoter_free", "tokens": 1, "capacity": 1},
        {"id": "cro_promoter_bound", "tokens": 0, "capacity": 1},
        
        # Layer 3: Signal places - Regulatory
        {"id": "cI_active", "tokens": 0, "capacity": 1, "is_signal_place": True, "signal_type": "REGULATORY"},
        {"id": "cro_active", "tokens": 0, "capacity": 1, "is_signal_place": True, "signal_type": "REGULATORY"},
        
        # Output: Decision states
        {"id": "lysogeny", "tokens": 0, "capacity": 1},
        {"id": "lysis", "tokens": 0, "capacity": 1},
        {"id": "undecided", "tokens": 1, "capacity": 1},
    ]
    
    transitions = [
        # Layer 0: Energy metabolism (no signal inputs)
        {
            "id": "ATP_consumption",
            "preset": [("ATP", 1)],
            "postset": [("ADP", 1)],
            "arc_types": []
        },
        {
            "id": "ATP_synthesis",
            "preset": [("ADP", 2)],
            "postset": [("ATP", 2)],
            "arc_types": []
        },
        {
            "id": "GTP_consumption",
            "preset": [("GTP", 1)],
            "postset": [("GDP", 1)],
            "arc_types": []
        },
        
        # Layer 1: Transcription (energy-dependent)
        {
            "id": "cI_transcription",
            "preset": [("cI_gene", 1), ("ATP", 1)],
            "postset": [("cI_gene", 1), ("cI_mRNA", 2), ("ADP", 1)],
            "arc_types": [
                {"source": "energy_high", "target": "cI_transcription", "type": "signal_flow"}
            ]
        },
        {
            "id": "cro_transcription",
            "preset": [("cro_gene", 1), ("ATP", 1)],
            "postset": [("cro_gene", 1), ("cro_mRNA", 2), ("ADP", 1)],
            "arc_types": [
                {"source": "energy_high", "target": "cro_transcription", "type": "signal_flow"}
            ]
        },
        
        # Layer 1: Translation (energy-dependent)
        {
            "id": "cI_translation",
            "preset": [("cI_mRNA", 1), ("GTP", 1)],
            "postset": [("cI_protein", 1), ("GDP", 1)],
            "arc_types": [
                {"source": "energy_high", "target": "cI_translation", "type": "signal_flow"}
            ]
        },
        {
            "id": "cro_translation",
            "preset": [("cro_mRNA", 1), ("GTP", 1)],
            "postset": [("cro_protein", 1), ("GDP", 1)],
            "arc_types": [
                {"source": "energy_high", "target": "cro_translation", "type": "signal_flow"}
            ]
        },
        
        # Layer 2: Quorum sensing (energy + spatial dependent)
        {
            "id": "autoinducer_synthesis",
            "preset": [("autoinducer_gene", 1), ("ATP", 1)],
            "postset": [("autoinducer_gene", 1), ("autoinducer_internal", 2), ("ADP", 1)],
            "arc_types": [
                {"source": "energy_high", "target": "autoinducer_synthesis", "type": "signal_flow"}
            ]
        },
        {
            "id": "autoinducer_export",
            "preset": [("autoinducer_internal", 1)],
            "postset": [("autoinducer_external", 1)],
            "arc_types": [
                {"source": "cI_location", "target": "autoinducer_export", "type": "signal_flow"}
            ]
        },
        {
            "id": "autoinducer_binding",
            "preset": [("autoinducer_external", 2), ("receptor", 1)],
            "postset": [("receptor_bound", 1)],
            "arc_types": []
        },
        {
            "id": "quorum_activation",
            "preset": [("receptor_bound", 3)],
            "postset": [("receptor_bound", 3), ("autoinducer", 1)],
            "arc_types": []
        },
        
        # Layer 3: Regulatory decisions (all upper layers)
        {
            "id": "cI_activation",
            "preset": [("cI_protein", 3)],
            "postset": [("cI_protein", 3), ("cI_active", 1)],
            "arc_types": [
                {"source": "quorum_reached", "target": "cI_activation", "type": "signal_flow"}
            ]
        },
        {
            "id": "cro_activation",
            "preset": [("cro_protein", 3)],
            "postset": [("cro_protein", 3), ("cro_active", 1)],
            "arc_types": [
                {"source": "energy_high", "target": "cro_activation", "type": "signal_flow"}
            ]
        },
        
        # Layer 3: Promoter binding (regulatory)
        {
            "id": "cI_binds_promoter",
            "preset": [("cI_promoter_free", 1)],
            "postset": [("cI_promoter_bound", 1)],
            "arc_types": [
                {"source": "cI_active", "target": "cI_binds_promoter", "type": "signal_flow"}
            ]
        },
        {
            "id": "cro_binds_promoter",
            "preset": [("cro_promoter_free", 1)],
            "postset": [("cro_promoter_bound", 1)],
            "arc_types": [
                {"source": "cro_active", "target": "cro_binds_promoter", "type": "signal_flow"}
            ]
        },
        
        # Layer 3: Decision outcomes (regulatory)
        {
            "id": "commit_to_lysogeny",
            "preset": [("undecided", 1), ("cI_promoter_bound", 1)],
            "postset": [("lysogeny", 1)],
            "arc_types": [
                {"source": "cI_active", "target": "commit_to_lysogeny", "type": "signal_flow"}
            ]
        },
        {
            "id": "commit_to_lysis",
            "preset": [("undecided", 1), ("cro_promoter_bound", 1)],
            "postset": [("lysis", 1)],
            "arc_types": [
                {"source": "cro_active", "target": "commit_to_lysis", "type": "signal_flow"}
            ]
        },
        
        # Layer 0: Degradation (no signals)
        {
            "id": "protein_degradation",
            "preset": [("cI_protein", 1)],
            "postset": [],
            "arc_types": []
        },
        {
            "id": "mRNA_degradation",
            "preset": [("cI_mRNA", 1)],
            "postset": [],
            "arc_types": []
        },
    ]
    
    # Build arc list from preset/postset and signal flow arcs
    arcs = []
    arc_id = 0
    
    for trans in transitions:
        trans_id = trans["id"]
        
        # Standard input arcs (consumption)
        for place_id, weight in trans["preset"]:
            arcs.append({
                "id": f"arc_{arc_id}",
                "source": place_id,
                "target": trans_id,
                "weight": weight,
                "type": "regular"
            })
            arc_id += 1
        
        # Standard output arcs (production)
        for place_id, weight in trans["postset"]:
            arcs.append({
                "id": f"arc_{arc_id}",
                "source": trans_id,
                "target": place_id,
                "weight": weight,
                "type": "regular"
            })
            arc_id += 1
        
        # Signal flow arcs
        for signal_arc in trans.get("arc_types", []):
            arcs.append({
                "id": f"arc_{arc_id}",
                "source": signal_arc["source"],
                "target": signal_arc["target"],
                "weight": 1,
                "type": "signal_flow"
            })
            arc_id += 1
    
    return {
        "places": places,
        "transitions": transitions,
        "arcs": arcs
    }


class SimplePlace:
    """Simple place wrapper for dict-based models."""
    def __init__(self, data: Dict[str, Any]):
        self.id = data['id']
        self.tokens = data.get('tokens', 0)
        self.capacity = data.get('capacity', float('inf'))
        self.is_signal_place = data.get('is_signal_place', False)
        self.signal_type = data.get('signal_type', None)


class SimpleTransition:
    """Simple transition wrapper for dict-based models."""
    def __init__(self, data: Dict[str, Any]):
        self.id = data['id']


class SimpleArc:
    """Simple arc wrapper for dict-based models."""
    def __init__(self, data: Dict[str, Any], places, transitions):
        self.id = data['id']
        self.weight = data.get('weight', 1)
        self.type = data.get('type', 'regular')
        
        # Resolve source and target
        source_id = data['source']
        target_id = data['target']
        
        self.source = places.get(source_id, transitions.get(source_id))
        self.target = transitions.get(target_id, places.get(target_id))


class SimpleModel:
    """Simple model wrapper to match expected interface."""
    def __init__(self, model_dict: Dict[str, Any]):
        self.places = {p['id']: SimplePlace(p) for p in model_dict['places']}
        self.transitions = {t['id']: SimpleTransition(t) for t in model_dict['transitions']}
        self.arcs = [SimpleArc(a, self.places, self.transitions) for a in model_dict['arcs']]
        self._dict = model_dict


def test_lambda_phage():
    """Test hierarchical exploration on Lambda phage model."""
    
    print("=" * 80)
    print("Lambda Phage Lysogeny Decision Model - Hierarchical Exploration Test")
    print("=" * 80)
    print()
    
    # Create model
    print("Creating Lambda phage model...")
    model_dict = create_lambda_phage_model()
    model = SimpleModel(model_dict)
    
    print(f"  Places: {len(model.places)}")
    print(f"  Transitions: {len(model.transitions)}")
    print(f"  Arcs: {len(model.arcs)}")
    
    signal_places = [p for p in model.places.values() if p.is_signal_place]
    print(f"  Signal places: {len(signal_places)}")
    for sp in signal_places:
        print(f"    - {sp.id} ({sp.signal_type})")
    print()
    
    # Initial marking
    initial_marking = {pid: p.tokens for pid, p in model.places.items()}
    
    # Test 1: Signal layer detection
    print("Step 1: Detecting signal layers...")
    detector = SignalLayerDetector(model)
    layer_assignment = detector.detect_layers()
    
    print(f"  Layers detected: {len(set(layer_assignment.values()))}")
    for layer in sorted(set(layer_assignment.values())):
        places_in_layer = [pid for pid, l in layer_assignment.items() if l == layer]
        print(f"    Layer {layer}: {len(places_in_layer)} signals")
        for pid in sorted(places_in_layer):
            signal_type = model.places[pid].signal_type if pid in model.places else 'N/A'
            print(f"      - {pid} ({signal_type})")
    print()
    
    # Test 2: Transition partitioning
    print("Step 2: Partitioning transitions by layer...")
    partitioner = TransitionPartitioner(model, layer_assignment)
    layer_transitions = partitioner.partition_transitions()
    
    for layer in sorted(layer_transitions.keys()):
        trans_ids = layer_transitions[layer]
        print(f"  Layer {layer}: {len(trans_ids)} transitions")
        for trans in sorted(trans_ids, key=lambda t: t.id):
            print(f"    - {trans.id}")
    print()
    
    # Test 3: Sequential hierarchical exploration
    print("Step 3: Sequential hierarchical exploration...")
    explorer_seq = HierarchicalExplorer(model)
    
    start_time = time.time()
    result_seq = explorer_seq.explore(
        initial_marking,
        max_states=10000,
        max_depth=50,
        find_deadlocks=True,
        use_parallel=False
    )
    seq_time = time.time() - start_time
    
    print(f"  Execution time: {seq_time:.4f}s")
    print(f"  Total states: {result_seq['total_states']}")
    print(f"  Total transitions: {result_seq['total_transitions']}")
    print(f"  Deadlocks: {len(result_seq['deadlocks'])}")
    print(f"  Layer count: {result_seq['layer_count']}")
    print()
    
    # States per layer
    if 'layer_stats' in result_seq:
        print("  States per layer:")
        for layer_num in sorted(result_seq['layer_stats'].keys()):
            stats = result_seq['layer_stats'][layer_num]
            print(f"    Layer {layer_num}: {stats['states']} states, "
                  f"{stats['transitions']} transitions")
    print()
    
    # Test 4: Parallel hierarchical exploration
    print("Step 4: Parallel hierarchical exploration (4 workers)...")
    explorer_par = HierarchicalExplorer(model)
    
    start_time = time.time()
    result_par = explorer_par.explore(
        initial_marking,
        max_states=10000,
        max_depth=50,
        find_deadlocks=True,
        use_parallel=True,
        num_workers=4
    )
    par_time = time.time() - start_time
    
    print(f"  Execution time: {par_time:.4f}s")
    print(f"  Total states: {result_par['total_states']}")
    print(f"  Total transitions: {result_par['total_transitions']}")
    print(f"  Deadlocks: {len(result_par['deadlocks'])}")
    print(f"  Layer count: {result_par['layer_count']}")
    print()
    
    # Comparison
    print("=" * 80)
    print("Performance Comparison")
    print("=" * 80)
    print()
    
    speedup = ((seq_time - par_time) / seq_time) * 100
    print(f"Sequential time:  {seq_time:.4f}s")
    print(f"Parallel time:    {par_time:.4f}s")
    print(f"Speedup:          {speedup:.1f}% faster")
    print()
    
    # Verify correctness
    print("Correctness checks:")
    states_match = result_seq['total_states'] == result_par['total_states']
    trans_match = result_seq['total_transitions'] == result_par['total_transitions']
    deadlock_match = len(result_seq['deadlocks']) == len(result_par['deadlocks'])
    
    print(f"  States match:      {'✅' if states_match else '❌'}")
    print(f"  Transitions match: {'✅' if trans_match else '❌'}")
    print(f"  Deadlocks match:   {'✅' if deadlock_match else '❌'}")
    print()
    
    if states_match and trans_match and deadlock_match:
        print("✅ All correctness checks PASSED!")
    else:
        print("❌ Some correctness checks FAILED!")
    print()
    
    # Biological interpretation
    print("=" * 80)
    print("Biological Interpretation")
    print("=" * 80)
    print()
    
    print("Signal Hierarchy (Lambda Phage Lysogeny Decision):")
    print()
    print("  Layer 0 (ENERGY):")
    print("    - ATP/GTP availability controls all energy-dependent processes")
    print("    - Foundation for all metabolic activity")
    print()
    print("  Layer 1 (SPATIAL):")
    print("    - Protein localization (cI location)")
    print("    - Affects autoinducer export and protein function")
    print()
    print("  Layer 2 (QUORUM):")
    print("    - Cell density sensing via autoinducer")
    print("    - Coordinates population-level decisions")
    print()
    print("  Layer 3 (REGULATORY):")
    print("    - CI vs Cro competition")
    print("    - Binary decision: lysogeny (dormancy) vs lysis (reproduction)")
    print()
    
    print("Key Insights:")
    print("  - Energy availability gates all processes (Layer 0)")
    print("  - Quorum sensing requires energy + localization (Layers 0-2)")
    print("  - Final decision depends on entire hierarchy (Layer 3)")
    print("  - Hierarchical exploration reduces state space by layer decomposition")
    print()
    
    return {
        "model_stats": {
            "places": len(model.places),
            "transitions": len(model.transitions),
            "arcs": len(model.arcs),
            "signal_places": len(signal_places),
            "layers": len(set(layer_assignment.values()))
        },
        "sequential": {
            "time": seq_time,
            "states": result_seq['total_states'],
            "transitions": result_seq['total_transitions'],
            "deadlocks": len(result_seq['deadlocks'])
        },
        "parallel": {
            "time": par_time,
            "states": result_par['total_states'],
            "transitions": result_par['total_transitions'],
            "deadlocks": len(result_par['deadlocks'])
        },
        "speedup_percent": speedup,
        "correctness": states_match and trans_match and deadlock_match
    }


if __name__ == "__main__":
    results = test_lambda_phage()
    
    # Save results
    output_dir = Path(__file__).parent.parent / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "lambda_phage_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    print()
    print("=" * 80)
    print("Test complete! 🚀")
    print("=" * 80)
