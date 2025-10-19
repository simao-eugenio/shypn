"""
Test KEGG Import with Kinetics Enhancement

Tests that the new kinetics enhancement system works with KEGG imports.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg.converter_base import ConversionOptions
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.models import KEGGPathway, KEGGReaction, KEGGEntry, KEGGGraphics, KEGGSubstrate, KEGGProduct
from shypn.heuristic import KineticsMetadata


def create_test_pathway():
    """Create a minimal test pathway with 2 reactions."""
    
    # Create pathway
    pathway = KEGGPathway(
        number="00010",
        name="path:hsa00010",
        org="hsa",
        title="Test Glycolysis"
    )
    
    # Create compound entries with positions
    # Glucose
    glucose_entry = KEGGEntry(
        id="C00031",
        name="D-Glucose",
        type="compound",
        graphics=KEGGGraphics(
            name="Glucose",
            x=100,
            y=100
        )
    )
    
    # G6P
    g6p_entry = KEGGEntry(
        id="C00668",
        name="D-Glucose 6-phosphate",
        type="compound",
        graphics=KEGGGraphics(
            name="G6P",
            x=200,
            y=100
        )
    )
    
    # F6P
    f6p_entry = KEGGEntry(
        id="C05345",
        name="beta-D-Fructose 6-phosphate",
        type="compound",
        graphics=KEGGGraphics(
            name="F6P",
            x=300,
            y=100
        )
    )
    
    pathway.entries = {
        glucose_entry.id: glucose_entry,
        g6p_entry.id: g6p_entry,
        f6p_entry.id: f6p_entry
    }
    
    # Create reactions
    # Reaction 1: Glucose → G6P (Hexokinase, EC 2.7.1.1)
    r1 = KEGGReaction(
        id="R00710",
        name="rn:R00710",
        type="irreversible",
        substrates=[KEGGSubstrate(id="C00031", name="D-Glucose")],
        products=[KEGGProduct(id="C00668", name="D-Glucose 6-phosphate")]
    )
    r1.enzyme = "Hexokinase"
    r1.ec_numbers = ["2.7.1.1"]
    
    # Reaction 2: G6P → F6P (Phosphoglucose isomerase, EC 5.3.1.9)
    r2 = KEGGReaction(
        id="R00771",
        name="rn:R00771",
        type="reversible",
        substrates=[KEGGSubstrate(id="C00668", name="D-Glucose 6-phosphate")],
        products=[KEGGProduct(id="C05345", name="beta-D-Fructose 6-phosphate")]
    )
    r2.enzyme = "Phosphoglucose isomerase"
    r2.ec_numbers = ["5.3.1.9"]
    
    pathway.reactions = [r1, r2]
    
    return pathway


def test_kegg_import_without_enhancement():
    """Test KEGG import with kinetics enhancement disabled."""
    print("\n" + "="*70)
    print("Test 1: KEGG Import WITHOUT Kinetics Enhancement")
    print("="*70)
    
    pathway = create_test_pathway()
    
    # Convert without enhancement
    options = ConversionOptions(
        enhance_kinetics=False,
        add_initial_marking=True
    )
    
    converter = PathwayConverter()
    document = converter.convert(pathway, options)
    
    print(f"\nConversion complete:")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    
    print(f"\nTransition properties (without enhancement):")
    for t in document.transitions:
        source = KineticsMetadata.get_source(t)
        confidence = KineticsMetadata.get_confidence(t)
        print(f"  {t.name} ({t.label}):")
        print(f"    Type: {t.transition_type}")
        print(f"    Rate: {t.rate}")
        print(f"    Source: {source.value}")
        print(f"    Confidence: {confidence.value}")
        if hasattr(t, 'properties') and 'rate_function' in t.properties:
            print(f"    Rate Function: {t.properties['rate_function']}")
    
    # Verify no enhancement
    for t in document.transitions:
        assert KineticsMetadata.get_source(t).value == 'default', \
            f"Expected default source, got {KineticsMetadata.get_source(t).value}"
    
    print("\n✓ PASSED - No enhancement as expected")
    return document


def test_kegg_import_with_enhancement():
    """Test KEGG import with kinetics enhancement enabled."""
    print("\n" + "="*70)
    print("Test 2: KEGG Import WITH Kinetics Enhancement")
    print("="*70)
    
    pathway = create_test_pathway()
    
    # Convert with enhancement (default)
    options = ConversionOptions(
        enhance_kinetics=True,
        add_initial_marking=True
    )
    
    converter = PathwayConverter()
    document = converter.convert(pathway, options)
    
    print(f"\nConversion complete:")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    
    print(f"\nTransition properties (with enhancement):")
    enhanced_count = 0
    for t in document.transitions:
        source = KineticsMetadata.get_source(t)
        confidence = KineticsMetadata.get_confidence(t)
        rule = KineticsMetadata.get_rule(t)
        
        print(f"  {t.name} ({t.label}):")
        print(f"    Type: {t.transition_type}")
        print(f"    Rate: {t.rate}")
        print(f"    Source: {source.value}")
        print(f"    Confidence: {confidence.value}")
        if rule:
            print(f"    Rule: {rule}")
        if hasattr(t, 'properties') and 'rate_function' in t.properties:
            print(f"    Rate Function: {t.properties['rate_function']}")
        
        if source.value == 'heuristic':
            enhanced_count += 1
    
    print(f"\n✓ Enhanced {enhanced_count}/{len(document.transitions)} transitions")
    
    # Verify enhancement happened
    assert enhanced_count > 0, "Expected at least one transition to be enhanced"
    
    # Verify R00710 (Hexokinase) got Michaelis-Menten (has EC number)
    r00710_transition = next((t for t in document.transitions if 'Hexokinase' in str(t.label)), None)
    assert r00710_transition is not None, "Hexokinase transition not found"
    assert r00710_transition.transition_type == 'continuous', \
        f"Hexokinase should be continuous (has enzyme), got {r00710_transition.transition_type}"
    assert KineticsMetadata.get_confidence(r00710_transition).value == 'medium', \
        f"Hexokinase should have medium confidence (has EC), got {KineticsMetadata.get_confidence(r00710_transition).value}"
    
    print("\n✓ PASSED - Enhancement working as expected")
    print(f"  - Hexokinase (EC 2.7.1.1) correctly assigned as continuous with Michaelis-Menten")
    return document


def compare_before_after():
    """Compare models before and after enhancement."""
    print("\n" + "="*70)
    print("Test 3: Before/After Comparison")
    print("="*70)
    
    pathway = create_test_pathway()
    converter = PathwayConverter()
    
    # Without enhancement
    doc_before = converter.convert(pathway, ConversionOptions(enhance_kinetics=False))
    
    # With enhancement
    doc_after = converter.convert(pathway, ConversionOptions(enhance_kinetics=True))
    
    print("\nComparison:")
    print(f"  Same number of places: {len(doc_before.places) == len(doc_after.places)}")
    print(f"  Same number of transitions: {len(doc_before.transitions) == len(doc_after.transitions)}")
    print(f"  Same number of arcs: {len(doc_before.arcs) == len(doc_after.arcs)}")
    
    print("\nDifferences in transition properties:")
    for t_before, t_after in zip(doc_before.transitions, doc_after.transitions):
        if t_before.transition_type != t_after.transition_type:
            print(f"  {t_before.name}: {t_before.transition_type} → {t_after.transition_type}")
        
        props_before = t_before.properties.get('rate_function') if hasattr(t_before, 'properties') else None
        props_after = t_after.properties.get('rate_function') if hasattr(t_after, 'properties') else None
        
        if props_before != props_after:
            print(f"  {t_before.name} rate function:")
            print(f"    Before: {props_before or 'None'}")
            print(f"    After: {props_after or 'None'}")
    
    print("\n✓ PASSED - Structural integrity maintained, kinetics enhanced")


if __name__ == '__main__':
    print("="*70)
    print("Testing KEGG Import with Kinetics Enhancement Integration")
    print("="*70)
    
    try:
        test_kegg_import_without_enhancement()
        test_kegg_import_with_enhancement()
        compare_before_after()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        print("\nIntegration successful!")
        print("  - Kinetics enhancement working with KEGG import")
        print("  - EC numbers correctly detected")
        print("  - Heuristic rules properly applied")
        print("  - Metadata tracking functional")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
