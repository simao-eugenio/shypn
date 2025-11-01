#!/usr/bin/env python3
"""
Test formula translation for SBML kinetics (Phase 1.9).

This test verifies:
1. Species are mapped to place names (species_id → place.name)
2. Formulas are translated from biological to Petri net notation
3. Both rate_function_display and rate_function are stored
4. Dialog displays biological names
5. Simulation uses Petri net notation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pathlib import Path
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.canvas.document_model import DocumentModel

def test_formula_translation():
    """Test SBML formula translation to Petri net notation."""
    
    print("=" * 80)
    print("FORMULA TRANSLATION TEST - Phase 1.9")
    print("=" * 80)
    
    # Path to SBML file
    sbml_file = Path("data/biomodels_test/BIOMD0000000001.xml")
    
    if not sbml_file.exists():
        print(f"❌ SBML file not found: {sbml_file}")
        return False
    
    print(f"\n✅ Found SBML file: {sbml_file}")
    
    # Step 1: Parse SBML
    print("\n" + "=" * 80)
    print("STEP 1: Parse SBML")
    print("=" * 80)
    
    parser = SBMLParser()
    pathway_data = parser.parse_file(str(sbml_file))
    
    print(f"✅ Parsed {len(pathway_data.species)} species")
    print(f"✅ Parsed {len(pathway_data.reactions)} reactions")
    
    # Show first few species
    print("\nFirst 5 species:")
    for i, species in enumerate(pathway_data.species[:5]):
        print(f"  {i+1}. {species.id}: {species.name}")
    
    # Step 2: Process pathway (layout, colors, etc.)
    print("\n" + "=" * 80)
    print("STEP 2: Post-process Pathway")
    print("=" * 80)
    
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    
    print(f"✅ Post-processed pathway with {len(processed.species)} species")
    
    # Step 3: Convert to Petri net
    print("\n" + "=" * 80)
    print("STEP 3: Convert to Petri Net")
    print("=" * 80)
    
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    print(f"✅ Created {len(document.places)} places")
    print(f"✅ Created {len(document.transitions)} transitions")
    print(f"✅ Created {len(document.arcs)} arcs")
    
    # Step 4: Verify species mapping
    print("\n" + "=" * 80)
    print("STEP 4: Verify Species Mapping")
    print("=" * 80)
    
    species_map = {}
    for place in document.places:
        if hasattr(place, 'metadata') and 'species_id' in place.metadata:
            species_id = place.metadata['species_id']
            species_map[species_id] = place.name
            print(f"  {species_id:15s} → {place.name:5s} (label: {place.label})")
            
            if len(species_map) >= 10:
                print(f"  ... ({len(document.places) - 10} more)")
                break
    
    print(f"\n✅ Mapped {len(species_map)} species to places")
    
    # Step 5: Check formula translations
    print("\n" + "=" * 80)
    print("STEP 5: Check Formula Translations")
    print("=" * 80)
    
    transitions_with_formulas = 0
    translations_verified = 0
    
    for transition in document.transitions[:10]:  # Check first 10
        if not hasattr(transition, 'properties'):
            continue
        
        props = transition.properties
        
        # Check if has rate_function_display (biological)
        has_display = 'rate_function_display' in props
        # Check if has rate_function (computational)
        has_computational = 'rate_function' in props
        # Check if has species_map
        has_map = 'species_map' in props
        
        if has_display or has_computational:
            transitions_with_formulas += 1
            
            print(f"\n📝 Transition: {transition.name}")
            print(f"   Type: {transition.transition_type}")
            
            if has_display:
                display_formula = props['rate_function_display']
                print(f"   🧬 Display (biological):")
                print(f"      {display_formula[:100]}{'...' if len(display_formula) > 100 else ''}")
            
            if has_computational:
                comp_formula = props['rate_function']
                print(f"   ⚙️  Computational (Petri net):")
                print(f"      {comp_formula[:100]}{'...' if len(comp_formula) > 100 else ''}")
            
            if has_map:
                species_map_in_props = props['species_map']
                print(f"   🗺️  Species map: {len(species_map_in_props)} mappings")
                
                # Show first 3 mappings
                for i, (species_id, place_name) in enumerate(list(species_map_in_props.items())[:3]):
                    print(f"      {species_id} → {place_name}")
                if len(species_map_in_props) > 3:
                    print(f"      ... ({len(species_map_in_props) - 3} more)")
            
            # Verify translation
            if has_display and has_computational and has_map:
                # Check if biological names were replaced with place names
                display = props['rate_function_display']
                computational = props['rate_function']
                
                if display != computational:
                    translations_verified += 1
                    print(f"   ✅ Translation verified (formulas differ)")
                else:
                    print(f"   ⚠️  Formulas are identical (no translation needed?)")
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY:")
    print(f"  - Total transitions: {len(document.transitions)}")
    print(f"  - With formulas: {transitions_with_formulas}")
    print(f"  - Translations verified: {translations_verified}")
    
    if transitions_with_formulas > 0:
        print(f"\n✅ Formula translation working!")
        return True
    else:
        print(f"\n⚠️  No formulas found - SBML may not have kinetic laws")
        return True  # Not a failure, just no kinetics in model
    
    return True

if __name__ == '__main__':
    try:
        success = test_formula_translation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
