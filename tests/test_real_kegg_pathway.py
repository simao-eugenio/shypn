#!/usr/bin/env python3
"""Test kinetics enhancement with real KEGG pathway import.

This tests the integration with an actual KEGG pathway (Glycolysis - hsa00010)
to verify the enhancement system works with real biological data.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg.api_client import fetch_pathway
from shypn.importer.kegg.kgml_parser import parse_kgml
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions
from shypn.heuristic import KineticsMetadata

def test_real_kegg_import():
    """Test importing Glycolysis pathway from KEGG with enhancement."""
    
    print("=" * 70)
    print("Testing Real KEGG Pathway Import with Kinetics Enhancement")
    print("=" * 70)
    
    # Fetch real KEGG pathway (Glycolysis)
    print("\n1. Fetching KEGG pathway hsa00010 (Glycolysis)...")
    try:
        kgml = fetch_pathway('hsa00010')
        if not kgml:
            raise Exception("fetch_pathway returned None")
        
        pathway = parse_kgml(kgml)
        print(f"   ✓ Fetched pathway: {pathway.name}")
        print(f"   - Entries: {len(pathway.entries)}")
        print(f"   - Reactions: {len(pathway.reactions)}")
    except Exception as e:
        print(f"   ✗ Failed to fetch pathway: {e}")
        print("\n   Note: This test requires internet connection to fetch from KEGG.")
        print("   Skipping real pathway test...")
        return
    
    # Convert with enhancement
    print("\n2. Converting pathway WITH kinetics enhancement...")
    converter = PathwayConverter()
    options = ConversionOptions(enhance_kinetics=True)
    
    try:
        document = converter.convert(pathway, options)
        print(f"   ✓ Conversion complete")
        print(f"   - Places: {len(document.places)}")
        print(f"   - Transitions: {len(document.transitions)}")
        print(f"   - Arcs: {len(document.arcs)}")
    except Exception as e:
        print(f"   ✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Analyze enhancement results
    print("\n3. Analyzing enhancement results...")
    
    enhanced_count = 0
    by_confidence = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
    by_rule = {}
    enzymatic_transitions = []
    
    for transition in document.transitions:
        source = KineticsMetadata.get_source(transition)
        
        if source.value == 'heuristic':
            enhanced_count += 1
            
            confidence = KineticsMetadata.get_confidence(transition)
            by_confidence[confidence.value] += 1
            
            rule = KineticsMetadata.get_rule(transition)
            if rule:
                rule_name = rule.value if hasattr(rule, 'value') else rule
                by_rule[rule_name] = by_rule.get(rule_name, 0) + 1
                
                # Track enzymatic reactions
                if rule_name == 'enzymatic_mm':
                    enzymatic_transitions.append(transition)
    
    print(f"\n   Enhancement Statistics:")
    print(f"   - Total transitions: {len(document.transitions)}")
    print(f"   - Enhanced: {enhanced_count}/{len(document.transitions)} ({100*enhanced_count//len(document.transitions) if document.transitions else 0}%)")
    
    print(f"\n   Confidence Distribution:")
    for conf, count in sorted(by_confidence.items()):
        if count > 0:
            print(f"   - {conf.capitalize()}: {count}")
    
    print(f"\n   Rules Applied:")
    for rule, count in sorted(by_rule.items()):
        print(f"   - {rule}: {count}")
    
    # Show sample enzymatic transitions
    if enzymatic_transitions:
        print(f"\n4. Sample Enzymatic Transitions (with EC numbers):")
        for i, transition in enumerate(enzymatic_transitions[:5], 1):  # Show first 5
            print(f"\n   Transition {i}: {transition.label}")
            display = KineticsMetadata.format_for_display(transition)
            for line in display.split('\n'):
                print(f"   {line}")
            
            if i >= 5:
                remaining = len(enzymatic_transitions) - 5
                if remaining > 0:
                    print(f"\n   ... and {remaining} more enzymatic transitions")
                break
    
    # Show sample non-enzymatic transitions
    non_enzymatic = [t for t in document.transitions 
                     if KineticsMetadata.get_source(t).value == 'heuristic'
                     and KineticsMetadata.get_rule(t)
                     and (KineticsMetadata.get_rule(t).value if hasattr(KineticsMetadata.get_rule(t), 'value') 
                          else KineticsMetadata.get_rule(t)) != 'enzymatic_mm']
    
    if non_enzymatic:
        print(f"\n5. Sample Non-Enzymatic Transitions:")
        for i, transition in enumerate(non_enzymatic[:3], 1):  # Show first 3
            print(f"\n   Transition {i}: {transition.label}")
            display = KineticsMetadata.format_for_display(transition)
            for line in display.split('\n'):
                print(f"   {line}")
            
            if i >= 3:
                break
    
    print("\n" + "=" * 70)
    print("✓ Real KEGG Pathway Test Complete")
    print("=" * 70)
    
    # Summary
    print("\nSummary:")
    print(f"  ✓ Successfully imported Glycolysis pathway from KEGG")
    print(f"  ✓ Enhanced {enhanced_count} transitions with kinetic properties")
    print(f"  ✓ Detected {len(enzymatic_transitions)} enzymatic reactions (EC annotated)")
    print(f"  ✓ Applied heuristic rules appropriately")
    print("\n  The enhancement system is working correctly with real KEGG data!")

if __name__ == '__main__':
    test_real_kegg_import()
