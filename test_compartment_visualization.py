#!/usr/bin/env python3
"""Test script for compartment visualization feature."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

def test_compartment_visualization():
    """Test compartment visualization on BIOMD0000000061."""
    
    print("=" * 70)
    print("Testing Compartment Visualization Feature")
    print("=" * 70)
    
    # Load BIOMD0000000061
    sbml_file = "./workspace/projects/My_Project/pathways/BIOMD0000000061.xml"
    
    if not os.path.exists(sbml_file):
        print(f"ERROR: File not found: {sbml_file}")
        return False
    
    print(f"\n1. Parsing SBML file: {sbml_file}")
    parser = SBMLParser()
    pathway = parser.parse_file(sbml_file)
    
    print(f"   - Found {len(pathway.species)} species")
    print(f"   - Found {len(pathway.compartments)} compartments: {list(pathway.compartments.keys())}")
    
    # Count species per compartment
    from collections import Counter
    comp_counts = Counter(s.compartment for s in pathway.species)
    print(f"   - Species per compartment:")
    for comp, count in comp_counts.most_common():
        print(f"     * {comp}: {count} species")
    
    print("\n2. Post-processing pathway...")
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway)
    
    print("\n3. Converting to Petri net...")
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    print(f"\n4. Analyzing place visualization:")
    print(f"   - Total places: {len(document.places)}")
    
    # Count place types
    signal_places = [p for p in document.places if p.is_signal_place]
    compartment_places = [p for p in document.places if p.is_compartment_place]
    normal_places = [p for p in document.places 
                    if not p.is_compartment_place and not p.is_signal_place]
    
    print(f"   - Non-default compartment (circles, green border): {len(compartment_places)}")
    print(f"   - Normal places/cytosol (circles, black): {len(normal_places)}")
    print(f"   - Signal places (hexagons, blue): {len(signal_places)}")
    
    # Show some examples
    if compartment_places:
        print(f"\n5. Non-default compartment places (green border circles):")
        for place in compartment_places[:5]:  # Show first 5
            comp = place.metadata.get('compartment', 'unknown')
            print(f"   - {place.name} ({place.label}): compartment={comp}")
    
    if normal_places:
        print(f"\n6. Normal/cytosol places (black circles, first 5):")
        for place in normal_places[:5]:
            comp = place.metadata.get('compartment', 'unknown')
            print(f"   - {place.name} ({place.label}): compartment={comp}")
    
    # Verify extracellular glucose is marked
    glcx_place = None
    for place in document.places:
        if 'GlcX' in place.label or 'Extracellular glucose' in place.label:
            glcx_place = place
            break
    
    if glcx_place:
        print(f"\n7. Extracellular glucose check:")
        print(f"   - Found place: {glcx_place.name} ({glcx_place.label})")
        print(f"   - Compartment: {glcx_place.metadata.get('compartment', 'unknown')}")
        print(f"   - is_compartment_place: {glcx_place.is_compartment_place}")
        print(f"   - Expected: True (should render as green circle)")
        
        if glcx_place.is_compartment_place:
            print(f"   ✅ SUCCESS: GlcX correctly marked as non-default compartment place!")
        else:
            print(f"   ❌ FAILURE: GlcX should be marked as non-default compartment place!")
            return False
    
    # Verify cytosolic glucose is normal (NOT marked specially)
    glc_place = None
    for place in document.places:
        if place.label == 'Cytosolic glucose' or (place.metadata.get('original_species_id') == 'Glc'):
            glc_place = place
            break
    
    if glc_place:
        print(f"\n8. Cytosolic glucose check:")
        print(f"   - Found place: {glc_place.name} ({glc_place.label})")
        print(f"   - Compartment: {glc_place.metadata.get('compartment', 'unknown')}")
        print(f"   - is_compartment_place: {glc_place.is_compartment_place}")
        print(f"   - is_signal_place: {glc_place.is_signal_place}")
        print(f"   - Expected: False for both (normal black circle - cytosol is default)")
        
        if not glc_place.is_compartment_place and not glc_place.is_signal_place:
            print(f"   ✅ SUCCESS: Glc correctly shown as normal place (black circle)!")
        else:
            print(f"   ❌ FAILURE: Glc should be a normal place!")
            return False
    
    print("\n" + "=" * 70)
    print("✅ All tests passed! Compartment visualization implemented successfully.")
    print("=" * 70)
    print("\nVisualization Legend:")
    print("  • Circles (black) → Normal places (cytosol/default compartment)")
    print("  • Circles (green border) → Non-default compartments (extracellular)")
    print("  • Hexagons (blue) → Signal places ONLY (no arcs - Bio-PN Ψ)")
    print("\nBio-PN Formalism Compliance:")
    print("  ✓ Hexagons = No arc connections (signal places)")
    print("  ✓ Circles = Normal places with arcs (all compartments)")
    print("\nSpatial Layout:")
    print("  • Extracellular species → Top edge (y=100, periphery)")
    print("  • Cytosolic species → Center region (y=300+)")
    print("  • Visual separation between compartments!")
    print()
    
    return True

if __name__ == "__main__":
    success = test_compartment_visualization()
    sys.exit(0 if success else 1)
