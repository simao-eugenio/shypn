#!/usr/bin/env python3
"""
Test script to compare layered vs spiral layout projection.

Usage:
    python scripts/test_spiral_layout.py BIOMD0000000001
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_validator import PathwayValidator
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def test_layout_comparison(biomodels_id: str):
    """Compare layered vs spiral layout for a BioModels pathway."""
    
    print(f"\n{'='*70}")
    print(f"LAYOUT COMPARISON TEST: {biomodels_id}")
    print(f"{'='*70}\n")
    
    # Fetch and parse SBML
    import urllib.request
    import tempfile
    
    url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml"
    temp_file = os.path.join(tempfile.gettempdir(), f"{biomodels_id}.xml")
    
    print(f"1. Fetching {biomodels_id} from BioModels...")
    urllib.request.urlretrieve(url, temp_file)
    print(f"   ✓ Downloaded to {temp_file}")
    
    print(f"\n2. Parsing SBML file...")
    parser = SBMLParser()
    pathway = parser.parse_file(temp_file)
    print(f"   ✓ Species: {len(pathway.species)}, Reactions: {len(pathway.reactions)}")
    
    print(f"\n3. Validating pathway...")
    validator = PathwayValidator()
    result = validator.validate(pathway)
    if result.is_valid:
        print(f"   ✓ Valid (warnings: {len(result.warnings)})")
    else:
        print(f"   ✗ Invalid (errors: {len(result.errors)})")
        return
    
    # Test LAYERED layout
    print(f"\n4. Testing LAYERED layout (top → bottom)...")
    postprocessor_layered = PathwayPostProcessor(
        spacing=150.0,
        scale_factor=1.0,
        use_tree_layout=True,
        use_spiral_layout=False  # Layered
    )
    processed_layered = postprocessor_layered.process(pathway)
    
    layered_width = processed_layered.metadata.get('canvas_width', 'N/A')
    layered_height = processed_layered.metadata.get('canvas_height', 'N/A')
    layered_type = processed_layered.metadata.get('layout_type', 'N/A')
    
    print(f"   Layout type: {layered_type}")
    print(f"   Canvas: {layered_width:.0f}x{layered_height:.0f}px")
    print(f"   Positions: {len(processed_layered.positions)}")
    
    # Test SPIRAL layout
    print(f"\n5. Testing SPIRAL layout (center → outward)...")
    postprocessor_spiral = PathwayPostProcessor(
        spacing=150.0,
        scale_factor=1.0,
        use_tree_layout=True,
        use_spiral_layout=True  # Spiral
    )
    processed_spiral = postprocessor_spiral.process(pathway)
    
    spiral_width = processed_spiral.metadata.get('canvas_width', 'N/A')
    spiral_height = processed_spiral.metadata.get('canvas_height', 'N/A')
    spiral_type = processed_spiral.metadata.get('layout_type', 'N/A')
    
    print(f"   Layout type: {spiral_type}")
    print(f"   Canvas: {spiral_width:.0f}x{spiral_height:.0f}px")
    print(f"   Positions: {len(processed_spiral.positions)}")
    
    # Comparison
    print(f"\n{'='*70}")
    print(f"COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(f"{'Layout':<15} {'Type':<25} {'Canvas Size':<20}")
    print(f"{'-'*70}")
    print(f"{'Layered':<15} {layered_type:<25} {layered_width:.0f}x{layered_height:.0f}px")
    print(f"{'Spiral':<15} {spiral_type:<25} {spiral_width:.0f}x{spiral_height:.0f}px")
    print(f"{'='*70}\n")
    
    print("✓ Test complete! Both layouts generated successfully.")
    print("\nTo use spiral layout in the UI, set use_spiral_layout=True")
    print("in PathwayPostProcessor initialization.\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_spiral_layout.py BIOMD0000000001")
        sys.exit(1)
    
    biomodels_id = sys.argv[1]
    test_layout_comparison(biomodels_id)
