"""
Test Pathway Post-Processor

Test the PathwayPostProcessor and all specialized processors.
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
from shypn.data.pathway.pathway_postprocessor import (
    PathwayPostProcessor,
    LayoutProcessor,
    ColorProcessor,
    UnitNormalizer,
    NameResolver,
    CompartmentGrouper,
)


def create_test_pathway() -> PathwayData:
    """Create a test pathway with multiple compartments."""
    
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
    
    # Mitochondrial species
    pyruvate = Species(
        id="pyruvate",
        name="Pyruvate",
        compartment="mitochondria",
        initial_concentration=1.2
    )
    
    acetyl_coa = Species(
        id="acetyl_coa",
        name="Acetyl-CoA",
        compartment="mitochondria",
        initial_concentration=0.3
    )
    
    # Species without names (for name resolution test)
    unnamed_species = Species(
        id="mystery_compound",
        name=None,  # No name
        compartment="cytosol",
        initial_concentration=0.5
    )
    
    # Reactions
    hexokinase = Reaction(
        id="hexokinase",
        name="Hexokinase",
        reactants=[("glucose", 1.0), ("atp", 1.0)],
        products=[("g6p", 1.0)],
        kinetic_law=KineticLaw(
            formula="Vmax * glucose / (Km + glucose)",
            rate_type="michaelis_menten",
            parameters={"Vmax": 10.0, "Km": 0.1}
        )
    )
    
    pyruvate_dehydrogenase = Reaction(
        id="pyruvate_dehydrogenase",
        name="Pyruvate Dehydrogenase",
        reactants=[("pyruvate", 1.0)],
        products=[("acetyl_coa", 1.0)]
    )
    
    unnamed_reaction = Reaction(
        id="mystery_reaction",
        name=None,  # No name
        reactants=[("mystery_compound", 1.0)],
        products=[("g6p", 1.0)]
    )
    
    return PathwayData(
        species=[glucose, atp, g6p, pyruvate, acetyl_coa, unnamed_species],
        reactions=[hexokinase, pyruvate_dehydrogenase, unnamed_reaction],
        compartments={
            "cytosol": "Cytoplasm",
            "mitochondria": "Mitochondria"
        },
        parameters={"Vmax": 10.0, "Km": 0.1},
        metadata={"name": "Test Glycolysis Pathway"}
    )


def test_layout_processor():
    """Test layout calculation."""
    print("\n" + "=" * 70)
    print("TEST 1: Layout Processor")
    print("=" * 70)
    
    pathway = create_test_pathway()
    processor = PathwayPostProcessor(spacing=150.0)
    processed = processor.process(pathway)
    
    print(f"\nPositions calculated: {len(processed.positions)}")
    print(f"Expected: {len(pathway.species) + len(pathway.reactions)}")
    
    # Check all elements have positions
    all_elements = (
        [s.id for s in pathway.species] +
        [r.id for r in pathway.reactions]
    )
    
    missing = [e for e in all_elements if e not in processed.positions]
    
    if not missing and len(processed.positions) > 0:
        print("\nSample positions:")
        for i, (element_id, (x, y)) in enumerate(processed.positions.items()):
            if i < 5:  # Show first 5
                print(f"  {element_id}: ({x:.1f}, {y:.1f})")
        
        print("\n✅ TEST PASSED: All elements positioned")
        return True
    else:
        print(f"\n❌ TEST FAILED: Missing positions for: {missing}")
        return False


def test_color_processor():
    """Test color assignment."""
    print("\n" + "=" * 70)
    print("TEST 2: Color Processor")
    print("=" * 70)
    
    pathway = create_test_pathway()
    processor = PathwayPostProcessor()
    processed = processor.process(pathway)
    
    print(f"\nColors assigned: {len(processed.colors)}")
    print(f"Compartments: {len(pathway.compartments)}")
    
    print("\nCompartment colors:")
    for comp, color in processed.colors.items():
        comp_name = pathway.compartments.get(comp, comp)
        print(f"  {comp_name}: {color}")
    
    if len(processed.colors) >= len(pathway.compartments):
        print("\n✅ TEST PASSED: Colors assigned to compartments")
        return True
    else:
        print("\n❌ TEST FAILED: Not all compartments have colors")
        return False


def test_unit_normalizer():
    """Test unit normalization (concentration → tokens)."""
    print("\n" + "=" * 70)
    print("TEST 3: Unit Normalizer")
    print("=" * 70)
    
    pathway = create_test_pathway()
    scale_factor = 2.0
    processor = PathwayPostProcessor(scale_factor=scale_factor)
    processed = processor.process(pathway)
    
    print(f"\nScale factor: {scale_factor}")
    print("\nConversion results:")
    
    all_converted = True
    for species in processed.species:
        expected_tokens = max(0, round(species.initial_concentration * scale_factor))
        print(f"  {species.name or species.id}:")
        print(f"    {species.initial_concentration} mM → {species.initial_tokens} tokens")
        print(f"    Expected: {expected_tokens} tokens")
        
        if species.initial_tokens != expected_tokens:
            all_converted = False
            print(f"    ❌ MISMATCH")
    
    if all_converted:
        print("\n✅ TEST PASSED: All concentrations normalized correctly")
        return True
    else:
        print("\n❌ TEST FAILED: Some conversions incorrect")
        return False


def test_name_resolver():
    """Test name resolution for unnamed elements."""
    print("\n" + "=" * 70)
    print("TEST 4: Name Resolver")
    print("=" * 70)
    
    pathway = create_test_pathway()
    processor = PathwayPostProcessor()
    processed = processor.process(pathway)
    
    print("\nName resolution:")
    
    unnamed_count = 0
    resolved_count = 0
    
    # Check species
    for original, processed_species in zip(pathway.species, processed.species):
        if original.name is None:
            unnamed_count += 1
            if processed_species.name is not None:
                resolved_count += 1
                print(f"  Species '{original.id}' → '{processed_species.name}'")
    
    # Check reactions
    for original, processed_reaction in zip(pathway.reactions, processed.reactions):
        if original.name is None:
            unnamed_count += 1
            if processed_reaction.name is not None:
                resolved_count += 1
                print(f"  Reaction '{original.id}' → '{processed_reaction.name}'")
    
    print(f"\nUnnamed elements: {unnamed_count}")
    print(f"Resolved names: {resolved_count}")
    
    if resolved_count == unnamed_count:
        print("\n✅ TEST PASSED: All unnamed elements resolved")
        return True
    else:
        print("\n❌ TEST FAILED: Some elements still unnamed")
        return False


def test_compartment_grouper():
    """Test compartment grouping."""
    print("\n" + "=" * 70)
    print("TEST 5: Compartment Grouper")
    print("=" * 70)
    
    pathway = create_test_pathway()
    processor = PathwayPostProcessor()
    processed = processor.process(pathway)
    
    print(f"\nCompartment groups: {len(processed.compartment_groups)}")
    
    print("\nGroup contents:")
    for comp, species_ids in processed.compartment_groups.items():
        comp_name = pathway.compartments.get(comp, comp)
        print(f"  {comp_name}: {len(species_ids)} species")
        for species_id in species_ids:
            species = next(s for s in pathway.species if s.id == species_id)
            print(f"    - {species.name or species_id}")
    
    # Verify all species are grouped
    total_grouped = sum(len(ids) for ids in processed.compartment_groups.values())
    
    if total_grouped == len(pathway.species):
        print("\n✅ TEST PASSED: All species grouped by compartment")
        return True
    else:
        print(f"\n❌ TEST FAILED: Expected {len(pathway.species)}, got {total_grouped}")
        return False


def test_real_sbml_file():
    """Test post-processing of parsed SBML file."""
    print("\n" + "=" * 70)
    print("TEST 6: Real SBML File")
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
        processor = PathwayPostProcessor(spacing=200.0, scale_factor=1.5)
        processed = processor.process(pathway)
        
        print(f"\nPost-processed data:")
        print(f"  Positions: {len(processed.positions)}")
        print(f"  Colors: {len(processed.colors)}")
        print(f"  Compartment groups: {len(processed.compartment_groups)}")
        
        print("\nToken assignments:")
        for species in processed.species:
            print(f"  {species.name}: {species.initial_tokens} tokens")
        
        if (len(processed.positions) > 0 and 
            len(processed.colors) > 0 and
            len(processed.compartment_groups) > 0):
            print("\n✅ TEST PASSED: SBML file post-processed successfully")
            return True
        else:
            print("\n❌ TEST FAILED: Incomplete post-processing")
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
    print("PATHWAY POST-PROCESSOR TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Layout Processor", test_layout_processor),
        ("Color Processor", test_color_processor),
        ("Unit Normalizer", test_unit_normalizer),
        ("Name Resolver", test_name_resolver),
        ("Compartment Grouper", test_compartment_grouper),
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
