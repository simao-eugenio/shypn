#!/usr/bin/env python3
"""Test quick load functionality - parse SBML and convert to Petri net."""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_quick_load(sbml_file):
    """Test the quick load workflow."""
    print(f"\n{'='*60}")
    print(f"Testing Quick Load: {os.path.basename(sbml_file)}")
    print(f"{'='*60}\n")
    
    # Step 1: Parse SBML
    print("1. Parsing SBML...")
    parser = SBMLParser()
    pathway_data = parser.parse_file(sbml_file)
    
    if not pathway_data:
        print("❌ Failed to parse SBML file")
        return False
    
    print(f"✓ Parsed: {len(pathway_data.species)} species, {len(pathway_data.reactions)} reactions")
    
    # Step 2: Minimal post-processing (grid fallback)
    print("\n2. Minimal post-processing (grid layout)...")
    postprocessor = PathwayPostProcessor(
        spacing=150.0,
        scale_factor=1.0,
        use_tree_layout=False,         # Disable hierarchical
        use_spiral_layout=False,       # Disable spiral
        use_raw_force_directed=False   # Disable force (will use grid fallback)
    )
    
    processed = postprocessor.process(pathway_data)
    
    if not processed.positions:
        print("❌ No positions generated")
        return False
    
    print(f"✓ Processed: {len(processed.positions)} positions")
    
    # Show first few positions
    for i, (element_id, (x, y)) in enumerate(list(processed.positions.items())[:5]):
        print(f"   {element_id}: ({x:.1f}, {y:.1f})")
    
    # Step 3: Convert to Petri net
    print("\n3. Converting to Petri net...")
    converter = PathwayConverter()
    document_model = converter.convert(processed)
    
    place_count = len(document_model.places)
    transition_count = len(document_model.transitions)
    arc_count = len(document_model.arcs)
    
    print(f"✓ Converted: {place_count} places, {transition_count} transitions, {arc_count} arcs")
    
    # Show first few objects
    if document_model.places:
        print(f"\nFirst place: {document_model.places[0].name} at ({document_model.places[0].x:.1f}, {document_model.places[0].y:.1f})")
    if document_model.transitions:
        print(f"First transition: {document_model.transitions[0].name} at ({document_model.transitions[0].x:.1f}, {document_model.transitions[0].y:.1f})")
    
    print(f"\n{'='*60}")
    print("✅ Quick load test PASSED")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test file
        sbml_file = "data/biomodels_test/BIOMD0000000001.xml"
    else:
        sbml_file = sys.argv[1]
    
    if not os.path.exists(sbml_file):
        print(f"ERROR: File not found: {sbml_file}")
        sys.exit(1)
    
    success = test_quick_load(sbml_file)
    sys.exit(0 if success else 1)
