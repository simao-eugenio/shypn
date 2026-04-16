#!/usr/bin/env python3
"""Test SBML import object creation"""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

# Test with a simple SBML file
sbml_file = "/tmp/BIOMD0000000001.xml"

print("=" * 60)
print("Testing SBML Import Object Creation")
print("=" * 60)

# Parse
parser = SBMLParser()
pathway = parser.parse_file(sbml_file)
print(f"\n1. Parsed: {len(pathway.species)} species, {len(pathway.reactions)} reactions")

# Post-process
postprocessor = PathwayPostProcessor(spacing=100, scale_factor=2.0)
processed = postprocessor.process(pathway)
print(f"2. Post-processed: {len(processed.positions)} positions")

# Convert
converter = PathwayConverter()
document = converter.convert(processed)
print(f"3. Converted: {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")

# Check first place
if document.places:
    place = document.places[0]
    print(f"\n4. First Place:")
    print(f"   - Type: {type(place).__name__}")
    print(f"   - Name: {place.name}")
    print(f"   - ID: {place.id}")
    print(f"   - Position: ({place.x}, {place.y})")
    print(f"   - Radius: {place.radius}")
    print(f"   - Border color: {place.border_color}")
    print(f"   - Has render method: {hasattr(place, 'render')}")
    print(f"   - Tokens: {place.tokens}")

print("\n" + "=" * 60)
print("✓ Test complete")
print("=" * 60)
