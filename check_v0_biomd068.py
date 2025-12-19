"""Check where V0 is defined in BIOMD0000000068"""
import sys
sys.path.insert(0, 'src')

from shypn.data.pathway.sbml_parser import SBMLParser

# Parse the model
parser = SBMLParser()
pathway = parser.parse_file('examples/biomodels/BIOMD0000000068.xml')

print("=" * 60)
print("GLOBAL PARAMETERS:")
print("=" * 60)
for param_id, value in pathway.parameters.items():
    print(f"  {param_id}: {value}")

print("\n" + "=" * 60)
print("REACTIONS AND LOCAL PARAMETERS:")
print("=" * 60)
for reaction in pathway.reactions:
    print(f"\nReaction: {reaction.id}")
    if reaction.kinetic_law:
        print(f"  Formula: {reaction.kinetic_law.formula}")
        if hasattr(reaction.kinetic_law, 'parameters') and reaction.kinetic_law.parameters:
            print(f"  Local parameters:")
            for param_id, value in reaction.kinetic_law.parameters.items():
                print(f"    {param_id}: {value}")
        else:
            print(f"  No local parameters")
            
print("\n" + "=" * 60)
print("CHECKING FOR V0 IN FORMULAS:")
print("=" * 60)
for reaction in pathway.reactions:
    if reaction.kinetic_law and 'V0' in reaction.kinetic_law.formula:
        print(f"\nReaction {reaction.id} uses V0:")
        print(f"  Formula: {reaction.kinetic_law.formula}")
        if hasattr(reaction.kinetic_law, 'parameters'):
            print(f"  Local params: {reaction.kinetic_law.parameters}")
