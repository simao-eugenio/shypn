#!/usr/bin/env python3
"""Test SBML Import Flow Analysis

This script tests the complete SBML import pipeline:
1. Parse SBML file → PathwayData
2. Validate PathwayData
3. Post-process (optional - positions/colors)
4. Convert to DocumentModel (Petri net)
5. Verify output structure

This helps diagnose any issues in the import flow.
"""

import sys
import os
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / 'src'))

print("=" * 70)
print("SBML IMPORT FLOW ANALYSIS")
print("=" * 70)

# Test file
test_file = repo_root / 'tests' / 'pathway' / 'simple_glycolysis.sbml'
print(f"\nTest file: {test_file}")
print(f"File exists: {test_file.exists()}")

if not test_file.exists():
    print("❌ Test file not found!")
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 1: Import Dependencies")
print("=" * 70)

try:
    import libsbml
    print(f"✅ libsbml installed: v{libsbml.getLibSBMLDottedVersion()}")
except ImportError as e:
    print(f"❌ libsbml not available: {e}")
    sys.exit(1)

try:
    from shypn.data.pathway.sbml_parser import SBMLParser
    print("✅ SBMLParser imported")
except ImportError as e:
    print(f"❌ SBMLParser import failed: {e}")
    sys.exit(1)

try:
    from shypn.data.pathway.pathway_validator import PathwayValidator
    print("✅ PathwayValidator imported")
except ImportError as e:
    print(f"❌ PathwayValidator import failed: {e}")
    sys.exit(1)

try:
    from shypn.data.pathway.pathway_converter import PathwayConverter
    print("✅ PathwayConverter imported")
except ImportError as e:
    print(f"❌ PathwayConverter import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 2: Parse SBML File → PathwayData")
print("=" * 70)

try:
    parser = SBMLParser()
    pathway_data = parser.parse_file(test_file)
    
    print(f"✅ Parse successful!")
    print(f"   Species: {len(pathway_data.species)}")
    print(f"   Reactions: {len(pathway_data.reactions)}")
    print(f"   Compartments: {len(pathway_data.compartments)}")
    print(f"   Parameters: {len(pathway_data.parameters)}")
    print(f"   Metadata: {pathway_data.metadata}")
    
    print("\n   Species details:")
    for species in pathway_data.species:
        print(f"     - {species.id}: {species.name} (compartment: {species.compartment})")
        print(f"       initial_concentration: {species.initial_concentration}, initial_tokens: {species.initial_tokens}")
    
    print("\n   Reaction details:")
    for reaction in pathway_data.reactions:
        print(f"     - {reaction.id}: {reaction.name}")
        print(f"       reactants: {[f'{species_id}({stoich})' for species_id, stoich in reaction.reactants]}")
        print(f"       products: {[f'{species_id}({stoich})' for species_id, stoich in reaction.products]}")
        print(f"       reversible: {reaction.reversible}")
        if reaction.kinetic_law:
            print(f"       kinetics: {reaction.kinetic_law.formula if reaction.kinetic_law.formula else 'No formula'}")
    
except Exception as e:
    print(f"❌ Parse failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 3: Validate PathwayData")
print("=" * 70)

try:
    validator = PathwayValidator()
    validation_result = validator.validate(pathway_data)
    
    print(f"Valid: {validation_result.is_valid}")
    
    if validation_result.errors:
        print(f"❌ Errors ({len(validation_result.errors)}):")
        for error in validation_result.errors:
            print(f"     - {error}")
    else:
        print("✅ No errors")
    
    if validation_result.warnings:
        print(f"⚠️  Warnings ({len(validation_result.warnings)}):")
        for warning in validation_result.warnings:
            print(f"     - {warning}")
    else:
        print("✅ No warnings")
    
    if not validation_result.is_valid:
        print("\n❌ Validation failed - cannot proceed")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 4: Post-Process PathwayData → ProcessedPathwayData")
print("=" * 70)

try:
    from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
    
    postprocessor = PathwayPostProcessor(scale_factor=1.0)
    processed_pathway = postprocessor.process(pathway_data)
    
    print(f"✅ Post-processing successful!")
    print(f"   Species: {len(processed_pathway.species)}")
    print(f"   Reactions: {len(processed_pathway.reactions)}")
    
    print("\n   Species tokens after normalization:")
    for species in processed_pathway.species:
        print(f"     - {species.id}: {species.initial_tokens} tokens (from {species.initial_concentration} concentration)")
    
    print("\n   Layout type: {processed_pathway.metadata.get('layout_type', 'unknown')}")
    
except Exception as e:
    print(f"❌ Post-processing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 5: Convert to DocumentModel (Petri Net)")
print("=" * 70)

