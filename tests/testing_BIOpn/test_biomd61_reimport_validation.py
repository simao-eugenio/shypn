#!/usr/bin/env python3
"""
Test BIOMD0000000061 import with automatic transition type validation.

This script re-imports the Hynne2001 Glycolysis model and verifies that
stochastic transitions with reversible formulas are automatically converted
to continuous type during import.
"""

import sys
import json
sys.path.insert(0, 'src')

from pathlib import Path
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter


def test_biomd61_reimport():
    """Re-import BIOMD0000000061 and verify automatic validation."""
    
    sbml_file = Path("workspace/projects/SBML/pathways/BIOMD0000000061.xml")
    output_file = Path("workspace/projects/SBML/models/BIOMD0000000061_test.shy")
    
    if not sbml_file.exists():
        print(f"❌ SBML file not found: {sbml_file}")
        return False
    
    print(f"\n{'='*80}")
    print(f"BIOMD0000000061 Re-Import Test with Auto-Validation")
    print(f"{'='*80}")
    print(f"\nInput:  {sbml_file}")
    print(f"Output: {output_file}")
    
    try:
        # Parse SBML
        print(f"\n1️⃣  Parsing SBML...")
        parser = SBMLParser()
        pathway_data = parser.parse_file(str(sbml_file))
        
        print(f"   ✓ Parsed:")
        print(f"     - {len(pathway_data.species)} species")
        print(f"     - {len(pathway_data.reactions)} reactions")
        print(f"     - {len(pathway_data.parameters)} parameters")
        
        # Post-process
        print(f"\n2️⃣  Post-processing...")
        postprocessor = PathwayPostProcessor()
        processed = postprocessor.process(pathway_data)
        
        print(f"   ✓ Processed:")
        print(f"     - {len(processed.species)} species")
        print(f"     - {len(processed.reactions)} reactions")
        
        # Convert to DocumentModel (triggers automatic validation)
        print(f"\n3️⃣  Converting to Petri net (with auto-validation)...")
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        print(f"   ✓ Converted:")
        print(f"     - {len(document.places)} places")
        print(f"     - {len(document.transitions)} transitions")
        print(f"     - {len(document.arcs)} arcs")
        
        # Analyze transition types
        print(f"\n4️⃣  Analyzing transition types...")
        
        stochastic_transitions = []
        continuous_transitions = []
        converted_transitions = []
        
        for t in document.transitions:
            if t.transition_type == 'stochastic':
                stochastic_transitions.append(t)
            elif t.transition_type == 'continuous':
                continuous_transitions.append(t)
            
            # Check if marked as converted
            if hasattr(t, 'properties') and 'enrichment_reason' in t.properties:
                reason = t.properties['enrichment_reason']
                if 'Converted from stochastic' in reason or 'reversible' in reason.lower():
                    converted_transitions.append(t)
        
        print(f"\n   Transition Type Distribution:")
        print(f"     - Continuous: {len(continuous_transitions)}")
        print(f"     - Stochastic: {len(stochastic_transitions)}")
        print(f"     - Auto-converted: {len(converted_transitions)}")
        
        # List converted transitions
        if converted_transitions:
            print(f"\n   🔄 Auto-Converted Transitions (Reversible Formulas Detected):")
            for t in converted_transitions:
                formula = t.properties.get('rate_function_display', 'N/A')
                print(f"     ✓ {t.name}: {t.label}")
                if ' - ' in formula:
                    print(f"       Formula: {formula[:60]}...")
        
        # Check for problematic stochastic transitions
        print(f"\n5️⃣  Checking for problematic stochastic transitions...")
        
        problematic = []
        for t in stochastic_transitions:
            if hasattr(t, 'properties') and 'rate_function' in t.properties:
                formula = t.properties['rate_function']
                if ' - ' in formula:
                    problematic.append((t, formula))
        
        if problematic:
            print(f"   ⚠️  WARNING: Found {len(problematic)} stochastic transitions with subtraction:")
            for t, formula in problematic:
                print(f"     - {t.name}: {formula[:60]}...")
            print(f"\n   ❌ TEST FAILED: Validation did not catch all reversible formulas!")
            return False
        else:
            print(f"   ✅ No problematic stochastic transitions found!")
        
        # Save model
        print(f"\n6️⃣  Saving model...")
        document.save_to_file(str(output_file))
        print(f"   ✓ Saved to: {output_file}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"✅ TEST PASSED: Automatic validation working correctly!")
        print(f"{'='*80}")
        print(f"\nResults:")
        print(f"  ✓ {len(converted_transitions)} transitions auto-converted")
        print(f"  ✓ 0 problematic stochastic transitions remaining")
        print(f"  ✓ Model ready for simulation")
        print(f"\nKey Benefits:")
        print(f"  • No manual fix script needed")
        print(f"  • Automatic detection of reversible reactions")
        print(f"  • Correct transition types from the start")
        print(f"  • Prevents negative rate errors during simulation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_biomd61_reimport()
    sys.exit(0 if success else 1)
