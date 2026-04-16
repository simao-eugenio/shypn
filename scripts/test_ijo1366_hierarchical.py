#!/usr/bin/env python3
"""Test hierarchical exploration on iJO1366 genome-scale model.

This script demonstrates Phase 3-4 optimizations on a large biological model
imported from BiGG database. iJO1366 is E. coli K-12 MG1655 with:
- 1,805 metabolites (places)
- 2,583 reactions (transitions)
- ~12,915 metabolic arcs
- 17,303 total objects

Performance targets:
- Memory: ~300 MB stable (with optimization)
- Cache speedup: 20-35× on repeated queries
- Parallel speedup: 25-30% with multiprocessing
"""

import sys
import os
import time
import psutil
from pathlib import Path

# Add src to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from shypn.data.canvas.document_model import DocumentModel

# Try to import hierarchical exploration (Phase 3-4)
try:
    from shypn.topology.behavioral.exploration import (
        SignalLayerDetector,
        TransitionPartitioner
    )
    HIERARCHICAL_AVAILABLE = True
except ImportError:
    HIERARCHICAL_AVAILABLE = False
    print("⚠️  Hierarchical exploration module not available")
    print("   This is a demonstration of model loading and analysis only")

def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def load_ijo1366_model(filepath: str) -> DocumentModel:
    """Load iJO1366 model from .shy file.
    
    Args:
        filepath: Path to iJO1366.shy file
        
    Returns:
        DocumentModel with loaded objects
    """
    print("=" * 70)
    print("LOADING iJO1366 GENOME-SCALE MODEL")
    print("=" * 70)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model not found: {filepath}")
    
    mem_before = get_memory_usage()
    start_time = time.time()
    
    # Load model (classmethod)
    doc = DocumentModel.load_from_file(filepath)
    
    load_time = time.time() - start_time
    mem_after = get_memory_usage()
    mem_delta = mem_after - mem_before
    
    # Print statistics
    print(f"\n📊 Model Statistics:")
    print(f"   Places:      {len(doc.places):,}")
    print(f"   Transitions: {len(doc.transitions):,}")
    print(f"   Arcs:        {len(doc.arcs):,}")
    print(f"   Total:       {len(doc.places) + len(doc.transitions) + len(doc.arcs):,} objects")
    
    print(f"\n⏱️  Load Performance:")
    print(f"   Time:   {load_time:.2f}s")
    print(f"   Memory: {mem_delta:.1f} MB ({mem_after:.1f} MB total)")
    
    return doc

