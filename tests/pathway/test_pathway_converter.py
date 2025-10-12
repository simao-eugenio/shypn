"""
Test Pathway Converter

Test the PathwayConverter and all specialized converters.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.data.pathway.pathway_data import (
    PathwayData,
    Species,
    Reaction,
    KineticLaw,
)
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter


def create_test_pathway() -> PathwayData:
    """Create a test pathway for conversion."""
    
    # Cytosol species
    glucose = Species(
        id="glucose",
        name="Glucose",
        compartment="cytosol",
        initial_concentration=5.0
    )
    
    atp = Species(
        id="atp",
        name="ATP",
        compartment="cytosol",
        initial_concentration=2.5
    )
    
    g6p = Species(
        id="g6p",
        name="Glucose-6-phosphate",
        compartment="cytosol",
        initial_concentration=0.0
    )
    
    adp = Species(
        id="adp",
        name="ADP",
        compartment="cytosol",
        initial_concentration=0.5
    )
    
    # Reactions
    hexokinase = Reaction(
        id="hexokinase",
        name="Hexokinase",
        reactants=[("glucose", 1.0), ("atp", 1.0)],
        products=[("g6p", 1.0), ("adp", 1.0)],
        kinetic_law=KineticLaw(
            formula="Vmax * glucose / (Km + glucose)",
            rate_type="michaelis_menten",
            parameters={"Vmax": 10.0, "Km": 0.1}
        )
    )
    
    return PathwayData(
        species=[glucose, atp, g6p, adp],
        reactions=[hexokinase],
        compartments={"cytosol": "Cytoplasm"},
        metadata={"name": "Test Glycolysis Pathway"}
    )


def test_species_to_places():
    """Test conversion of species to places."""
    print("\n" + "=" * 70)
    print("TEST 1: Species to Places Conversion")
    print("=" * 70)
    
    pathway = create_test_pathway()
    
    # Post-process to get positions and tokens
    postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = postprocessor.process(pathway)
    
    # Convert to document
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    print(f"\nSpecies count: {len(processed.species)}")
    print(f"Places created: {len(document.places)}")
    
    # Verify each species has a corresponding place
    all_converted = True
    for species in processed.species:
        matching_place = None
        for place in document.places:
            if hasattr(place, 'metadata') and place.metadata.get('species_id') == species.id:
                matching_place = place
                break
        
        if matching_place:
            print(f"\n✓ Species '{species.name}':")
            print(f"  → Place '{matching_place.label}'")
            print(f"  → Tokens: {matching_place.tokens} (from {species.initial_concentration} mM)")
            print(f"  → Position: ({matching_place.x:.1f}, {matching_place.y:.1f})")
            
            # Verify token count
            expected_tokens = species.initial_tokens
            if matching_place.tokens != expected_tokens:
                print(f"  ✗ Token mismatch: expected {expected_tokens}, got {matching_place.tokens}")
                all_converted = False
        else:
            print(f"\n✗ Species '{species.name}' has no matching place")
            all_converted = False
    
    if all_converted and len(document.places) == len(processed.species):
        print("\n✅ TEST PASSED: All species converted to places correctly")
        return True
    else:
        print("\n❌ TEST FAILED: Some species not converted properly")
        return False


def test_reactions_to_transitions():
    """Test conversion of reactions to transitions."""
    print("\n" + "=" * 70)
    print("TEST 2: Reactions to Transitions Conversion")
    print("=" * 70)
    
    pathway = create_test_pathway()
    postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = postprocessor.process(pathway)
    
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    print(f"\nReactions count: {len(processed.reactions)}")
    print(f"Transitions created: {len(document.transitions)}")
    
    # Verify each reaction has a corresponding transition
    all_converted = True
    for reaction in processed.reactions:
        matching_transition = None
        for transition in document.transitions:
            if hasattr(transition, 'metadata') and transition.metadata.get('reaction_id') == reaction.id:
                matching_transition = transition
                break
        
        if matching_transition:
            print(f"\n✓ Reaction '{reaction.name}':")
            print(f"  → Transition '{matching_transition.label}'")
            print(f"  → Type: {matching_transition.transition_type}")
            print(f"  → Rate: {matching_transition.rate}")
            print(f"  → Position: ({matching_transition.x:.1f}, {matching_transition.y:.1f})")
            
            # Verify kinetic properties
            if reaction.kinetic_law:
                if reaction.kinetic_law.rate_type == "michaelis_menten":
                    if matching_transition.transition_type != "continuous":
                        print(f"  ✗ Type mismatch: expected continuous, got {matching_transition.transition_type}")
                        all_converted = False
        else:
            print(f"\n✗ Reaction '{reaction.name}' has no matching transition")
            all_converted = False
    
    if all_converted and len(document.transitions) == len(processed.reactions):
        print("\n✅ TEST PASSED: All reactions converted to transitions correctly")
        return True
    else:
        print("\n❌ TEST FAILED: Some reactions not converted properly")
        return False


def test_stoichiometry_to_arcs():
    """Test conversion of stoichiometry to arcs."""
    print("\n" + "=" * 70)
    print("TEST 3: Stoichiometry to Arcs Conversion")
    print("=" * 70)
    
    pathway = create_test_pathway()
    postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = postprocessor.process(pathway)
    
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    print(f"\nReactions: {len(processed.reactions)}")
    print(f"Arcs created: {len(document.arcs)}")
    
    # Count expected arcs (reactants + products)
    expected_arc_count = 0
    for reaction in processed.reactions:
        expected_arc_count += len(reaction.reactants) + len(reaction.products)
    
    print(f"Expected arcs: {expected_arc_count}")
    
    # Display arc details
    print("\nArc details:")
    for arc in document.arcs:
        source_label = arc.source.label if hasattr(arc.source, 'label') else arc.source.name
        target_label = arc.target.label if hasattr(arc.target, 'label') else arc.target.name
        print(f"  {source_label} → {target_label} (weight: {arc.weight})")
    
    if len(document.arcs) == expected_arc_count:
        print("\n✅ TEST PASSED: All stoichiometric relationships converted to arcs")
        return True
    else:
        print(f"\n❌ TEST FAILED: Expected {expected_arc_count} arcs, got {len(document.arcs)}")
        return False


def test_arc_connectivity():
    """Test that arcs properly connect places and transitions."""
    print("\n" + "=" * 70)
    print("TEST 4: Arc Connectivity")
    print("=" * 70)
    
    pathway = create_test_pathway()
    postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = postprocessor.process(pathway)
    
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    
    print(f"\nChecking {len(document.arcs)} arcs...")
    
    all_valid = True
    for arc in document.arcs:
        source_is_place = isinstance(arc.source, Place)
        target_is_place = isinstance(arc.target, Place)
        
        # Must be bipartite: Place↔Transition only
        if source_is_place == target_is_place:
            source_type = "Place" if source_is_place else "Transition"
            target_type = "Place" if target_is_place else "Transition"
            print(f"  ✗ Invalid connection: {source_type} → {target_type}")
            all_valid = False
        else:
            source_label = arc.source.label if hasattr(arc.source, 'label') else arc.source.name
            target_label = arc.target.label if hasattr(arc.target, 'label') else arc.target.name
            print(f"  ✓ Valid: {source_label} → {target_label}")
    
    if all_valid:
        print("\n✅ TEST PASSED: All arcs have valid bipartite connections")
        return True
    else:
        print("\n❌ TEST FAILED: Some arcs have invalid connections")
        return False


def test_document_integrity():
    """Test that the document model is complete and consistent."""
    print("\n" + "=" * 70)
    print("TEST 5: Document Model Integrity")
    print("=" * 70)
    
    pathway = create_test_pathway()
    postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = postprocessor.process(pathway)
    
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    place_count, transition_count, arc_count = document.get_object_count()
    
    print(f"\nDocument statistics:")
    print(f"  Places: {place_count}")
    print(f"  Transitions: {transition_count}")
    print(f"  Arcs: {arc_count}")
    
    # Check that all objects have IDs
    all_have_ids = True
    for place in document.places:
        if not hasattr(place, 'id') or place.id is None:
            print(f"  ✗ Place '{place.label}' has no ID")
            all_have_ids = False
    
    for transition in document.transitions:
        if not hasattr(transition, 'id') or transition.id is None:
            print(f"  ✗ Transition '{transition.label}' has no ID")
            all_have_ids = False
    
    for arc in document.arcs:
        if not hasattr(arc, 'id') or arc.id is None:
            print(f"  ✗ Arc has no ID")
            all_have_ids = False
    
    # Check that document is not empty
    if document.is_empty():
        print("  ✗ Document is empty")
        all_have_ids = False
    
    if all_have_ids and not document.is_empty():
        print("\n✅ TEST PASSED: Document model is complete and consistent")
        return True
    else:
        print("\n❌ TEST FAILED: Document model has integrity issues")
        return False


def test_real_sbml_file():
    """Test conversion of real SBML file."""
    print("\n" + "=" * 70)
    print("TEST 6: Real SBML File Conversion")
    print("=" * 70)
    
    try:
        from shypn.data.pathway.sbml_parser import SBMLParser
        
        test_file = Path(__file__).parent / 'simple_glycolysis.sbml'
        
        if not test_file.exists():
            print(f"⚠️  Test file not found: {test_file}")
            return True  # Skip test
        
        # Parse SBML
        parser = SBMLParser()
        pathway = parser.parse_file(str(test_file))
        
        print(f"\nParsed pathway:")
        print(f"  Species: {len(pathway.species)}")
        print(f"  Reactions: {len(pathway.reactions)}")
        
        # Post-process
        postprocessor = PathwayPostProcessor(spacing=200.0, scale_factor=1.5)
        processed = postprocessor.process(pathway)
        
        # Convert
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        place_count, transition_count, arc_count = document.get_object_count()
        
        print(f"\nConverted document:")
        print(f"  Places: {place_count}")
        print(f"  Transitions: {transition_count}")
        print(f"  Arcs: {arc_count}")
        
        print(f"\nPlace tokens:")
        for place in document.places:
            print(f"  {place.label}: {place.tokens} tokens")
        
        if place_count > 0 and transition_count > 0 and arc_count > 0:
            print("\n✅ TEST PASSED: SBML file converted successfully")
            return True
        else:
            print("\n❌ TEST FAILED: Incomplete conversion")
            return False
            
    except ImportError:
        print("⚠️  SBMLParser not available, skipping test")
        return True
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("PATHWAY CONVERTER TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Species to Places", test_species_to_places),
        ("Reactions to Transitions", test_reactions_to_transitions),
        ("Stoichiometry to Arcs", test_stoichiometry_to_arcs),
        ("Arc Connectivity", test_arc_connectivity),
        ("Document Integrity", test_document_integrity),
        ("Real SBML File", test_real_sbml_file),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ TEST ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Result: {passed_count}/{total_count} tests passed")
    print("=" * 70)
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
