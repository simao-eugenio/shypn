#!/usr/bin/env python3
"""Test script to verify the source/sink builder fix.

This tests that energy signal places (NAD, CoA, ATP, etc.) that are
stoichiometrically connected to biochemical reactions via SignalFlowArcs
do NOT get artificial source/sink transitions.

The old behavior created confusing "artificial patterns" where:
- Real connections: NAD → T17 (R02569) → NADH ✓
- Artificial plumbing: NAD_source → NAD → NAD_sink ✗

The new behavior skips source/sink for signals connected to reactions.

Usage:
    python dev/test_source_sink_fix.py eco00020

This will:
1. Import the KEGG pathway
2. Enrich with stoichiometry
3. Verify no source/sink for connected energy signals
4. Report results
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.services.enrichment.stoichiometry import KEGGStoichiometryEnricher


def main(pathway_id='eco00020'):
    """Test the source/sink builder fix."""
    
    print("=" * 80)
    print(f"TESTING SOURCE/SINK FIX: {pathway_id}")
    print("=" * 80)
    print()
    
    # Step 1: Parse KGML
    print(f"Step 1: Parsing KGML for {pathway_id}...")
    parser = KGMLParser()
    pathway = parser.parse_online(pathway_id)
    print(f"  ✓ Parsed: {len(pathway.entries)} entries, {len(pathway.reactions)} reactions")
    
    # Step 2: Convert to Petri net
    print("\nStep 2: Converting to Petri net...")
    converter = PathwayConverter()
    document = converter.convert(pathway, None)
    print(f"  ✓ Converted: {len(document.places)} places, {len(document.transitions)} transitions")
    
    # Step 3: Enrich stoichiometry
    print("\nStep 3: Enriching stoichiometry...")
    enricher = KEGGStoichiometryEnricher()
    result = enricher.enrich_document(document)
    print(f"  ✓ {result.get_summary()}")
    
    # Step 4: Analyze results
    print("\n" + "=" * 80)
    print("ANALYSIS: Energy Signal Places")
    print("=" * 80)
    
    # Find energy signal places
    energy_signals = []
    for place in document.places:
        if place.is_signal_place and hasattr(place, 'signal_type'):
            from shypn.netobjs.signal_type import SignalType
            if place.signal_type == SignalType.ENERGY:
                energy_signals.append(place)
    
    print(f"\nFound {len(energy_signals)} energy signal places")
    
    # Check each for source/sink connections
    print("\nChecking for artificial source/sink transitions:")
    issues_found = 0
    successes = 0
    
    for place in energy_signals:
        # Count connections to real reactions vs source/sink
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        reactions = 0
        sources_sinks = 0
        
        for arc in document.arcs:
            if isinstance(arc, SignalFlowArc) and (arc.source == place or arc.target == place):
                transition = arc.target if arc.source == place else arc.source
                from shypn.netobjs.transition import Transition
                if isinstance(transition, Transition):
                    label = transition.label or transition.name
                    if '_source' in label or '_sink' in label:
                        sources_sinks += 1
                    else:
                        # Check if it's a real reaction
                        is_real = False
                        if hasattr(transition, 'metadata') and transition.metadata:
                            if 'kegg_reaction_id' in transition.metadata:
                                is_real = True
                        if is_real or ('R' in label and any(c.isdigit() for c in label)):
                            reactions += 1
        
        if reactions > 0 and sources_sinks > 0:
            print(f"  ✗ {place.name} ({place.id}): Connected to {reactions} reactions BUT has {sources_sinks} source/sink")
            issues_found += 1
        elif reactions > 0 and sources_sinks == 0:
            print(f"  ✓ {place.name} ({place.id}): Connected to {reactions} reactions, NO source/sink")
            successes += 1
        elif reactions == 0 and sources_sinks > 0:
            print(f"  ⓘ {place.name} ({place.id}): No reactions, has {sources_sinks} source/sink (expected)")
    
    # Summary
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if issues_found == 0:
        print(f"\n✓ SUCCESS: {successes} energy signals properly connected without artificial source/sink")
        print(f"\nThe fix works correctly! Energy cofactors (NAD, CoA, ATP) that are")
        print(f"stoichiometrically connected to biochemical reactions do not get")
        print(f"unnecessary source/sink transitions.")
        return 0
    else:
        print(f"\n✗ FAILURE: {issues_found} energy signals have unnecessary source/sink transitions")
        print(f"\nThe fix may not be working. Check the SignalSourceSinkBuilder logic.")
        return 1


if __name__ == '__main__':
    pathway_id = sys.argv[1] if len(sys.argv) > 1 else 'eco00020'
    sys.exit(main(pathway_id))
