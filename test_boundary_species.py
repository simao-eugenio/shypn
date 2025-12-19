#!/usr/bin/env python3
"""Test boundary species visualization."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

def test_boundary_species():
    """Test that boundary species are marked as signal places."""
    
    print("=" * 70)
    print("Testing Boundary Species Visualization (BIOMD0000000062)")
    print("=" * 70)
    
    sbml_file = "./workspace/projects/My_Project/pathways/BIOMD0000000062.xml"
    
    if not os.path.exists(sbml_file):
        print(f"ERROR: File not found: {sbml_file}")
        return False
    
    print(f"\n1. Parsing SBML file...")
    parser = SBMLParser()
    pathway = parser.parse_file(sbml_file)
    
    print(f"   - Found {len(pathway.species)} species")
    
    # Check for boundary species in metadata
    boundary_species = [s for s in pathway.species 
                       if s.metadata.get('boundary_condition')]
    print(f"   - Boundary species: {len(boundary_species)}")
    for s in boundary_species:
        print(f"     * {s.id} ({s.name})")
    
    print("\n2. Post-processing...")
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway)
    
    print("\n3. Converting to Petri net...")
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    print(f"\n4. Analyzing place types:")
    
    # Count place types
    signal_places = [p for p in document.places if p.is_signal_place]
    default_comp = [p for p in document.places if p.is_default_compartment_place]
    non_default_comp = [p for p in document.places if p.is_compartment_place]
    
    print(f"   - Signal places (blue hexagons): {len(signal_places)}")
    print(f"   - Default compartment (brown circles): {len(default_comp)}")
    print(f"   - Non-default compartment (green hexagons): {len(non_default_comp)}")
    
    # Find the boundary species place
    if signal_places:
        print(f"\n5. Signal places (boundary species):")
        for place in signal_places:
            comp = place.metadata.get('compartment', 'unknown')
            boundary = place.metadata.get('boundary_condition', False)
            print(f"   - {place.name} ({place.label})")
            print(f"     Compartment: {comp}")
            print(f"     Boundary condition: {boundary}")
            print(f"     is_signal_place: {place.is_signal_place}")
    
    # Verify boundary species is marked as signal place
    boundary_place = None
    for place in document.places:
        if place.metadata.get('original_species_id') == 'To':
            boundary_place = place
            break
    
    if boundary_place:
        print(f"\n6. Verification: 'To' (exogenous Trp)")
        print(f"   - is_signal_place: {boundary_place.is_signal_place}")
        print(f"   - Expected: True (blue hexagon)")
        
        if boundary_place.is_signal_place:
            print(f"   ✅ SUCCESS: Boundary species correctly marked as signal place!")
        else:
            print(f"   ❌ FAILURE: Boundary species should be marked as signal place!")
            return False
    
    print("\n" + "=" * 70)
    print("✅ All tests passed! Boundary species show as signal places.")
    print("=" * 70)
    print("\nVisualization:")
    print("  • Blue hexagons ⬢ → Boundary species (constant sources/sinks)")
    print("  • Brown circles ● → Default compartment")
    print("  • Green hexagons ⬢ → Non-default compartments")
    print()
    
    return True

if __name__ == "__main__":
    success = test_boundary_species()
    sys.exit(0 if success else 1)
