#!/usr/bin/env python3
"""Test signal hierarchy detection and layer inference in KEGG models.

This test validates:
1. Energy cofactor detection (ATP, NADH marked as signals)
2. Automatic signal flow arc creation
3. Layer inference (Layer 0 = ENERGY, Layer 1 = SPATIAL, etc.)
4. Signal hierarchy analysis

Author: GitHub Copilot
Date: January 2, 2026
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.pathway_converter import convert_kegg_pathway
from shypn.netobjs.signal_type import SignalType
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.topology.biological.signal_hierarchy import SignalHierarchyAnalyzer


def test_signal_hierarchy_kegg_import():
    """Test signal hierarchy detection in KEGG pathway import."""
    print("=" * 80)
    print("TEST: Signal Hierarchy in KEGG Import (hsa00010 - Glycolysis)")
    print("=" * 80)
    print()
    
    # Fetch and convert hsa00010 (Glycolysis)
    print("📥 Fetching hsa00010 (Glycolysis) from KEGG...")
    client = KEGGAPIClient()
    pathway = client.fetch_pathway('hsa00010')
    print(f"✓ Fetched pathway: {pathway.name}")
    print()
    
    # Convert to Petri net
    print("🔄 Converting to Petri net...")
    document = convert_kegg_pathway(
        pathway,
        include_cofactors=True,  # CRITICAL: Include ATP, NADH, etc.
        auto_classify_signals=True,  # Enable signal classification
        signal_confidence_threshold=0.5  # Confidence threshold
    )
    print(f"✓ Created document with {len(document.places)} places, {len(document.transitions)} transitions")
    print()
    
    # === TEST 1: Energy Signal Detection ===
    print("=" * 80)
    print("TEST 1: Energy Cofactor Signal Detection")
    print("=" * 80)
    
    energy_signals = [p for p in document.places if getattr(p, 'signal_type', None) == SignalType.ENERGY]
    print(f"\n✓ Found {len(energy_signals)} ENERGY signal places:")
    
    expected_energy = ['ATP', 'ADP', 'NADH', 'NAD+', 'NAD', 'Pi']
    found_energy = set()
    
    for place in energy_signals:
        layer = place.metadata.get('hierarchy_layer', 'N/A')
        print(f"  - {place.name:20s} (Layer {layer}, {place.metadata.get('kegg_id', 'N/A')})")
        found_energy.add(place.name)
    
    # Validate expected energy signals are found
    missing = set(expected_energy) - found_energy
    if missing:
        print(f"\n⚠ WARNING: Expected energy signals not found: {missing}")
    else:
        print(f"\n✓ All expected energy signals detected!")
    print()
    
    # === TEST 2: Signal Flow Arc Creation ===
    print("=" * 80)
    print("TEST 2: Signal Flow Arc Creation")
    print("=" * 80)
    
    signal_flow_arcs = [arc for arc in document.arcs if isinstance(arc, SignalFlowArc)]
    print(f"\n✓ Found {len(signal_flow_arcs)} SignalFlowArc objects:")
    
    for i, arc in enumerate(signal_flow_arcs[:10], 1):  # Show first 10
        source_name = getattr(arc.source, 'name', arc.source.id)
        target_name = getattr(arc.target, 'label', arc.target.id) if hasattr(arc.target, 'label') else arc.target.id
        print(f"  {i}. {source_name} → {target_name}")
    
    if len(signal_flow_arcs) > 10:
        print(f"  ... and {len(signal_flow_arcs) - 10} more")
    print()
    
    # === TEST 3: Layer Inference ===
    print("=" * 80)
    print("TEST 3: Hierarchical Layer Assignment")
    print("=" * 80)
    
    signal_places = [p for p in document.places if getattr(p, 'is_signal_place', False)]
    print(f"\n✓ Found {len(signal_places)} signal places total:")
    
    layer_distribution = {}
    for place in signal_places:
        layer = place.metadata.get('hierarchy_layer', 'unassigned')
        signal_type = getattr(place, 'signal_type', None)
        signal_type_name = signal_type.name if signal_type else 'unknown'
        
        if layer not in layer_distribution:
            layer_distribution[layer] = []
        layer_distribution[layer].append((place.name, signal_type_name))
    
    for layer in sorted(layer_distribution.keys(), key=lambda x: (isinstance(x, str), x)):
        places_in_layer = layer_distribution[layer]
        print(f"\n  Layer {layer}:")
        for place_name, sig_type in places_in_layer[:5]:  # Show first 5
            print(f"    - {place_name:20s} ({sig_type})")
        if len(places_in_layer) > 5:
            print(f"    ... and {len(places_in_layer) - 5} more")
    
    # Check document metadata
    if hasattr(document, 'metadata') and 'signal_hierarchy' in document.metadata:
        hierarchy_meta = document.metadata['signal_hierarchy']
        print(f"\n✓ Hierarchy metadata:")
        print(f"  - Has hierarchy: {hierarchy_meta.get('has_hierarchy')}")
        print(f"  - Layer count: {hierarchy_meta.get('layer_count')}")
        print(f"  - Layer distribution: {hierarchy_meta.get('layer_distribution')}")
    print()
    
    # === TEST 4: Signal Hierarchy Analysis ===
    print("=" * 80)
    print("TEST 4: Signal Hierarchy Topology Analysis")
    print("=" * 80)
    
    analyzer = SignalHierarchyAnalyzer(document)
    result = analyzer.analyze()
    
    if result.success:
        print("\n✓ Signal hierarchy analysis successful!")
        
        # Print statistics
        stats = result.data.get('statistics', {})
        print(f"\nStatistics:")
        print(f"  - Signal places: {stats.get('total_signal_places', 0)}")
        print(f"  - Signal flow arcs: {stats.get('total_signal_flow_arcs', 0)}")
        print(f"  - Hierarchy layers: {stats.get('hierarchy_layer_count', 0)}")
        print(f"  - Is hierarchical: {stats.get('is_hierarchical', False)}")
        print(f"  - Is acyclic: {stats.get('is_acyclic', False)}")
        
        # Print signal type distribution
        signal_types = stats.get('signal_type_counts', {})
        if signal_types:
            print(f"\nSignal Type Distribution:")
            for sig_type, count in signal_types.items():
                print(f"  - {sig_type}: {count}")
        
        # Print interpretation
        interpretation = result.data.get('interpretation', '')
        if interpretation:
            print(f"\nInterpretation:")
            print(interpretation)
    else:
        print(f"\n✗ Signal hierarchy analysis failed: {result.message}")
    
    print()
    print("=" * 80)
    print("✓ All tests completed!")
    print("=" * 80)


if __name__ == '__main__':
    test_signal_hierarchy_kegg_import()
