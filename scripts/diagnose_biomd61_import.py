#!/usr/bin/env python3
"""
Diagnose all issues during BIOMD0000000061.xml import.
"""

import sys
import logging
from pathlib import Path
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.netobjs.test_arc import TestArc

# Set up logging to capture all warnings and errors
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s]: %(message)s',
    stream=sys.stdout
)

def main():
    sbml_path = Path("workspace/projects/My_Project/pathways/BIOMD0000000061.xml")
    
    if not sbml_path.exists():
        print(f"❌ File not found: {sbml_path}")
        return False
    
    print("=" * 80)
    print("BIOMD0000000061.xml - Complete Diagnostic")
    print("=" * 80)
    
    # Parse SBML
    print("\n" + "=" * 80)
    print("PHASE 1: SBML PARSING")
    print("=" * 80)
    parser = SBMLParser()
    pathway = parser.parse_file(str(sbml_path))
    
    print(f"\n✓ Parsed: {len(pathway.species)} species, {len(pathway.reactions)} reactions")
    
    # Check for parsing issues
    reactions_with_modifiers = [r for r in pathway.reactions if r.modifiers]
    reactions_with_kinetics = [r for r in pathway.reactions if r.kinetic_law]
    
    print(f"  - Reactions with modifiers: {len(reactions_with_modifiers)}")
    print(f"  - Reactions with kinetic laws: {len(reactions_with_kinetics)}")
    
    # Postprocess
    print("\n" + "=" * 80)
    print("PHASE 2: PATHWAY POSTPROCESSING")
    print("=" * 80)
    postprocessor = PathwayPostProcessor()
    processed_pathway = postprocessor.process(pathway)
    
    print(f"\n✓ Postprocessed: Positions assigned to {len(processed_pathway.positions)} objects")
    
    # Convert
    print("\n" + "=" * 80)
    print("PHASE 3: PETRI NET CONVERSION")
    print("=" * 80)
    converter = PathwayConverter()
    document = converter.convert(processed_pathway)
    
    # Analyze results
    print("\n" + "=" * 80)
    print("ANALYSIS: DOCUMENT STRUCTURE")
    print("=" * 80)
    
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    normal_arcs = [arc for arc in document.arcs if not isinstance(arc, TestArc)]
    
    print(f"\nPlaces: {len(document.places)}")
    print(f"Transitions: {len(document.transitions)}")
    print(f"Arcs: {len(document.arcs)}")
    print(f"  - Normal arcs: {len(normal_arcs)}")
    print(f"  - Test arcs: {len(test_arcs)}")
    
    # Check transition types
    stochastic_transitions = [t for t in document.transitions if hasattr(t, 'behavior') and t.behavior and t.behavior.__class__.__name__ == 'StochasticBehavior']
    continuous_transitions = [t for t in document.transitions if hasattr(t, 'behavior') and t.behavior and t.behavior.__class__.__name__ == 'ContinuousBehavior']
    immediate_transitions = [t for t in document.transitions if hasattr(t, 'behavior') and t.behavior and t.behavior.__class__.__name__ == 'ImmediateBehavior']
    
    print(f"\nTransition types:")
    print(f"  - Stochastic: {len(stochastic_transitions)}")
    print(f"  - Continuous: {len(continuous_transitions)}")
    print(f"  - Immediate: {len(immediate_transitions)}")
    print(f"  - No behavior: {len(document.transitions) - len(stochastic_transitions) - len(continuous_transitions) - len(immediate_transitions)}")
    
    # Check for issues
    print("\n" + "=" * 80)
    print("ANALYSIS: POTENTIAL ISSUES")
    print("=" * 80)
    
    issues_found = 0
    
    # Issue 1: Places with no arcs
    places_no_arcs = []
    for place in document.places:
        connected = any(arc.source == place or arc.target == place for arc in document.arcs)
        if not connected:
            places_no_arcs.append(place)
    
    if places_no_arcs:
        issues_found += 1
        print(f"\n⚠️  Issue {issues_found}: Disconnected places ({len(places_no_arcs)})")
        for place in places_no_arcs[:5]:
            print(f"     - {place.name} (ID: {place.id})")
    
    # Issue 2: Transitions with no input arcs
    transitions_no_inputs = []
    for transition in document.transitions:
        has_input = any(arc.target == transition for arc in document.arcs)
        if not has_input:
            transitions_no_inputs.append(transition)
    
    if transitions_no_inputs:
        issues_found += 1
        print(f"\n⚠️  Issue {issues_found}: Transitions with no inputs ({len(transitions_no_inputs)})")
        for trans in transitions_no_inputs[:5]:
            print(f"     - {trans.name} (ID: {trans.id})")
    
    # Issue 3: Transitions with no output arcs
    transitions_no_outputs = []
    for transition in document.transitions:
        has_output = any(arc.source == transition for arc in document.arcs)
        if not has_output:
            transitions_no_outputs.append(transition)
    
    if transitions_no_outputs:
        issues_found += 1
        print(f"\n⚠️  Issue {issues_found}: Transitions with no outputs ({len(transitions_no_outputs)})")
        for trans in transitions_no_outputs[:5]:
            print(f"     - {trans.name} (ID: {trans.id})")
    
    # Issue 4: Mixed role species (already checked by converter)
    mixed_role_species = []
    for species_id, place in enumerate(document.places):
        is_catalyst = any(isinstance(arc, TestArc) and arc.source == place for arc in document.arcs)
        is_reactant = any(not isinstance(arc, TestArc) and arc.source == place and hasattr(arc.target, 'behavior') for arc in document.arcs)
        if is_catalyst and is_reactant:
            mixed_role_species.append(place)
    
    if mixed_role_species:
        issues_found += 1
        print(f"\n⚠️  Issue {issues_found}: Mixed role species ({len(mixed_role_species)})")
        print(f"     (Already reported by converter)")
    
    # Issue 5: Transitions without kinetic metadata
    transitions_no_kinetics = [t for t in document.transitions 
                               if not hasattr(t, 'kinetic_metadata') or t.kinetic_metadata is None]
    
    if transitions_no_kinetics:
        issues_found += 1
        print(f"\n⚠️  Issue {issues_found}: Transitions without kinetic metadata ({len(transitions_no_kinetics)})")
        for trans in transitions_no_kinetics[:5]:
            print(f"     - {trans.name} (ID: {trans.id})")
    
    # Issue 6: Check for rate function errors
    transitions_with_rate_errors = []
    for transition in document.transitions:
        if hasattr(transition, 'properties') and transition.properties:
            rate_function = transition.properties.get('rate_function')
            if rate_function:
                # Check for common issues
                if '^' in rate_function:
                    print(f"\n⚠️  Found unconverted '^' operator in {transition.name}")
                    transitions_with_rate_errors.append(transition)
    
    if transitions_with_rate_errors:
        issues_found += 1
        print(f"\n⚠️  Issue {issues_found}: Rate functions with unconverted operators ({len(transitions_with_rate_errors)})")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if issues_found == 0:
        print("\n✅ No structural issues found!")
    else:
        print(f"\n⚠️  Found {issues_found} types of potential issues")
        print("\nNote: Some 'issues' may be intentional model features:")
        print("  - Boundary species (sources/sinks) have one-way connections")
        print("  - Mixed role species represent cofactors with dual functions")
        print("  - Some warnings are informational, not errors")
    
    print(f"\nModel type: {document.metadata.get('model_type', 'Standard')}")
    print(f"Has test arcs: {document.metadata.get('has_test_arcs', False)}")
    
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