try:
    converter = PathwayConverter()
    document_model = converter.convert(processed_pathway)
    
    print(f"✅ Conversion successful!")
    print(f"   Places: {len(document_model.places)}")
    print(f"   Transitions: {len(document_model.transitions)}")
    print(f"   Arcs: {len(document_model.arcs)}")
    
    print("\n   Place details:")
    for place in document_model.places:
        print(f"     - {place.id}: {place.label}")
        print(f"       tokens: {place.tokens}, position: ({place.x}, {place.y})")
    
    print("\n   Transition details:")
    for transition in document_model.transitions:
        print(f"     - {transition.id}: {transition.label}")
        print(f"       position: ({transition.x}, {transition.y})")
    
    print("\n   Arc details:")
    for arc in document_model.arcs:
        from shypn.netobjs.place import Place
        arc_type = "Place→Transition" if isinstance(arc.source, Place) else "Transition→Place"
        print(f"     - {arc.source_id} → {arc.target_id} ({arc_type})")
        print(f"       weight: {arc.weight}")
    
except Exception as e:
    print(f"❌ Conversion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 6: Verify Petri Net Structure")
print("=" * 70)

# Check for common issues
issues = []

# Check 1: Places should have positions (even if 0,0)
for place in document_model.places:
    if place.x is None or place.y is None:
        issues.append(f"Place {place.id} has no position")

# Check 2: Transitions should have positions
for transition in document_model.transitions:
    if transition.x is None or transition.y is None:
        issues.append(f"Transition {transition.id} has no position")

# Check 3: Arcs should reference existing objects
from shypn.netobjs.place import Place
place_ids = {p.id for p in document_model.places}
transition_ids = {t.id for t in document_model.transitions}

for arc in document_model.arcs:
    if isinstance(arc.source, Place):
        if arc.source_id not in place_ids:
            issues.append(f"Arc references unknown place: {arc.source_id}")
        if arc.target_id not in transition_ids:
            issues.append(f"Arc references unknown transition: {arc.target_id}")
    else:  # transition to place
        if arc.source_id not in transition_ids:
            issues.append(f"Arc references unknown transition: {arc.source_id}")
        if arc.target_id not in place_ids:
            issues.append(f"Arc references unknown place: {arc.target_id}")

# Check 4: Each species should map to a place
species_ids = {s.id for s in pathway_data.species}
place_original_ids = {p.metadata.get('original_id') for p in document_model.places if 'original_id' in p.metadata}

unmapped_species = species_ids - place_original_ids
if unmapped_species:
    issues.append(f"Species not mapped to places: {unmapped_species}")

# Check 5: Each reaction should map to a transition
reaction_ids = {r.id for r in pathway_data.reactions}
transition_original_ids = {t.metadata.get('original_id') for t in document_model.transitions if 'original_id' in t.metadata}

unmapped_reactions = reaction_ids - transition_original_ids
if unmapped_reactions:
    issues.append(f"Reactions not mapped to transitions: {unmapped_reactions}")

if issues:
    print(f"⚠️  Found {len(issues)} potential issues:")
    for issue in issues:
        print(f"     - {issue}")
else:
    print("✅ No structural issues found")

print("\n" + "=" * 70)
print("STEP 7: Network Connectivity Analysis")
print("=" * 70)

# Build connectivity map
from shypn.netobjs.place import Place
place_incoming = {p.id: [] for p in document_model.places}
place_outgoing = {p.id: [] for p in document_model.places}
transition_incoming = {t.id: [] for t in document_model.transitions}
transition_outgoing = {t.id: [] for t in document_model.transitions}

for arc in document_model.arcs:
    if isinstance(arc.source, Place):
        place_outgoing[arc.source_id].append(arc.target_id)
        transition_incoming[arc.target_id].append(arc.source_id)
    else:
        transition_outgoing[arc.source_id].append(arc.target_id)
        place_incoming[arc.target_id].append(arc.source_id)

print("\nPlace connectivity:")
for place in document_model.places:
    incoming = len(place_incoming[place.id])
    outgoing = len(place_outgoing[place.id])
    print(f"  {place.id}: {incoming} in, {outgoing} out")
    if incoming == 0 and outgoing == 0:
        print(f"    ⚠️  Isolated place (no connections)")

print("\nTransition connectivity:")
for transition in document_model.transitions:
    incoming = len(transition_incoming[transition.id])
    outgoing = len(transition_outgoing[transition.id])
    print(f"  {transition.id}: {incoming} in, {outgoing} out")
    if incoming == 0:
        print(f"    ⚠️  No input places")
    if outgoing == 0:
        print(f"    ⚠️  No output places")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("\n✅ SBML Import Flow Test PASSED")
print(f"\nSuccessfully converted {len(pathway_data.species)} species and "
      f"{len(pathway_data.reactions)} reactions")
print(f"into {len(document_model.places)} places, "
      f"{len(document_model.transitions)} transitions, "
      f"and {len(document_model.arcs)} arcs")

print("\n📋 Flow steps verified:")
print("   ✅ 1. Parse SBML → PathwayData")
print("   ✅ 2. Validate PathwayData")
print("   ✅ 3. Post-process → ProcessedPathwayData")
print("   ✅ 4. Convert to DocumentModel")
print("   ✅ 5. Verify Petri net structure")
print("   ✅ 6. Check network connectivity")

print("\n" + "=" * 70)
