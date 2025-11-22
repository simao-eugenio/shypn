#!/usr/bin/env python3
"""
Test if BIOMD0000000061.xml modifiers are converted to test arcs.
"""

from pathlib import Path
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.netobjs.test_arc import TestArc


def main():
    sbml_path = Path("workspace/projects/My_Project/pathways/BIOMD0000000061.xml")
    
    if not sbml_path.exists():
        print(f"❌ File not found: {sbml_path}")
        return False
    
    print("=" * 80)
    print("BIOMD0000000061.xml - Modifier to Test Arc Verification")
    print("=" * 80)
    
    # Parse SBML
    print("\n📖 Step 1: Parsing SBML...")
    parser = SBMLParser()
    pathway = parser.parse_file(str(sbml_path))
    
    # Check parsed modifiers
    print(f"\n📊 Parsed Pathway Data:")
    print(f"   Species: {len(pathway.species)}")
    print(f"   Reactions: {len(pathway.reactions)}")
    
    reactions_with_modifiers = [r for r in pathway.reactions if r.modifiers]
    print(f"   Reactions with modifiers: {len(reactions_with_modifiers)}")
    
    if reactions_with_modifiers:
        print(f"\n   Reactions with modifiers:")
        for reaction in reactions_with_modifiers:
            print(f"      • {reaction.id} ({reaction.name})")
            for modifier_id in reaction.modifiers:
                print(f"        - Modifier: {modifier_id}")
    
    # Convert to Petri net
    print(f"\n🔄 Step 2: Postprocessing pathway...")
    postprocessor = PathwayPostProcessor()
    processed_pathway = postprocessor.process(pathway)
    
    print(f"\n🔄 Step 3: Converting to Petri Net...")
    converter = PathwayConverter()
    document = converter.convert(processed_pathway)
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    
    print(f"\n📐 Converted Document:")
    print(f"   Places: {len(document.places)}")
    print(f"   Transitions: {len(document.transitions)}")
    print(f"   Total arcs: {len(document.arcs)}")
    print(f"   Test arcs: {len(test_arcs)}")
    
    # Check metadata
    has_test_arcs = document.metadata.get('has_test_arcs', False)
    model_type = document.metadata.get('model_type', 'Standard Petri Net')
    
    print(f"\n📋 Document Metadata:")
    print(f"   has_test_arcs: {has_test_arcs}")
    print(f"   model_type: {model_type}")
    
    # Display test arcs
    if test_arcs:
        print(f"\n✅ Test Arcs Created:")
        for i, arc in enumerate(test_arcs, 1):
            source_name = arc.source.name if hasattr(arc.source, 'name') else str(arc.source.id)
            target_name = arc.target.name if hasattr(arc.target, 'name') else str(arc.target.id)
            print(f"   {i}. {source_name} ⋯⋯◇→ {target_name}")
            print(f"      Arc ID: {arc.id}")
            print(f"      Weight: {arc.weight}")
            print(f"      Consumes tokens: {arc.consumes_tokens()}")
    else:
        print(f"\n❌ No test arcs created!")
        print(f"   Expected: 2 test arcs (G6P → vGlcTrans, AMP → vPFK)")
    
    # Verification
    print(f"\n" + "=" * 80)
    expected_modifiers = 2
    if len(test_arcs) == expected_modifiers:
        print(f"✅ SUCCESS: {len(test_arcs)} test arcs created as expected")
        return True
    else:
        print(f"⚠️ MISMATCH: Expected {expected_modifiers} test arcs, found {len(test_arcs)}")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
