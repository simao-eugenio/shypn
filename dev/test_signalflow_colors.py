#!/usr/bin/env python3
"""Test script to verify SignalFlowArc colors during import.

Tests both KEGG and SBML import pipelines to ensure SignalFlowArcs
receive correct light gray color (0.7, 0.7, 0.7) before canvas rendering.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

def test_sbml_signalflow_colors():
    """Test SBML import - verify SignalFlowArcs have light gray color."""
    from shypn.data.pathway.sbml_parser import SBMLParser
    from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
    from shypn.data.pathway.pathway_converter import PathwayConverter
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    
    print("\n" + "="*70)
    print("TEST: SBML SignalFlowArc Color Enforcement")
    print("="*70)
    
    # Use a test model with signal places (parameters create signal places)
    test_file = Path(__file__).parent.parent / 'workspace' / 'projects' / 'Biochemical-Examples' / 'pathways' / 'BIOMD0000000064.xml'
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📄 Loading: {test_file.name}")
    
    try:
        # Full SBML import pipeline
        parser = SBMLParser()
        parsed_pathway = parser.parse_file(str(test_file))
        
        postprocessor = PathwayPostProcessor(scale_factor=1.0)
        processed_pathway = postprocessor.process(parsed_pathway)
        
        converter = PathwayConverter()
        document = converter.convert(processed_pathway)
        
        # Find all SignalFlowArcs
        signal_arcs = [arc for arc in document.arcs if isinstance(arc, SignalFlowArc)]
        signal_places = [p for p in document.places if getattr(p, 'is_signal_place', False)]
        
        print(f"\n📊 Results:")
        print(f"   Total places: {len(document.places)}")
        print(f"   Signal places: {len(signal_places)}")
        print(f"   Total arcs: {len(document.arcs)}")
        print(f"   SignalFlowArcs: {len(signal_arcs)}")
        
        if not signal_arcs:
            print("   ℹ️  No SignalFlowArcs found (model may not have signal places)")
            return True
        
        # Check colors
        LIGHT_GRAY = (0.7, 0.7, 0.7)
        correct_count = 0
        wrong_count = 0
        
        for i, arc in enumerate(signal_arcs[:5], 1):  # Show first 5
            color = arc.color
            is_correct = color == LIGHT_GRAY
            
            if is_correct:
                correct_count += 1
                status = "✅"
            else:
                wrong_count += 1
                status = "❌"
            
            print(f"   {status} Arc {i}: color={color} (expected {LIGHT_GRAY})")
        
        if len(signal_arcs) > 5:
            # Check remaining silently
            for arc in signal_arcs[5:]:
                if arc.color == LIGHT_GRAY:
                    correct_count += 1
                else:
                    wrong_count += 1
        
        print(f"\n📈 Summary:")
        print(f"   ✅ Correct colors: {correct_count}/{len(signal_arcs)}")
        print(f"   ❌ Wrong colors: {wrong_count}/{len(signal_arcs)}")
        
        success = wrong_count == 0
        if success:
            print(f"\n🎉 PASS: All SignalFlowArcs have correct light gray color!")
        else:
            print(f"\n💥 FAIL: {wrong_count} SignalFlowArcs have wrong color!")
        
        return success
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kegg_signalflow_colors():
    """Test KEGG import - verify SignalFlowArcs have light gray color."""
    from shypn.importer.kegg.pathway_converter import PathwayConverter as KEGGConverter
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    
    print("\n" + "="*70)
    print("TEST: KEGG SignalFlowArc Color Enforcement")
    print("="*70)
    
    # Use a test KEGG pathway (glycolysis - hsa00010)
    test_pathway_id = "hsa00010"
    
    print(f"📄 Loading KEGG pathway: {test_pathway_id} (glycolysis)")
    print("   Note: This requires network connection to KEGG API")
    
    try:
        converter = KEGGConverter()
        
        # Import pathway
        from shypn.importer.kegg.kegg_api import fetch_kegg_pathway
        
        print("   Fetching from KEGG...")
        pathway_data = fetch_kegg_pathway(test_pathway_id)
        
        if not pathway_data:
            print("   ❌ Failed to fetch pathway from KEGG")
            return False
        
        print("   Converting to Petri net...")
        
        from shypn.importer.kegg.kegg_pathway_converter import KEGGConversionOptions
        options = KEGGConversionOptions()
        
        document = converter.convert(pathway_data, options)
        
        # Find all SignalFlowArcs
        signal_arcs = [arc for arc in document.arcs if isinstance(arc, SignalFlowArc)]
        
        print(f"\n📊 Results:")
        print(f"   Total arcs: {len(document.arcs)}")
        print(f"   SignalFlowArcs: {len(signal_arcs)}")
        
        if not signal_arcs:
            print("   ℹ️  No SignalFlowArcs found")
            return True
        
        # Check colors
        LIGHT_GRAY = (0.7, 0.7, 0.7)
        correct_count = 0
        wrong_count = 0
        
        for i, arc in enumerate(signal_arcs[:5], 1):  # Show first 5
            color = arc.color
            is_correct = color == LIGHT_GRAY
            
            if is_correct:
                correct_count += 1
                status = "✅"
            else:
                wrong_count += 1
                status = "❌"
            
            print(f"   {status} Arc {i}: color={color} (expected {LIGHT_GRAY})")
        
        if len(signal_arcs) > 5:
            # Check remaining silently
            for arc in signal_arcs[5:]:
                if arc.color == LIGHT_GRAY:
                    correct_count += 1
                else:
                    wrong_count += 1
        
        print(f"\n📈 Summary:")
        print(f"   ✅ Correct colors: {correct_count}/{len(signal_arcs)}")
        print(f"   ❌ Wrong colors: {wrong_count}/{len(signal_arcs)}")
        
        success = wrong_count == 0
        if success:
            print(f"\n🎉 PASS: All SignalFlowArcs have correct light gray color!")
        else:
            print(f"\n💥 FAIL: {wrong_count} SignalFlowArcs have wrong color!")
        
        return success
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("="*70)
    print("SignalFlowArc Color Enforcement Test Suite")
    print("="*70)
    print("\nVerifying that SignalFlowArcs receive light gray (0.7, 0.7, 0.7)")
    print("color during import pipeline, before canvas rendering.")
    
    results = {}
    
    # Test SBML
    results['sbml'] = test_sbml_signalflow_colors()
    
    # Test KEGG
    print("\n")
    user_input = input("Test KEGG import? (requires network, may be slow) [y/N]: ")
    if user_input.lower() == 'y':
        results['kegg'] = test_kegg_signalflow_colors()
    else:
        print("\nℹ️  Skipping KEGG test")
        results['kegg'] = None
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    for test_name, result in results.items():
        if result is None:
            print(f"  {test_name.upper()}: ⊘ SKIPPED")
        elif result:
            print(f"  {test_name.upper()}: ✅ PASS")
        else:
            print(f"  {test_name.upper()}: ❌ FAIL")
    
    print("="*70)
    
    # Exit code
    if results['sbml'] is False or results['kegg'] is False:
        sys.exit(1)
    else:
        sys.exit(0)