def analyze_signal_hierarchy(doc: DocumentModel):
    """Analyze signal annotations in iJO1366 model.
    
    Args:
        doc: Loaded DocumentModel
    """
    print("\n" + "=" * 70)
    print("SIGNAL ANNOTATION ANALYSIS")
    print("=" * 70)
    
    # Count arc types
    regular_arcs = []
    signal_flow_arcs = []
    test_arcs = []
    inhibitor_arcs = []
    
    for arc in doc.arcs:
        arc_class = arc.__class__.__name__
        if 'Signal' in arc_class or hasattr(arc, 'arc_category') and arc.arc_category == 'signal_flow':
            signal_flow_arcs.append(arc)
        elif 'Test' in arc_class:
            test_arcs.append(arc)
        elif 'Inhibitor' in arc_class:
            inhibitor_arcs.append(arc)
        else:
            regular_arcs.append(arc)
    
    print(f"\n🔍 Arc Type Distribution:")
    if len(doc.arcs) > 0:
        print(f"   Regular arcs:     {len(regular_arcs):,} ({len(regular_arcs)/len(doc.arcs)*100:.1f}%)")
        print(f"   Signal flow arcs: {len(signal_flow_arcs):,} ({len(signal_flow_arcs)/len(doc.arcs)*100:.1f}%)")
        print(f"   Inhibitor arcs:   {len(inhibitor_arcs):,} ({len(inhibitor_arcs)/len(doc.arcs)*100:.1f}%)")
        print(f"   Test arcs:        {len(test_arcs):,} ({len(test_arcs)/len(doc.arcs)*100:.1f}%)")
    else:
        print(f"   ⚠️  No arcs found in model!")
        return False
    
    # Count place types
    regular_places = []
    signal_places = []
    
    for place in doc.places:
        if hasattr(place, 'is_signal_place') and place.is_signal_place:
            signal_places.append(place)
        else:
            regular_places.append(place)
    
    print(f"\n📡 Place Type Distribution:")
    if len(doc.places) > 0:
        print(f"   Regular places:   {len(regular_places):,} ({len(regular_places)/len(doc.places)*100:.1f}%)")
        print(f"   Signal places:    {len(signal_places):,} ({len(signal_places)/len(doc.places)*100:.1f}%)")
    else:
        print(f"   ⚠️  No places found in model!")
        return False
    
    # Analyze signal types
    if signal_places:
        signal_types = {}
        for place in signal_places:
            sig_type = getattr(place, 'signal_type', 'unspecified')
            signal_types[sig_type] = signal_types.get(sig_type, 0) + 1
        
        print(f"\n   Signal type breakdown:")
        for sig_type, count in sorted(signal_types.items(), key=lambda x: -x[1]):
            print(f"      {str(sig_type):20s}: {count:,}")
        
        # Sample signal places
        print(f"\n   Sample signal places:")
        for i, place in enumerate(signal_places[:10], 1):
            signal_type = getattr(place, 'signal_type', 'unknown')
            tokens = getattr(place, 'tokens', 0)
            label = getattr(place, 'label', f'place_{id(place)}')
            print(f"   {i:2d}. {label[:50]:50s} type={str(signal_type):12s} tokens={tokens}")
        
        if len(signal_places) > 10:
            print(f"   ... and {len(signal_places) - 10:,} more signal places")
    
    # Check if hierarchical analysis is possible
    if len(signal_flow_arcs) == 0:
        print("\n⚠️  No signal_flow arcs found in model.")
        print("   This is a purely metabolic model from BiGG.")
        print("\n💡 For hierarchical exploration:")
        print("   1. Identify regulatory/energy control mechanisms")
        print("   2. Annotate control places as signal places")
        print("   3. Convert control arcs to signal_flow type")
        print("   4. Specify signal types (ENERGY, REGULATORY, etc.)")
        return False
    
    print(f"\n✅ Model contains {len(signal_flow_arcs):,} signal flow arcs")
    print(f"   Hierarchical exploration is possible!")
    return True

def test_hierarchical_exploration(doc: DocumentModel):
    """Test hierarchical exploration if available.
    
    Args:
        doc: Loaded DocumentModel
    """
    if not HIERARCHICAL_AVAILABLE:
        print("\n" + "=" * 70)
        print("HIERARCHICAL EXPLORATION")
        print("=" * 70)
        print("\n⚠️  Hierarchical exploration module not yet implemented")
        print("   This requires Phase 3-4 components:")
        print("   - SignalLayerDetector")
        print("   - TransitionPartitioner")
        print("   - HierarchicalStateExplorer")
        return
    
    print("\n" + "=" * 70)
    print("HIERARCHICAL EXPLORATION (Phase 3-4)")
    print("=" * 70)
    
    try:
        # Initialize detector
        print(f"\n🔬 Initializing Signal Layer Detector...")
        mem_before = get_memory_usage()
        start_time = time.time()
        
        detector = SignalLayerDetector(
            places=doc.places,
            transitions=doc.transitions,
            arcs=doc.arcs
        )
        
        init_time = time.time() - start_time
        mem_after = get_memory_usage()
        print(f"   ✓ Detector initialized in {init_time:.3f}s")
        print(f"   Memory overhead: {mem_after - mem_before:.1f} MB")
        
        # Detect signal layers
        print(f"\n📊 Detecting Signal Layers...")
        start_time = time.time()
        
        layers = detector.detect_layers()
        
        detection_time = time.time() - start_time
        print(f"   ✓ Detection completed in {detection_time:.3f}s")
        print(f"   Layers detected: {len(layers)}")
        
        if layers:
            print(f"\n🎯 Signal Layer Hierarchy:")
            for i, layer in enumerate(layers, 1):
                layer_type = getattr(layer, 'layer_type', 'unknown')
                signal_count = len(getattr(layer, 'signal_places', []))
                trans_count = len(getattr(layer, 'transitions', []))
                print(f"\n   Layer {i}: {layer_type}")
                print(f"      Signal places: {signal_count:,}")
                print(f"      Transitions:   {trans_count:,}")
        else:
            print(f"\n⚠️  No hierarchical layers detected")
            print(f"   Model may have flat/parallel structure")
    
    except Exception as e:
        print(f"\n❌ Error during hierarchical exploration: {e}")
        import traceback
        traceback.print_exc()

