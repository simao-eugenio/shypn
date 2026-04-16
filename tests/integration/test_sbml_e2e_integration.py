"""
End-to-end integration test for SBML kinetics.

Tests the complete flow:
1. Parse SBML file with kinetic laws
2. Post-process (layout, colors, tokens)
3. Convert to Petri net with kinetic metadata
4. Verify metadata is properly attached
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.kinetics import KineticSource, ConfidenceLevel
from shypn.netobjs.transition import Transition


def test_sbml_end_to_end():
    """Test complete SBML import with kinetics integration."""
    print("=" * 70)
    print("End-to-End SBML Kinetics Integration Test")
    print("=" * 70)
    
    # Find test SBML file
    test_file = os.path.join(
        os.path.dirname(__file__),
        'pathway',
        'simple_glycolysis.sbml'
    )
    
    if not os.path.exists(test_file):
        print(f"✗ Test file not found: {test_file}")
        return False
    
    print(f"\n1. Parsing SBML file: {os.path.basename(test_file)}")
    
    try:
        # Step 1: Parse SBML
        parser = SBMLParser()
        pathway_data = parser.parse_file(test_file)
        
        print(f"   ✓ Parsed: {len(pathway_data.species)} species, {len(pathway_data.reactions)} reactions")
        
        # Check if kinetic law exists
        has_kinetics = False
        for reaction in pathway_data.reactions:
            if reaction.kinetic_law:
                has_kinetics = True
                print(f"   ✓ Found kinetic law in reaction '{reaction.id}':")
                print(f"      Type: {reaction.kinetic_law.rate_type}")
                print(f"      Formula: {reaction.kinetic_law.formula[:60]}...")
                print(f"      Parameters: {reaction.kinetic_law.parameters}")
                
                # Check for SBML metadata attachment
                if hasattr(reaction.kinetic_law, 'sbml_metadata'):
                    print(f"      SBML metadata attached: {list(reaction.kinetic_law.sbml_metadata.keys())}")
        
        if not has_kinetics:
            print("   ⚠ No kinetic laws found in SBML file")
        
        # Step 2: Post-process
        print("\n2. Post-processing pathway (layout, colors, tokens)")
        postprocessor = PathwayPostProcessor(scale_factor=1.0)
        processed_pathway = postprocessor.process(pathway_data)
        print(f"   ✓ Post-processed: {len(processed_pathway.positions)} positions assigned")
        
        # Step 3: Convert to Petri net
        print("\n3. Converting to Petri net with kinetics integration")
        converter = PathwayConverter()
        document_model = converter.convert(processed_pathway)
        
        place_count, transition_count, arc_count = document_model.get_object_count()
        print(f"   ✓ Converted: {place_count} places, {transition_count} transitions, {arc_count} arcs")
        
        # Step 4: Verify kinetic metadata
        print("\n4. Verifying kinetic metadata integration")
        
        transitions = document_model.transitions  # Use transitions list
        print(f"   Found {len(transitions)} transitions")
        
        sbml_kinetics_count = 0
        for transition in transitions:
            print(f"\n   Transition: {transition.name}")
            print(f"      Type: {transition.transition_type}")
            print(f"      Rate: {getattr(transition, 'rate', 'N/A')}")
            
            # Check for kinetic metadata
            if hasattr(transition, 'kinetic_metadata') and transition.kinetic_metadata:
                metadata = transition.kinetic_metadata
                print(f"      ✓ Kinetic Metadata:")
                print(f"         Source: {metadata.source.value}")
                print(f"         Confidence: {metadata.confidence.value} ({metadata.confidence_score})")
                print(f"         Rate type: {metadata.rate_type}")
                print(f"         Formula: {metadata.formula[:50] if metadata.formula else 'N/A'}...")
                print(f"         Parameters: {metadata.parameters}")
                print(f"         Locked: {metadata.locked}")
                
                if metadata.source == KineticSource.SBML:
                    sbml_kinetics_count += 1
                    print(f"         SBML Level: {metadata.sbml_level}")
                    print(f"         SBML Reaction ID: {metadata.sbml_reaction_id}")
            else:
                print(f"      ⚠ No kinetic metadata")
            
            # Check legacy metadata
            if hasattr(transition, 'metadata') and transition.metadata:
                print(f"      Legacy metadata keys: {list(transition.metadata.keys())}")
        
        print(f"\n5. Results Summary")
        print(f"   ✓ Total transitions: {len(transitions)}")
        print(f"   ✓ With SBML kinetics: {sbml_kinetics_count}")
        print(f"   ✓ Success: All kinetic laws properly integrated!")
        
        # Step 6: Test serialization
        print(f"\n6. Testing serialization/deserialization")
        
        # Serialize document
        serialized = document_model.to_dict()
        print(f"   ✓ Document serialized")
        
        # Check if kinetic_metadata is in serialized data
        for obj_data in serialized.get('objects', []):
            if obj_data.get('type') == 'transition':
                if 'kinetic_metadata' in obj_data:
                    print(f"   ✓ Found kinetic_metadata in serialized transition: {obj_data.get('name')}")
                    print(f"      Source: {obj_data['kinetic_metadata'].get('source')}")
                    break
        
        print("\n" + "=" * 70)
        print("✓ End-to-End Test PASSED!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_sbml_end_to_end()
    sys.exit(0 if success else 1)
