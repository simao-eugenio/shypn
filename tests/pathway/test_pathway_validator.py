"""
Test Pathway Validator

Test the PathwayValidator class with valid and invalid pathway data.
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
from shypn.data.pathway.pathway_validator import PathwayValidator


def create_valid_pathway() -> PathwayData:
    """Create a valid pathway for testing."""
    
    # Species
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
    
    # Reaction
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
    
    return PathwayData(
        species=[glucose, atp, g6p],
        reactions=[hexokinase],
        compartments={"cytosol": "Cytoplasm"}
    )


def create_invalid_pathway_missing_species() -> PathwayData:
    """Create pathway with invalid species reference."""
    
    reaction = Reaction(
        id="bad_reaction",
        name="Bad Reaction",
        reactants=[("nonexistent_species", 1.0)],  # ❌ Species doesn't exist
        products=[("g6p", 1.0)]
    )
    
    return PathwayData(
        species=[],
        reactions=[reaction]
    )


def create_invalid_pathway_bad_stoichiometry() -> PathwayData:
    """Create pathway with invalid stoichiometry."""
    
    glucose = Species(id="glucose", name="Glucose", compartment="cytosol")
    g6p = Species(id="g6p", name="G6P", compartment="cytosol")
    
    reaction = Reaction(
        id="bad_reaction",
        name="Bad Reaction",
        reactants=[("glucose", -1.0)],  # ❌ Negative stoichiometry
        products=[("g6p", 0.0)]         # ❌ Zero stoichiometry
    )
    
    return PathwayData(
        species=[glucose, g6p],
        reactions=[reaction],
        compartments={"cytosol": "Cytoplasm"}
    )


def create_pathway_with_warnings() -> PathwayData:
    """Create pathway that's valid but has warnings."""
    
    # Orphaned species (not in any reaction)
    glucose = Species(id="glucose", name="Glucose", compartment="cytosol")
    orphan = Species(id="orphan", name="Orphaned Species", compartment="cytosol")
    g6p = Species(id="g6p", name="G6P", compartment="cytosol")
    
    # Reaction without kinetics
    reaction = Reaction(
        id="simple_reaction",
        name="Simple Reaction",
        reactants=[("glucose", 1.0)],
        products=[("g6p", 1.0)],
        kinetic_law=None  # ⚠️ No kinetics
    )
    
    return PathwayData(
        species=[glucose, orphan, g6p],
        reactions=[reaction],
        compartments={"cytosol": "Cytoplasm"}
    )


def test_valid_pathway():
    """Test validation of valid pathway."""
    print("\n" + "=" * 70)
    print("TEST 1: Valid Pathway")
    print("=" * 70)
    
    pathway = create_valid_pathway()
    validator = PathwayValidator()
    result = validator.validate(pathway)
    
    print(f"\nResult: {result}")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    
    if result.is_valid:
        print("\n✅ TEST PASSED: Pathway is valid")
        return True
    else:
        print("\n❌ TEST FAILED: Expected valid pathway")
        for error in result.errors:
            print(f"  - {error}")
        return False


def test_invalid_species_reference():
    """Test validation of pathway with invalid species reference."""
    print("\n" + "=" * 70)
    print("TEST 2: Invalid Species Reference")
    print("=" * 70)
    
    pathway = create_invalid_pathway_missing_species()
    validator = PathwayValidator()
    result = validator.validate(pathway)
    
    print(f"\nResult: {result}")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {len(result.errors)}")
    
    if not result.is_valid:
        print("\nErrors found:")
        for error in result.errors:
            print(f"  ❌ {error}")
        print("\n✅ TEST PASSED: Correctly detected invalid pathway")
        return True
    else:
        print("\n❌ TEST FAILED: Should have detected errors")
        return False


def test_invalid_stoichiometry():
    """Test validation of pathway with invalid stoichiometry."""
    print("\n" + "=" * 70)
    print("TEST 3: Invalid Stoichiometry")
    print("=" * 70)
    
    pathway = create_invalid_pathway_bad_stoichiometry()
    validator = PathwayValidator()
    result = validator.validate(pathway)
    
    print(f"\nResult: {result}")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {len(result.errors)}")
    
    if not result.is_valid:
        print("\nErrors found:")
        for error in result.errors:
            print(f"  ❌ {error}")
        print("\n✅ TEST PASSED: Correctly detected invalid stoichiometry")
        return True
    else:
        print("\n❌ TEST FAILED: Should have detected errors")
        return False


def test_pathway_with_warnings():
    """Test validation of pathway with warnings."""
    print("\n" + "=" * 70)
    print("TEST 4: Pathway with Warnings")
    print("=" * 70)
    
    pathway = create_pathway_with_warnings()
    validator = PathwayValidator()
    result = validator.validate(pathway)
    
    print(f"\nResult: {result}")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    
    if result.is_valid and len(result.warnings) > 0:
        print("\nWarnings found:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")
        print("\n✅ TEST PASSED: Correctly detected warnings")
        return True
    else:
        print("\n❌ TEST FAILED: Should have warnings but be valid")
        return False


def test_real_sbml_file():
    """Test validation of parsed SBML file."""
    print("\n" + "=" * 70)
    print("TEST 5: Real SBML File")
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
        
        # Validate
        validator = PathwayValidator()
        result = validator.validate(pathway)
        
        print(f"\nValidation result: {result}")
        print(f"Valid: {result.is_valid}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  ❌ {error}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  ⚠️  {warning}")
        
        if result.is_valid:
            print("\n✅ TEST PASSED: SBML file validated successfully")
            return True
        else:
            print("\n❌ TEST FAILED: SBML file has validation errors")
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
    print("PATHWAY VALIDATOR TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Valid Pathway", test_valid_pathway),
        ("Invalid Species Reference", test_invalid_species_reference),
        ("Invalid Stoichiometry", test_invalid_stoichiometry),
        ("Pathway with Warnings", test_pathway_with_warnings),
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
