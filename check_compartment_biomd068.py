#!/usr/bin/env python3
"""Check compartments in BIOMD0000000068."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel

model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000068.shy"
document = DocumentModel.load_from_file(model_path)

print("="*80)
print("COMPARTMENT ANALYSIS - BIOMD0000000068")
print("="*80)

# Check all places for compartment properties
compartment_places = []
regular_places = []

print("\nAll places:")
for p in document.places:
    is_comp = getattr(p, 'is_compartment_place', False)
    comp_id = getattr(p, 'compartment_id', None)
    
    if is_comp:
        compartment_places.append(p)
        print(f"  [COMPARTMENT] {p.label}: tokens={p.tokens}, compartment_id={comp_id}")
    else:
        regular_places.append(p)
        print(f"  {p.label}: tokens={p.tokens}, compartment_id={comp_id}")

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Total places: {len(document.places)}")
print(f"Compartment places: {len(compartment_places)}")
print(f"Regular places: {len(regular_places)}")

# Check transitions that reference "compartment"
print(f"\n{'='*80}")
print(f"TRANSITIONS REFERENCING 'compartment'")
print(f"{'='*80}")

for t in document.transitions:
    rate = getattr(t, 'rate', None)
    if rate and isinstance(rate, str) and 'compartment' in rate.lower():
        print(f"\n{t.label}:")
        print(f"  Rate: {rate}")
        
        # Check properties
        props = getattr(t, 'properties', {})
        if 'rate_function' in props:
            print(f"  Rate function: {props['rate_function']}")

# Check if there are parameters named 'compartment'
print(f"\n{'='*80}")
print(f"PARAMETERS")
print(f"{'='*80}")

# Check transitions with kinetic metadata
for t in document.transitions:
    if hasattr(t, 'kinetic_metadata') and t.kinetic_metadata:
        if hasattr(t.kinetic_metadata, 'parameters'):
            params = t.kinetic_metadata.parameters
            if 'compartment' in params:
                print(f"\n{t.label}:")
                print(f"  compartment parameter = {params['compartment']}")

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)
print("""
If transitions reference 'compartment' in formulas but no compartment 
place exists, it means:

1. The SBML file has a compartment definition
2. But it wasn't converted to a compartment place (visual representation)
3. The 'compartment' is stored as a PARAMETER instead

This is valid - compartments can be:
  - Spatial places (with is_compartment_place=True)
  - OR parameters (just a volume/size value)

Check if 'compartment' appears in kinetic parameters.
""")
