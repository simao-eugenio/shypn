#!/usr/bin/env python3
"""
Check mass balance analysis on BIOMD0000000061.xml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.topology.biological.mass_balance import MassBalanceAnalyzer


def main():
    sbml_path = Path("workspace/projects/My_Project/pathways/BIOMD0000000061.xml")
    
    if not sbml_path.exists():
        print(f"❌ File not found: {sbml_path}")
        return False
    
    print("=" * 80)
    print("BIOMD0000000061 - Mass Balance Analysis")
    print("=" * 80)
    
    # Import model
    print("\n📖 Importing SBML...")
    parser = SBMLParser()
    pathway = parser.parse_file(str(sbml_path))
    
    postprocessor = PathwayPostProcessor()
    processed_pathway = postprocessor.process(pathway)
    
    converter = PathwayConverter()
    document = converter.convert(processed_pathway)
    
    print(f"✓ Model imported: {len(document.places)} places, {len(document.transitions)} transitions")
    
    # Run mass balance analysis
    print("\n⚖️  Running Mass Balance Analysis...")
    analyzer = MassBalanceAnalyzer(document)
    result = analyzer.analyze()
    
    # Display results
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    
    stats = result.data['statistics']
    print(f"\nTotal transitions: {stats['total_transitions']}")
    print(f"Balanced: {stats['balanced']}")
    print(f"Unbalanced: {stats['unbalanced']}")
    print(f"Incomplete data: {stats.get('incomplete', 0)}")
    print(f"Balance rate: {stats['balance_rate']*100:.1f}%")
    
    place_formulas = result.data['place_formulas']
    print(f"\nPlaces with chemical formulas: {stats['places_with_formulas']}")
    print(f"Places without formulas: {stats['places_without_formulas']}")
    
    # Show what formulas were found
    print(f"\n{'='*80}")
    print("CHEMICAL FORMULAS FOUND")
    print(f"{'='*80}")
    
    if place_formulas:
        for place in document.places:
            if place.id in place_formulas:
                formula_dict = place_formulas[place.id]
                formula_str = ''.join([f"{elem}{count}" if count > 1 else elem 
                                      for elem, count in sorted(formula_dict.items())])
                print(f"  {place.name:20} → {formula_str}")
    else:
        print("  (No formulas found - analyzer will skip all transitions)")
    
    # Show unbalanced transitions
    unbalanced = result.data['unbalanced_transitions']
    if unbalanced:
        print(f"\n{'='*80}")
        print(f"UNBALANCED TRANSITIONS ({len(unbalanced)})")
        print(f"{'='*80}")
        
        for trans_info in unbalanced[:10]:  # Show first 10
            trans_name = trans_info['transition_name']
            imbalances = trans_info.get('imbalances', {})
            
            print(f"\n{trans_name}:")
            if imbalances:
                for element, data in imbalances.items():
                    if isinstance(data, dict):
                        diff = data.get('difference', 0)
                        input_val = data.get('input', 0)
                        output_val = data.get('output', 0)
                        print(f"  {element}: input={input_val}, output={output_val}, diff={diff:+.1f}")
            else:
                print(f"  (Cannot check - missing formulas for reactants/products)")
    else:
        print(f"\n✅ All transitions are mass-balanced!")
    
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