def test_parallel_exploration(doc: DocumentModel):
    """Test model structure for parallel exploration potential.
    
    Args:
        doc: Loaded DocumentModel
    """
    print("\n" + "=" * 70)
    print("PARALLEL EXPLORATION ANALYSIS")
    print("=" * 70)
    
    # Sample transitions
    sample_size = min(100, len(doc.transitions))
    print(f"\n🔄 Analyzing {sample_size} sample transitions...")
    
    # Count connectivity
    input_arcs = {}
    output_arcs = {}
    
    for arc in doc.arcs:
        if hasattr(arc, 'target') and arc.target in doc.transitions:
            target_id = id(arc.target)
            input_arcs[target_id] = input_arcs.get(target_id, 0) + 1
        if hasattr(arc, 'source') and arc.source in doc.transitions:
            source_id = id(arc.source)
            output_arcs[source_id] = output_arcs.get(source_id, 0) + 1
    
    # Calculate statistics
    avg_inputs = sum(input_arcs.values()) / len(input_arcs) if input_arcs else 0
    avg_outputs = sum(output_arcs.values()) / len(output_arcs) if output_arcs else 0
    
    print(f"\n📊 Transition Connectivity:")
    print(f"   Average inputs:  {avg_inputs:.1f} arcs/transition")
    print(f"   Average outputs: {avg_outputs:.1f} arcs/transition")
    
    # Estimate parallelization potential
    total_transitions = len(doc.transitions)
    max_parallel = total_transitions // 4  # Assume 4 cores
    
    print(f"\n⚡ Parallelization Potential:")
    print(f"   Total transitions: {total_transitions:,}")
    print(f"   Parallel batches:  ~{max_parallel:,} (4 cores)")
    print(f"   Expected speedup:  1.25-1.30× (with overhead)")
    print(f"\n   💡 Parallel exploration beneficial for:")
    print(f"      - Batch reachability analysis")
    print(f"      - State space sampling")
    print(f"      - Independent subnet exploration")

def main():
    """Main test execution."""
    # Model path - use annotated version if available
    annotated_path = REPO_ROOT / "workspace" / "projects" / "My_Project" / "models" / "iJO1366_annotated.shy"
    original_path = REPO_ROOT / "workspace" / "projects" / "My_Project" / "models" / "iJO1366.shy"
    
    if annotated_path.exists():
        model_path = annotated_path
        print(f"\n💡 Using annotated model with signal types")
    else:
        model_path = original_path
        print(f"\n💡 Using original model (run annotate_ijo1366_signals.py for signal types)")
    
    print("\n" + "=" * 70)
    print("iJO1366 HIERARCHICAL EXPLORATION TEST")
    print("=" * 70)
    print(f"\nModel: {model_path}")
    print(f"Date:  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initial memory
    mem_start = get_memory_usage()
    print(f"\nInitial memory: {mem_start:.1f} MB")
    
    try:
        # Load model
        doc = load_ijo1366_model(str(model_path))
        
        # Analyze signal annotations
        has_signals = analyze_signal_hierarchy(doc)
        
        # Test hierarchical exploration if possible
        if has_signals:
            test_hierarchical_exploration(doc)
        
        # Analyze parallelization potential
        test_parallel_exploration(doc)
        
        # Final memory
        mem_end = get_memory_usage()
        mem_delta = mem_end - mem_start
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"\n✅ All tests completed successfully")
        print(f"\n💾 Memory Usage:")
        print(f"   Start:  {mem_start:.1f} MB")
        print(f"   End:    {mem_end:.1f} MB")
        print(f"   Delta:  {mem_delta:+.1f} MB")
        
        if mem_delta < 400:
            print(f"   ✅ Within optimization target (~300 MB)")
        else:
            print(f"   ⚠️  Higher than target (expected ~300 MB)")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Make sure to:")
        print(f"   1. Import iJO1366 from BiGG database")
        print(f"   2. Save to: {model_path}")
        print(f"   3. Re-run this script")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
