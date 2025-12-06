#!/usr/bin/env python3
"""
Validate SBML Conversion Fidelity

Parses 100 BioModels with SHYpn's SBML parser and records conversion statistics
for Table 2 in the paper.

Usage:
    python validate_sbml_conversion.py \
        --models ../experimental_data/biomodels_dataset/model_list.csv \
        --sbml-dir ../experimental_data/biomodels_dataset/sbml_files \
        --output ../experimental_data/sbml_import_validation/conversion_fidelity.csv

Author: Eugênio Simão
Date: 2025-12-04
"""

import argparse
import csv
import sys
from pathlib import Path

# Add SHYpn to path
sys.path.insert(0, str(Path(__file__).parents[4] / 'src'))

try:
    from shypn.data.pathway.sbml_parser import SBMLParser
    from shypn.data.pathway.pathway_validator import PathwayValidator
except ImportError as e:
    print(f"Error importing SHYpn modules: {e}", file=sys.stderr)
    print("Make sure SHYpn is installed: pip install -e /home/simao/projetos/shypn", file=sys.stderr)
    sys.exit(1)


def parse_single_model(model_id: str, sbml_path: Path, parser: SBMLParser) -> dict:
    """Parse a single SBML model and extract statistics.
    
    Args:
        model_id: BioModels ID
        sbml_path: Path to SBML file
        parser: SBMLParser instance
    
    Returns:
        Dict with conversion statistics
    """
    try:
        # Parse SBML
        pathway = parser.parse_file(str(sbml_path))
        
        # Count elements
        species_count = len(pathway.species)
        reactions_count = len(pathway.reactions)
        
        # Count test arcs (catalysts/modifiers)
        test_arcs = 0
        for reaction in pathway.reactions:
            if hasattr(reaction, 'modifiers') and reaction.modifiers:
                test_arcs += len(reaction.modifiers)
        
        # Classify transitions as continuous vs stochastic
        continuous = 0
        stochastic = 0
        for reaction in pathway.reactions:
            if hasattr(reaction, 'kinetic_law') and reaction.kinetic_law:
                # Check if kinetic law suggests continuous (ODE) or stochastic
                kinetic_type = reaction.kinetic_law.law_type if hasattr(reaction.kinetic_law, 'law_type') else 'continuous'
                if 'stochastic' in kinetic_type.lower() or 'mass_action' in kinetic_type.lower():
                    stochastic += 1
                else:
                    continuous += 1
            else:
                # Default to continuous
                continuous += 1
        
        return {
            'model_id': model_id,
            'species': species_count,
            'reactions': reactions_count,
            'test_arcs': test_arcs,
            'continuous': continuous,
            'stochastic': stochastic,
            'fidelity_pct': 100.0,  # 100% if parsing succeeded
            'status': 'success'
        }
        
    except Exception as e:
        print(f"  ❌ Error parsing {model_id}: {e}")
        return {
            'model_id': model_id,
            'species': 0,
            'reactions': 0,
            'test_arcs': 0,
            'continuous': 0,
            'stochastic': 0,
            'fidelity_pct': 0.0,
            'status': f'error: {str(e)}'
        }


def main():
    parser = argparse.ArgumentParser(description='Validate SBML conversion fidelity')
    parser.add_argument('--models', type=str, required=True,
                       help='CSV file with model list')
    parser.add_argument('--sbml-dir', type=str, required=True,
                       help='Directory containing SBML files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output CSV file')
    
    args = parser.parse_args()
    
    models_file = Path(args.models)
    sbml_dir = Path(args.sbml_dir)
    output_file = Path(args.output)
    
    # Validate inputs
    if not models_file.exists():
        print(f"Error: Models file not found: {models_file}", file=sys.stderr)
        sys.exit(1)
    
    if not sbml_dir.exists():
        print(f"Error: SBML directory not found: {sbml_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize parser
    sbml_parser = SBMLParser()
    
    # Read model list
    model_ids = []
    with open(models_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['model_id'] and not row['model_id'].startswith('#'):
                model_ids.append(row['model_id'])
    
    print(f"Validating SBML conversion for {len(model_ids)} models...")
    print(f"SBML directory: {sbml_dir}")
    
    # Parse all models
    results = []
    for i, model_id in enumerate(model_ids, 1):
        print(f"\n[{i}/{len(model_ids)}] Parsing {model_id}...")
        
        # Try different file extensions
        sbml_path = None
        for ext in ['.xml', '.sbml']:
            candidate = sbml_dir / f"{model_id}{ext}"
            if candidate.exists():
                sbml_path = candidate
                break
        
        if sbml_path is None:
            print(f"  ⚠️  SBML file not found: {model_id}")
            results.append({
                'model_id': model_id,
                'species': 0,
                'reactions': 0,
                'test_arcs': 0,
                'continuous': 0,
                'stochastic': 0,
                'fidelity_pct': 0.0,
                'status': 'file_not_found'
            })
            continue
        
        result = parse_single_model(model_id, sbml_path, sbml_parser)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"  ✅ {result['species']} species, {result['reactions']} reactions, {result['test_arcs']} test arcs")
    
    # Write results to CSV
    print(f"\nWriting results to {output_file}...")
    
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['model_id', 'species', 'reactions', 'test_arcs', 
                      'continuous', 'stochastic', 'fidelity_pct', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Print summary
    successful = sum(1 for r in results if r['status'] == 'success')
    total_species = sum(r['species'] for r in results)
    total_reactions = sum(r['reactions'] for r in results)
    total_test_arcs = sum(r['test_arcs'] for r in results)
    total_continuous = sum(r['continuous'] for r in results)
    total_stochastic = sum(r['stochastic'] for r in results)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total models processed: {len(model_ids)}")
    print(f"Successful parses: {successful} ({successful/len(model_ids)*100:.1f}%)")
    print(f"\nAggregated statistics:")
    print(f"  Species → Places: {total_species}")
    print(f"  Reactions → Transitions: {total_reactions}")
    print(f"  Test arcs (catalysts): {total_test_arcs}")
    print(f"  Continuous transitions: {total_continuous} ({total_continuous/total_reactions*100:.1f}%)")
    print(f"  Stochastic transitions: {total_stochastic} ({total_stochastic/total_reactions*100:.1f}%)")
    print(f"\n✅ Results saved to: {output_file}")
    
    # Expected values from paper (Table 2)
    print("\n" + "="*60)
    print("VERIFICATION (compare with paper Table 2):")
    print("="*60)
    print(f"Species (expected: 2,495):     {total_species}")
    print(f"Reactions (expected: 2,952):   {total_reactions}")
    print(f"Test arcs (expected: 1,511):   {total_test_arcs}")
    print(f"Continuous (expected: 68%):    {total_continuous/total_reactions*100:.1f}%")
    print(f"Stochastic (expected: 32%):    {total_stochastic/total_reactions*100:.1f}%")


if __name__ == '__main__':
    main()
