"""
Test SBML Parser

Test the SBMLParser class with a simple SBML file.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser


def test_sbml_parser():
    """Test parsing a simple SBML file."""
    
    print("=" * 70)
    print("SBML Parser Test")
    print("=" * 70)
    print()
    
    # Get test file path
    test_file = Path(__file__).parent / 'simple_glycolysis.sbml'
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"Test file: {test_file.name}")
    print()
    
    try:
        # Create parser
        parser = SBMLParser()
        
        # Parse file
        print("Parsing SBML file...")
        pathway = parser.parse_file(str(test_file))
        
        print("✅ Parsing successful!")
        print()
        
        # Display results
        print("=" * 70)
        print("PATHWAY DATA")
        print("=" * 70)
        print()
        
        print(f"Model: {pathway.metadata.get('model_name')}")
        print(f"SBML Level: {pathway.metadata.get('sbml_level')}")
        print(f"SBML Version: {pathway.metadata.get('sbml_version')}")
        print()
        
        # Species
        print(f"Species ({len(pathway.species)}):")
        for species in pathway.species:
            print(f"  • {species.name}")
            print(f"    ID: {species.id}")
            print(f"    Compartment: {species.compartment}")
            print(f"    Initial concentration: {species.initial_concentration} mM")
            print()
        
        # Reactions
        print(f"Reactions ({len(pathway.reactions)}):")
        for reaction in pathway.reactions:
            print(f"  • {reaction.name}")
            print(f"    ID: {reaction.id}")
            print(f"    Reversible: {reaction.reversible}")
            
            # Reactants
            reactant_names = []
            for species_id, stoich in reaction.reactants:
                species = pathway.get_species_by_id(species_id)
                name = species.name if species else species_id
                if stoich != 1.0:
                    reactant_names.append(f"{stoich} {name}")
                else:
                    reactant_names.append(name)
            
            # Products
            product_names = []
            for species_id, stoich in reaction.products:
                species = pathway.get_species_by_id(species_id)
                name = species.name if species else species_id
                if stoich != 1.0:
                    product_names.append(f"{stoich} {name}")
                else:
                    product_names.append(name)
            
            print(f"    Equation: {' + '.join(reactant_names)} → {' + '.join(product_names)}")
            
            # Kinetics
            if reaction.kinetic_law:
                print(f"    Kinetics: {reaction.kinetic_law.rate_type}")
                print(f"    Formula: {reaction.kinetic_law.formula}")
                if reaction.kinetic_law.parameters:
                    print(f"    Parameters: {reaction.kinetic_law.parameters}")
            print()
        
        # Compartments
        if pathway.compartments:
            print(f"Compartments ({len(pathway.compartments)}):")
            for comp_id, comp_name in pathway.compartments.items():
                print(f"  • {comp_name} ({comp_id})")
            print()
        
        # Parameters
        if pathway.parameters:
            print(f"Global Parameters ({len(pathway.parameters)}):")
            for param_id, param_value in pathway.parameters.items():
                print(f"  • {param_id}: {param_value}")
            print()
        
        print("=" * 70)
        print("✅ TEST PASSED")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sbml_parser()
    sys.exit(0 if success else 1)
