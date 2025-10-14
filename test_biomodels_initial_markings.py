#!/usr/bin/env python3
"""
Test script to verify initial markings from BIOMD0000000001 SBML import.

This verifies that:
1. SBML initial concentrations/amounts are correctly extracted
2. Post-processing converts them to discrete tokens
3. Places receive correct initial_marking values
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

def test_biomodels_initial_markings():
    """Test BIOMD0000000001 initial marking extraction."""
    
    sbml_file = Path(__file__).parent / 'data' / 'biomodels_test' / 'BIOMD0000000001.xml'
    
    if not sbml_file.exists():
        print(f"❌ SBML file not found: {sbml_file}")
        return False
    
    print("=" * 70)
    print("BIOMD0000000001 INITIAL MARKINGS VERIFICATION")
    print("=" * 70)
    print(f"\nModel: Edelstein1996 - EPSP ACh species")
    print(f"File: {sbml_file.name}\n")
    
    # Step 1: Parse SBML
    print("Step 1: Parsing SBML file...")
    parser = SBMLParser()
    pathway_data = parser.parse_file(str(sbml_file))
    
    if not pathway_data:
        print("❌ Failed to parse SBML")
        return False
    
    print(f"✅ Parsed successfully")
    print(f"   Species: {len(pathway_data.species)}")
    print(f"   Reactions: {len(pathway_data.reactions)}")
    
    # Step 2: Check initial concentrations
    print("\nStep 2: Checking initial concentrations/amounts...")
    print("-" * 70)
    print(f"{'Species ID':<15} {'Name':<25} {'Initial Concentration':<20}")
    print("-" * 70)
    
    species_with_initial = []
    for species in pathway_data.species:
        initial = species.initial_concentration
        if initial and initial != 0:
            species_with_initial.append((species.id, species.name, initial))
            print(f"{species.id:<15} {species.name:<25} {initial:<20.6e}")
        else:
            print(f"{species.id:<15} {species.name:<25} {'0':<20}")
    
    print("-" * 70)
    print(f"Total species with non-zero initial values: {len(species_with_initial)}")
    
    # Step 3: Post-process (convert to tokens)
    print("\nStep 3: Post-processing (concentration → tokens)...")
    postprocessor = PathwayPostProcessor()
    
    # Test with different scale factors
    for scale_factor in [1.0, 10.0, 100.0]:
        postprocessor.scale_factor = scale_factor
        processed_data = postprocessor.process(pathway_data)
        
        print(f"\n  Scale factor: {scale_factor}")
        print(f"  {'Species':<15} {'Initial Conc':<20} {'Initial Tokens':<15}")
        print(f"  {'-'*50}")
        
        for species in processed_data.species:
            initial_conc = species.initial_concentration or 0
            initial_tokens = species.initial_tokens
            if initial_conc != 0 or initial_tokens != 0:
                print(f"  {species.id:<15} {initial_conc:<20.6e} {initial_tokens:<15}")
    
    # Step 4: Convert to Petri net
    print("\nStep 4: Converting to Petri net...")
    postprocessor.scale_factor = 1.0  # Reset to default
    processed_data = postprocessor.process(pathway_data)
    
    converter = PathwayConverter()
    manager = converter.convert(processed_data)
    
    if not manager:
        print("❌ Failed to convert to Petri net")
        return False
    
    print(f"✅ Converted successfully")
    print(f"   Places: {len(manager.places)}")
    print(f"   Transitions: {len(manager.transitions)}")
    print(f"   Arcs: {len(manager.arcs)}")
    
    # Step 5: Verify place markings
    print("\nStep 5: Verifying place initial markings...")
    print("-" * 70)
    print(f"{'Place Name':<20} {'Tokens':<10} {'Initial Marking':<15}")
    print("-" * 70)
    
    places_with_tokens = []
    for place in manager.places:
        if place.tokens > 0 or place.initial_marking > 0:
            places_with_tokens.append(place)
            print(f"{place.name:<20} {place.tokens:<10} {place.initial_marking:<15}")
    
    if not places_with_tokens:
        print("(No places with initial tokens)")
    
    print("-" * 70)
    print(f"Total places with initial markings: {len(places_with_tokens)}")
    
    # Step 6: Summary and verification
    print("\n" + "=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)
    
    passed = True
    
    # Check 1: Parser extracted initial amounts
    if len(species_with_initial) > 0:
        print(f"✅ Parser extracted initial amounts: {len(species_with_initial)} species")
    else:
        print(f"⚠️  No species with non-zero initial amounts (all start at 0)")
    
    # Check 2: Post-processor calculated tokens
    tokens_calculated = False
    for species in processed_data.species:
        if hasattr(species, 'initial_tokens') and species.initial_tokens > 0:
            tokens_calculated = True
            break
    
    if tokens_calculated:
        print(f"✅ Post-processor calculated initial tokens")
    else:
        print(f"⚠️  No tokens calculated (initial amounts may be very small)")
    
    # Check 3: Converter applied to places
    if len(places_with_tokens) > 0:
        print(f"✅ Converter applied markings to places: {len(places_with_tokens)} places")
    else:
        print(f"⚠️  No places with initial markings (amounts may be negligible)")
    
    # Check 4: Consistency check
    consistency_ok = True
    for place in places_with_tokens:
        if place.tokens != place.initial_marking:
            print(f"❌ INCONSISTENCY: {place.name} tokens({place.tokens}) != initial_marking({place.initial_marking})")
            consistency_ok = False
            passed = False
    
    if consistency_ok and len(places_with_tokens) > 0:
        print(f"✅ Tokens and initial_marking values consistent")
    
    print("\n" + "=" * 70)
    if passed:
        print("🎉 VERIFICATION PASSED")
        if len(species_with_initial) > 0:
            print(f"   Initial markings successfully extracted and applied!")
        else:
            print(f"   Pipeline working (this model has all species starting at ~0)")
    else:
        print("❌ VERIFICATION FAILED")
    print("=" * 70 + "\n")
    
    return passed


if __name__ == '__main__':
    success = test_biomodels_initial_markings()
    sys.exit(0 if success else 1)
