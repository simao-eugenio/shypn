#!/usr/bin/env python3
"""Test that SBML formulas are properly set as rate_function."""

import sys
sys.path.insert(0, 'src')

from shypn.data.pathway.pathway_data import Species, Reaction, KineticLaw, PathwayData
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

# Create simple pathway with kinetic law
glucose = Species(
    id="Glc",
    name="Glucose",
    compartment="cytosol",
    initial_concentration=5.0
)

g6p = Species(
    id="G6P",
    name="Glucose-6-phosphate",
    compartment="cytosol",
    initial_concentration=0.0
)

atp = Species(
    id="ATP",
    name="ATP",
    compartment="cytosol",
    initial_concentration=2.5
)

# Hexokinase reaction with explicit SBML formula
hexokinase = Reaction(
    id="HK",
    name="Hexokinase",
    reactants=[("Glc", 1.0), ("ATP", 1.0)],
    products=[("G6P", 1.0)],
    kinetic_law=KineticLaw(
        formula="Vmax * Glc / (Km + Glc)",  # SBML formula
        rate_type="michaelis_menten",
        parameters={"Vmax": 10.0, "Km": 0.1}
    )
)

pathway = PathwayData(
    species=[glucose, g6p, atp],
    reactions=[hexokinase],
    compartments={"cytosol": "Cytoplasm"},
    metadata={"name": "Test Glycolysis"}
)

# Process and convert
postprocessor = PathwayPostProcessor()
processed = postprocessor.process(pathway)

# Add source_file to pathway metadata so converter can use it
processed.metadata['source_file'] = 'test.xml'

converter = PathwayConverter()
document = converter.convert(processed)

# Check results
print("="*70)
print("Rate Function Integration Test")
print("="*70)

for transition in document.transitions:
    print(f"\nTransition: {transition.name} ({transition.label})")
    print(f"  Type: {transition.transition_type}")
    print(f"  Rate: {transition.rate}")
    
    # Check for rate_function in properties
    if 'rate_function' in transition.properties:
        print(f"  ✅ rate_function: {transition.properties['rate_function']}")
    else:
        print(f"  ❌ NO rate_function in properties!")
    
    # Check for kinetic_metadata
    if hasattr(transition, 'kinetic_metadata') and transition.kinetic_metadata:
        km = transition.kinetic_metadata
        print(f"  ✅ kinetic_metadata:")
        print(f"     - Source: {km.source}")
        print(f"     - Formula: {km.formula}")
        print(f"     - Parameters: {km.parameters}")
    else:
        print(f"  ❌ NO kinetic_metadata!")

print("\n" + "="*70)
print("Test Summary:")

has_rate_function = all(
    'rate_function' in t.properties 
    for t in document.transitions
)

has_metadata = all(
    hasattr(t, 'kinetic_metadata') and t.kinetic_metadata
    for t in document.transitions
)

if has_rate_function and has_metadata:
    print("✅ PASS: Both rate_function and kinetic_metadata are set!")
    print("\nThe SBML formulas are now ready to be:")
    print("1. Displayed in the Transition Property Dialog")
    print("2. Evaluated during simulation using place concentrations")
    print("3. Used as processing_time/post_time expressions")
else:
    print("❌ FAIL: Missing rate_function or kinetic_metadata")
    if not has_rate_function:
        print("  - rate_function not set in properties")
    if not has_metadata:
        print("  - kinetic_metadata not attached")

print("="*70)
